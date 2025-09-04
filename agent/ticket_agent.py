"""
Ticket Agent for ServiceNow Ticket Agent.
Orchestrates learning, processing, and knowledge management for ticket handling.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from .base_agent import BaseAgent
from .learning_agent import LearningAgent
from .response_processor import ResponseProcessor
from .knowledge_base import KnowledgeBase
from logging_config import get_main_logger


class TicketAgent(BaseAgent):
    """Main agent that orchestrates ticket processing and learning."""
    
    def __init__(self, agent_id: str = "ticket_agent_001"):
        super().__init__(agent_id, "ticket_orchestrator")
        self.logger = get_main_logger()
        
        # Initialize sub-agents
        self.learning_agent = LearningAgent("learning_agent_001")
        self.response_processor = ResponseProcessor("response_processor_001")
        
        # Initialize knowledge base
        self.knowledge_base = KnowledgeBase()
        
        # Agent coordination
        self.agent_pipeline = [
            self.learning_agent,
            self.response_processor
        ]
        
        # Performance tracking
        self.pipeline_performance = {}
        self.coordination_metrics = {
            "total_coordinations": 0,
            "successful_coordinations": 0,
            "failed_coordinations": 0,
            "average_pipeline_time": 0.0
        }
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process ticket through the complete agent pipeline."""
        start_time = time.time()
        
        try:
            self.logger.info(f"Ticket agent starting processing for ticket: {input_data.get('ticket_number', 'unknown')}")
            
            # Extract ticket information
            ticket_data = input_data.get("ticket", {})
            ticket_number = ticket_data.get("number", "unknown")
            
            # Initialize processing context
            processing_context = {
                "ticket_number": ticket_number,
                "start_time": start_time,
                "pipeline_steps": [],
                "learning_insights": {},
                "enhanced_response": {},
                "quality_metrics": {}
            }
            
            # Execute agent pipeline
            final_result = await self._execute_pipeline(ticket_data, processing_context)
            
            # Calculate overall processing time
            total_time = time.time() - start_time
            
            # Update coordination metrics
            await self._update_coordination_metrics(total_time, True)
            
            # Store learning data in knowledge base
            await self._store_learning_data(ticket_data, final_result, processing_context)
            
            # Generate comprehensive response
            comprehensive_response = {
                "ticket_number": ticket_number,
                "processing_result": final_result,
                "pipeline_performance": processing_context["pipeline_steps"],
                "learning_insights": processing_context["learning_insights"],
                "quality_metrics": processing_context["quality_metrics"],
                "processing_time": total_time,
                "orchestrator_agent": self.agent_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Ticket agent completed processing in {total_time:.3f}s")
            return comprehensive_response
            
        except Exception as e:
            total_time = time.time() - start_time
            await self._update_coordination_metrics(total_time, False)
            self.logger.error(f"Ticket agent processing failed: {e}")
            raise
    
    async def learn(self, input_data: Dict[str, Any], response: Dict[str, Any], 
                   feedback: Optional[Dict[str, Any]] = None) -> bool:
        """Learn from the complete ticket processing experience."""
        try:
            # Extract learning components
            ticket_data = input_data.get("ticket", {})
            processing_result = response.get("processing_result", {})
            pipeline_performance = response.get("pipeline_performance", [])
            
            # Learn from each agent in the pipeline
            learning_results = []
            
            # Learning agent learning
            if self.learning_agent.is_active:
                learning_result = await self.learning_agent.learn(
                    ticket_data, processing_result, feedback
                )
                learning_results.append(("learning_agent", learning_result))
            
            # Response processor learning
            if self.response_processor.is_active:
                processor_result = await self.response_processor.learn(
                    ticket_data, processing_result, feedback
                )
                learning_results.append(("response_processor", processor_result))
            
            # Update pipeline performance metrics
            self._update_pipeline_performance(pipeline_performance)
            
            # Store coordination learning
            await self._learn_coordination_patterns(ticket_data, response, feedback)
            
            self.logger.info(f"Ticket agent learning completed: {learning_results}")
            return all(result for _, result in learning_results)
            
        except Exception as e:
            self.logger.error(f"Ticket agent learning failed: {e}")
            return False
    
    async def _execute_pipeline(self, ticket_data: Dict[str, Any], 
                               processing_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent pipeline for ticket processing."""
        current_data = ticket_data.copy()
        
        for i, agent in enumerate(self.agent_pipeline):
            if not agent.is_active:
                self.logger.warning(f"Agent {agent.agent_id} is inactive, skipping")
                continue
            
            step_start_time = time.time()
            step_name = f"step_{i+1}_{agent.agent_type}"
            
            try:
                self.logger.info(f"Executing {step_name} with agent {agent.agent_id}")
                
                # Process with current agent
                step_result = await agent.process(current_data)
                
                # Update processing context
                processing_context["pipeline_steps"].append({
                    "step": step_name,
                    "agent_id": agent.agent_id,
                    "agent_type": agent.agent_type,
                    "execution_time": time.time() - step_start_time,
                    "success": True,
                    "result": step_result
                })
                
                # Update current data for next agent
                if agent.agent_type == "learning":
                    processing_context["learning_insights"] = step_result
                    current_data["learning_insights"] = step_result
                elif agent.agent_type == "response_processor":
                    processing_context["enhanced_response"] = step_result
                    current_data["enhanced_response"] = step_result
                    processing_context["quality_metrics"] = {
                        "quality_score": step_result.get("quality_score", 0.0),
                        "enhancements_applied": step_result.get("enhancements_applied", []),
                        "learning_confidence": step_result.get("learning_confidence", 0.0)
                    }
                
                self.logger.info(f"{step_name} completed successfully in {time.time() - step_start_time:.3f}s")
                
            except Exception as e:
                step_time = time.time() - step_start_time
                self.logger.error(f"{step_name} failed: {e}")
                
                # Record failure in processing context
                processing_context["pipeline_steps"].append({
                    "step": step_name,
                    "agent_id": agent.agent_id,
                    "agent_type": agent.agent_type,
                    "execution_time": step_time,
                    "success": False,
                    "error": str(e)
                })
                
                # Continue pipeline with error handling
                current_data["error"] = str(e)
                current_data["failed_step"] = step_name
        
        return current_data
    
    async def _store_learning_data(self, ticket_data: Dict[str, Any], 
                                  final_result: Dict[str, Any], 
                                  processing_context: Dict[str, Any]):
        """Store learning data in the knowledge base."""
        try:
            # Store response pattern
            pattern_key = self._generate_pattern_key(ticket_data)
            response_data = final_result.get("enhanced_response", {})
            
            if response_data:
                self.knowledge_base.store_response_pattern(
                    pattern_key, response_data, success_rate=0.8
                )
            
            # Store learning history
            for step in processing_context["pipeline_steps"]:
                if step["success"] and step["agent_type"] in ["learning", "response_processor"]:
                    self.knowledge_base.store_learning_history(
                        step["agent_id"],
                        pattern_key,
                        step["result"],
                        success=True
                    )
            
            self.logger.info(f"Learning data stored for pattern: {pattern_key}")
            
        except Exception as e:
            self.logger.error(f"Failed to store learning data: {e}")
    
    def _generate_pattern_key(self, ticket_data: Dict[str, Any]) -> str:
        """Generate a pattern key for the ticket."""
        ticket_type = ticket_data.get("type", "unknown")
        priority = ticket_data.get("priority", "unknown")
        labels = ticket_data.get("labels", [])
        category = ticket_data.get("category", "unknown")
        
        # Create comprehensive pattern key
        pattern_key = f"{ticket_type}:{priority}:{category}:{','.join(sorted(labels))}"
        return pattern_key
    
    async def _update_coordination_metrics(self, processing_time: float, success: bool):
        """Update coordination performance metrics."""
        self.coordination_metrics["total_coordinations"] += 1
        
        if success:
            self.coordination_metrics["successful_coordinations"] += 1
        else:
            self.coordination_metrics["failed_coordinations"] += 1
        
        # Update average pipeline time
        total_time = self.coordination_metrics["average_pipeline_time"] * (self.coordination_metrics["total_coordinations"] - 1)
        total_time += processing_time
        self.coordination_metrics["average_pipeline_time"] = total_time / self.coordination_metrics["total_coordinations"]
    
    def _update_pipeline_performance(self, pipeline_steps: List[Dict[str, Any]]):
        """Update pipeline performance tracking."""
        for step in pipeline_steps:
            step_name = step["step"]
            execution_time = step["execution_time"]
            success = step["success"]
            
            if step_name not in self.pipeline_performance:
                self.pipeline_performance[step_name] = {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "total_time": 0.0,
                    "average_time": 0.0
                }
            
            performance = self.pipeline_performance[step_name]
            performance["total_executions"] += 1
            performance["total_time"] += execution_time
            
            if success:
                performance["successful_executions"] += 1
            
            performance["average_time"] = performance["total_time"] / performance["total_executions"]
    
    async def _learn_coordination_patterns(self, ticket_data: Dict[str, Any], 
                                         response: Dict[str, Any], 
                                         feedback: Optional[Dict[str, Any]] = None):
        """Learn coordination patterns and optimize pipeline."""
        try:
            # Analyze pipeline performance
            pipeline_steps = response.get("pipeline_performance", [])
            
            # Identify bottlenecks
            bottlenecks = []
            for step in pipeline_steps:
                if step["execution_time"] > 1.0:  # Steps taking more than 1 second
                    bottlenecks.append({
                        "step": step["step"],
                        "agent_id": step["agent_id"],
                        "execution_time": step["execution_time"]
                    })
            
            # Store coordination insights
            if bottlenecks:
                coordination_insight = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "bottlenecks": bottlenecks,
                    "total_processing_time": response.get("processing_time", 0),
                    "ticket_characteristics": {
                        "type": ticket_data.get("type"),
                        "priority": ticket_data.get("priority"),
                        "complexity": len(ticket_data.get("labels", []))
                    }
                }
                
                # Store in knowledge base for future optimization
                self.knowledge_base.store_best_practice(
                    "coordination",
                    "bottleneck_identification",
                    f"Identified bottlenecks: {bottlenecks}",
                    effectiveness_score=0.8
                )
            
        except Exception as e:
            self.logger.error(f"Failed to learn coordination patterns: {e}")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all agents."""
        agent_statuses = {}
        
        for agent in self.agent_pipeline:
            agent_statuses[agent.agent_id] = agent.get_health_status()
        
        return {
            "orchestrator_status": self.get_health_status(),
            "agent_statuses": agent_statuses,
            "pipeline_performance": self.pipeline_performance,
            "coordination_metrics": self.coordination_metrics,
            "knowledge_base_stats": self.knowledge_base.get_knowledge_stats()
        }
    
    def optimize_pipeline(self) -> Dict[str, Any]:
        """Analyze and suggest pipeline optimizations."""
        optimizations = []
        
        # Analyze step performance
        for step_name, performance in self.pipeline_performance.items():
            if performance["average_time"] > 2.0:  # Steps taking more than 2 seconds on average
                optimizations.append({
                    "step": step_name,
                    "issue": "High execution time",
                    "current_average": performance["average_time"],
                    "recommendation": "Consider caching or optimization"
                })
            
            success_rate = performance["successful_executions"] / performance["total_executions"]
            if success_rate < 0.9:  # Success rate below 90%
                optimizations.append({
                    "step": step_name,
                    "issue": "Low success rate",
                    "current_rate": success_rate,
                    "recommendation": "Investigate failure causes and improve error handling"
                })
        
        # Pipeline order optimization
        if len(self.pipeline_performance) > 1:
            # Suggest reordering based on performance
            step_performance = [
                (step, perf["average_time"], perf["successful_executions"] / perf["total_executions"])
                for step, perf in self.pipeline_performance.items()
            ]
            
            # Sort by execution time (fastest first) and success rate
            step_performance.sort(key=lambda x: (x[1], -x[2]))
            
            if step_performance != list(self.pipeline_performance.keys()):
                optimizations.append({
                    "step": "pipeline_order",
                    "issue": "Suboptimal pipeline order",
                    "recommendation": f"Consider reordering: {[step for step, _, _ in step_performance]}"
                })
        
        return {
            "optimizations": optimizations,
            "total_suggestions": len(optimizations),
            "pipeline_efficiency_score": self._calculate_pipeline_efficiency()
        }
    
    def _calculate_pipeline_efficiency(self) -> float:
        """Calculate overall pipeline efficiency score."""
        if not self.pipeline_performance:
            return 0.0
        
        efficiency_scores = []
        
        for step_name, performance in self.pipeline_performance.items():
            # Time efficiency (faster is better)
            time_score = max(0, 1 - (performance["average_time"] / 5.0))  # Normalize to 5 seconds
            
            # Success efficiency
            success_score = performance["successful_executions"] / performance["total_executions"]
            
            # Combined efficiency for this step
            step_efficiency = (time_score + success_score) / 2
            efficiency_scores.append(step_efficiency)
        
        return sum(efficiency_scores) / len(efficiency_scores)
    
    async def health_check_all_agents(self) -> Dict[str, Any]:
        """Perform health check on all agents in the pipeline."""
        health_results = {}
        
        for agent in self.agent_pipeline:
            try:
                health_status = await agent.health_check()
                health_results[agent.agent_id] = {
                    "healthy": health_status,
                    "status": agent.get_health_status()
                }
            except Exception as e:
                health_results[agent.agent_id] = {
                    "healthy": False,
                    "error": str(e)
                }
        
        # Overall health check
        overall_healthy = all(result["healthy"] for result in health_results.values())
        
        return {
            "overall_healthy": overall_healthy,
            "agent_health": health_results,
            "timestamp": datetime.utcnow().isoformat()
        }
