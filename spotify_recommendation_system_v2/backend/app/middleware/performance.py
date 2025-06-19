"""
Performance monitoring middleware
"""
import time
import psutil
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from loguru import logger


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for monitoring application performance
    """
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Monitor request performance
        """
        # Get initial system metrics
        start_time = time.time()
        start_cpu = psutil.cpu_percent()
        start_memory = psutil.virtual_memory().percent
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate metrics
            process_time = time.time() - start_time
            end_cpu = psutil.cpu_percent()
            end_memory = psutil.virtual_memory().percent
            
            # Add performance headers
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            response.headers["X-CPU-Usage"] = f"{end_cpu:.1f}"
            response.headers["X-Memory-Usage"] = f"{end_memory:.1f}"
            
            # Log slow requests
            if process_time > self.slow_request_threshold:
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} - "
                    f"Time: {process_time:.3f}s, CPU: {start_cpu:.1f}% -> {end_cpu:.1f}%, "
                    f"Memory: {start_memory:.1f}% -> {end_memory:.1f}%"
                )
            
            # Log performance metrics for monitoring
            if hasattr(request.state, 'request_id'):
                logger.debug(
                    f"[{request.state.request_id}] Performance - "
                    f"Time: {process_time:.3f}s, CPU: {end_cpu:.1f}%, Memory: {end_memory:.1f}%"
                )
            
            return response
            
        except Exception as e:
            # Calculate time even for failed requests
            process_time = time.time() - start_time
            
            # Log performance for failed requests
            logger.error(
                f"Failed request performance: {request.method} {request.url.path} - "
                f"Time: {process_time:.3f}s, Error: {str(e)}"
            )
            
            # Re-raise the exception
            raise 