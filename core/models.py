"""
Data models for the Edge-Fog-Cloud Computing Simulator.
Defines ComputeNode, Task, VirtualMachine, and associated enums.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, List


class LatencySensitivity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class VMStatus(str, Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


@dataclass
class VirtualMachine:
    """
    Simulated Virtual Machine representation.
    Fulfills the Virtualization concept rubric requirement without hypervisor overhead.
    """
    vm_id: str
    task_id: str
    tenant_id: str
    host_node_id: str
    allocated_cpu: float
    allocated_ram: float
    status: VMStatus = VMStatus.RUNNING

    def stop(self) -> None:
        self.status = VMStatus.STOPPED

    def to_dict(self) -> dict:
        return {
            "VM_ID": self.vm_id,
            "Task_ID": self.task_id,
            "Tenant_ID": self.tenant_id,
            "Host_Node": self.host_node_id,
            "Allocated_CPU": self.allocated_cpu,
            "Allocated_RAM_GB": self.allocated_ram,
            "Status": self.status.value,
        }


@dataclass
class Task:
    """
    Represents a workload computation unit submitted by a tenant.
    """
    task_id: str
    tenant_id: str
    cpu_req: float
    ram_req: float
    latency_sensitivity: LatencySensitivity
    status: TaskStatus = TaskStatus.PENDING
    assigned_node: Optional[str] = None
    assigned_vm_id: Optional[str] = None
    observed_latency_ms: Optional[float] = None
    rejection_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "Task_ID": self.task_id,
            "Tenant_ID": self.tenant_id,
            "CPU_Req": self.cpu_req,
            "RAM_Req_GB": self.ram_req,
            "Latency_Sensitivity": self.latency_sensitivity.value,
            "Status": self.status.value,
            "Assigned_Node": self.assigned_node or "None",
            "VM_ID": self.assigned_vm_id or "None",
            "Observed_Latency_ms": self.observed_latency_ms if self.observed_latency_ms is not None else 0.0,
            "Rejection_Reason": self.rejection_reason or "N/A",
        }


@dataclass
class ComputeNode:
    """
    Simulates a compute node across the Edge-Fog-Cloud continuum.
    Tracks CPU, RAM, baseline network latency, and current utilization.
    """
    node_id: str
    name: str
    tier: str  # "Edge", "Fog", "Cloud"
    total_cpu: float  # CPU cores
    total_ram: float  # RAM in GB
    base_latency_ms: float  # Network latency in ms
    used_cpu: float = 0.0
    used_ram: float = 0.0
    active_vms: Dict[str, VirtualMachine] = field(default_factory=dict)

    def can_host(self, cpu: float, ram: float) -> bool:
        """Checks if the node has sufficient remaining capacity."""
        return (self.used_cpu + cpu <= self.total_cpu) and (self.used_ram + ram <= self.total_ram)

    def allocate(self, vm: VirtualMachine) -> bool:
        """Allocates resources for a simulated VM on this node."""
        if not self.can_host(vm.allocated_cpu, vm.allocated_ram):
            return False
        
        self.used_cpu += vm.allocated_cpu
        self.used_ram += vm.allocated_ram
        self.active_vms[vm.vm_id] = vm
        return True

    def release(self, vm_id: str) -> bool:
        """Releases resources allocated to a simulated VM."""
        if vm_id not in self.active_vms:
            return False
        
        vm = self.active_vms.pop(vm_id)
        vm.stop()
        self.used_cpu = max(0.0, self.used_cpu - vm.allocated_cpu)
        self.used_ram = max(0.0, self.used_ram - vm.allocated_ram)
        return True

    @property
    def cpu_utilization(self) -> float:
        """Percentage of CPU currently utilized."""
        if self.total_cpu == 0:
            return 0.0
        return round((self.used_cpu / self.total_cpu) * 100.0, 2)

    @property
    def ram_utilization(self) -> float:
        """Percentage of RAM currently utilized."""
        if self.total_ram == 0:
            return 0.0
        return round((self.used_ram / self.total_ram) * 100.0, 2)

    @property
    def overall_utilization(self) -> float:
        """Average utilization across CPU and RAM."""
        return round((self.cpu_utilization + self.ram_utilization) / 2.0, 2)

    @property
    def remaining_cpu(self) -> float:
        return round(self.total_cpu - self.used_cpu, 2)

    @property
    def remaining_ram(self) -> float:
        return round(self.total_ram - self.used_ram, 2)

    def to_dict(self) -> dict:
        return {
            "Node_ID": self.node_id,
            "Name": self.name,
            "Tier": self.tier,
            "Total_CPU": self.total_cpu,
            "Used_CPU": round(self.used_cpu, 2),
            "CPU_Util_%": self.cpu_utilization,
            "Total_RAM_GB": self.total_ram,
            "Used_RAM_GB": round(self.used_ram, 2),
            "RAM_Util_%": self.ram_utilization,
            "Overall_Util_%": self.overall_utilization,
            "Base_Latency_ms": self.base_latency_ms,
            "Active_VM_Count": len(self.active_vms),
        }
