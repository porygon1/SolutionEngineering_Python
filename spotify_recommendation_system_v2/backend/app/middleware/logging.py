"""
Logging middleware for request/response logging
"""
import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from loguru import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log details
        """
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        
        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"[{request_id}] {response.status_code} - "
                f"{process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"[{request_id}] ERROR - {process_time:.3f}s - {str(e)}"
            )
            
            # Re-raise the exception
            raise 