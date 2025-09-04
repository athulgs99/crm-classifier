"""
Response Processor for ServiceNow Ticket Agent.
Analyzes and enhances responses using intelligent agents and learning systems.
"""

import time
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from .base_agent import BaseAgent
from .learning_agent import LearningAgent
from logging_config import get_main_logger


class ResponseProcessor(BaseAgent):
    """Agent that processes and enhances responses using learning capabilities."""
    
    def __init__(self, agent_id: str = "response_processor_001"):
        super().__init__(agent_id, "response_processor")
        self.logger = get_main_logger()
        
        # Initialize learning agent
        self.learning_agent = LearningAgent("learning_agent_001")
        
        # Response enhancement strategies
        self.enhancement_strategies = {
            "ticket_priority": self._enhance_priority_handling,
            "sla_compliance": self._enhance_sla_handling,
            "user_experience": self._enhance_user_experience,
            "technical_accuracy": self._enhance_technical_content
        }
        
        # Quality metrics
        self.quality_scores = []
        self.response_templates = {}
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and generate enhanced response."""
        start_time = time.time()
        
        try:
            # Extract base response from input
            base_response = input_data.get("response", {})
            ticket_data = input_data.get("ticket", {})
            
            # Apply learning insights
            learning_insights = await self.learning_agent.process(ticket_data)
            
            # Enhance response using multiple strategies
            enhanced_response = await self._apply_enhancement_strategies(
                base_response, ticket_data, learning_insights
            )
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(enhanced_response, ticket_data)
            
            # Add metadata
            final_response = {
                "response": enhanced_response,
                "quality_score": quality_score,
                "enhancements_applied": list(self.enhancement_strategies.keys()),
                "learning_confidence": learning_insights.get("confidence", 0.0),
                "processing_timestamp": datetime.utcnow().isoformat(),
                "processor_agent": self.agent_id
            }
            
            # Update metrics
            await self.update_metrics(time.time() - start_time, True)
            
            # Learn from this interaction
            await self._learn_from_interaction(ticket_data, final_response)
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"Response processing failed: {e}")
            await self.update_metrics(time.time() - start_time, False)
            raise
    
    async def learn(self, input_data: Dict[str, Any], response: Dict[str, Any], 
                   feedback: Optional[Dict[str, Any]] = None) -> bool:
        """Learn from response processing and feedback."""
        try:
            # Extract learning data
            ticket_data = input_data.get("ticket", {})
            quality_score = response.get("quality_score", 0.0)
            
            # Create feedback for learning agent
            learning_feedback = {
                "success": feedback.get("success", True) if feedback else True,
                "quality_score": quality_score,
                "user_satisfaction": feedback.get("user_satisfaction", 0.5) if feedback else 0.5,
                "response_time": feedback.get("response_time", 0.0) if feedback else 0.0
            }
            
            # Learn from the interaction
            await self.learning_agent.learn(ticket_data, response, learning_feedback)
            
            # Update quality metrics
            self.quality_scores.append({
                "timestamp": datetime.utcnow(),
                "quality_score": quality_score,
                "feedback": learning_feedback
            })
            
            # Keep only recent quality scores
            if len(self.quality_scores) > 100:
                self.quality_scores = self.quality_scores[-100:]
            
            self.logger.info(f"Response processor learned from interaction with quality score: {quality_score}")
            return True
            
        except Exception as e:
            self.logger.error(f"Learning failed in response processor: {e}")
            return False
    
    async def _apply_enhancement_strategies(self, base_response: Dict[str, Any], 
                                          ticket_data: Dict[str, Any], 
                                          learning_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Apply multiple enhancement strategies to the response."""
        enhanced_response = base_response.copy()
        
        # Apply each enhancement strategy
        for strategy_name, strategy_func in self.enhancement_strategies.items():
            try:
                enhanced_response = await strategy_func(enhanced_response, ticket_data, learning_insights)
            except Exception as e:
                self.logger.warning(f"Enhancement strategy {strategy_name} failed: {e}")
                continue
        
        return enhanced_response
    
    async def _enhance_priority_handling(self, response: Dict[str, Any], 
                                       ticket_data: Dict[str, Any], 
                                       learning_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance response based on ticket priority."""
        priority = ticket_data.get("priority", "medium")
        
        if priority == "high":
            # Add urgency indicators
            response["urgency"] = "immediate"
            response["escalation_required"] = True
            response["priority_handling"] = "expedited"
        elif priority == "critical":
            # Add critical handling instructions
            response["urgency"] = "critical"
            response["escalation_required"] = True
            response["priority_handling"] = "immediate_escalation"
            response["notification_channels"] = ["sms", "email", "slack"]
        
        return response
    
    async def _enhance_sla_handling(self, response: Dict[str, Any], 
                                  ticket_data: Dict[str, Any], 
                                  learning_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance response with SLA compliance information."""
        sla_status = ticket_data.get("sla_status", {})
        
        if sla_status:
            response["sla_compliance"] = {
                "status": sla_status.get("status", "unknown"),
                "breach_risk": sla_status.get("breach_risk", "low"),
                "time_remaining": sla_status.get("time_remaining", 0),
                "recommended_actions": self._get_sla_recommendations(sla_status)
            }
        
        return response
    
    async def _enhance_user_experience(self, response: Dict[str, Any], 
                                     ticket_data: Dict[str, Any], 
                                     learning_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance response for better user experience."""
        # Add user-friendly elements
        response["user_experience"] = {
            "clarity_score": self._calculate_clarity_score(response),
            "actionable_items": self._extract_actionable_items(response),
            "estimated_resolution_time": self._estimate_resolution_time(ticket_data),
            "next_steps": self._generate_next_steps(response)
        }
        
        return response
    
    async def _enhance_technical_content(self, response: Dict[str, Any], 
                                       ticket_data: Dict[str, Any], 
                                       learning_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance technical accuracy and completeness."""
        # Add technical validation
        response["technical_validation"] = {
            "completeness_score": self._calculate_completeness_score(response),
            "accuracy_indicators": self._get_accuracy_indicators(response),
            "technical_references": self._extract_technical_references(response),
            "validation_status": "pending_review"
        }
        
        return response
    
    def _get_sla_recommendations(self, sla_status: Dict[str, Any]) -> List[str]:
        """Generate SLA-specific recommendations."""
        recommendations = []
        
        if sla_status.get("breach_risk") == "high":
            recommendations.extend([
                "Immediate escalation to senior support",
                "24/7 monitoring required",
                "Customer notification of potential SLA breach"
            ])
        elif sla_status.get("breach_risk") == "medium":
            recommendations.extend([
                "Priority escalation within 2 hours",
                "Regular status updates to customer",
                "Resource allocation review"
            ])
        
        return recommendations
    
    def _calculate_clarity_score(self, response: Dict[str, Any]) -> float:
        """Calculate clarity score for the response."""
        # Simple heuristic - can be enhanced with NLP
        text_content = str(response.get("message", "")) + str(response.get("description", ""))
        
        if not text_content:
            return 0.0
        
        # Score based on length, structure, and readability
        words = text_content.split()
        sentences = text_content.split('.')
        
        if not words or not sentences:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        
        # Prefer sentences between 10-20 words
        if 10 <= avg_sentence_length <= 20:
            return 0.9
        elif 5 <= avg_sentence_length <= 25:
            return 0.7
        else:
            return 0.5
    
    def _extract_actionable_items(self, response: Dict[str, Any]) -> List[str]:
        """Extract actionable items from response."""
        actionable_items = []
        text_content = str(response.get("message", "")) + str(response.get("description", ""))
        
        # Simple keyword-based extraction
        action_keywords = ["please", "should", "must", "need to", "require", "action required"]
        
        sentences = text_content.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in action_keywords):
                actionable_items.append(sentence.strip())
        
        return actionable_items[:5]  # Limit to 5 items
    
    def _estimate_resolution_time(self, ticket_data: Dict[str, Any]) -> str:
        """Estimate resolution time based on ticket characteristics."""
        priority = ticket_data.get("priority", "medium")
        complexity = ticket_data.get("labels", [])
        
        if priority == "critical":
            return "2-4 hours"
        elif priority == "high":
            return "4-8 hours"
        elif priority == "medium":
            return "1-2 business days"
        else:
            return "3-5 business days"
    
    def _generate_next_steps(self, response: Dict[str, Any]) -> List[str]:
        """Generate next steps for the user."""
        next_steps = [
            "Review the provided information",
            "Contact support if clarification is needed",
            "Follow up on any requested actions"
        ]
        
        # Add specific steps based on response content
        if response.get("escalation_required"):
            next_steps.append("Await escalation confirmation")
        
        if response.get("sla_compliance", {}).get("breach_risk") == "high":
            next_steps.append("Monitor SLA status closely")
        
        return next_steps
    
    def _calculate_completeness_score(self, response: Dict[str, Any]) -> float:
        """Calculate completeness score for technical content."""
        required_fields = ["message", "priority", "status", "assignee"]
        present_fields = sum(1 for field in required_fields if response.get(field))
        
        return present_fields / len(required_fields)
    
    def _get_accuracy_indicators(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Get indicators of technical accuracy."""
        return {
            "data_validation": "pending",
            "technical_review": "required",
            "peer_verification": "recommended"
        }
    
    def _extract_technical_references(self, response: Dict[str, Any]) -> List[str]:
        """Extract technical references from response."""
        # This would typically use NLP to extract technical terms
        # For now, return a simple list
        return ["API documentation", "System logs", "Error codes"]
    
    def _calculate_quality_score(self, response: Dict[str, Any], ticket_data: Dict[str, Any]) -> float:
        """Calculate overall quality score for the response."""
        scores = []
        
        # Clarity score
        scores.append(self._calculate_clarity_score(response))
        
        # Completeness score
        scores.append(self._calculate_completeness_score(response))
        
        # Priority handling score
        priority_score = 1.0 if response.get("priority_handling") else 0.5
        scores.append(priority_score)
        
        # SLA handling score
        sla_score = 1.0 if response.get("sla_compliance") else 0.5
        scores.append(sla_score)
        
        # User experience score
        ux_score = 1.0 if response.get("user_experience") else 0.5
        scores.append(ux_score)
        
        # Technical validation score
        tech_score = 1.0 if response.get("technical_validation") else 0.5
        scores.append(tech_score)
        
        return sum(scores) / len(scores)
    
    async def _learn_from_interaction(self, ticket_data: Dict[str, Any], 
                                    final_response: Dict[str, Any]):
        """Learn from the current interaction."""
        # Create feedback for learning
        feedback = {
            "success": True,  # Assuming successful processing
            "quality_score": final_response.get("quality_score", 0.0),
            "user_satisfaction": 0.8,  # Default value
            "response_time": 0.0  # Will be updated by metrics
        }
        
        # Learn from this interaction
        await self.learning_agent.learn(ticket_data, final_response, feedback)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        return {
            "total_responses_processed": self.metrics["requests_processed"],
            "average_quality_score": sum(score["quality_score"] for score in self.quality_scores) / len(self.quality_scores) if self.quality_scores else 0.0,
            "quality_score_trend": [score["quality_score"] for score in self.quality_scores[-10:]],
            "enhancement_strategies": list(self.enhancement_strategies.keys()),
            "learning_agent_status": self.learning_agent.get_health_status(),
            "response_templates_count": len(self.response_templates)
        }
