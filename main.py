from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path
import asyncio
import time
from typing import Dict, Any, List

from servicenow.client import GitHubClient
from llm.summarizer import TicketSummarizer
from llm.responder import ResponseGenerator
from sla_tracker import SLATracker
from session_manager import SessionManager
from validation import ticket_validator, request_validator, ValidationError
from logging_config import log_api_request, log_ticket_processing, log_error, get_main_logger
from config import settings

# Import intelligent agent system
from agent import TicketAgent

app = FastAPI(title="ServiceNow Ticket Agent", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Simple CORS middleware (keeping it simple as requested)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
github_client = GitHubClient()
summarizer = TicketSummarizer()
responder = ResponseGenerator()
sla_tracker = SLATracker()
session_manager = SessionManager()

# Initialize intelligent agent system
ticket_agent = TicketAgent("main_ticket_agent_001")

# Initialize logging
main_logger = get_main_logger()
main_logger.info("ServiceNow Ticket Agent started successfully with intelligent agent system")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard for ticket management"""
    stats = session_manager.get_statistics()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats
    })

@app.get("/api/health")
async def health_check():
    """Health check endpoint for the system"""
    try:
        # Check all components
        agent_health = await ticket_agent.health_check_all_agents()
        
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {
                "github_client": True,
                "summarizer": True,
                "responder": True,
                "sla_tracker": True,
                "session_manager": True,
                "ticket_agent": agent_health["overall_healthy"]
            },
            "agent_health": agent_health,
            "version": "1.0.0"
        }
        
        return health_status
    except Exception as e:
        main_logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/api/tickets")
async def get_recent_tickets(limit: Any = 10):
    """Fetch recent tickets from GitHub"""
    start_time = time.time()
    try:
        # Validate limit parameter
        is_valid, error = request_validator.validate_limit(limit)
        if not is_valid:
            log_api_request("GET", f"/api/tickets?limit={limit}", 400)
            raise HTTPException(status_code=400, detail=error.message)
        
        tickets = github_client.get_issues(limit=limit)
        response_time = time.time() - start_time
        log_api_request("GET", f"/api/tickets?limit={limit}", 200, response_time)
        log_ticket_processing("batch", f"Fetched {len(tickets)} tickets", f"Limit: {limit}")
        
        return {"success": True, "tickets": tickets}
    except HTTPException:
        raise
    except Exception as e:
        response_time = time.time() - start_time
        log_api_request("GET", f"/api/tickets?limit={limit}", 500)
        log_error("API_ERROR", f"Failed to fetch tickets with limit {limit}", e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/ticket/{ticket_number}")
async def get_ticket(ticket_number: Any):
    """Fetch specific ticket by number"""
    try:
        # Validate ticket number parameter
        is_valid, error = request_validator.validate_ticket_number(ticket_number)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error.message)
        
        ticket = github_client.get_issue_by_number(ticket_number)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return {"success": True, "ticket": ticket}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/process-ticket")
async def process_ticket(ticket_number: Any):
    """Process ticket using intelligent agent system: summarize, generate response, check SLA"""
    start_time = time.time()
    try:
        log_ticket_processing(ticket_number, "STARTED", "Processing ticket with intelligent agent system")
        
        # Validate ticket number parameter
        is_valid, error = request_validator.validate_ticket_number(ticket_number)
        if not is_valid:
            log_api_request("POST", f"/api/process-ticket?ticket_number={ticket_number}", 400)
            log_ticket_processing(ticket_number, "VALIDATION_FAILED", f"Invalid ticket number: {error.message}")
            raise HTTPException(status_code=400, detail=error.message)
        
        # Fetch ticket
        ticket = github_client.get_issue_by_number(ticket_number)
        if not ticket:
            log_api_request("POST", f"/api/process-ticket?ticket_number={ticket_number}", 404)
            log_ticket_processing(ticket_number, "NOT_FOUND", "Ticket not found in GitHub")
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Validate ticket data before processing
        is_valid, validation_errors = ticket_validator.validate_ticket(ticket)
        if not is_valid:
            # Check if it's a duplicate request
            duplicate_errors = [e for e in validation_errors if e.code == "DUPLICATE_REQUEST"]
            if duplicate_errors:
                log_api_request("POST", f"/api/process-ticket?ticket_number={ticket_number}", 409)
                log_ticket_processing(ticket_number, "DUPLICATE_REQUEST", "Ticket already processed")
                raise HTTPException(status_code=409, detail=duplicate_errors[0].message)
            
            # For other validation errors, return detailed error information
            error_details = [{"field": e.field, "message": e.message, "code": e.code} for e in validation_errors]
            log_api_request("POST", f"/api/process-ticket?ticket_number={ticket_number}", 422)
            log_ticket_processing(ticket_number, "VALIDATION_FAILED", f"Found {len(validation_errors)} validation errors")
            raise HTTPException(status_code=422, detail={
                "message": "Ticket validation failed",
                "errors": error_details
            })
        
        # Mark ticket as processed to prevent duplicates
        ticket_validator.mark_ticket_processed(ticket["number"])
        
        # Check SLA
        log_ticket_processing(ticket_number, "SLA_CHECK", "Checking SLA compliance")
        sla_status = sla_tracker.get_sla_status(ticket)
        breach_info = sla_tracker.check_sla_breach(ticket)
        
        # Send SLA alert if breached
        if breach_info:
            log_ticket_processing(ticket_number, "SLA_BREACH", f"SLA breached by {breach_info.get('elapsed_hours', 0)} hours")
            await sla_tracker.send_sla_alert(breach_info)
        
        # Use intelligent agent system for processing
        log_ticket_processing(ticket_number, "AGENT_PROCESSING", "Processing with intelligent agent system")
        
        # Prepare input for the agent
        agent_input = {
            "ticket": ticket,
            "sla_status": sla_status,
            "breach_info": breach_info,
            "ticket_number": ticket_number
        }
        
        # Process with ticket agent
        agent_result = await ticket_agent.process(agent_input)
        
        # Extract results from agent processing
        enhanced_response = agent_result.get("enhanced_response", {})
        learning_insights = agent_result.get("learning_insights", {})
        quality_metrics = agent_result.get("quality_metrics", {})
        
        # Fallback to traditional processing if agent system fails
        if not enhanced_response or not enhanced_response.get("response"):
            log_ticket_processing(ticket_number, "AGENT_FALLBACK", "Using traditional processing as fallback")
            
            # Summarize ticket
            summary = await summarizer.summarize_ticket(ticket)
            
            # Generate response
            response = await responder.generate_response(ticket, summary)
            
            enhanced_response = {
                "response": response,
                "summary": summary,
                "fallback_used": True
            }
        
        # Add to session history
        log_ticket_processing(ticket_number, "HISTORY_UPDATE", "Adding to session history")
        session_manager.add_ticket_to_history(
            ticket, 
            enhanced_response.get("summary", {}), 
            enhanced_response.get("response", {}), 
            sla_status
        )
        
        response_time = time.time() - start_time
        log_api_request("POST", f"/api/process-ticket?ticket_number={ticket_number}", 200, response_time)
        log_ticket_processing(ticket_number, "COMPLETED", f"Successfully processed in {response_time:.3f}s")
        
        # Learn from this interaction
        await ticket_agent.learn(agent_input, agent_result)
        
        return {
            "success": True,
            "ticket": ticket,
            "enhanced_response": enhanced_response,
            "learning_insights": learning_insights,
            "quality_metrics": quality_metrics,
            "sla_status": sla_status,
            "sla_breached": breach_info is not None,
            "agent_processing": True,
            "processing_time": response_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        response_time = time.time() - start_time
        log_api_request("POST", f"/api/process-ticket?ticket_number={ticket_number}", 500)
        log_error("PROCESSING_ERROR", f"Failed to process ticket {ticket_number}", e)
        log_ticket_processing(ticket_number, "FAILED", f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/history")
async def get_history():
    """Get session history"""
    return {"success": True, "history": session_manager.get_session_history()}

@app.get("/api/history/search")
async def search_history(query: str):
    """Search session history"""
    results = session_manager.search_history(query)
    return {"success": True, "results": results}

@app.get("/api/statistics")
async def get_statistics():
    """Get session statistics"""
    stats = session_manager.get_statistics()
    return {"success": True, "statistics": stats}

@app.post("/api/history/clear")
async def clear_history():
    """Clear session history"""
    session_manager.clear_history()
    return {"success": True, "message": "History cleared"}

@app.get("/api/history/export")
async def export_history():
    """Export session history as JSON"""
    history_json = session_manager.export_history()
    return JSONResponse(content=history_json, media_type="application/json")

@app.get("/api/validation/status")
async def get_validation_status():
    """Get validation statistics and processed tickets"""
    return {
        "success": True,
        "processed_tickets": list(ticket_validator.get_processed_tickets()),
        "validation_config": {
            "max_description_length": ticket_validator.MAX_DESCRIPTION_LENGTH,
            "max_title_length": ticket_validator.MAX_TITLE_LENGTH,
            "max_comments_count": ticket_validator.MAX_COMMENTS_COUNT,
            "max_labels_count": ticket_validator.MAX_LABELS_COUNT,
            "required_fields": ticket_validator.REQUIRED_FIELDS
        }
    }

@app.post("/api/validation/clear-processed")
async def clear_processed_tickets():
    """Clear the list of processed tickets"""
    ticket_validator.clear_processed_tickets()
    return {"success": True, "message": "Processed tickets list cleared"}

# New endpoints for intelligent agent system
@app.get("/api/agents/status")
async def get_agents_status():
    """Get status of all intelligent agents"""
    try:
        agent_status = ticket_agent.get_agent_status()
        return {"success": True, "agent_status": agent_status}
    except Exception as e:
        main_logger.error(f"Failed to get agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {str(e)}")

@app.get("/api/agents/health")
async def get_agents_health():
    """Get health status of all agents"""
    try:
        health_status = await ticket_agent.health_check_all_agents()
        return {"success": True, "health_status": health_status}
    except Exception as e:
        main_logger.error(f"Failed to get agent health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent health: {str(e)}")

@app.get("/api/agents/optimize")
async def optimize_agents():
    """Get optimization suggestions for the agent pipeline"""
    try:
        optimizations = ticket_agent.optimize_pipeline()
        return {"success": True, "optimizations": optimizations}
    except Exception as e:
        main_logger.error(f"Failed to optimize agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize agents: {str(e)}")

@app.get("/api/knowledge/stats")
async def get_knowledge_stats():
    """Get knowledge base statistics"""
    try:
        knowledge_stats = ticket_agent.knowledge_base.get_knowledge_stats()
        return {"success": True, "knowledge_stats": knowledge_stats}
    except Exception as e:
        main_logger.error(f"Failed to get knowledge stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge stats: {str(e)}")

@app.post("/api/knowledge/export")
async def export_knowledge():
    """Export knowledge base"""
    try:
        export_path = f"knowledge_export_{int(time.time())}.json"
        success = ticket_agent.knowledge_base.export_knowledge(export_path)
        
        if success:
            return {"success": True, "message": f"Knowledge exported to {export_path}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to export knowledge")
    except Exception as e:
        main_logger.error(f"Failed to export knowledge: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export knowledge: {str(e)}")

@app.post("/api/knowledge/cleanup")
async def cleanup_knowledge():
    """Clean up old knowledge base data"""
    try:
        ticket_agent.knowledge_base.cleanup_old_data(settings.KNOWLEDGE_CLEANUP_DAYS)
        return {"success": True, "message": f"Knowledge base cleaned up (kept {settings.KNOWLEDGE_CLEANUP_DAYS} days)"}
    except Exception as e:
        main_logger.error(f"Failed to cleanup knowledge: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup knowledge: {str(e)}")

# Global exception handler for validation errors
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with detailed error information"""
    if exc.status_code == 422:
        # Validation error - return structured error response
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    elif exc.status_code == 409:
        # Conflict - duplicate request
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "Conflict", "detail": exc.detail}
        )
    else:
        # Other HTTP errors
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "HTTP Error", "detail": exc.detail}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
