"""
Admin controls and override system for rate limiting.

This module provides administrative capabilities for managing rate limits including:
- Override system for testing and emergency situations
- Bulk operations for rate limit management
- Configuration management
- Emergency controls
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from .storage import RateLimitStorage, RateLimitEntry


@dataclass
class AdminOverrideRequest:
    """Request for admin override."""
    identifier: str
    operation_type: str
    justification: str
    duration_hours: int = 24
    requested_by: str = "admin"
    requested_at: float = None
    
    def __post_init__(self):
        if self.requested_at is None:
            self.requested_at = time.time()


@dataclass
class AdminAction:
    """Record of admin action."""
    action_type: str
    identifier: str
    operation_type: str
    details: Dict[str, Any]
    performed_by: str
    performed_at: float
    success: bool


class AdminOverride:
    """Admin override system for rate limiting."""
    
    def __init__(self, storage: RateLimitStorage, config: Dict[str, Any]):
        """Initialize admin override system.
        
        Args:
            storage: Rate limit storage instance
            config: Admin configuration
        """
        self.storage = storage
        self.config = config
        self.override_enabled = config.get("override_enabled", True)
        self.emergency_override_enabled = config.get("emergency_override_enabled", True)
        self.require_justification = config.get("require_justification", True)
        
        # Admin limits (higher than regular limits)
        self.admin_daily_limit = config.get("admin_daily_limit", 50000)
        self.admin_weekly_limit = config.get("admin_weekly_limit", 200000)
        self.admin_monthly_limit = config.get("admin_monthly_limit", 800000)
        
        # Initialize admin log
        self.admin_log_path = storage.data_directory / "admin_log.json"
        self._initialize_admin_log()
        
        logger.info("Admin override system initialized")
    
    def _initialize_admin_log(self):
        """Initialize admin action log."""
        if not self.admin_log_path.exists():
            initial_log = {
                "created": time.time(),
                "actions": []
            }
            with open(self.admin_log_path, 'w') as f:
                json.dump(initial_log, f, indent=2)
    
    def _log_admin_action(self, action: AdminAction):
        """Log admin action."""
        try:
            with open(self.admin_log_path, 'r') as f:
                log_data = json.load(f)
            
            log_data["actions"].append({
                "action_type": action.action_type,
                "identifier": action.identifier,
                "operation_type": action.operation_type,
                "details": action.details,
                "performed_by": action.performed_by,
                "performed_at": action.performed_at,
                "success": action.success,
                "timestamp_human": datetime.fromtimestamp(action.performed_at).isoformat()
            })
            
            # Keep only last 1000 actions
            log_data["actions"] = log_data["actions"][-1000:]
            
            with open(self.admin_log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")
    
    def request_override(self, request: AdminOverrideRequest) -> bool:
        """Request admin override for rate limiting.
        
        Args:
            request: Admin override request
            
        Returns:
            True if override granted, False otherwise
        """
        if not self.override_enabled:
            logger.warning("Admin override is disabled")
            return False
        
        if self.require_justification and not request.justification:
            logger.warning("Justification required for admin override")
            return False
        
        try:
            # Get or create rate limit entry
            entry = self.storage.get_usage_data(request.identifier, request.operation_type)
            if entry is None:
                entry = RateLimitEntry(
                    identifier=request.identifier,
                    operation_type=request.operation_type,
                    usage_records=[],
                    total_usage=0,
                    first_usage=time.time(),
                    last_usage=time.time()
                )
            
            # Set override
            entry.override_active = True
            entry.override_expiry = time.time() + (request.duration_hours * 3600)
            
            # Save entry
            success = self.storage.save_usage_data(entry)
            
            # Log admin action
            action = AdminAction(
                action_type="override_granted",
                identifier=request.identifier,
                operation_type=request.operation_type,
                details={
                    "justification": request.justification,
                    "duration_hours": request.duration_hours,
                    "expiry_time": entry.override_expiry
                },
                performed_by=request.requested_by,
                performed_at=time.time(),
                success=success
            )
            self._log_admin_action(action)
            
            if success:
                logger.info(f"Admin override granted for {request.identifier}:{request.operation_type}")
            else:
                logger.error(f"Failed to grant admin override for {request.identifier}:{request.operation_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error requesting admin override: {e}")
            return False
    
    def revoke_override(self, identifier: str, operation_type: str, 
                       admin_user: str = "admin") -> bool:
        """Revoke admin override.
        
        Args:
            identifier: Unique identifier
            operation_type: Operation type
            admin_user: Admin user performing the action
            
        Returns:
            True if successfully revoked, False otherwise
        """
        try:
            entry = self.storage.get_usage_data(identifier, operation_type)
            if entry is None:
                logger.warning(f"No rate limit entry found for {identifier}:{operation_type}")
                return False
            
            # Remove override
            entry.override_active = False
            entry.override_expiry = None
            
            # Save entry
            success = self.storage.save_usage_data(entry)
            
            # Log admin action
            action = AdminAction(
                action_type="override_revoked",
                identifier=identifier,
                operation_type=operation_type,
                details={},
                performed_by=admin_user,
                performed_at=time.time(),
                success=success
            )
            self._log_admin_action(action)
            
            if success:
                logger.info(f"Admin override revoked for {identifier}:{operation_type}")
            else:
                logger.error(f"Failed to revoke admin override for {identifier}:{operation_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error revoking admin override: {e}")
            return False
    
    def emergency_override(self, operation_type: str, duration_hours: int = 1,
                          admin_user: str = "admin", justification: str = "Emergency") -> bool:
        """Emergency override for all users of an operation type.
        
        Args:
            operation_type: Operation type to override
            duration_hours: Duration of override in hours
            admin_user: Admin user performing the action
            justification: Justification for emergency override
            
        Returns:
            True if successful, False otherwise
        """
        if not self.emergency_override_enabled:
            logger.warning("Emergency override is disabled")
            return False
        
        try:
            # Get all identifiers for this operation type
            all_identifiers = self.storage.get_all_identifiers()
            affected_identifiers = [
                identifier for identifier, op_type in all_identifiers 
                if op_type == operation_type
            ]
            
            success_count = 0
            
            for identifier in affected_identifiers:
                request = AdminOverrideRequest(
                    identifier=identifier,
                    operation_type=operation_type,
                    justification=f"Emergency override: {justification}",
                    duration_hours=duration_hours,
                    requested_by=admin_user
                )
                
                if self.request_override(request):
                    success_count += 1
            
            # Log emergency action
            action = AdminAction(
                action_type="emergency_override",
                identifier="*",
                operation_type=operation_type,
                details={
                    "justification": justification,
                    "duration_hours": duration_hours,
                    "affected_identifiers": len(affected_identifiers),
                    "successful_overrides": success_count
                },
                performed_by=admin_user,
                performed_at=time.time(),
                success=success_count > 0
            )
            self._log_admin_action(action)
            
            logger.info(f"Emergency override applied to {success_count}/{len(affected_identifiers)} identifiers")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error applying emergency override: {e}")
            return False
    
    def reset_usage(self, identifier: str, operation_type: str, 
                   admin_user: str = "admin") -> bool:
        """Reset usage data for identifier and operation type.
        
        Args:
            identifier: Unique identifier
            operation_type: Operation type
            admin_user: Admin user performing the action
            
        Returns:
            True if successful, False otherwise
        """
        try:
            entry = self.storage.get_usage_data(identifier, operation_type)
            if entry is None:
                logger.warning(f"No rate limit entry found for {identifier}:{operation_type}")
                return False
            
            # Reset usage data
            old_usage = entry.total_usage
            entry.usage_records = []
            entry.total_usage = 0
            entry.blocked_count = 0
            entry.first_usage = time.time()
            entry.last_usage = time.time()
            
            # Save entry
            success = self.storage.save_usage_data(entry)
            
            # Log admin action
            action = AdminAction(
                action_type="usage_reset",
                identifier=identifier,
                operation_type=operation_type,
                details={
                    "old_usage": old_usage,
                    "old_blocked_count": entry.blocked_count
                },
                performed_by=admin_user,
                performed_at=time.time(),
                success=success
            )
            self._log_admin_action(action)
            
            if success:
                logger.info(f"Usage reset for {identifier}:{operation_type}")
            else:
                logger.error(f"Failed to reset usage for {identifier}:{operation_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error resetting usage: {e}")
            return False
    
    def bulk_reset_usage(self, operation_type: str, admin_user: str = "admin") -> int:
        """Reset usage data for all identifiers of an operation type.
        
        Args:
            operation_type: Operation type to reset
            admin_user: Admin user performing the action
            
        Returns:
            Number of identifiers reset
        """
        try:
            all_identifiers = self.storage.get_all_identifiers()
            target_identifiers = [
                identifier for identifier, op_type in all_identifiers 
                if op_type == operation_type
            ]
            
            success_count = 0
            
            for identifier in target_identifiers:
                if self.reset_usage(identifier, operation_type, admin_user):
                    success_count += 1
            
            # Log bulk action
            action = AdminAction(
                action_type="bulk_usage_reset",
                identifier="*",
                operation_type=operation_type,
                details={
                    "target_identifiers": len(target_identifiers),
                    "successful_resets": success_count
                },
                performed_by=admin_user,
                performed_at=time.time(),
                success=success_count > 0
            )
            self._log_admin_action(action)
            
            logger.info(f"Bulk usage reset: {success_count}/{len(target_identifiers)} identifiers")
            return success_count
            
        except Exception as e:
            logger.error(f"Error in bulk usage reset: {e}")
            return 0
    
    def get_override_status(self, identifier: Optional[str] = None,
                           operation_type: Optional[str] = None) -> Dict[str, Any]:
        """Get override status for identifiers.
        
        Args:
            identifier: Optional specific identifier
            operation_type: Optional specific operation type
            
        Returns:
            Dictionary containing override status
        """
        try:
            overrides = {}
            
            if identifier and operation_type:
                # Get specific override
                entry = self.storage.get_usage_data(identifier, operation_type)
                if entry and entry.override_active:
                    overrides[f"{identifier}:{operation_type}"] = {
                        "active": True,
                        "expiry": entry.override_expiry,
                        "expiry_human": datetime.fromtimestamp(entry.override_expiry).isoformat() if entry.override_expiry else None
                    }
            else:
                # Get all overrides
                all_identifiers = self.storage.get_all_identifiers()
                
                for ident, op_type in all_identifiers:
                    if operation_type and op_type != operation_type:
                        continue
                    if identifier and ident != identifier:
                        continue
                    
                    entry = self.storage.get_usage_data(ident, op_type)
                    if entry and entry.override_active:
                        key = f"{ident}:{op_type}"
                        overrides[key] = {
                            "active": True,
                            "expiry": entry.override_expiry,
                            "expiry_human": datetime.fromtimestamp(entry.override_expiry).isoformat() if entry.override_expiry else None
                        }
            
            return {
                "override_enabled": self.override_enabled,
                "emergency_override_enabled": self.emergency_override_enabled,
                "active_overrides": overrides,
                "total_active": len(overrides)
            }
            
        except Exception as e:
            logger.error(f"Error getting override status: {e}")
            return {"error": str(e)}
    
    def get_admin_log(self, limit: int = 100, 
                     action_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get admin action log.
        
        Args:
            limit: Maximum number of actions to return
            action_type: Optional filter by action type
            
        Returns:
            List of admin actions
        """
        try:
            with open(self.admin_log_path, 'r') as f:
                log_data = json.load(f)
            
            actions = log_data.get("actions", [])
            
            # Filter by action type if specified
            if action_type:
                actions = [action for action in actions if action.get("action_type") == action_type]
            
            # Sort by timestamp (newest first) and limit
            actions.sort(key=lambda x: x.get("performed_at", 0), reverse=True)
            
            return actions[:limit]
            
        except Exception as e:
            logger.error(f"Error getting admin log: {e}")
            return []
    
    def cleanup_expired_overrides(self) -> int:
        """Clean up expired overrides.
        
        Returns:
            Number of overrides cleaned up
        """
        try:
            cleanup_count = 0
            current_time = time.time()
            
            all_identifiers = self.storage.get_all_identifiers()
            
            for identifier, operation_type in all_identifiers:
                entry = self.storage.get_usage_data(identifier, operation_type)
                
                if entry and entry.override_active and entry.override_expiry:
                    if current_time > entry.override_expiry:
                        # Override expired
                        entry.override_active = False
                        entry.override_expiry = None
                        
                        if self.storage.save_usage_data(entry):
                            cleanup_count += 1
                            
                            # Log cleanup
                            action = AdminAction(
                                action_type="override_expired",
                                identifier=identifier,
                                operation_type=operation_type,
                                details={},
                                performed_by="system",
                                performed_at=current_time,
                                success=True
                            )
                            self._log_admin_action(action)
            
            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} expired overrides")
            
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired overrides: {e}")
            return 0
    
    def get_admin_stats(self) -> Dict[str, Any]:
        """Get admin statistics and system status.
        
        Returns:
            Dictionary containing admin statistics
        """
        try:
            # Get recent admin actions
            recent_actions = self.get_admin_log(limit=100)
            
            # Count by action type
            action_counts = {}
            for action in recent_actions:
                action_type = action.get("action_type", "unknown")
                action_counts[action_type] = action_counts.get(action_type, 0) + 1
            
            # Get current overrides
            override_status = self.get_override_status()
            
            # Get system stats
            all_identifiers = self.storage.get_all_identifiers()
            
            return {
                "system_status": {
                    "override_enabled": self.override_enabled,
                    "emergency_override_enabled": self.emergency_override_enabled,
                    "require_justification": self.require_justification
                },
                "limits": {
                    "admin_daily_limit": self.admin_daily_limit,
                    "admin_weekly_limit": self.admin_weekly_limit,
                    "admin_monthly_limit": self.admin_monthly_limit
                },
                "current_overrides": override_status.get("total_active", 0),
                "total_identifiers": len(all_identifiers),
                "recent_actions": {
                    "total": len(recent_actions),
                    "by_type": action_counts
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting admin stats: {e}")
            return {"error": str(e)}
    
    def validate_admin_permissions(self, admin_user: str, action: str) -> bool:
        """Validate admin permissions for an action.
        
        Args:
            admin_user: Admin user requesting action
            action: Action being requested
            
        Returns:
            True if permitted, False otherwise
        """
        # Basic permission validation
        # In a real system, this would check against a permission system
        
        if not admin_user or admin_user == "anonymous":
            return False
        
        # For now, allow all actions for any authenticated admin
        # This should be expanded with proper role-based access control
        return True