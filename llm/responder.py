import openai
import anthropic
from typing import Dict, Any
from config import settings

class ResponseGenerator:
    """Generate professional yet friendly responses for tickets"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
            self.openai_client = openai
        elif settings.ANTHROPIC_API_KEY:
            self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    async def generate_response(self, ticket_data: Dict[str, Any], summary: Dict[str, Any]) -> str:
        """Generate professional yet friendly response"""
        prompt = self._create_response_prompt(ticket_data, summary)
        
        if self.openai_client:
            return await self._generate_with_openai(prompt)
        elif self.anthropic_client:
            return await self._generate_with_anthropic(prompt)
        else:
            return self._generate_fallback_response(ticket_data, summary)
    
    def _create_response_prompt(self, ticket_data: Dict[str, Any], summary: Dict[str, Any]) -> str:
        """Create prompt for response generation"""
        return f"""
        Generate a professional yet friendly response for this IT support ticket.
        
        Ticket: {ticket_data.get("number")} - {ticket_data.get("title")}
        Priority: {ticket_data.get("priority")}
        
        Summary: {summary.get("summary", "Issue logged for investigation")}
        Next Steps: {", ".join(summary.get("next_steps", []))}
        ETA: {summary.get("eta", "24-48 hours")}
        
        Requirements:
        - Professional yet friendly tone
        - Acknowledge the issue
        - Provide clear next steps
        - Include ETA if available
        - Keep it concise (2-3 paragraphs max)
        - End with a professional closing
        
        Format as a complete email response.
        """
    
    async def _generate_with_openai(self, prompt: str) -> str:
        """Generate response using OpenAI"""
        try:
            response = self.openai_client.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional IT support representative. Write clear, helpful responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._generate_fallback_response({}, {})
    
    async def _generate_with_anthropic(self, prompt: str) -> str:
        """Generate response using Anthropic Claude"""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Anthropic API error: {e}")
            return self._generate_fallback_response({}, {})
    
    def _generate_fallback_response(self, ticket_data: Dict[str, Any], summary: Dict[str, Any]) -> str:
        """Fallback response template"""
        return f"""
        Dear User,

        Thank you for reporting this issue (Ticket #{ticket_data.get("number", "N/A")}). We have successfully logged your request and our technical team has been notified.

        **Issue Summary:**
        {summary.get("summary", "Your issue has been documented and is under investigation.")}

        **Next Steps:**
        {", ".join(summary.get("next_steps", ["Our team will investigate the issue", "We will provide updates as we progress", "You will be notified of any significant developments"]))}

        **Estimated Resolution Time:** {summary.get("eta", "24-48 hours")}

        We appreciate your patience and will keep you updated on our progress. If you have any additional information that might help us resolve this issue faster, please don't hesitate to reply to this ticket.

        Best regards,
        IT Support Team
        """
