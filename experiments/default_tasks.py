"""
Preset workload tasks for the Edge-Fog-Cloud Computing Simulator.
Contains 12 realistic heterogeneous tasks spanning diverse CPU, RAM,
latency sensitivities, and multiple tenants.
"""

from typing import List
from core.models import Task, LatencySensitivity


def get_default_workload() -> List[Task]:
    """
    Returns a standard test workload of 12 tasks meeting all assignment specifications:
    - At least 10 tasks
    - Diverse CPU cores (0.5 to 12.0)
    - Diverse RAM (1.0 GB to 24.0 GB)
    - Latency sensitivities (high, medium, low)
    - Multiple tenants (tenant_traffic, tenant_health, tenant_analytics)
    """
    return [
        # Tenant: Traffic & Smart Mobility (Time-critical IoT)
        Task(
            task_id="TASK-01",
            tenant_id="tenant_traffic",
            cpu_req=1.0,
            ram_req=2.0,
            latency_sensitivity=LatencySensitivity.HIGH,
        ),
        Task(
            task_id="TASK-02",
            tenant_id="tenant_traffic",
            cpu_req=1.5,
            ram_req=2.0,
            latency_sensitivity=LatencySensitivity.HIGH,
        ),
        Task(
            task_id="TASK-03",
            tenant_id="tenant_traffic",
            cpu_req=2.0,
            ram_req=4.0,
            latency_sensitivity=LatencySensitivity.MEDIUM,
        ),
        Task(
            task_id="TASK-04",
            tenant_id="tenant_traffic",
            cpu_req=4.0,
            ram_req=8.0,
            latency_sensitivity=LatencySensitivity.LOW,
        ),

        # Tenant: Smart Healthcare (Telemetry, Imaging, Diagnostics)
        Task(
            task_id="TASK-05",
            tenant_id="tenant_health",
            cpu_req=0.5,
            ram_req=1.0,
            latency_sensitivity=LatencySensitivity.HIGH,
        ),
        Task(
            task_id="TASK-06",
            tenant_id="tenant_health",
            cpu_req=2.0,
            ram_req=4.0,
            latency_sensitivity=LatencySensitivity.HIGH,
        ),
        Task(
            task_id="TASK-07",
            tenant_id="tenant_health",
            cpu_req=6.0,
            ram_req=12.0,
            latency_sensitivity=LatencySensitivity.MEDIUM,
        ),
        Task(
            task_id="TASK-08",
            tenant_id="tenant_health",
            cpu_req=8.0,
            ram_req=16.0,
            latency_sensitivity=LatencySensitivity.LOW,
        ),

        # Tenant: Big Data Analytics & Model Training
        Task(
            task_id="TASK-09",
            tenant_id="tenant_analytics",
            cpu_req=2.0,
            ram_req=4.0,
            latency_sensitivity=LatencySensitivity.MEDIUM,
        ),
        Task(
            task_id="TASK-10",
            tenant_id="tenant_analytics",
            cpu_req=4.0,
            ram_req=8.0,
            latency_sensitivity=LatencySensitivity.LOW,
        ),
        Task(
            task_id="TASK-11",
            tenant_id="tenant_analytics",
            cpu_req=8.0,
            ram_req=16.0,
            latency_sensitivity=LatencySensitivity.LOW,
        ),
        Task(
            task_id="TASK-12",
            tenant_id="tenant_analytics",
            cpu_req=12.0,
            ram_req=24.0,
            latency_sensitivity=LatencySensitivity.LOW,
        ),
    ]


def get_overload_workload() -> List[Task]:
    """
    Returns a heavy workload that deliberately exceeds Edge and Fog capacity,
    triggering task rejection and spillover testing.
    """
    tasks = get_default_workload()
    extra_heavy_tasks = [
        Task(
            task_id=f"OVERLOAD-{i:02d}",
            tenant_id="tenant_stress",
            cpu_req=16.0,
            ram_req=32.0,
            latency_sensitivity=LatencySensitivity.HIGH,
        )
        for i in range(1, 8)
    ]
    return tasks + extra_heavy_tasks
