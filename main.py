"""
Interactive CLI for Edge-Fog-Cloud Computing Simulator.
Allows terminal-based interactive simulation, policy switching, and experiment triggers.
"""

import sys
import pandas as pd
from core.simulator import Simulator
from core.models import Task, LatencySensitivity
from core.placement import LatencyFirstPolicy, CapacityAwarePolicy
from core.security import SecurityGateway, UserSession, Role, AccessDeniedError
from experiments.default_tasks import get_default_workload, get_overload_workload
from experiments.runner import run_all_experiments


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title.upper()}")
    print("=" * 65)


def display_results(sim: Simulator, policy_name: str):
    print_header(f"Simulation Results - {policy_name}")
    metrics = sim.get_qos_metrics()
    
    print("\n--- QoS Summary Metrics ---")
    print(f"Total Tasks:          {metrics['Total_Tasks']}")
    print(f"Successful Tasks:     {metrics['Successful_Tasks']} ({metrics['Success_Rate_%']}%)")
    print(f"Rejected Tasks:       {metrics['Rejected_Tasks']}")
    print(f"Average Latency:      {metrics['Avg_Latency_ms']} ms")
    print(f"Allocated Resources:  {metrics['Total_Allocated_CPU']} Cores | {metrics['Total_Allocated_RAM_GB']} GB RAM")

    print("\n--- Node Utilization ---")
    nodes_df = sim.get_nodes_df()
    print(nodes_df[["Name", "Tier", "Used_CPU", "Total_CPU", "CPU_Util_%", "Used_RAM_GB", "Total_RAM_GB", "RAM_Util_%", "Active_VM_Count"]].to_string(index=False))

    print("\n--- Task Placement Decisions (Sample) ---")
    tasks_df = sim.get_tasks_df()
    print(tasks_df[["Task_ID", "Tenant_ID", "CPU_Req", "RAM_Req_GB", "Latency_Sensitivity", "Status", "Assigned_Node", "VM_ID", "Observed_Latency_ms"]].head(10).to_string(index=False))


def cli_run_workload(use_capacity_aware: bool = False):
    policy = CapacityAwarePolicy() if use_capacity_aware else LatencyFirstPolicy()
    workload = get_default_workload()
    sim = Simulator()
    sim.run_workload(workload, policy)
    display_results(sim, policy.name)


def cli_run_overload():
    sim = Simulator()
    workload = get_overload_workload()
    sim.run_workload(workload, LatencyFirstPolicy())
    display_results(sim, "Latency-First (Under Heavy Overload)")


def cli_test_security():
    print_header("Multi-Tenant Security & Isolation Test")
    sim = Simulator()
    workload = get_default_workload()
    sim.run_workload(workload, LatencyFirstPolicy())

    gateway = SecurityGateway()
    alice = UserSession("alice", "tenant_traffic", Role.TENANT)
    
    print("\n[Step 1] Authenticated as Tenant 'tenant_traffic' (Alice)")
    alice_tasks = gateway.get_tasks_for_tenant(alice, sim.tasks)
    print(f"-> SUCCESS: Successfully retrieved Alice's own tasks ({len(alice_tasks)} tasks found).")

    print("\n[Step 2] Attempting unauthorized access: Querying 'tenant_health' records...")
    try:
        gateway.get_tasks_for_tenant(alice, sim.tasks, requested_tenant_id="tenant_health")
        print("-> FAILED: Security breach! Unauthorized access was incorrectly permitted.")
    except AccessDeniedError as e:
        print(f"-> BLOCKED (Expected): {e}")

    print("\n[Step 3] Security Audit Trail:")
    audit_df = pd.DataFrame([l.to_dict() for l in gateway.audit_logs])
    print(audit_df.to_string(index=False))


def main_menu():
    while True:
        print_header("ARM 305: Edge-Fog-Cloud Computing Simulator")
        print("1. Run Default Workload (Policy 1: Latency-First)")
        print("2. Run Default Workload (Policy 2: Capacity-Aware)")
        print("3. Run Overload Stress Test (Task Rejection / Spillover)")
        print("4. Test Multi-Tenant Security & Unauthorized Access Denial")
        print("5. Run All 4 Assignment Experiments & Export Charts/Tables")
        print("6. Launch Streamlit Web UI")
        print("0. Exit")
        print("-" * 65)

        choice = input("Enter choice (0-6): ").strip()

        if choice == "1":
            cli_run_workload(use_capacity_aware=False)
        elif choice == "2":
            cli_run_workload(use_capacity_aware=True)
        elif choice == "3":
            cli_run_overload()
        elif choice == "4":
            cli_test_security()
        elif choice == "5":
            run_all_experiments()
        elif choice == "6":
            print("\nTo launch the Streamlit Web UI, run:")
            print("  streamlit run app.py\n")
        elif choice == "0":
            print("\nExiting simulator. Goodbye!")
            sys.exit(0)
        else:
            print("\nInvalid choice. Please enter 0-6.")


if __name__ == "__main__":
    main_menu()
