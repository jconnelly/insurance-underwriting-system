"""
LangSmith tracing integration for AI underwriting evaluations.

This module provides decorators and utilities for tracing AI evaluations
with LangSmith, capturing run IDs and providing shareable URLs.
"""

import os
import functools
from typing import Dict, Any, Optional, Callable, Union
from datetime import datetime
import uuid

from loguru import logger

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from langsmith import Client, traceable
    from langsmith.run_trees import RunTree
    LANGSMITH_AVAILABLE = True
except ImportError:
    logger.warning("LangSmith not available. Install with: pip install langsmith")
    LANGSMITH_AVAILABLE = False


class LangSmithTracer:
    """LangSmith tracing manager for underwriting evaluations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize LangSmith tracer.
        
        Args:
            config: LangSmith configuration dict
        """
        self.config = config or {}
        self.enabled = self._is_enabled()
        self.client = None
        self.project_name = self.config.get("project_name", "Insurance-Underwriting-System")
        self.base_url = self.config.get("base_url", "https://smith.langchain.com")
        
        if self.enabled and LANGSMITH_AVAILABLE:
            self._initialize_client()
    
    def _is_enabled(self) -> bool:
        """Check if LangSmith tracing is enabled."""
        # Check config setting
        if not self.config.get("enabled", True):
            return False
        
        # Check environment variable
        if os.getenv("LANGSMITH_TRACING_V2", "").lower() in ("false", "0", "no"):
            return False
        
        # Check if API key is available
        api_key = self.config.get("api_key") or os.getenv("LANGSMITH_API_KEY")
        if not api_key:
            logger.info("LangSmith API key not found. Tracing disabled.")
            return False
        
        return LANGSMITH_AVAILABLE
    
    def _initialize_client(self):
        """Initialize LangSmith client."""
        try:
            api_key = self.config.get("api_key") or os.getenv("LANGSMITH_API_KEY")
            api_url = self.config.get("api_url") or os.getenv("LANGSMITH_ENDPOINT")
            
            self.client = Client(
                api_key=api_key,
                api_url=api_url
            )
            
            # Set environment variables for langchain integration
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = self.project_name
            if api_key:
                os.environ["LANGCHAIN_API_KEY"] = api_key
            if api_url:
                os.environ["LANGCHAIN_ENDPOINT"] = api_url
            
            logger.info(f"LangSmith tracing initialized for project: {self.project_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangSmith client: {e}")
            self.enabled = False
    
    def trace_evaluation(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[list] = None
    ):
        """Decorator for tracing AI evaluations.
        
        Args:
            name: Name of the traced operation
            metadata: Additional metadata to include
            tags: Tags for the run
        """
        def decorator(func: Callable):
            if not self.enabled:
                # Return unmodified function if tracing disabled
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    result = func(*args, **kwargs)
                    # Add empty run info if tracing disabled
                    if hasattr(result, '__dict__'):
                        result.langsmith_run_id = None
                        result.langsmith_run_url = None
                    return result
                return wrapper
            
            @traceable(name=name, project_name=self.project_name, metadata=metadata, tags=tags)
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    result = await func(*args, **kwargs)
                    
                    # Capture run information
                    run_id = self._get_current_run_id()
                    run_url = self._build_run_url(run_id) if run_id else None
                    
                    # Attach run info to result if possible
                    if hasattr(result, '__dict__'):
                        result.langsmith_run_id = run_id
                        result.langsmith_run_url = run_url
                    
                    logger.info(f"LangSmith trace completed: {name}, Run ID: {run_id}")
                    return result
                    
                except Exception as e:
                    logger.error(f"Error in traced function {name}: {e}")
                    raise
            
            @traceable(name=name, project_name=self.project_name, metadata=metadata, tags=tags)
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    
                    # Capture run information
                    run_id = self._get_current_run_id()
                    run_url = self._build_run_url(run_id) if run_id else None
                    
                    # Attach run info to result if possible
                    if hasattr(result, '__dict__'):
                        result.langsmith_run_id = run_id
                        result.langsmith_run_url = run_url
                    
                    logger.info(f"LangSmith trace completed: {name}, Run ID: {run_id}")
                    return result
                    
                except Exception as e:
                    logger.error(f"Error in traced function {name}: {e}")
                    raise
            
            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def trace_batch_evaluation(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[list] = None
    ):
        """Decorator for tracing batch AI evaluations.
        
        Args:
            name: Name of the traced operation
            metadata: Additional metadata to include
            tags: Tags for the run
        """
        def decorator(func: Callable):
            if not self.enabled:
                # Return unmodified function if tracing disabled
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    result = func(*args, **kwargs)
                    # Add empty run info to batch results
                    if isinstance(result, list):
                        for item in result:
                            if hasattr(item, '__dict__'):
                                item.langsmith_run_id = None
                                item.langsmith_run_url = None
                    return result
                return wrapper
            
            @traceable(name=name, project_name=self.project_name, metadata=metadata, tags=tags)
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    result = await func(*args, **kwargs)
                    
                    # Capture run information for batch
                    run_id = self._get_current_run_id()
                    run_url = self._build_run_url(run_id) if run_id else None
                    
                    # Attach run info to all results in batch
                    if isinstance(result, list):
                        for item in result:
                            if hasattr(item, '__dict__'):
                                item.langsmith_batch_run_id = run_id
                                item.langsmith_batch_run_url = run_url
                    
                    logger.info(f"LangSmith batch trace completed: {name}, Run ID: {run_id}")
                    return result
                    
                except Exception as e:
                    logger.error(f"Error in traced batch function {name}: {e}")
                    raise
            
            @traceable(name=name, project_name=self.project_name, metadata=metadata, tags=tags)
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    
                    # Capture run information for batch
                    run_id = self._get_current_run_id()
                    run_url = self._build_run_url(run_id) if run_id else None
                    
                    # Attach run info to all results in batch
                    if isinstance(result, list):
                        for item in result:
                            if hasattr(item, '__dict__'):
                                item.langsmith_batch_run_id = run_id
                                item.langsmith_batch_run_url = run_url
                    
                    logger.info(f"LangSmith batch trace completed: {name}, Run ID: {run_id}")
                    return result
                    
                except Exception as e:
                    logger.error(f"Error in traced batch function {name}: {e}")
                    raise
            
            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def trace_comparison(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[list] = None
    ):
        """Decorator for tracing A/B testing comparisons.
        
        Args:
            name: Name of the traced operation
            metadata: Additional metadata to include
            tags: Tags for the run
        """
        def decorator(func: Callable):
            if not self.enabled:
                # Return unmodified function if tracing disabled
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    result = func(*args, **kwargs)
                    # Add empty run info to comparison results
                    if isinstance(result, dict):
                        for key, value in result.items():
                            if hasattr(value, '__dict__'):
                                value.langsmith_comparison_run_id = None
                                value.langsmith_comparison_run_url = None
                    return result
                return wrapper
            
            @traceable(name=name, project_name=self.project_name, metadata=metadata, tags=tags)
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    result = await func(*args, **kwargs)
                    
                    # Capture run information for comparison
                    run_id = self._get_current_run_id()
                    run_url = self._build_run_url(run_id) if run_id else None
                    
                    # Attach run info to comparison results
                    if isinstance(result, dict):
                        for key, value in result.items():
                            if hasattr(value, '__dict__'):
                                value.langsmith_comparison_run_id = run_id
                                value.langsmith_comparison_run_url = run_url
                    
                    logger.info(f"LangSmith comparison trace completed: {name}, Run ID: {run_id}")
                    return result
                    
                except Exception as e:
                    logger.error(f"Error in traced comparison function {name}: {e}")
                    raise
            
            @traceable(name=name, project_name=self.project_name, metadata=metadata, tags=tags)
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    
                    # Capture run information for comparison
                    run_id = self._get_current_run_id()
                    run_url = self._build_run_url(run_id) if run_id else None
                    
                    # Attach run info to comparison results
                    if isinstance(result, dict):
                        for key, value in result.items():
                            if hasattr(value, '__dict__'):
                                value.langsmith_comparison_run_id = run_id
                                value.langsmith_comparison_run_url = run_url
                    
                    logger.info(f"LangSmith comparison trace completed: {name}, Run ID: {run_id}")
                    return result
                    
                except Exception as e:
                    logger.error(f"Error in traced comparison function {name}: {e}")
                    raise
            
            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def _get_current_run_id(self) -> Optional[str]:
        """Get the current LangSmith run ID."""
        try:
            # Try to get run ID from current context
            from langsmith.run_helpers import get_current_run_tree
            
            current_run = get_current_run_tree()
            if current_run and hasattr(current_run, 'id'):
                return str(current_run.id)
            
            # Fallback: check environment or thread-local storage
            run_id = os.getenv("LANGSMITH_RUN_ID")
            if run_id:
                return run_id
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not get current run ID: {e}")
            return None
    
    def _build_run_url(self, run_id: str) -> str:
        """Build shareable LangSmith run URL.
        
        Args:
            run_id: LangSmith run ID
            
        Returns:
            Shareable URL for the run
        """
        if not run_id:
            return None
        
        # Build public URL (similar to the example provided)
        return f"{self.base_url}/public/{run_id}/r"
    
    def create_manual_trace(
        self,
        name: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[list] = None
    ) -> Optional[str]:
        """Create a manual trace entry.
        
        Args:
            name: Name of the operation
            inputs: Input data
            outputs: Output data
            metadata: Additional metadata
            tags: Tags for the run
            
        Returns:
            Run ID if successful, None otherwise
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            # Create a manual run
            run = self.client.create_run(
                name=name,
                project_name=self.project_name,
                inputs=inputs,
                outputs=outputs,
                run_type="llm",
                metadata=metadata or {},
                tags=tags or []
            )
            
            return str(run.id) if run else None
            
        except Exception as e:
            logger.error(f"Failed to create manual trace: {e}")
            return None
    
    def get_run_info(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific run.
        
        Args:
            run_id: LangSmith run ID
            
        Returns:
            Run information dict or None
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            run = self.client.read_run(run_id)
            return {
                "id": str(run.id),
                "name": run.name,
                "url": self._build_run_url(str(run.id)),
                "status": getattr(run, 'status', 'unknown'),
                "start_time": run.start_time,
                "end_time": run.end_time,
                "metadata": run.extra or {}
            }
        except Exception as e:
            logger.error(f"Failed to get run info for {run_id}: {e}")
            return None


# Global tracer instance
_global_tracer: Optional[LangSmithTracer] = None


def get_tracer(config: Optional[Dict[str, Any]] = None) -> LangSmithTracer:
    """Get global LangSmith tracer instance.
    
    Args:
        config: Optional configuration to initialize tracer
        
    Returns:
        LangSmith tracer instance
    """
    global _global_tracer
    
    if _global_tracer is None:
        _global_tracer = LangSmithTracer(config)
    
    return _global_tracer


def trace_ai_evaluation(
    name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[list] = None
):
    """Convenience decorator for tracing AI evaluations.
    
    Args:
        name: Name of the operation (auto-generated if None)
        metadata: Additional metadata
        tags: Tags for the run
    """
    def decorator(func: Callable):
        operation_name = name or f"ai_evaluation_{func.__name__}"
        tracer = get_tracer()
        return tracer.trace_evaluation(
            operation_name,
            metadata=metadata,
            tags=tags
        )(func)
    
    return decorator


def trace_batch_evaluation(
    name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[list] = None
):
    """Convenience decorator for tracing batch evaluations.
    
    Args:
        name: Name of the operation (auto-generated if None)
        metadata: Additional metadata
        tags: Tags for the run
    """
    def decorator(func: Callable):
        operation_name = name or f"batch_evaluation_{func.__name__}"
        tracer = get_tracer()
        return tracer.trace_batch_evaluation(
            operation_name,
            metadata=metadata,
            tags=tags
        )(func)
    
    return decorator


def trace_ab_testing(
    name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[list] = None
):
    """Convenience decorator for tracing A/B testing comparisons.
    
    Args:
        name: Name of the operation (auto-generated if None)
        metadata: Additional metadata
        tags: Tags for the run
    """
    def decorator(func: Callable):
        operation_name = name or f"ab_testing_{func.__name__}"
        tracer = get_tracer()
        return tracer.trace_comparison(
            operation_name,
            metadata=metadata,
            tags=tags
        )(func)
    
    return decorator