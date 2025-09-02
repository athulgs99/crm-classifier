import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from config import settings

class SLATracker:
    """Track SLA compliance and send alerts"""
    
    def __init__(self):
        self.sla_thresholds = settings.SLA_THRESHOLDS
        self.manager_email = settings.MANAGER_EMAIL
    
    def check_sla_breach(self, ticket_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if ticket has breached SLA"""
        created_time = datetime.fromisoformat(ticket_data.get("created_time").replace("Z", "+00:00"))
        current_time = datetime.now(created_time.tzinfo)
        elapsed_hours = (current_time - created_time).total_seconds() / 3600
        
        priority = ticket_data.get("priority", "P3")
        threshold_hours = self.sla_thresholds.get(priority, 24)
        
        if elapsed_hours > threshold_hours:
            return {
                "breached": True,
                "ticket_number": ticket_data.get("number"),
                "priority": priority,
                "elapsed_hours": round(elapsed_hours, 2),
                "threshold_hours": threshold_hours,
                "breach_time": current_time.isoformat()
            }
        
        return None
    
    async def send_sla_alert(self, breach_info: Dict[str, Any]) -> bool:
        """Send email alert to manager about SLA breach"""
        if not all([settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD, self.manager_email]):
            print("Email configuration incomplete. Skipping SLA alert.")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_USERNAME
            msg['To'] = self.manager_email
            msg['Subject'] = f"SLA BREACH ALERT - Ticket #{breach_info['ticket_number']}"
            
            body = self._create_alert_email_body(breach_info)
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            
            text = msg.as_string()
            server.sendmail(settings.EMAIL_USERNAME, self.manager_email, text)
            server.quit()
            
            print(f"SLA alert sent for ticket #{breach_info['ticket_number']}")
            return True
            
        except Exception as e:
            print(f"Failed to send SLA alert: {e}")
            return False
    
    def _create_alert_email_body(self, breach_info: Dict[str, Any]) -> str:
        """Create email body for SLA breach alert"""
        return f"""
SLA BREACH ALERT

Ticket Details:
- Ticket Number: {breach_info['ticket_number']}
- Priority: {breach_info['priority']}
- Elapsed Time: {breach_info['elapsed_hours']} hours
- SLA Threshold: {breach_info['threshold_hours']} hours
- Breach Time: {breach_info['breach_time']}

Action Required:
This ticket has exceeded its SLA threshold. Please review and take appropriate action.

Best regards,
Ticket Agent System
        """
    
    def get_sla_status(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get current SLA status for a ticket"""
        created_time = datetime.fromisoformat(ticket_data.get("created_time").replace("Z", "+00:00"))
        current_time = datetime.now(created_time.tzinfo)
        elapsed_hours = (current_time - created_time).total_seconds() / 3600
        
        priority = ticket_data.get("priority", "P3")
        threshold_hours = self.sla_thresholds.get(priority, 24)
        
        return {
            "ticket_number": ticket_data.get("number"),
            "priority": priority,
            "elapsed_hours": round(elapsed_hours, 2),
            "threshold_hours": threshold_hours,
            "remaining_hours": max(0, threshold_hours - elapsed_hours),
            "status": "breached" if elapsed_hours > threshold_hours else "within_sla"
        }
