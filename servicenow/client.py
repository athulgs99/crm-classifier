import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from config import settings
from validation import ticket_validator, ValidationError
from logging_config import log_ticket_processing, log_error

class GitHubClient:
    """Client for fetching GitHub issues as tickets"""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.repo = settings.GITHUB_REPO
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TicketAgent/1.0"
        })
    
    def get_issues(self, limit: int = 10, state: str = "open") -> List[Dict[str, Any]]:
        """Fetch recent issues from GitHub"""
        url = f"{self.base_url}/repos/{self.repo}/issues"
        params = {
            "state": state,
            "per_page": limit,
            "sort": "created",
            "direction": "desc"
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            issues = response.json()
            log_ticket_processing("batch", f"Successfully fetched {len(issues)} issues from GitHub", f"Repo: {self.repo}")
            return [self._format_issue(issue) for issue in issues]
        except Exception as e:
            log_error("GITHUB_API_ERROR", f"Failed to fetch issues from {self.repo}", e)
            return []
    
    def get_issue_by_number(self, issue_number: int) -> Optional[Dict[str, Any]]:
        """Fetch specific issue by number"""
        url = f"{self.base_url}/repos/{self.repo}/issues/{issue_number}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            issue = response.json()
            log_ticket_processing(issue_number, "FETCHED", f"Successfully fetched issue from GitHub")
            return self._format_issue(issue)
        except Exception as e:
            log_error("GITHUB_API_ERROR", f"Failed to fetch issue {issue_number}", e)
            return None
    
    def _format_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Format GitHub issue as ticket with validation"""
        # Map GitHub labels to priority
        priority = self._determine_priority(issue.get("labels", []))
        
        # Format ticket data
        ticket_data = {
            "number": issue.get("number"),
            "title": issue.get("title", ""),
            "description": issue.get("body", ""),
            "priority": priority,
            "owner": issue.get("assignee", {}).get("login") if issue.get("assignee") else "Unassigned",
            "created_time": issue.get("created_at"),
            "updated_time": issue.get("updated_at"),
            "state": issue.get("state"),
            "labels": [label["name"] for label in issue.get("labels", [])],
            "comments_count": issue.get("comments", 0),
            "url": issue.get("html_url")
        }
        
        # Validate the formatted ticket data
        is_valid, errors = ticket_validator.validate_ticket(ticket_data)
        
        if not is_valid:
            # Log validation errors but don't fail completely
            ticket_number = ticket_data.get('number', 'unknown')
            log_ticket_processing(ticket_number, "VALIDATION_WARNINGS", f"Found {len(errors)} validation warnings")
            
            # Apply fixes for common issues
            ticket_data = self._apply_validation_fixes(ticket_data, errors)
        
        return ticket_data
    
    def _apply_validation_fixes(self, ticket_data: Dict[str, Any], errors: List[ValidationError]) -> Dict[str, Any]:
        """Apply automatic fixes for validation errors"""
        fixed_data = ticket_data.copy()
        
        for error in errors:
            if error.code == "PAYLOAD_TOO_LARGE":
                if error.field == "description":
                    # Truncate description if too long
                    max_length = ticket_validator.MAX_DESCRIPTION_LENGTH
                    fixed_data["description"] = fixed_data["description"][:max_length] + "..."
                elif error.field == "title":
                    # Truncate title if too long
                    max_length = ticket_validator.MAX_TITLE_LENGTH
                    fixed_data["title"] = fixed_data["title"][:max_length] + "..."
            
            elif error.code == "EMPTY_REQUIRED_FIELD":
                if error.field == "description":
                    fixed_data["description"] = "No description provided"
                elif error.field == "title":
                    fixed_data["title"] = "Untitled Issue"
            
            elif error.code == "INVALID_DATA_TYPE":
                if error.field == "number" and isinstance(fixed_data["number"], str):
                    try:
                        fixed_data["number"] = int(fixed_data["number"])
                    except (ValueError, TypeError):
                        fixed_data["number"] = 0
                elif error.field == "comments_count" and isinstance(fixed_data["comments_count"], str):
                    try:
                        fixed_data["comments_count"] = int(fixed_data["comments_count"])
                    except (ValueError, TypeError):
                        fixed_data["comments_count"] = 0
        
        return fixed_data
    
    def _determine_priority(self, labels: List[Dict[str, Any]]) -> str:
        """Determine priority based on GitHub labels"""
        label_names = [label["name"].lower() for label in labels]
        
        if any(label in ["critical", "urgent", "p1", "high-priority"] for label in label_names):
            return "P1"
        elif any(label in ["high", "p2", "important"] for label in label_names):
            return "P2"
        elif any(label in ["low", "p4", "minor"] for label in label_names):
            return "P4"
        else:
            return "P3"  # Default priority
