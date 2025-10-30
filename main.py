"""
FastAPI Service for CrewAI Agents
Provides endpoints for academic paper research
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agent_manager import AgentManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Arize telemetry BEFORE any CrewAI imports
from setup_arize_telemetry import setup_arize_telemetry
setup_arize_telemetry()

# Initialize Service15 tracing (Arize/Langfuse support)
try:
    from service15.tracing import setup_tracing
    setup_tracing(
        service_name="service15-city-mapping",
        project_name="UrbanZeroServices"
    )
    logger.info("Service15 tracing initialized")
except Exception as e:
    logger.warning(f"Service15 tracing not available: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="Service 7 - SME API",
    description="API for academic paper research using CrewAI agents",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="service15/static"), name="static")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent manager
agent_manager = AgentManager()

# Import and include service15 routes
from service15.routes import router as mapping_router
from service15.routes.chat import router as chat_router
# from service15.routes.chat_crew import router as chat_crew_router  # Disabled - has import errors
from service15.routes.chat_haiku import router as chat_haiku_router
from service15.routes.solar import router as solar_router
# from service15.routes.async_crew import router as async_crew_router  # Disabled - has import errors
from service15.routes.cache import router as cache_router
app.include_router(
    mapping_router,
    prefix="/api/mapping",
    tags=["mapping"]
)
app.include_router(
    chat_router,
    prefix="/api/mapping",
    tags=["mapping-chat"]
)
# app.include_router(
#     chat_crew_router,
#     prefix="/api/mapping",
#     tags=["mapping-chat-crew"]
# )
app.include_router(
    solar_router,
    prefix="/api/solar",
    tags=["solar"]
)
# app.include_router(
#     async_crew_router,
#     prefix="/api/mapping/async",
#     tags=["async-mapping"]
# )
app.include_router(
    cache_router,
    prefix="/api/mapping/cache",
    tags=["cache"]
)
app.include_router(
    chat_haiku_router,
    prefix="/api/mapping",
    tags=["mapping-chat-haiku"]
)

# Request/Response models
class ResearchRequest(BaseModel):
    topic: str = "net zero carbon capture"
    
class ResearchResponse(BaseModel):
    success: bool
    topic: str
    results: Optional[Dict[Any, Any]] = None
    error: Optional[str] = None

class StatusResponse(BaseModel):
    success: bool
    status: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str

class TopicRequest(BaseModel):
    topic: str
    depth: str = "intermediate"  # basic, intermediate, comprehensive
    include_citations: bool = True
class TopicResponse(BaseModel):
    success: bool
    topic: str
    analysis: Optional[Dict[Any, Any]] = None
    error: Optional[str] = None
class ReportRequest(BaseModel):
    title: str
    topics: list[str]
    format: str = "markdown"  # markdown, html, pdf
    length: str = "standard"  # brief, standard, detailed
class ReportResponse(BaseModel):
    success: bool
    report: Optional[Dict[Any, Any]] = None
    error: Optional[str] = None

# Simplified authentication dependency
async def verify_authentication():
    """
    Simplified authentication check
    In production, implement proper authentication
    """
    # Add your authentication logic here
    return True

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup"""
    try:
        await agent_manager.initialize_agents()
        logger.info("Agents initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agents: {e}")

# API Endpoints

@app.get("/")
async def read_index():
    """
    Serve the test page at root
    """
    return FileResponse("static/index.html")

@app.get("/map")
async def read_map():
    """
    Serve the city boundary map page with API key injected
    """
    from fastapi.responses import HTMLResponse

    # Read the HTML template
    with open("service15/static/city_map_v2.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    # Get Google Maps API key from environment
    google_maps_key = os.getenv("GOOGLE_MAPS_API_KEY", "YOUR_API_KEY_HERE")

    # Replace the placeholder with actual API key
    html_content = html_content.replace("YOUR_API_KEY_HERE", google_maps_key)

    return HTMLResponse(content=html_content)

@app.get("/chat-map")
async def read_chat_map():
    """
    Serve the city boundary map page with AI chat assistant
    """
    from fastapi.responses import HTMLResponse

    # Read the HTML template
    with open("service15/static/city_map_with_chat.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    # Get Google Maps API key from environment
    google_maps_key = os.getenv("GOOGLE_MAPS_API_KEY", "YOUR_API_KEY_HERE")

    # Replace the placeholder with actual API key
    html_content = html_content.replace("YOUR_API_KEY_HERE", google_maps_key)

    return HTMLResponse(content=html_content)

@app.get("/map/test")
async def test_api_key():
    """
    Serve the API key diagnostic page
    """
    return FileResponse("service15/static/test_api_key.html")

@app.get("/map/debug")
async def debug_map():
    """
    Serve the debug map page with detailed logging
    """
    return FileResponse("service15/static/debug_map.html")

@app.get("/map/test-buildings")
async def test_building_viz():
    """
    Serve the building visualization test page
    """
    from fastapi.responses import HTMLResponse

    # Read the HTML template
    with open("service15/static/test_building_viz.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    # Get Google Maps API key from environment
    google_maps_key = os.getenv("GOOGLE_MAPS_API_KEY", "YOUR_API_KEY_HERE")

    # Replace the placeholder with actual API key
    html_content = html_content.replace("YOUR_API_KEY_HERE", google_maps_key)

    return HTMLResponse(content=html_content)

@app.get("/api/mapping/cities/{city_name}")
async def get_city_boundaries(city_name: str):
    """
    Get city boundaries from local GeoJSON dataset
    Searches for cities matching the given name (case-insensitive)
    Returns all matching cities with their polygon boundaries
    """
    import json
    from pathlib import Path

    try:
        # Load the cities GeoJSON file
        cities_file = Path("service15/cities.geojson")
        if not cities_file.exists():
            return {"success": False, "error": "Cities dataset not found", "features": []}

        with open(cities_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Filter cities by name (case-insensitive)
        city_upper = city_name.upper()
        matching_cities = [
            feature for feature in data['features']
            if feature['properties']['NAME'].upper() == city_upper
        ]

        return {
            "success": True,
            "type": "FeatureCollection",
            "features": matching_cities,
            "metadata": {
                "source": "geojson-world-cities",
                "query": city_name,
                "feature_count": len(matching_cities)
            }
        }

    except Exception as e:
        logger.error(f"Error loading city boundaries: {str(e)}")
        return {"success": False, "error": str(e), "features": []}

@app.post("/api/research/papers", response_model=ResearchResponse)
async def research_papers(
    request: ResearchRequest,
    authenticated: bool = Depends(verify_authentication)
):
    """
    Execute academic paper research for a given topic
    """
    try:
        logger.info(f"Starting paper research for topic: {request.topic}")
        
        # Execute agent task
        results = await execute_agent_task(
            agent_id="web-researcher",
            task_type="conduct_research",
            input_data={"topic": request.topic}
        )
        
        return ResearchResponse(
            success=True,
            topic=request.topic,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Paper research error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/agents/status", response_model=StatusResponse)
async def get_agent_status(authenticated: bool = Depends(verify_authentication)):
    """
    Get the status of all agents
    """
    try:
        status = await execute_agent_task(
            agent_id="manager",
            task_type="get_status",
            input_data={}
        )
        
        return StatusResponse(success=True, status=status)
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat()
    )

# @app.post("/api/research/topic", response_model=TopicResponse)
# async def research_topic(
#     request: TopicRequest,
#     authenticated: bool = Depends(verify_authentication)
# ):
#     """
#     Conduct in-depth analysis of a specific research topic
#     """
#     try:
#         logger.info(f"Starting topic analysis: {request.topic} (depth: {request.depth})")
        
#         # For now, return mocked data until CrewAI integration is complete
#         # TODO: Integrate with actual CrewAI topic analysis agent
#         analysis = {
#             "topic": request.topic,
#             "depth": request.depth,
#             "summary": f"Comprehensive analysis of {request.topic}",
#             "key_findings": [
#                 f"Finding 1: Advances in {request.topic} show promising results",
#                 f"Finding 2: Economic viability of {request.topic} is improving",
#                 f"Finding 3: Policy support for {request.topic} is growing globally"
#             ],
#             "trends": [
#                 "Increased investment in research and development",
#                 "Growing industry adoption",
#                 "Technological breakthroughs reducing costs"
#             ],
#             "challenges": [
#                 "Scaling from pilot to commercial deployment",
#                 "Infrastructure requirements",
#                 "Regulatory framework development"
#             ],
#             "opportunities": [
#                 "Cross-sector collaboration potential",
#                 "Emerging market applications",
#                 "Innovation in supporting technologies"
#             ],
#             "citations": [
#                 {
#                     "title": f"Recent Advances in {request.topic}",
#                     "authors": ["Research Team A"],
#                     "year": 2024,
#                     "journal": "Nature Sustainability"
#                 },
#                 {
#                     "title": f"Economic Analysis of {request.topic}",
#                     "authors": ["Economics Group B"],
#                     "year": 2023,
#                     "journal": "Energy Economics"
#                 }
#             ] if request.include_citations else [],
#             "timestamp": datetime.now().isoformat()
#         }
        
#         return TopicResponse(
#             success=True,
#             topic=request.topic,
#             analysis=analysis
#         )
        
#     except Exception as e:
#         logger.error(f"Topic research error: {e}")
#         return TopicResponse(
#             success=False,
#             topic=request.topic,
#             analysis=None,
#             error=str(e)
#         )

# @app.post("/api/research/report", response_model=ReportResponse)
# async def generate_report(
#     request: ReportRequest,
#     authenticated: bool = Depends(verify_authentication)
# ):
#     """
#     Generate a comprehensive research report on multiple topics
#     """
#     try:
#         logger.info(f"Generating report: {request.title} with {len(request.topics)} topics")
        
#         # For now, return mocked report until CrewAI integration is complete
#         # TODO: Integrate with actual CrewAI report generation agent
#         report_content = f"# {request.title}\n\n"
#         report_content += f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
#         report_content += "## Executive Summary\n\n"
#         report_content += f"This report provides a comprehensive analysis of {', '.join(request.topics)}, "
#         report_content += "examining current trends, challenges, and opportunities in each area.\n\n"
        
#         sections = []
#         for topic in request.topics:
#             section = {
#                 "title": topic.title(),
#                 "content": f"### {topic.title()}\n\n" +
#                           f"The field of {topic} has seen significant developments in recent years. " +
#                           f"Key innovations include advanced technologies, improved efficiency, and " +
#                           f"reduced costs. Market adoption is accelerating with strong policy support.\n\n" +
#                           f"**Key Points:**\n" +
#                           f"- Technological breakthroughs driving progress\n" +
#                           f"- Economic viability improving rapidly\n" +
#                           f"- Growing global investment and support\n\n"
#             }
#             sections.append(section)
#             report_content += section["content"]
        
#         report_content += "## Conclusions\n\n"
#         report_content += "The analyzed topics show strong potential for contributing to net zero goals. "
#         report_content += "Continued investment and policy support will be crucial for scaling these solutions.\n\n"
        
#         report_content += "## Recommendations\n\n"
#         report_content += "1. Increase funding for research and development\n"
#         report_content += "2. Develop supportive regulatory frameworks\n"
#         report_content += "3. Foster public-private partnerships\n"
#         report_content += "4. Invest in infrastructure development\n"
        
#         report = {
#             "title": request.title,
#             "format": request.format,
#             "length": request.length,
#             "topics": request.topics,
#             "content": report_content,
#             "sections": sections,
#             "generated_at": datetime.now().isoformat(),
#             "word_count": len(report_content.split())
#         }
        
#         return ReportResponse(
#             success=True,
#             report=report
#         )
        
#     except Exception as e:
#         logger.error(f"Report generation error: {e}")
#         return ReportResponse(
#             success=False,
#             report=None,
#             error=str(e)
#         )


async def execute_agent_task(
    agent_id: str,
    task_type: str,
    input_data: Dict[Any, Any],
    timeout: int = 120
) -> Dict[Any, Any]:
    """
    Execute an agent task with timeout
    
    Args:
        agent_id: Identifier for the agent
        task_type: Type of task to execute
        input_data: Input data for the task
        timeout: Timeout in seconds (default: 120)
        
    Returns:
        Task results as dictionary
    """
    try:
        # Create task with timeout
        task = asyncio.create_task(
            agent_manager.execute_task(agent_id, task_type, input_data)
        )
        
        # Wait for task with timeout
        result = await asyncio.wait_for(task, timeout=timeout)
        
        return result
        
    except asyncio.TimeoutError:
        logger.error(f"Agent task timeout: {agent_id}/{task_type}")
        raise Exception("Agent task timeout")
    except Exception as e:
        logger.error(f"Agent task failed: {e}")
        raise


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8011))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
