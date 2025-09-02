from typing import Dict, Any, List
from datetime import datetime
import json

class SessionManager:
    """Manage session-based ticket history"""
    
    def __init__(self):
        self.session_history: List[Dict[str, Any]] = []
    
    def add_ticket_to_history(self, ticket_data: Dict[str, Any], summary: Dict[str, Any], response: str, sla_status: Dict[str, Any]):
        """Add processed ticket to session history with duplicate detection"""
        ticket_number = ticket_data.get("number")
        
        # Check if ticket already exists in history
        existing_entry = self.get_ticket_by_number(ticket_number)
        if existing_entry:
            # Update existing entry instead of creating duplicate
            existing_entry.update({
                "timestamp": datetime.now().isoformat(),
                "summary": summary,
                "response": response,
                "sla_status": sla_status,
                "processed": True,
                "updated": True
            })
            print(f"Updated existing ticket #{ticket_number} in session history")
        else:
            # Add new entry
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "ticket_data": ticket_data,
                "summary": summary,
                "response": response,
                "sla_status": sla_status,
                "processed": True,
                "updated": False
            }
            
            self.session_history.append(history_entry)
            print(f"Added ticket #{ticket_number} to session history")
    
    def get_session_history(self) -> List[Dict[str, Any]]:
        """Get all tickets in current session"""
        return self.session_history
    
    def search_history(self, query: str) -> List[Dict[str, Any]]:
        """Search session history by ticket number or title"""
        query = query.lower()
        results = []
        
        for entry in self.session_history:
            ticket = entry.get("ticket_data", {})
            if (query in str(ticket.get("number", "")).lower() or 
                query in ticket.get("title", "").lower() or
                query in ticket.get("description", "").lower()):
                results.append(entry)
        
        return results
    
    def get_ticket_by_number(self, ticket_number: Any) -> Dict[str, Any]:
        """Get specific ticket from session history"""
        # Convert ticket_number to int for comparison
        try:
            if isinstance(ticket_number, str):
                ticket_number = int(ticket_number)
        except (ValueError, TypeError):
            return {}
        
        for entry in self.session_history:
            entry_number = entry.get("ticket_data", {}).get("number")
            if entry_number == ticket_number:
                return entry
        return {}
    
    def clear_history(self):
        """Clear session history"""
        self.session_history = []
        print("Session history cleared")
    
    def export_history(self) -> str:
        """Export session history as JSON"""
        return json.dumps(self.session_history, indent=2, default=str)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        if not self.session_history:
            return {"total_tickets": 0, "breached_sla": 0, "avg_processing_time": 0}
        
        breached_count = sum(1 for entry in self.session_history 
                           if entry.get("sla_status", {}).get("status") == "breached")
        
        return {
            "total_tickets": len(self.session_history),
            "breached_sla": breached_count,
            "avg_processing_time": len(self.session_history)  # Simplified for now
        }
