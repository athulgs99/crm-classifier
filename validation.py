import re
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from logging_config import log_validation_event, log_error

@dataclass
class ValidationError:
    field: str
    message: str
    code: str

class TicketValidator:
    """Comprehensive validation for ticket data"""
    
    # Configuration
    MAX_DESCRIPTION_LENGTH = 10000
    MAX_TITLE_LENGTH = 200
    MAX_COMMENTS_COUNT = 1000
    MAX_LABELS_COUNT = 20
    
    # Required fields for a valid ticket
    REQUIRED_FIELDS = ["number", "title", "description", "created_time", "state"]
    
    # Field type definitions
    FIELD_TYPES = {
        "number": int,
        "title": str,
        "description": str,
        "priority": str,
        "owner": str,
        "created_time": str,
        "updated_time": str,
        "state": str,
        "comments_count": int,
        "labels": list
    }
    
    def __init__(self):
        self.processed_tickets = set()  # Track processed ticket IDs for duplicate detection
    
    def validate_ticket(self, ticket_data: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
        """Validate ticket data comprehensively"""
        errors = []
        
        ticket_number = ticket_data.get("number", "unknown")
        
        # Check for missing required fields
        missing_errors = self._validate_required_fields(ticket_data)
        errors.extend(missing_errors)
        
        # Validate data types
        type_errors = self._validate_data_types(ticket_data)
        errors.extend(type_errors)
        
        # Validate payload sizes
        size_errors = self._validate_payload_sizes(ticket_data)
        errors.extend(size_errors)
        
        # Check for duplicate processing
        duplicate_errors = self._check_duplicate_processing(ticket_data)
        errors.extend(duplicate_errors)
        
        # Validate specific field formats
        format_errors = self._validate_field_formats(ticket_data)
        errors.extend(format_errors)
        
        # Log validation results
        if errors:
            log_validation_event("FAILED", ticket_number, f"Found {len(errors)} validation errors", "WARNING")
            for error in errors:
                log_validation_event("ERROR_DETAIL", ticket_number, f"{error.field}: {error.message}", "WARNING")
        else:
            log_validation_event("SUCCESS", ticket_number, "All validations passed", "INFO")
        
        return len(errors) == 0, errors
    
    def _validate_required_fields(self, ticket_data: Dict[str, Any]) -> List[ValidationError]:
        """Check for missing required fields"""
        errors = []
        
        for field in self.REQUIRED_FIELDS:
            if field not in ticket_data or ticket_data[field] is None:
                errors.append(ValidationError(
                    field=field,
                    message=f"Required field '{field}' is missing",
                    code="MISSING_REQUIRED_FIELD"
                ))
            elif isinstance(ticket_data[field], str) and not ticket_data[field].strip():
                errors.append(ValidationError(
                    field=field,
                    message=f"Required field '{field}' cannot be empty",
                    code="EMPTY_REQUIRED_FIELD"
                ))
        
        return errors
    
    def _validate_data_types(self, ticket_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate data types for all fields"""
        errors = []
        
        for field, expected_type in self.FIELD_TYPES.items():
            if field in ticket_data and ticket_data[field] is not None:
                try:
                    if expected_type == int:
                        # Handle string numbers
                        if isinstance(ticket_data[field], str):
                            ticket_data[field] = int(ticket_data[field])
                        elif not isinstance(ticket_data[field], int):
                            raise ValueError(f"Expected int, got {type(ticket_data[field])}")
                    
                    elif expected_type == str:
                        if not isinstance(ticket_data[field], str):
                            ticket_data[field] = str(ticket_data[field])
                    
                    elif expected_type == list:
                        if not isinstance(ticket_data[field], list):
                            errors.append(ValidationError(
                                field=field,
                                message=f"Field '{field}' must be a list, got {type(ticket_data[field])}",
                                code="INVALID_DATA_TYPE"
                            ))
                
                except (ValueError, TypeError) as e:
                    errors.append(ValidationError(
                        field=field,
                        message=f"Invalid data type for '{field}': {str(e)}",
                        code="INVALID_DATA_TYPE"
                    ))
        
        return errors
    
    def _validate_payload_sizes(self, ticket_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate payload sizes to prevent oversized data"""
        errors = []
        
        # Check description length
        if "description" in ticket_data and ticket_data["description"]:
            if len(ticket_data["description"]) > self.MAX_DESCRIPTION_LENGTH:
                errors.append(ValidationError(
                    field="description",
                    message=f"Description too long ({len(ticket_data['description'])} chars). Max allowed: {self.MAX_DESCRIPTION_LENGTH}",
                    code="PAYLOAD_TOO_LARGE"
                ))
        
        # Check title length
        if "title" in ticket_data and ticket_data["title"]:
            if len(ticket_data["title"]) > self.MAX_TITLE_LENGTH:
                errors.append(ValidationError(
                    field="title",
                    message=f"Title too long ({len(ticket_data['title'])} chars). Max allowed: {self.MAX_TITLE_LENGTH}",
                    code="PAYLOAD_TOO_LARGE"
                ))
        
        # Check comments count
        if "comments_count" in ticket_data and ticket_data["comments_count"]:
            if ticket_data["comments_count"] > self.MAX_COMMENTS_COUNT:
                errors.append(ValidationError(
                    field="comments_count",
                    message=f"Comments count too high ({ticket_data['comments_count']}). Max allowed: {self.MAX_COMMENTS_COUNT}",
                    code="PAYLOAD_TOO_LARGE"
                ))
        
        # Check labels count
        if "labels" in ticket_data and ticket_data["labels"]:
            if len(ticket_data["labels"]) > self.MAX_LABELS_COUNT:
                errors.append(ValidationError(
                    field="labels",
                    message=f"Too many labels ({len(ticket_data['labels'])}). Max allowed: {self.MAX_LABELS_COUNT}",
                    code="PAYLOAD_TOO_LARGE"
                ))
        
        return errors
    
    def _check_duplicate_processing(self, ticket_data: Dict[str, Any]) -> List[ValidationError]:
        """Check if ticket has already been processed"""
        errors = []
        
        ticket_number = ticket_data.get("number")
        if ticket_number is not None:
            if ticket_number in self.processed_tickets:
                errors.append(ValidationError(
                    field="number",
                    message=f"Ticket #{ticket_number} has already been processed in this session",
                    code="DUPLICATE_REQUEST"
                ))
        
        return errors
    
    def _validate_field_formats(self, ticket_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate specific field formats"""
        errors = []
        
        # Validate priority format
        if "priority" in ticket_data and ticket_data["priority"]:
            valid_priorities = ["P1", "P2", "P3", "P4"]
            if ticket_data["priority"] not in valid_priorities:
                errors.append(ValidationError(
                    field="priority",
                    message=f"Invalid priority '{ticket_data['priority']}'. Must be one of: {valid_priorities}",
                    code="INVALID_FORMAT"
                ))
        
        # Validate state format
        if "state" in ticket_data and ticket_data["state"]:
            valid_states = ["open", "closed", "reopened"]
            if ticket_data["state"].lower() not in valid_states:
                errors.append(ValidationError(
                    field="state",
                    message=f"Invalid state '{ticket_data['state']}'. Must be one of: {valid_states}",
                    code="INVALID_FORMAT"
                ))
        
        # Validate date formats
        for date_field in ["created_time", "updated_time"]:
            if date_field in ticket_data and ticket_data[date_field]:
                if not self._is_valid_date_format(ticket_data[date_field]):
                    errors.append(ValidationError(
                        field=date_field,
                        message=f"Invalid date format for '{date_field}'. Expected ISO format",
                        code="INVALID_FORMAT"
                    ))
        
        return errors
    
    def _is_valid_date_format(self, date_string: str) -> bool:
        """Check if date string is in valid ISO format"""
        try:
            datetime.fromisoformat(date_string.replace("Z", "+00:00"))
            return True
        except (ValueError, TypeError):
            return False
    
    def mark_ticket_processed(self, ticket_number: int):
        """Mark a ticket as processed to prevent duplicates"""
        self.processed_tickets.add(ticket_number)
        log_validation_event("PROCESSED", ticket_number, "Ticket marked as processed to prevent duplicates", "INFO")
    
    def get_processed_tickets(self) -> set:
        """Get list of processed ticket numbers"""
        return self.processed_tickets.copy()
    
    def clear_processed_tickets(self):
        """Clear processed tickets list"""
        count = len(self.processed_tickets)
        self.processed_tickets.clear()
        log_validation_event("CLEARED", "system", f"Cleared {count} processed tickets", "INFO")

class RequestValidator:
    """Validate API request parameters"""
    
    def validate_ticket_number(self, ticket_number: Any) -> Tuple[bool, Optional[ValidationError]]:
        """Validate ticket number parameter"""
        try:
            if isinstance(ticket_number, str):
                ticket_number = int(ticket_number)
            
            if not isinstance(ticket_number, int) or ticket_number <= 0:
                return False, ValidationError(
                    field="ticket_number",
                    message="Ticket number must be a positive integer",
                    code="INVALID_TICKET_NUMBER"
                )
            
            return True, None
            
        except (ValueError, TypeError):
            return False, ValidationError(
                field="ticket_number",
                message="Ticket number must be a valid integer",
                code="INVALID_TICKET_NUMBER"
            )
    
    def validate_limit(self, limit: Any) -> Tuple[bool, Optional[ValidationError]]:
        """Validate limit parameter"""
        try:
            if isinstance(limit, str):
                limit = int(limit)
            
            if not isinstance(limit, int) or limit <= 0 or limit > 100:
                return False, ValidationError(
                    field="limit",
                    message="Limit must be a positive integer between 1 and 100",
                    code="INVALID_LIMIT"
                )
            
            return True, None
            
        except (ValueError, TypeError):
            return False, ValidationError(
                field="limit",
                message="Limit must be a valid integer",
                code="INVALID_LIMIT"
            )

# Global validator instances
ticket_validator = TicketValidator()
request_validator = RequestValidator()
