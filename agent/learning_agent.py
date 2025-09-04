"""
Learning Agent for ServiceNow Ticket Agent.
Analyzes responses, learns from patterns, and improves over time.
"""

import json
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import asyncio
from .base_agent import BaseAgent
from logging_config import get_main_logger


class LearningAgent(BaseAgent):
    """Agent that learns from responses and improves decision making."""
    
    def __init__(self, agent_id: str = "learning_agent_001"):
        super().__init__(agent_id, "learning")
        self.logger = get_main_logger()
        
        # Learning data structures
        self.response_patterns = defaultdict(list)
        self.success_metrics = defaultdict(list)
        self.error_patterns = defaultdict(int)
        self.learning_history = []
        
        # Learning parameters
        self.min_samples_for_learning = 10
        self.learning_threshold = 0.7
        self.pattern_memory_size = 1000
        
        # Performance tracking
        self.accuracy_history = []
        self.improvement_rate = 0.0
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and apply learned patterns."""
        start_time = time.time()
        
        try:
            # Analyze input for patterns
            input_pattern = self._extract_pattern(input_data)
            
            # Apply learned knowledge
            learned_response = await self._apply_learned_knowledge(input_pattern)
            
            # Generate response with learning insights
            response = {
                "response": learned_response,
                "confidence": self._calculate_confidence(input_pattern),
                "learning_applied": True,
                "patterns_used": len(self.response_patterns.get(input_pattern, [])),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Update metrics
            await self.update_metrics(time.time() - start_time, True)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Learning agent processing failed: {e}")
            await self.update_metrics(time.time() - start_time, False)
            raise
    
    async def learn(self, input_data: Dict[str, Any], response: Dict[str, Any], 
                   feedback: Optional[Dict[str, Any]] = None) -> bool:
        """Learn from input, response, and feedback."""
        try:
            # Extract patterns from input
            input_pattern = self._extract_pattern(input_data)
            
            # Record learning data
            learning_entry = {
                "timestamp": datetime.utcnow(),
                "input_pattern": input_pattern,
                "response": response,
                "feedback": feedback,
                "success": feedback.get("success", True) if feedback else True
            }
            
            # Store in learning history
            self.learning_history.append(learning_entry)
            
            # Update pattern database
            self._update_patterns(input_pattern, response, feedback)
            
            # Update success metrics
            self._update_success_metrics(input_pattern, feedback)
            
            # Clean up old data
            self._cleanup_old_data()
            
            # Calculate improvement rate
            self._calculate_improvement_rate()
            
            self.logger.info(f"Learning agent learned from {input_pattern} pattern")
            return True
            
        except Exception as e:
            self.logger.error(f"Learning failed: {e}")
            return False
    
    def _extract_pattern(self, input_data: Dict[str, Any]) -> str:
        """Extract key patterns from input data."""
        # Extract ticket type, priority, labels, etc.
        ticket_type = input_data.get("type", "unknown")
        priority = input_data.get("priority", "unknown")
        labels = input_data.get("labels", [])
        
        # Create pattern key
        pattern_key = f"{ticket_type}:{priority}:{','.join(sorted(labels))}"
        return pattern_key
    
    async def _apply_learned_knowledge(self, pattern: str) -> Dict[str, Any]:
        """Apply learned knowledge to generate response."""
        if pattern in self.response_patterns:
            # Get most successful responses for this pattern
            successful_responses = [
                resp for resp in self.response_patterns[pattern]
                if resp.get("success_rate", 0) > self.learning_threshold
            ]
            
            if successful_responses:
                # Return the most successful response
                best_response = max(successful_responses, 
                                 key=lambda x: x.get("success_rate", 0))
                return best_response.get("response", {})
        
        # Fallback to default response
        return {"message": "No learned pattern available", "pattern": pattern}
    
    def _calculate_confidence(self, pattern: str) -> float:
        """Calculate confidence level for a pattern."""
        if pattern not in self.response_patterns:
            return 0.0
        
        responses = self.response_patterns[pattern]
        if not responses:
            return 0.0
        
        # Calculate average success rate
        success_rates = [resp.get("success_rate", 0) for resp in responses]
        return sum(success_rates) / len(success_rates)
    
    def _update_patterns(self, pattern: str, response: Dict[str, Any], 
                        feedback: Optional[Dict[str, Any]] = None):
        """Update pattern database with new information."""
        success_rate = feedback.get("success_rate", 0.5) if feedback else 0.5
        
        pattern_entry = {
            "response": response,
            "success_rate": success_rate,
            "usage_count": 1,
            "last_used": datetime.utcnow(),
            "feedback_count": 1 if feedback else 0
        }
        
        # Check if pattern already exists
        existing_patterns = self.response_patterns[pattern]
        for i, existing in enumerate(existing_patterns):
            if existing.get("response") == response:
                # Update existing pattern
                existing["usage_count"] += 1
                existing["last_used"] = datetime.utcnow()
                existing["success_rate"] = (existing["success_rate"] + success_rate) / 2
                if feedback:
                    existing["feedback_count"] += 1
                return
        
        # Add new pattern
        self.response_patterns[pattern].append(pattern_entry)
    
    def _update_success_metrics(self, pattern: str, feedback: Optional[Dict[str, Any]] = None):
        """Update success metrics for patterns."""
        if not feedback:
            return
        
        success = feedback.get("success", True)
        self.success_metrics[pattern].append({
            "timestamp": datetime.utcnow(),
            "success": success,
            "feedback_score": feedback.get("score", 0)
        })
    
    def _cleanup_old_data(self):
        """Clean up old learning data to prevent memory bloat."""
        cutoff_time = datetime.utcnow() - timedelta(days=30)
        
        # Clean learning history
        self.learning_history = [
            entry for entry in self.learning_history
            if entry["timestamp"] > cutoff_time
        ]
        
        # Clean old patterns
        for pattern in list(self.response_patterns.keys()):
            self.response_patterns[pattern] = [
                resp for resp in self.response_patterns[pattern]
                if resp["last_used"] > cutoff_time
            ]
            
            # Remove empty patterns
            if not self.response_patterns[pattern]:
                del self.response_patterns[pattern]
    
    def _calculate_improvement_rate(self):
        """Calculate how much the agent is improving over time."""
        if len(self.accuracy_history) < 2:
            return
        
        recent_accuracy = self.accuracy_history[-10:] if len(self.accuracy_history) >= 10 else self.accuracy_history
        if len(recent_accuracy) >= 2:
            self.improvement_rate = recent_accuracy[-1] - recent_accuracy[0]
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics."""
        total_patterns = sum(len(patterns) for patterns in self.response_patterns.values())
        unique_patterns = len(self.response_patterns)
        
        return {
            "total_patterns_learned": total_patterns,
            "unique_pattern_types": unique_patterns,
            "learning_history_size": len(self.learning_history),
            "improvement_rate": self.improvement_rate,
            "accuracy_history": self.accuracy_history[-20:],  # Last 20 entries
            "most_common_patterns": self._get_top_patterns(5),
            "learning_efficiency": self._calculate_learning_efficiency()
        }
    
    def _get_top_patterns(self, limit: int) -> List[Tuple[str, int]]:
        """Get top patterns by usage count."""
        pattern_usage = {}
        for pattern, responses in self.response_patterns.items():
            total_usage = sum(resp.get("usage_count", 0) for resp in responses)
            pattern_usage[pattern] = total_usage
        
        return sorted(pattern_usage.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def _calculate_learning_efficiency(self) -> float:
        """Calculate learning efficiency based on success rates."""
        if not self.response_patterns:
            return 0.0
        
        total_efficiency = 0.0
        pattern_count = 0
        
        for pattern, responses in self.response_patterns.items():
            if responses:
                avg_success = sum(resp.get("success_rate", 0) for resp in responses) / len(responses)
                total_efficiency += avg_success
                pattern_count += 1
        
        return total_efficiency / pattern_count if pattern_count > 0 else 0.0
    
    def export_knowledge(self) -> Dict[str, Any]:
        """Export learned knowledge for backup or transfer."""
        return {
            "agent_id": self.agent_id,
            "export_timestamp": datetime.utcnow().isoformat(),
            "response_patterns": dict(self.response_patterns),
            "success_metrics": dict(self.success_metrics),
            "learning_history": [
                {
                    "timestamp": entry["timestamp"].isoformat(),
                    "input_pattern": entry["input_pattern"],
                    "response": entry["response"],
                    "feedback": entry["feedback"],
                    "success": entry["success"]
                }
                for entry in self.learning_history
            ]
        }
    
    def import_knowledge(self, knowledge_data: Dict[str, Any]) -> bool:
        """Import knowledge from exported data."""
        try:
            if knowledge_data.get("agent_id") != self.agent_id:
                self.logger.warning("Importing knowledge from different agent")
            
            # Import patterns
            for pattern, responses in knowledge_data.get("response_patterns", {}).items():
                self.response_patterns[pattern] = responses
            
            # Import metrics
            for pattern, metrics in knowledge_data.get("success_metrics", {}).items():
                self.success_metrics[pattern] = metrics
            
            # Import history
            for entry in knowledge_data.get("learning_history", []):
                entry["timestamp"] = datetime.fromisoformat(entry["timestamp"])
                self.learning_history.append(entry)
            
            self.logger.info("Knowledge imported successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Knowledge import failed: {e}")
            return False
