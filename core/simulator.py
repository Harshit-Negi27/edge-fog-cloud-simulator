"""
Simulation Orchestrator for the Edge-Fog-Cloud Computing Simulator.
Coordinates ComputeNodes, Workload execution, VM lifecycle, and QoS metric tracking.
"""

from typing import List, Dict, Optional
import copy
import pandas as pd

from core.models import (
    ComputeNode,
    Task,
    VirtualMachine,
    TaskStatus,
    VMStatus,
    LatencySensitivity,
)
from core.placement import BasePlacementPolicy, LatencyFirstPolicy, CapacityAwarePolicy


class Simulator:
    """
    Core simulator managing the three-tier computing cluster and processing workloads.
    """

    def __init__(self, nodes: Optional[List[ComputeNode]] = None):
        self.nodes: List[ComputeNode] = nodes or self.get_default_nodes()
        self.tasks: List[Task] = []
        self.vms: Dict[str, VirtualMachine] = {}
        self.vm_counter: int = 1

    @staticmethod
    def get_default_nodes() -> List[ComputeNode]:
        """
        Creates standard 3-tier node topology:
        1. Edge: Low latency (10ms), Small capacity (4 CPU, 8 GB RAM)
        2. Fog: Medium latency (45ms), Medium capacity (16 CPU, 32 GB RAM)
        3. Cloud: High latency (150ms), Large capacity (64 CPU, 128 GB RAM)
        """
        return [
            ComputeNode(
                node_id="node_edge_01",
                name="Edge Node 1",
                tier="Edge",
                total_cpu=4.0,
                total_ram=8.0,
                base_latency_ms=10.0,
            ),
            ComputeNode(
                node_id="node_fog_01",
                name="Fog Node 1",
                tier="Fog",
                total_cpu=16.0,
                total_ram=32.0,
                base_latency_ms=45.0,
            ),
            ComputeNode(
                node_id="node_cloud_01",
                name="Cloud Data Center",
                tier="Cloud",
                total_cpu=64.0,
                total_ram=128.0,
                base_latency_ms=150.0,
            ),
        ]

    def reset(self, new_nodes: Optional[List[ComputeNode]] = None) -> None:
        """Resets the simulator state for a fresh run."""
        self.nodes = new_nodes or self.get_default_nodes()
        self.tasks.clear()
        self.vms.clear()
        self.vm_counter = 1

    def run_workload(
        self,
        tasks: List[Task],
        policy: BasePlacementPolicy,
    ) -> List[Task]:
        """
        Executes a batch of tasks against the cluster using the specified placement policy.
        """
        processed_tasks: List[Task] = []

        for original_task in tasks:
            # Deepcopy to preserve original input across multiple experiment runs
            task = copy.deepcopy(original_task)
            selected_node = policy.select_node(task, self.nodes)

            if selected_node:
                # 1. Create simulated VM record
                vm_id = f"VM-{self.vm_counter:03d}"
                self.vm_counter += 1

                vm = VirtualMachine(
                    vm_id=vm_id,
                    task_id=task.task_id,
                    tenant_id=task.tenant_id,
                    host_node_id=selected_node.name,
                    allocated_cpu=task.cpu_req,
                    allocated_ram=task.ram_req,
                    status=VMStatus.RUNNING,
                )

                # 2. Allocate resources on node
                selected_node.allocate(vm)
                self.vms[vm_id] = vm

                # 3. Update task status and QoS latency
                task.status = TaskStatus.RUNNING
                task.assigned_node = selected_node.name
                task.assigned_vm_id = vm_id
                task.observed_latency_ms = selected_node.base_latency_ms
                task.rejection_reason = None
            else:
                # Task rejected due to overload
                task.status = TaskStatus.REJECTED
                task.assigned_node = None
                task.assigned_vm_id = None
                task.observed_latency_ms = None
                task.rejection_reason = "Overload: Insufficient CPU/RAM on candidate nodes"

            self.tasks.append(task)
            processed_tasks.append(task)

        return processed_tasks

    def stop_vm(self, vm_id: str) -> bool:
        """Stops and deallocates a VM from its host node."""
        if vm_id not in self.vms:
            return False
        
        vm = self.vms[vm_id]
        for node in self.nodes:
            if vm_id in node.active_vms:
                node.release(vm_id)
                vm.stop()
                return True
        return False

    def get_tasks_df(self) -> pd.DataFrame:
        """Returns all executed tasks as a pandas DataFrame."""
        return pd.DataFrame([t.to_dict() for t in self.tasks])

    def get_nodes_df(self) -> pd.DataFrame:
        """Returns node resource and utilization status as a DataFrame."""
        return pd.DataFrame([n.to_dict() for n in self.nodes])

    def get_vms_df(self) -> pd.DataFrame:
        """Returns all simulated VM records as a DataFrame."""
        return pd.DataFrame([v.to_dict() for v in self.vms.values()])

    def get_qos_metrics(self) -> dict:
        """Calculates comprehensive QoS and performance summary metrics."""
        total = len(self.tasks)
        if total == 0:
            return {
                "Total_Tasks": 0,
                "Successful_Tasks": 0,
                "Rejected_Tasks": 0,
                "Success_Rate_%": 0.0,
                "Avg_Latency_ms": 0.0,
                "Total_Allocated_CPU": 0.0,
                "Total_Allocated_RAM_GB": 0.0,
                "Node_Utilizations": {n.name: n.overall_utilization for n in self.nodes},
            }

        successful = [t for t in self.tasks if t.status == TaskStatus.RUNNING]
        rejected = [t for t in self.tasks if t.status == TaskStatus.REJECTED]
        avg_latency = (
            sum(t.observed_latency_ms for t in successful) / len(successful)
            if successful
            else 0.0
        )

        return {
            "Total_Tasks": total,
            "Successful_Tasks": len(successful),
            "Rejected_Tasks": len(rejected),
            "Success_Rate_%": round((len(successful) / total) * 100.0, 2),
            "Avg_Latency_ms": round(avg_latency, 2),
            "Total_Allocated_CPU": round(sum(n.used_cpu for n in self.nodes), 2),
            "Total_Allocated_RAM_GB": round(sum(n.used_ram for n in self.nodes), 2),
            "Node_Utilizations": {n.name: n.overall_utilization for n in self.nodes},
        }
