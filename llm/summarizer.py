import openai
import anthropic
from typing import Dict, Any, Optional
from config import settings

class TicketSummarizer:
    """Summarize tickets and suggest next steps"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
            self.openai_client = openai
        elif settings.ANTHROPIC_API_KEY:
            self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    async def summarize_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize ticket and suggest next steps"""
        prompt = self._create_summary_prompt(ticket_data)
        
        if self.openai_client:
            return await self._summarize_with_openai(prompt)
        elif self.anthropic_client:
            return await self._summarize_with_anthropic(prompt)
        else:
            return self._generate_fallback_summary(ticket_data)
    
    def _create_summary_prompt(self, ticket_data: Dict[str, Any]) -> str:
        """Create prompt for ticket summarization"""
        return f"""
        Please analyze this IT support ticket and provide a concise summary with next steps.
        
        Ticket Details:
        - Number: {ticket_data.get("number")}
        - Title: {ticket_data.get("title")}
        - Priority: {ticket_data.get("priority")}
        - Owner: {ticket_data.get("owner")}
        - Created: {ticket_data.get("created_time")}
        - Description: {ticket_data.get("description", "No description provided")}
        
        Please provide:
        1. **Issue Summary** (2-3 sentences)
        2. **Root Cause Analysis** (if apparent)
        3. **Suggested Next Steps** (3-5 actionable items)
        4. **Estimated Resolution Time** (if possible)
        5. **Priority Assessment** (confirm if current priority is appropriate)
        
        Format the response as JSON with keys: summary, root_cause, next_steps, eta, priority_assessment
        """
    
    async def _summarize_with_openai(self, prompt: str) -> Dict[str, Any]:
        """Summarize using OpenAI"""
        try:
            response = self.openai_client.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful IT support analyst. Provide clear, actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return self._parse_summary_response(response.choices[0].message.content)
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._generate_fallback_summary({})
    
    async def _summarize_with_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Summarize using Anthropic Claude"""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return self._parse_summary_response(response.content[0].text)
        except Exception as e:
            print(f"Anthropic API error: {e}")
            return self._generate_fallback_summary({})
    
    def _parse_summary_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        try:
            import json
            return json.loads(response_text)
        except:
            return self._generate_fallback_summary({})
    
    def _generate_fallback_summary(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback summary when LLM is unavailable"""
        return {
            "summary": f"Issue logged: {ticket_data.get("title", "Technical issue")}",
            "root_cause": "Requires investigation",
            "next_steps": [
                "Review ticket details",
                "Contact user if additional information needed",
                "Update ticket status",
                "Assign to appropriate team member"
            ],
            "eta": "24-48 hours",
            "priority_assessment": "Review required"
        }
