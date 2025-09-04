"""
Base agent class for ServiceNow Ticket Agent.
Defines the interface and common functionality for all agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from logging_config import get_main_logger


class BaseAgent(ABC):
    """Base class for all intelligent agents."""
    
    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.logger = get_main_logger()
        self.created_at = datetime.utcnow()
        self.last_active = datetime.utcnow()
        self.is_active = True
        self.metrics = {
            "requests_processed": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "average_response_time": 0.0,
            "total_response_time": 0.0
        }
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return response."""
        pass
    
    @abstractmethod
    async def learn(self, input_data: Dict[str, Any], response: Dict[str, Any], 
                   feedback: Optional[Dict[str, Any]] = None) -> bool:
        """Learn from input, response, and feedback."""
        pass
    
    async def update_metrics(self, response_time: float, success: bool):
        """Update agent performance metrics."""
        self.metrics["requests_processed"] += 1
        self.metrics["total_response_time"] += response_time
        
        if success:
            self.metrics["successful_responses"] += 1
        else:
            self.metrics["failed_responses"] += 1
        
        # Calculate average response time
        self.metrics["average_response_time"] = (
            self.metrics["total_response_time"] / self.metrics["requests_processed"]
        )
        
        self.last_active = datetime.utcnow()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get agent health and performance status."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "metrics": self.metrics.copy(),
            "uptime_seconds": (datetime.utcnow() - self.created_at).total_seconds()
        }
    
    def activate(self):
        """Activate the agent."""
        self.is_active = True
        self.logger.info(f"Agent {self.agent_id} activated")
    
    def deactivate(self):
        """Deactivate the agent."""
        self.is_active = False
        self.logger.info(f"Agent {self.agent_id} deactivated")
    
    async def health_check(self) -> bool:
        """Perform health check on the agent."""
        try:
            # Basic health check - can be overridden by subclasses
            return self.is_active and self.metrics["requests_processed"] >= 0
        except Exception as e:
            self.logger.error(f"Health check failed for agent {self.agent_id}: {e}")
            return False
    
    def reset_metrics(self):
        """Reset agent metrics."""
        self.metrics = {
            "requests_processed": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "average_response_time": 0.0,
            "total_response_time": 0.0
        }
        self.logger.info(f"Metrics reset for agent {self.agent_id}")
    
    def __str__(self) -> str:
        return f"{self.agent_type}({self.agent_id})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(agent_id='{self.agent_id}', agent_type='{self.agent_type}')"
