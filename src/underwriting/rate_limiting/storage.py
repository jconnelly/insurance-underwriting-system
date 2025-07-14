"""
File-based storage system for rate limiting data.

This module provides persistent storage for rate limiting information,
usage tracking, and analytics data with automatic cleanup and backup.
"""

import json
import os
import time
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from threading import Lock

from loguru import logger


@dataclass
class UsageRecord:
    """Individual usage record for tracking."""
    timestamp: float
    user_id: Optional[str] = None
    operation_type: str = "default"
    resource_consumed: int = 1
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RateLimitEntry:
    """Rate limit entry with usage tracking."""
    identifier: str
    operation_type: str
    usage_records: List[UsageRecord]
    total_usage: int
    first_usage: float
    last_usage: float
    blocked_count: int = 0
    override_active: bool = False
    override_expiry: Optional[float] = None


class RateLimitStorage:
    """File-based storage for rate limiting data."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize rate limit storage.
        
        Args:
            config: Storage configuration dictionary
        """
        self.config = config
        self.data_directory = Path(config.get("data_directory", "rate_limit_data"))
        self.cleanup_interval = config.get("cleanup_interval_hours", 24) * 3600
        self.retention_days = config.get("retention_days", 90)
        self.backup_enabled = config.get("backup_enabled", True)
        self.backup_interval = config.get("backup_interval_hours", 12) * 3600
        
        # Thread safety
        self._lock = Lock()
        
        # Initialize storage
        self._initialize_storage()
        
        # Last cleanup and backup timestamps
        self._last_cleanup = time.time()
        self._last_backup = time.time()
        
        logger.info(f"Rate limit storage initialized at {self.data_directory}")
    
    def _initialize_storage(self):
        """Initialize storage directory and files."""
        try:
            # Create main directory
            self.data_directory.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            (self.data_directory / "usage").mkdir(exist_ok=True)
            (self.data_directory / "analytics").mkdir(exist_ok=True)
            (self.data_directory / "backups").mkdir(exist_ok=True)
            (self.data_directory / "overrides").mkdir(exist_ok=True)
            
            # Create index file if it doesn't exist
            index_file = self.data_directory / "index.json"
            if not index_file.exists():
                initial_index = {
                    "created": time.time(),
                    "last_updated": time.time(),
                    "version": "1.0",
                    "entries": {}
                }
                with open(index_file, 'w') as f:
                    json.dump(initial_index, f, indent=2)
            
            logger.info("Rate limit storage initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize rate limit storage: {e}")
            raise
    
    def get_usage_data(self, identifier: str, operation_type: str) -> Optional[RateLimitEntry]:
        """Get usage data for a specific identifier and operation.
        
        Args:
            identifier: Unique identifier (e.g., user ID, IP address)
            operation_type: Type of operation being rate limited
            
        Returns:
            Rate limit entry if found, None otherwise
        """
        with self._lock:
            try:
                file_path = self._get_usage_file_path(identifier, operation_type)
                if not file_path.exists():
                    return None
                
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Convert back to RateLimitEntry
                usage_records = [
                    UsageRecord(**record) for record in data.get("usage_records", [])
                ]
                
                return RateLimitEntry(
                    identifier=data["identifier"],
                    operation_type=data["operation_type"],
                    usage_records=usage_records,
                    total_usage=data["total_usage"],
                    first_usage=data["first_usage"],
                    last_usage=data["last_usage"],
                    blocked_count=data.get("blocked_count", 0),
                    override_active=data.get("override_active", False),
                    override_expiry=data.get("override_expiry")
                )
                
            except Exception as e:
                logger.error(f"Failed to get usage data for {identifier}:{operation_type}: {e}")
                return None
    
    def save_usage_data(self, entry: RateLimitEntry) -> bool:
        """Save usage data to storage.
        
        Args:
            entry: Rate limit entry to save
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                file_path = self._get_usage_file_path(entry.identifier, entry.operation_type)
                
                # Convert to serializable format
                data = {
                    "identifier": entry.identifier,
                    "operation_type": entry.operation_type,
                    "usage_records": [asdict(record) for record in entry.usage_records],
                    "total_usage": entry.total_usage,
                    "first_usage": entry.first_usage,
                    "last_usage": entry.last_usage,
                    "blocked_count": entry.blocked_count,
                    "override_active": entry.override_active,
                    "override_expiry": entry.override_expiry
                }
                
                # Ensure directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Save data
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                # Update index
                self._update_index(entry.identifier, entry.operation_type)
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to save usage data: {e}")
                return False
    
    def record_usage(self, identifier: str, operation_type: str, 
                    user_id: Optional[str] = None, resource_consumed: int = 1,
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Record a usage event.
        
        Args:
            identifier: Unique identifier
            operation_type: Type of operation
            user_id: Optional user identifier
            resource_consumed: Amount of resource consumed
            metadata: Optional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get existing entry or create new one
            entry = self.get_usage_data(identifier, operation_type)
            if entry is None:
                entry = RateLimitEntry(
                    identifier=identifier,
                    operation_type=operation_type,
                    usage_records=[],
                    total_usage=0,
                    first_usage=time.time(),
                    last_usage=time.time()
                )
            
            # Add usage record
            usage_record = UsageRecord(
                timestamp=time.time(),
                user_id=user_id,
                operation_type=operation_type,
                resource_consumed=resource_consumed,
                metadata=metadata
            )
            
            entry.usage_records.append(usage_record)
            entry.total_usage += resource_consumed
            entry.last_usage = time.time()
            
            # Save updated entry
            return self.save_usage_data(entry)
            
        except Exception as e:
            logger.error(f"Failed to record usage: {e}")
            return False
    
    def record_block(self, identifier: str, operation_type: str) -> bool:
        """Record a blocked request.
        
        Args:
            identifier: Unique identifier
            operation_type: Type of operation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            entry = self.get_usage_data(identifier, operation_type)
            if entry is None:
                entry = RateLimitEntry(
                    identifier=identifier,
                    operation_type=operation_type,
                    usage_records=[],
                    total_usage=0,
                    first_usage=time.time(),
                    last_usage=time.time()
                )
            
            entry.blocked_count += 1
            entry.last_usage = time.time()
            
            return self.save_usage_data(entry)
            
        except Exception as e:
            logger.error(f"Failed to record block: {e}")
            return False
    
    def get_usage_in_window(self, identifier: str, operation_type: str, 
                           window_start: float, window_end: float) -> List[UsageRecord]:
        """Get usage records within a time window.
        
        Args:
            identifier: Unique identifier
            operation_type: Type of operation
            window_start: Start timestamp
            window_end: End timestamp
            
        Returns:
            List of usage records in the window
        """
        entry = self.get_usage_data(identifier, operation_type)
        if entry is None:
            return []
        
        return [
            record for record in entry.usage_records
            if window_start <= record.timestamp <= window_end
        ]
    
    def get_total_usage_in_window(self, identifier: str, operation_type: str,
                                 window_start: float, window_end: float) -> int:
        """Get total usage in a time window.
        
        Args:
            identifier: Unique identifier
            operation_type: Type of operation
            window_start: Start timestamp
            window_end: End timestamp
            
        Returns:
            Total usage in the window
        """
        records = self.get_usage_in_window(identifier, operation_type, window_start, window_end)
        return sum(record.resource_consumed for record in records)
    
    def cleanup_old_data(self) -> int:
        """Clean up old data based on retention policy.
        
        Returns:
            Number of records cleaned up
        """
        if time.time() - self._last_cleanup < self.cleanup_interval:
            return 0
        
        with self._lock:
            try:
                cleanup_count = 0
                cutoff_time = time.time() - (self.retention_days * 24 * 3600)
                
                # Get all usage files
                usage_dir = self.data_directory / "usage"
                for file_path in usage_dir.rglob("*.json"):
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        # Filter out old records
                        original_count = len(data.get("usage_records", []))
                        data["usage_records"] = [
                            record for record in data.get("usage_records", [])
                            if record.get("timestamp", 0) > cutoff_time
                        ]
                        
                        # Update total usage
                        data["total_usage"] = sum(
                            record.get("resource_consumed", 1) 
                            for record in data["usage_records"]
                        )
                        
                        # Save if changed
                        if len(data["usage_records"]) < original_count:
                            if data["usage_records"]:
                                with open(file_path, 'w') as f:
                                    json.dump(data, f, indent=2)
                            else:
                                # Remove empty files
                                file_path.unlink()
                            
                            cleanup_count += original_count - len(data["usage_records"])
                    
                    except Exception as e:
                        logger.error(f"Failed to cleanup file {file_path}: {e}")
                        continue
                
                self._last_cleanup = time.time()
                logger.info(f"Cleaned up {cleanup_count} old usage records")
                
                return cleanup_count
                
            except Exception as e:
                logger.error(f"Failed to cleanup old data: {e}")
                return 0
    
    def backup_data(self) -> bool:
        """Create backup of rate limiting data.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.backup_enabled:
            return True
        
        if time.time() - self._last_backup < self.backup_interval:
            return True
        
        try:
            backup_dir = self.data_directory / "backups"
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = backup_dir / backup_name
            
            # Create backup
            shutil.copytree(self.data_directory / "usage", backup_path)
            
            # Cleanup old backups (keep last 10)
            backups = sorted(backup_dir.glob("backup_*"), key=lambda x: x.stat().st_mtime)
            for old_backup in backups[:-10]:
                shutil.rmtree(old_backup)
            
            self._last_backup = time.time()
            logger.info(f"Created backup: {backup_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def get_analytics_data(self, operation_type: Optional[str] = None,
                          start_time: Optional[float] = None,
                          end_time: Optional[float] = None) -> Dict[str, Any]:
        """Get analytics data for reporting.
        
        Args:
            operation_type: Optional filter by operation type
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            Analytics data dictionary
        """
        try:
            analytics = {
                "total_requests": 0,
                "total_blocked": 0,
                "unique_identifiers": set(),
                "operation_types": {},
                "hourly_distribution": {},
                "daily_distribution": {},
                "top_users": {}
            }
            
            # Process all usage files
            usage_dir = self.data_directory / "usage"
            for file_path in usage_dir.rglob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Filter by operation type if specified
                    if operation_type and data.get("operation_type") != operation_type:
                        continue
                    
                    identifier = data.get("identifier", "unknown")
                    op_type = data.get("operation_type", "unknown")
                    
                    analytics["unique_identifiers"].add(identifier)
                    analytics["total_blocked"] += data.get("blocked_count", 0)
                    
                    # Process usage records
                    for record in data.get("usage_records", []):
                        timestamp = record.get("timestamp", 0)
                        
                        # Apply time filters
                        if start_time and timestamp < start_time:
                            continue
                        if end_time and timestamp > end_time:
                            continue
                        
                        analytics["total_requests"] += 1
                        
                        # Operation type stats
                        if op_type not in analytics["operation_types"]:
                            analytics["operation_types"][op_type] = 0
                        analytics["operation_types"][op_type] += 1
                        
                        # Time distribution
                        dt = datetime.fromtimestamp(timestamp)
                        hour_key = dt.strftime("%Y-%m-%d %H:00")
                        day_key = dt.strftime("%Y-%m-%d")
                        
                        if hour_key not in analytics["hourly_distribution"]:
                            analytics["hourly_distribution"][hour_key] = 0
                        analytics["hourly_distribution"][hour_key] += 1
                        
                        if day_key not in analytics["daily_distribution"]:
                            analytics["daily_distribution"][day_key] = 0
                        analytics["daily_distribution"][day_key] += 1
                        
                        # Top users
                        if identifier not in analytics["top_users"]:
                            analytics["top_users"][identifier] = 0
                        analytics["top_users"][identifier] += 1
                
                except Exception as e:
                    logger.error(f"Failed to process analytics file {file_path}: {e}")
                    continue
            
            # Convert set to count
            analytics["unique_identifiers"] = len(analytics["unique_identifiers"])
            
            # Sort top users
            analytics["top_users"] = dict(
                sorted(analytics["top_users"].items(), key=lambda x: x[1], reverse=True)[:10]
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get analytics data: {e}")
            return {}
    
    def _get_usage_file_path(self, identifier: str, operation_type: str) -> Path:
        """Get file path for usage data.
        
        Args:
            identifier: Unique identifier
            operation_type: Type of operation
            
        Returns:
            Path to usage file
        """
        # Create safe filename
        safe_identifier = "".join(c for c in identifier if c.isalnum() or c in "._-")
        safe_operation = "".join(c for c in operation_type if c.isalnum() or c in "._-")
        
        return self.data_directory / "usage" / f"{safe_identifier}_{safe_operation}.json"
    
    def _update_index(self, identifier: str, operation_type: str):
        """Update the index with entry information.
        
        Args:
            identifier: Unique identifier
            operation_type: Type of operation
        """
        try:
            index_file = self.data_directory / "index.json"
            
            # Load existing index
            with open(index_file, 'r') as f:
                index = json.load(f)
            
            # Update entry
            key = f"{identifier}:{operation_type}"
            index["entries"][key] = {
                "identifier": identifier,
                "operation_type": operation_type,
                "last_updated": time.time()
            }
            
            index["last_updated"] = time.time()
            
            # Save updated index
            with open(index_file, 'w') as f:
                json.dump(index, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to update index: {e}")
    
    def get_all_identifiers(self) -> List[Tuple[str, str]]:
        """Get all identifiers and operation types.
        
        Returns:
            List of (identifier, operation_type) tuples
        """
        try:
            index_file = self.data_directory / "index.json"
            
            with open(index_file, 'r') as f:
                index = json.load(f)
            
            return [
                (entry["identifier"], entry["operation_type"])
                for entry in index.get("entries", {}).values()
            ]
            
        except Exception as e:
            logger.error(f"Failed to get all identifiers: {e}")
            return []
    
    def clear_all_data(self) -> bool:
        """Clear all rate limiting data (admin function).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove all usage files
            usage_dir = self.data_directory / "usage"
            if usage_dir.exists():
                shutil.rmtree(usage_dir)
                usage_dir.mkdir()
            
            # Reset index
            index_file = self.data_directory / "index.json"
            initial_index = {
                "created": time.time(),
                "last_updated": time.time(),
                "version": "1.0",
                "entries": {}
            }
            with open(index_file, 'w') as f:
                json.dump(initial_index, f, indent=2)
            
            logger.info("All rate limiting data cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear all data: {e}")
            return False