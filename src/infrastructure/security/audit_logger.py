"""
Audit logging for security and compliance.
"""
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List  # ADD List HERE
from uuid import UUID, uuid4

from src.infrastructure.database.sqlite.connection import db_connection

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logger for tracking security-relevant events.
    """
    
    # Event types
    EVENT_AUTH_LOGIN = "auth.login"
    EVENT_AUTH_LOGOUT = "auth.logout"
    EVENT_AUTH_LOGIN_FAILED = "auth.login_failed"
    EVENT_AUTH_PASSWORD_CHANGE = "auth.password_change"
    EVENT_AUTH_PASSWORD_RESET = "auth.password_reset"
    EVENT_AUTH_EMAIL_VERIFIED = "auth.email_verified"
    
    EVENT_USER_CREATED = "user.created"
    EVENT_USER_UPDATED = "user.updated"
    EVENT_USER_DELETED = "user.deleted"
    EVENT_USER_ROLE_CHANGED = "user.role_changed"
    
    EVENT_API_KEY_CREATED = "api_key.created"
    EVENT_API_KEY_REVOKED = "api_key.revoked"
    EVENT_API_KEY_USED = "api_key.used"
    
    EVENT_CONVERSATION_CREATED = "conversation.created"
    EVENT_CONVERSATION_DELETED = "conversation.deleted"
    EVENT_MESSAGE_SENT = "message.sent"
    
    EVENT_IMAGE_GENERATED = "image.generated"
    EVENT_CHART_GENERATED = "chart.generated"
    EVENT_ASSET_DELETED = "asset.deleted"
    
    EVENT_ADMIN_ACTION = "admin.action"
    EVENT_SETTINGS_CHANGED = "settings.changed"
    
    def __init__(self):
        pass
    
    async def log(
        self,
        event_type: str,
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Log an audit event.
        """
        event_id = str(uuid4())
        
        query = """
            INSERT INTO audit_logs (
                id, user_id, action, resource_type, resource_id,
                details, ip_address, user_agent, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        db_connection.execute(query, (
            event_id,
            str(user_id) if user_id else None,
            event_type,
            resource_type,
            str(resource_id) if resource_id else None,
            json.dumps(details) if details else None,
            ip_address,
            user_agent,
            datetime.utcnow().isoformat(),
        ))
        
        # Also log to application logger
        log_details = f"user={user_id} resource={resource_type}/{resource_id}"
        if details:
            log_details += f" details={json.dumps(details)}"
        
        logger.info(f"AUDIT: {event_type} | {log_details}")
    
    async def log_auth_login(
        self,
        user_id: UUID,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None,
    ) -> None:
        """Log authentication attempt."""
        event_type = self.EVENT_AUTH_LOGIN if success else self.EVENT_AUTH_LOGIN_FAILED
        
        details = {"success": success}
        if failure_reason:
            details["failure_reason"] = failure_reason
        
        await self.log(
            event_type=event_type,
            user_id=user_id if success else None,
            resource_type="user",
            resource_id=user_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    async def log_auth_logout(
        self,
        user_id: UUID,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log user logout."""
        await self.log(
            event_type=self.EVENT_AUTH_LOGOUT,
            user_id=user_id,
            resource_type="user",
            resource_id=user_id,
            ip_address=ip_address,
        )
    
    async def log_user_created(
        self,
        user_id: UUID,
        created_by: Optional[UUID] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log user creation."""
        await self.log(
            event_type=self.EVENT_USER_CREATED,
            user_id=created_by,
            resource_type="user",
            resource_id=user_id,
            details={"created_user_id": str(user_id)},
            ip_address=ip_address,
        )
    
    async def log_user_updated(
        self,
        user_id: UUID,
        updated_by: UUID,
        changes: Dict[str, Any],
        ip_address: Optional[str] = None,
    ) -> None:
        """Log user update."""
        await self.log(
            event_type=self.EVENT_USER_UPDATED,
            user_id=updated_by,
            resource_type="user",
            resource_id=user_id,
            details={"changes": changes},
            ip_address=ip_address,
        )
    
    async def log_role_changed(
        self,
        user_id: UUID,
        changed_by: UUID,
        old_role: str,
        new_role: str,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log role change."""
        await self.log(
            event_type=self.EVENT_USER_ROLE_CHANGED,
            user_id=changed_by,
            resource_type="user",
            resource_id=user_id,
            details={"old_role": old_role, "new_role": new_role},
            ip_address=ip_address,
        )
    
    async def log_api_key_created(
        self,
        user_id: UUID,
        key_id: str,
        key_name: str,
        scopes: list,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log API key creation."""
        await self.log(
            event_type=self.EVENT_API_KEY_CREATED,
            user_id=user_id,
            resource_type="api_key",
            resource_id=UUID(key_id) if key_id else None,
            details={"key_name": key_name, "scopes": scopes},
            ip_address=ip_address,
        )
    
    async def log_api_key_revoked(
        self,
        user_id: UUID,
        key_id: str,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log API key revocation."""
        await self.log(
            event_type=self.EVENT_API_KEY_REVOKED,
            user_id=user_id,
            resource_type="api_key",
            resource_id=UUID(key_id) if key_id else None,
            ip_address=ip_address,
        )
    
    async def log_conversation_created(
        self,
        user_id: UUID,
        conversation_id: UUID,
        model_name: str,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log conversation creation."""
        await self.log(
            event_type=self.EVENT_CONVERSATION_CREATED,
            user_id=user_id,
            resource_type="conversation",
            resource_id=conversation_id,
            details={"model_name": model_name},
            ip_address=ip_address,
        )
    
    async def log_message_sent(
        self,
        user_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
        tokens_used: int,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log message sent."""
        await self.log(
            event_type=self.EVENT_MESSAGE_SENT,
            user_id=user_id,
            resource_type="message",
            resource_id=message_id,
            details={
                "conversation_id": str(conversation_id),
                "tokens_used": tokens_used,
            },
            ip_address=ip_address,
        )
    
    async def log_image_generated(
        self,
        user_id: UUID,
        asset_id: UUID,
        model_used: str,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log image generation."""
        await self.log(
            event_type=self.EVENT_IMAGE_GENERATED,
            user_id=user_id,
            resource_type="asset",
            resource_id=asset_id,
            details={"model_used": model_used},
            ip_address=ip_address,
        )
    
    async def log_admin_action(
        self,
        admin_id: UUID,
        action: str,
        target_type: str,
        target_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log admin action."""
        await self.log(
            event_type=self.EVENT_ADMIN_ACTION,
            user_id=admin_id,
            resource_type=target_type,
            resource_id=target_id,
            details={"action": action, **(details or {})},
            ip_address=ip_address,
        )
    
    async def get_user_audit_logs(
        self,
        user_id: UUID,
        limit: int = 100,
        skip: int = 0,
        event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get audit logs for a specific user.
        """
        if event_type:
            query = """
                SELECT * FROM audit_logs
                WHERE user_id = ? AND action = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params = (str(user_id), event_type, limit, skip)
        else:
            query = """
                SELECT * FROM audit_logs
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params = (str(user_id), limit, skip)
        
        rows = db_connection.fetch_all(query, params)
        
        logs = []
        for row in rows:
            logs.append({
                "id": row["id"],
                "action": row["action"],
                "resource_type": row["resource_type"],
                "resource_id": row["resource_id"],
                "details": json.loads(row["details"]) if row["details"] else None,
                "ip_address": row["ip_address"],
                "created_at": row["created_at"],
            })
        
        return logs
    
    async def get_resource_audit_logs(
        self,
        resource_type: str,
        resource_id: UUID,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get audit logs for a specific resource.
        """
        query = """
            SELECT * FROM audit_logs
            WHERE resource_type = ? AND resource_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        
        rows = db_connection.fetch_all(query, (resource_type, str(resource_id), limit))
        
        logs = []
        for row in rows:
            logs.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "action": row["action"],
                "details": json.loads(row["details"]) if row["details"] else None,
                "ip_address": row["ip_address"],
                "created_at": row["created_at"],
            })
        
        return logs
    
    async def get_recent_activity(
        self,
        limit: int = 50,
        event_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent activity across all users.
        """
        if event_types:
            placeholders = ','.join(['?' for _ in event_types])
            query = f"""
                SELECT * FROM audit_logs
                WHERE action IN ({placeholders})
                ORDER BY created_at DESC
                LIMIT ?
            """
            params = [*event_types, limit]
        else:
            query = """
                SELECT * FROM audit_logs
                ORDER BY created_at DESC
                LIMIT ?
            """
            params = [limit]
        
        rows = db_connection.fetch_all(query, params)
        
        logs = []
        for row in rows:
            logs.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "action": row["action"],
                "resource_type": row["resource_type"],
                "resource_id": row["resource_id"],
                "details": json.loads(row["details"]) if row["details"] else None,
                "ip_address": row["ip_address"],
                "user_agent": row["user_agent"],
                "created_at": row["created_at"],
            })
        
        return logs