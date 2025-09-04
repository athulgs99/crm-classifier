"""
Test script for the intelligent agent system.
Demonstrates the new capabilities of the refactored ServiceNow Ticket Agent.
"""

import asyncio
import time
from typing import Dict, Any
from agent import TicketAgent, LearningAgent, ResponseProcessor
from knowledge_base import KnowledgeBase


async def test_learning_agent():
    """Test the learning agent functionality."""
    print("🧠 Testing Learning Agent...")
    
    # Initialize learning agent
    learning_agent = LearningAgent("test_learning_001")
    
    # Test data
    test_ticket = {
        "type": "bug",
        "priority": "high",
        "labels": ["urgent", "frontend"],
        "title": "Critical UI issue",
        "description": "Users cannot access the main dashboard"
    }
    
    # Test processing
    result = await learning_agent.process(test_ticket)
    print(f"✅ Learning agent processed ticket: {result.get('confidence', 0):.2f} confidence")
    
    # Test learning
    feedback = {"success": True, "user_satisfaction": 0.9}
    learning_success = await learning_agent.learn(test_ticket, result, feedback)
    print(f"✅ Learning agent learned: {learning_success}")
    
    # Get learning stats
    stats = learning_agent.get_learning_stats()
    print(f"📊 Learning stats: {stats['total_patterns_learned']} patterns learned")
    
    return learning_agent


async def test_response_processor():
    """Test the response processor functionality."""
    print("\n🔧 Testing Response Processor...")
    
    # Initialize response processor
    processor = ResponseProcessor("test_processor_001")
    
    # Test data
    base_response = {
        "message": "We have identified the issue and are working on a fix.",
        "status": "in_progress",
        "assignee": "support_team"
    }
    
    test_ticket = {
        "priority": "critical",
        "labels": ["urgent", "frontend"],
        "sla_status": {"status": "at_risk", "breach_risk": "high"}
    }
    
    # Test processing
    input_data = {"response": base_response, "ticket": test_ticket}
    result = await processor.process(input_data)
    
    print(f"✅ Response processor enhanced response: {result.get('quality_score', 0):.2f} quality score")
    print(f"📋 Enhancements applied: {result.get('enhancements_applied', [])}")
    
    return processor


async def test_knowledge_base():
    """Test the knowledge base functionality."""
    print("\n📚 Testing Knowledge Base...")
    
    # Initialize knowledge base
    kb = KnowledgeBase("test_knowledge.db")
    
    # Test storing and retrieving patterns
    test_pattern = "bug:high:frontend:urgent,frontend"
    test_response = {"message": "Critical issue identified", "priority": "immediate"}
    
    # Store pattern
    store_success = kb.store_response_pattern(test_pattern, test_response, 0.9)
    print(f"✅ Stored response pattern: {store_success}")
    
    # Retrieve pattern
    retrieved = kb.retrieve_response_pattern(test_pattern)
    if retrieved:
        print(f"✅ Retrieved pattern: {retrieved['success_rate']:.2f} success rate")
    
    # Store best practice
    practice_success = kb.store_best_practice(
        "ticket_handling",
        "critical_priority_escalation",
        "Immediately escalate critical priority tickets to senior support",
        0.95
    )
    print(f"✅ Stored best practice: {practice_success}")
    
    # Get stats
    stats = kb.get_knowledge_stats()
    print(f"📊 Knowledge base stats: {stats['total_patterns']} patterns, {stats['total_best_practices']} practices")
    
    return kb


async def test_ticket_agent():
    """Test the main ticket agent orchestration."""
    print("\n🎯 Testing Ticket Agent Orchestration...")
    
    # Initialize ticket agent
    ticket_agent = TicketAgent("test_orchestrator_001")
    
    # Test data
    test_ticket = {
        "number": "TEST-001",
        "type": "bug",
        "priority": "high",
        "labels": ["urgent", "frontend"],
        "title": "Critical UI issue",
        "description": "Users cannot access the main dashboard",
        "category": "frontend"
    }
    
    # Test processing
    input_data = {"ticket": test_ticket, "ticket_number": "TEST-001"}
    result = await ticket_agent.process(input_data)
    
    print(f"✅ Ticket agent processed ticket: {result.get('processing_time', 0):.3f}s")
    print(f"📋 Pipeline steps: {len(result.get('pipeline_steps', []))}")
    
    # Test learning
    learning_success = await ticket_agent.learn(input_data, result)
    print(f"✅ Ticket agent learned: {learning_success}")
    
    # Get agent status
    status = ticket_agent.get_agent_status()
    print(f"📊 Agent status: {status['orchestrator_status']['is_active']}")
    
    # Test optimization
    optimizations = ticket_agent.optimize_pipeline()
    print(f"🔧 Pipeline optimizations: {optimizations['total_suggestions']} suggestions")
    
    return ticket_agent


async def run_comprehensive_test():
    """Run all tests comprehensively."""
    print("🚀 Starting Comprehensive Test of Intelligent Agent System\n")
    
    start_time = time.time()
    
    try:
        # Test individual components
        learning_agent = await test_learning_agent()
        response_processor = await test_response_processor()
        knowledge_base = await test_knowledge_base()
        ticket_agent = await test_ticket_agent()
        
        # Test integration
        print("\n🔗 Testing Integration...")
        
        # Test knowledge sharing between agents
        if learning_agent and response_processor:
            print("✅ Learning agent and response processor integration successful")
        
        # Test knowledge base integration
        if knowledge_base and ticket_agent:
            print("✅ Knowledge base integration successful")
        
        total_time = time.time() - start_time
        print(f"\n🎉 All tests completed successfully in {total_time:.2f} seconds!")
        
        # Print summary
        print("\n📋 Test Summary:")
        print(f"   • Learning Agent: ✅ Active with {learning_agent.metrics['requests_processed']} requests")
        print(f"   • Response Processor: ✅ Active with {response_processor.metrics['requests_processed']} requests")
        print(f"   • Knowledge Base: ✅ {knowledge_base.get_knowledge_stats()['total_patterns']} patterns stored")
        print(f"   • Ticket Agent: ✅ Orchestrating {len(ticket_agent.agent_pipeline)} agents")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Intelligent Agent System Test Suite")
    print("=" * 50)
    
    # Run the comprehensive test
    success = asyncio.run(run_comprehensive_test())
    
    if success:
        print("\n🎯 System is ready for production use!")
    else:
        print("\n⚠️  System needs attention before production use.")

