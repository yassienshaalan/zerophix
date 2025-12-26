from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
import asyncio
import json
import logging
import os
from datetime import datetime
import hashlib
import uuid

from ..config import RedactionConfig
from ..pipelines.redaction import RedactionPipeline
from ..performance.optimization import BatchProcessor, StreamProcessor
from ..security import SecureAuditLogger, ComplianceValidator, ZeroTrustValidator, ComplianceStandard

# Pydantic models for API
class RedactionRequest(BaseModel):
    """Request model for text redaction"""
    text: str = Field(..., description="Text to redact", max_length=100000)
    country: str = Field(default="AU", description="Country code for policy selection")
    company: Optional[str] = Field(default=None, description="Company policy overlay")
    detectors: List[str] = Field(default=["regex", "custom", "spacy"], description="Detectors to use")
    masking_style: str = Field(default="hash", description="Redaction strategy")
    use_cache: bool = Field(default=True, description="Use caching for performance")
    include_confidence: bool = Field(default=True, description="Include confidence scores")
    
    # Advanced Accuracy Features
    enable_ensemble_voting: bool = Field(default=True, description="Enable weighted voting for conflict resolution")
    enable_context_propagation: bool = Field(default=True, description="Propagate high-confidence entities across document")
    allow_list: List[str] = Field(default_factory=list, description="List of terms to never redact")
    
    # Security and compliance fields
    user_id: Optional[str] = Field(default=None, description="User identifier for audit")
    purpose: Optional[str] = Field(default="redaction", description="Processing purpose for compliance")
    lawful_basis: Optional[str] = Field(default=None, description="GDPR lawful basis")
    data_classification: str = Field(default="SENSITIVE", description="Data sensitivity classification")
    consent_obtained: bool = Field(default=False, description="Data subject consent status")
    
    @validator('country')
    def validate_country(cls, v):
        allowed_countries = ['AU', 'US', 'EU', 'UK', 'CA']
        if v.upper() not in allowed_countries:
            raise ValueError(f'Country must be one of: {allowed_countries}')
        return v.upper()
    
    @validator('masking_style')
    def validate_masking_style(cls, v):
        allowed_styles = ['mask', 'hash', 'encrypt', 'synthetic', 'preserve_format', 'differential_privacy']
        if v not in allowed_styles:
            raise ValueError(f'Masking style must be one of: {allowed_styles}')
        return v
    
    @validator('data_classification')
    def validate_data_classification(cls, v):
        allowed_classifications = ['PUBLIC', 'INTERNAL', 'SENSITIVE', 'RESTRICTED']
        if v.upper() not in allowed_classifications:
            raise ValueError(f'Data classification must be one of: {allowed_classifications}')
        return v.upper()

class BatchRedactionRequest(BaseModel):
    """Request model for batch redaction"""
    texts: List[str] = Field(..., description="List of texts to redact", max_items=1000)
    country: str = Field(default="AU", description="Country code for policy selection")
    company: Optional[str] = Field(default=None, description="Company policy overlay")
    detectors: List[str] = Field(default=["regex", "custom"], description="Detectors to use")
    masking_style: str = Field(default="hash", description="Redaction strategy")
    parallel_processing: bool = Field(default=True, description="Use parallel processing")

    # Advanced Accuracy Features
    enable_ensemble_voting: bool = Field(default=True, description="Enable weighted voting for conflict resolution")
    enable_context_propagation: bool = Field(default=True, description="Propagate high-confidence entities across document")
    allow_list: List[str] = Field(default_factory=list, description="List of terms to never redact")
    
    @validator('texts')
    def validate_texts(cls, v):
        if not v:
            raise ValueError('At least one text is required')
        for text in v:
            if len(text) > 10000:
                raise ValueError('Individual text length cannot exceed 10,000 characters')
        return v

class RedactionResponse(BaseModel):
    """Response model for redaction results"""
    success: bool
    redacted_text: str
    entities_found: int
    processing_time: float
    spans: List[Dict[str, Any]]
    stats: Dict[str, Any]
    request_id: str

class ScanResponse(BaseModel):
    """Response model for scan-only results"""
    success: bool
    entities_found: int
    processing_time: float
    spans: List[Dict[str, Any]]
    stats: Dict[str, Any]
    request_id: str

class BatchRedactionResponse(BaseModel):
    """Response model for batch redaction results"""
    success: bool
    results: List[RedactionResponse]
    total_processing_time: float
    batch_stats: Dict[str, Any]
    request_id: str

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    uptime: float
    cache_stats: Dict[str, Any]
    performance_summary: Dict[str, Any]

class FileRedactionRequest(BaseModel):
    """Request model for file redaction"""
    country: str = Field(default="AU", description="Country code")
    company: Optional[str] = Field(default=None, description="Company policy")
    detectors: List[str] = Field(default=["regex", "custom"], description="Detectors to use")
    masking_style: str = Field(default="hash", description="Redaction strategy")
    preserve_formatting: bool = Field(default=True, description="Preserve document formatting")

    # Advanced Accuracy Features
    enable_ensemble_voting: bool = Field(default=True, description="Enable weighted voting for conflict resolution")
    enable_context_propagation: bool = Field(default=True, description="Propagate high-confidence entities across document")
    allow_list: List[str] = Field(default_factory=list, description="List of terms to never redact")

# API App
app = FastAPI(
    title="ZeroPhi PII Redaction API",
    description="Enterprise-grade PII/PSI/PHI redaction service with security and compliance",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

def get_cloud_logging_config() -> Dict[str, Any]:
    """Get cloud logging configuration from environment variables"""
    config = {}
    
    # Azure
    if os.environ.get("AZURE_LOGGING_ENABLED", "false").lower() == "true":
        config["azure"] = {
            "enabled": True,
            "connection_string": os.environ.get("AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING")
        }
        
    # AWS
    if os.environ.get("AWS_LOGGING_ENABLED", "false").lower() == "true":
        config["aws"] = {
            "enabled": True,
            "region": os.environ.get("AWS_REGION", "us-east-1"),
            "log_group": os.environ.get("AWS_LOG_GROUP", "zerophix-audit"),
            "stream_name": os.environ.get("AWS_LOG_STREAM", "audit-stream")
        }
        
    # GCP
    if os.environ.get("GCP_LOGGING_ENABLED", "false").lower() == "true":
        config["gcp"] = {
            "enabled": True
            # GCP usually uses implicit auth or GOOGLE_APPLICATION_CREDENTIALS
        }
        
    return config

# Global state
app_state = {
    "start_time": datetime.now(),
    "request_count": 0,
    "pipeline_cache": {},
    "active_requests": {},
    "audit_logger": SecureAuditLogger(cloud_config=get_cloud_logging_config()),
    "zero_trust_validator": ZeroTrustValidator()
}

# Dependency for authentication (implement as needed)
async def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[str]:
    """Validate API key (customize based on your auth system)"""
    if not credentials:
        return None
    
    # In production, validate against your auth system
    # For now, accept any non-empty token
    return credentials.credentials if credentials.credentials else None

# Dependency for pipeline
async def get_pipeline(request: Union[RedactionRequest, BatchRedactionRequest, FileRedactionRequest]) -> RedactionPipeline:
    """Get or create redaction pipeline with caching"""
    # Extract advanced config
    enable_voting = getattr(request, 'enable_ensemble_voting', True)
    enable_context = getattr(request, 'enable_context_propagation', True)
    allow_list = tuple(sorted(getattr(request, 'allow_list', [])))
    
    # Create cache key based on configuration
    config_key = f"{request.country}_{request.company}_{hash(tuple(sorted(request.detectors)))}_{enable_voting}_{enable_context}_{hash(allow_list)}"
    
    if config_key not in app_state["pipeline_cache"]:
        config = RedactionConfig(
            country=request.country,
            company=request.company,
            detectors=request.detectors,
            masking_style=getattr(request, 'masking_style', 'hash'),
            parallel_detection=True,
            use_async=True,
            cache_detections=getattr(request, 'use_cache', True),
            enable_ensemble_voting=enable_voting,
            enable_context_propagation=enable_context,
            allow_list=list(allow_list)
        )
        pipeline = RedactionPipeline(config)
        app_state["pipeline_cache"][config_key] = pipeline
    
    return app_state["pipeline_cache"][config_key]

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logging.info("ZeroPhi API starting up...")
    app_state["start_time"] = datetime.now()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logging.info("ZeroPhi API shutting down...")
    # Clear pipeline cache
    app_state["pipeline_cache"].clear()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    uptime = (datetime.now() - app_state["start_time"]).total_seconds()
    
    # Get stats from a sample pipeline if available
    cache_stats = {}
    performance_summary = {}
    
    if app_state["pipeline_cache"]:
        sample_pipeline = next(iter(app_state["pipeline_cache"].values()))
        cache_stats = sample_pipeline.cache.get_stats() if sample_pipeline.cache else {}
        performance_summary = sample_pipeline.get_performance_summary()
    
    return HealthResponse(
        status="healthy",
        version="0.2.0",
        uptime=uptime,
        cache_stats=cache_stats,
        performance_summary=performance_summary
    )

@app.post("/redact", response_model=RedactionResponse)
async def redact_text(
    request: RedactionRequest,
    http_request: Request,
    pipeline: RedactionPipeline = Depends(get_pipeline),
    api_key: Optional[str] = Depends(get_api_key)
):
    """Redact PII/PSI/PHI from text with security and compliance validation"""
    request_id = str(uuid.uuid4())
    app_state["request_count"] += 1
    app_state["active_requests"][request_id] = {"start_time": datetime.now()}
    
    # Build user context for security validation
    user_context = {
        "user_id": request.user_id,
        "ip_address": http_request.client.host,
        "user_agent": http_request.headers.get("user-agent"),
        "authenticated": api_key is not None,
        "purpose": request.purpose,
        "lawful_basis": request.lawful_basis,
        "consent_obtained": request.consent_obtained,
        "data_classification": request.data_classification,
        "business_hours": 9 <= datetime.now().hour <= 17,  # Simple business hours check
        "authorized_user": api_key is not None,  # Basic authorization check
        "device_managed": True,  # Assume managed device for API access
        "internal_network": http_request.client.host.startswith("192.168.") or http_request.client.host.startswith("10."),
        "known_ip_address": True  # Could implement IP whitelist
    }
    
    # Log API access
    app_state["audit_logger"].log_api_access(
        endpoint="/redact",
        method="POST",
        status_code=200,  # Will update if error occurs
        user_id=request.user_id,
        ip_address=http_request.client.host,
        user_agent=http_request.headers.get("user-agent"),
        request_size=len(request.text)
    )
    
    try:
        start_time = datetime.now()
        
        # Perform redaction with security context
        result = pipeline.redact(request.text, user_context=user_context, session_id=request_id)
        
        # Check for security errors
        if "error" in result:
            app_state["audit_logger"].log_api_access(
                endpoint="/redact",
                method="POST",
                status_code=403,
                user_id=request.user_id,
                ip_address=http_request.client.host,
                response_size=len(str(result))
            )
            raise HTTPException(status_code=403, detail=result["error"])
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        response = RedactionResponse(
            success=True,
            redacted_text=result["text"],
            entities_found=len(result.get("spans", [])),
            processing_time=processing_time,
            spans=result.get("spans", []) if request.include_confidence else [],
            stats=result.get("stats", {}),
            request_id=request_id
        )
        
        # Log successful API response
        app_state["audit_logger"].log_api_access(
            endpoint="/redact",
            method="POST",
            status_code=200,
            user_id=request.user_id,
            ip_address=http_request.client.host,
            response_size=len(response.redacted_text)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        # Log API error
        app_state["audit_logger"].log_api_access(
            endpoint="/redact",
            method="POST",
            status_code=500,
            user_id=request.user_id,
            ip_address=http_request.client.host
        )
        
        app_state["audit_logger"].log_security_event(
            event_type="API_ERROR",
            description=f"Redaction API error: {str(e)}",
            severity="HIGH",
            user_id=request.user_id,
            additional_details={"request_id": request_id, "endpoint": "/redact"}
        )
        
        logging.error(f"Redaction failed for request {request_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Redaction failed: {str(e)}")
    
    finally:
        app_state["active_requests"].pop(request_id, None)

@app.post("/scan", response_model=ScanResponse)
async def scan_text(
    request: RedactionRequest,
    http_request: Request,
    pipeline: RedactionPipeline = Depends(get_pipeline),
    api_key: Optional[str] = Depends(get_api_key)
):
    """Scan text for PII/PSI/PHI without redaction"""
    request_id = str(uuid.uuid4())
    app_state["request_count"] += 1
    app_state["active_requests"][request_id] = {"start_time": datetime.now()}
    
    # Log API access
    app_state["audit_logger"].log_api_access(
        endpoint="/scan",
        method="POST",
        status_code=200,
        user_id=request.user_id,
        ip_address=http_request.client.host,
        user_agent=http_request.headers.get("user-agent"),
        request_size=len(request.text)
    )
    
    try:
        start_time = datetime.now()
        
        # Perform scan (detection only)
        # Note: pipeline.scan() returns list of entities, not the full result dict like redact()
        # But we might want to use redact() with a special flag or just use scan() and format it
        
        # Using pipeline.scan() directly
        entities = pipeline.scan(request.text)
        
        # Format spans
        spans = []
        for entity in entities:
            spans.append({
                "text": entity.text,
                "start": entity.start,
                "end": entity.end,
                "entity_type": entity.entity_type,
                "score": entity.score,
                "source": entity.source
            })
            
        processing_time = (datetime.now() - start_time).total_seconds()
        
        response = ScanResponse(
            success=True,
            entities_found=len(spans),
            processing_time=processing_time,
            spans=spans,
            stats={"detector_count": len(request.detectors)},
            request_id=request_id
        )
        
        return response
        
    except Exception as e:
        logging.error(f"Scan failed for request {request_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")
    
    finally:
        app_state["active_requests"].pop(request_id, None)

@app.post("/redact/batch", response_model=BatchRedactionResponse)
async def redact_batch(
    request: BatchRedactionRequest,
    background_tasks: BackgroundTasks,
    pipeline: RedactionPipeline = Depends(get_pipeline),
    api_key: Optional[str] = Depends(get_api_key)
):
    """Batch redact multiple texts"""
    request_id = str(uuid.uuid4())
    app_state["request_count"] += 1
    
    try:
        start_time = datetime.now()
        
        # Use batch processing
        if request.parallel_processing:
            results = await pipeline.batch_redact_async(request.texts)
        else:
            results = [pipeline.redact(text) for text in request.texts]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Convert results to response format
        response_results = []
        total_entities = 0
        
        for i, result in enumerate(results):
            if result:
                entities_found = len(result.get("spans", []))
                total_entities += entities_found
                
                response_results.append(RedactionResponse(
                    success=True,
                    redacted_text=result["text"],
                    entities_found=entities_found,
                    processing_time=result.get("stats", {}).get("total_time", 0),
                    spans=result.get("spans", []),
                    stats=result.get("stats", {}),
                    request_id=f"{request_id}-{i}"
                ))
            else:
                response_results.append(RedactionResponse(
                    success=False,
                    redacted_text="",
                    entities_found=0,
                    processing_time=0,
                    spans=[],
                    stats={},
                    request_id=f"{request_id}-{i}"
                ))
        
        batch_stats = {
            "total_texts": len(request.texts),
            "successful_redactions": sum(1 for r in response_results if r.success),
            "total_entities_found": total_entities,
            "average_processing_time": processing_time / len(request.texts),
            "throughput_texts_per_second": len(request.texts) / max(processing_time, 0.001)
        }
        
        return BatchRedactionResponse(
            success=True,
            results=response_results,
            total_processing_time=processing_time,
            batch_stats=batch_stats,
            request_id=request_id
        )
        
    except Exception as e:
        logging.error(f"Batch redaction failed for request {request_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch redaction failed: {str(e)}")

@app.post("/redact/file")
async def redact_file(
    file: UploadFile = File(...),
    country: str = "AU",
    company: Optional[str] = None,
    detectors: str = "regex,custom",  # comma-separated
    masking_style: str = "hash",
    preserve_formatting: bool = True,
    enable_ensemble_voting: bool = True,
    enable_context_propagation: bool = True,
    allow_list: Optional[str] = None, # comma-separated
    api_key: Optional[str] = Depends(get_api_key)
):
    """Redact PII/PSI/PHI from uploaded file"""
    request_id = str(uuid.uuid4())
    
    try:
        # Validate file type
        allowed_types = ["text/plain", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
        
        # Read file content
        content = await file.read()
        
        # Extract text based on file type
        if file.content_type == "text/plain":
            text = content.decode('utf-8')
        elif file.content_type == "application/pdf":
            # PDF processing (requires pypdf2)
            text = await extract_pdf_text(content)
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # DOCX processing (requires python-docx)
            text = await extract_docx_text(content)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Parse allow_list
        allow_list_items = [item.strip() for item in allow_list.split(',')] if allow_list else []

        # Create redaction request
        redaction_request = RedactionRequest(
            text=text,
            country=country,
            company=company,
            detectors=detectors.split(','),
            masking_style=masking_style,
            enable_ensemble_voting=enable_ensemble_voting,
            enable_context_propagation=enable_context_propagation,
            allow_list=allow_list_items
        )
        
        # Get pipeline and redact
        pipeline = await get_pipeline(redaction_request)
        result = pipeline.redact(text)
        
        # Return redacted content
        return {
            "success": True,
            "original_filename": file.filename,
            "redacted_text": result["text"],
            "entities_found": len(result.get("spans", [])),
            "file_stats": {
                "original_size": len(content),
                "text_length": len(text),
                "redacted_length": len(result["text"])
            },
            "request_id": request_id
        }
        
    except Exception as e:
        logging.error(f"File redaction failed for request {request_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File redaction failed: {str(e)}")

@app.get("/stats")
async def get_api_stats(api_key: Optional[str] = Depends(get_api_key)):
    """Get API usage statistics"""
    uptime = (datetime.now() - app_state["start_time"]).total_seconds()
    
    stats = {
        "uptime_seconds": uptime,
        "total_requests": app_state["request_count"],
        "active_requests": len(app_state["active_requests"]),
        "cached_pipelines": len(app_state["pipeline_cache"]),
        "requests_per_second": app_state["request_count"] / max(uptime, 1)
    }
    
    # Add performance stats from pipelines
    if app_state["pipeline_cache"]:
        pipeline_stats = []
        for key, pipeline in app_state["pipeline_cache"].items():
            performance_summary = pipeline.get_performance_summary()
            pipeline_stats.append({
                "config": key,
                "performance": performance_summary
            })
        stats["pipeline_performance"] = pipeline_stats
    
    return stats

@app.delete("/cache")
async def clear_cache(api_key: Optional[str] = Depends(get_api_key)):
    """Clear all caches"""
    try:
        # Clear pipeline caches
        for pipeline in app_state["pipeline_cache"].values():
            pipeline.clear_cache()
        
        # Clear pipeline cache
        app_state["pipeline_cache"].clear()
        
        return {"success": True, "message": "All caches cleared"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")

# Helper functions for file processing
async def extract_pdf_text(content: bytes) -> str:
    """Extract text from PDF content"""
    try:
        import PyPDF2
        import io
        
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except ImportError:
        raise HTTPException(status_code=500, detail="PDF processing not available. Install PyPDF2.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")

async def extract_docx_text(content: bytes) -> str:
    """Extract text from DOCX content"""
    try:
        from docx import Document
        import io
        
        doc = Document(io.BytesIO(content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except ImportError:
        raise HTTPException(status_code=500, detail="DOCX processing not available. Install python-docx.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DOCX extraction failed: {str(e)}")

# WebSocket endpoint for real-time redaction
@app.websocket("/ws/redact")
async def websocket_redact(websocket):
    """WebSocket endpoint for real-time redaction"""
    await websocket.accept()
    
    try:
        while True:
            # Receive text data
            data = await websocket.receive_json()
            
            # Validate request
            if "text" not in data:
                await websocket.send_json({"error": "Missing 'text' field"})
                continue
            
            # Create redaction request
            request = RedactionRequest(**data)
            pipeline = await get_pipeline(request)
            
            # Perform redaction
            result = pipeline.redact(request.text)
            
            # Send result
            await websocket.send_json({
                "success": True,
                "redacted_text": result["text"],
                "entities_found": len(result.get("spans", [])),
                "stats": result.get("stats", {})
            })
            
    except Exception as e:
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)