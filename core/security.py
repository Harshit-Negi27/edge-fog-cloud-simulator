"""
Security and Multi-Tenancy module for the Edge-Fog-Cloud Computing Simulator.
Implements Role-Based Access Control (RBAC) and Tenant Data Isolation.
Demonstrates unauthorized access prevention (Rubric Section 2 & Experiment 3).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.models import Task, VirtualMachine


class Role(str, Enum):
    ADMIN = "ADMIN"
    TENANT = "TENANT"


class AccessDeniedError(Exception):
    """Raised when a tenant attempts to access unauthorized tenant resources."""
    pass


@dataclass
class UserSession:
    """Represents an authenticated session."""
    username: str
    tenant_id: str
    role: Role = Role.TENANT


@dataclass
class AuditLog:
    """Records security events for reporting and auditing."""
    timestamp: str
    requester_tenant: str
    target_tenant: str
    action: str
    status: str  # "ALLOWED" or "DENIED"
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Timestamp": self.timestamp,
            "Requester": self.requester_tenant,
            "Target": self.target_tenant,
            "Action": self.action,
            "Status": self.status,
            "Details": self.details,
        }


class SecurityGateway:
    """
    Guards access to tasks and VM data.
    Ensures strict multi-tenant isolation.
    """

    def __init__(self):
        self.audit_logs: List[AuditLog] = []

    def log_event(
        self,
        requester: str,
        target: str,
        action: str,
        status: str,
        details: str,
    ) -> None:
        log_entry = AuditLog(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            requester_tenant=requester,
            target_tenant=target,
            action=action,
            status=status,
            details=details,
        )
        self.audit_logs.append(log_entry)

    def can_access(self, session: UserSession, target_tenant_id: str) -> bool:
        """Admins can view all; tenants can only view their own records."""
        if session.role == Role.ADMIN:
            return True
        return session.tenant_id == target_tenant_id

    def get_tasks_for_tenant(
        self,
        session: UserSession,
        all_tasks: List[Task],
        requested_tenant_id: Optional[str] = None,
    ) -> List[Task]:
        """
        Retrieves task records with strict tenant isolation.
        Raises AccessDeniedError if cross-tenant unauthorized query is made.
        """
        target = requested_tenant_id or session.tenant_id

        if not self.can_access(session, target):
            msg = (
                f"SECURITY VIOLATION [403 Forbidden]: Tenant '{session.tenant_id}' "
                f"is denied access to private records of Tenant '{target}'."
            )
            self.log_event(
                requester=session.tenant_id,
                target=target,
                action="VIEW_TASKS",
                status="DENIED",
                details=msg,
            )
            raise AccessDeniedError(msg)

        # Authorized access
        self.log_event(
            requester=session.tenant_id,
            target=target,
            action="VIEW_TASKS",
            status="ALLOWED",
            details="Access granted under tenant isolation policy.",
        )

        if session.role == Role.ADMIN and requested_tenant_id is None:
            return all_tasks
        
        return [t for t in all_tasks if t.tenant_id == target]

    def get_vms_for_tenant(
        self,
        session: UserSession,
        all_vms: List[VirtualMachine],
        requested_tenant_id: Optional[str] = None,
    ) -> List[VirtualMachine]:
        """
        Retrieves VM records with strict tenant isolation.
        """
        target = requested_tenant_id or session.tenant_id

        if not self.can_access(session, target):
            msg = (
                f"SECURITY VIOLATION [403 Forbidden]: Tenant '{session.tenant_id}' "
                f"attempted unauthorized inspection of VM instances belonging to '{target}'."
            )
            self.log_event(
                requester=session.tenant_id,
                target=target,
                action="VIEW_VMS",
                status="DENIED",
                details=msg,
            )
            raise AccessDeniedError(msg)

        self.log_event(
            requester=session.tenant_id,
            target=target,
            action="VIEW_VMS",
            status="ALLOWED",
            details="Access granted under tenant isolation policy.",
        )

        if session.role == Role.ADMIN and requested_tenant_id is None:
            return all_vms

        return [v for v in all_vms if v.tenant_id == target]
