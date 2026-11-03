# ARM 305: Edge, Fog, and Cloud Computing Simulator

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![UI](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/Academic-Mini--Project-green.svg)](#)

A locally runnable Python simulation platform modeling rule-based task placement, resource utilization, simulated virtualization, and multi-tenant security across an **Edge-Fog-Cloud** hierarchy.

---

## 📌 Features & Architecture Overview

The simulator models a three-tier computing cluster:
- **Edge Node:** Ultra-low latency (10 ms), resource-constrained (4 CPU cores, 8 GB RAM).
- **Fog Node:** Balanced latency (45 ms), medium capacity (16 CPU cores, 32 GB RAM).
- **Cloud Data Center:** High latency (150 ms), abundant capacity (64 CPU cores, 128 GB RAM).

### Core Components
1. **Node & Resource Simulator (`core/models.py`):** Live tracking of CPU/RAM utilization and network latencies.
2. **Workload Generator (`experiments/default_tasks.py`):** 12 heterogeneous benchmark tasks with varying CPU, RAM, and latency sensitivities (`low`, `medium`, `high`) across multiple tenants.
3. **Dual Placement Policies (`core/placement.py`):**
   - **Policy 1: Latency-First (Greedy):** Prioritizes lowest latency tier matching task sensitivity (`HIGH` $\rightarrow$ Edge, `MEDIUM` $\rightarrow$ Fog, `LOW` $\rightarrow$ Cloud).
   - **Policy 2: Capacity-Aware (Balanced):** Evaluates resource headroom while factoring latency penalties to avoid edge bottlenecks.
4. **Simulated Virtualization (`VirtualMachine`):** Manages virtual machine records (`VM_ID`, `Host_Node`, allocated CPU/RAM, status `RUNNING` / `STOPPED`) without physical hypervisor overhead.
5. **Multi-Tenant Security Gateway (`core/security.py`):** Role-Based Access Control (RBAC) ensuring tenant isolation. Cross-tenant inspection attempts trigger `403 Forbidden` and log security audit entries.
6. **QoS Analytics & Visualizations:** Outputs summary tables and high-resolution charts comparing latencies, utilization, and overload admission.

---

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.9 or higher installed.
- Git (optional, for version control).

### 2. Clone / Open Directory
```bash
cd cdef
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 💻 How to Run the Simulator

### Option A: Interactive Streamlit Web UI (Recommended for Demo)
Launch the interactive web dashboard with real-time sliders, VM controls, and security testing:
```bash
streamlit run app.py
```
> The dashboard will automatically open in your default browser at `http://localhost:8501`.

### Option B: Interactive Command-Line Interface (CLI)
Run the terminal-based interactive menu:
```bash
python main.py
```

### Option C: Automated Batch Experiments & Report Artifact Generator
Run all 4 assignment experiments in headless mode and save all `.png` charts and `.csv` tables to the `outputs/` folder:
```bash
python -m experiments.runner
```

---

## 🧪 Experiments Summary (Rubric Section 4)

All four required experiments are automated in [`experiments/runner.py`](experiments/runner.py):

| Experiment | Setup | Expected Outcome | Actual Outcome / Evidence |
| :--- | :--- | :--- | :--- |
| **Exp 1: Policy Comparison** | 12 identical tasks run against *Latency-First* vs *Capacity-Aware*. | Latency-First minimizes average response time; Capacity-Aware balances cluster load. | [exp1_policy_comparison.png](outputs/charts/exp1_policy_comparison.png) & [exp1_summary_comparison.csv](outputs/tables/exp1_summary_comparison.csv) |
| **Exp 2: Overload & Rejection** | 19 high-demand tasks (130+ CPU) submitted to 84-core cluster. | Edge & Fog saturate; tasks spill over to Cloud; remaining tasks rejected gracefully. | [exp2_overload_analysis.png](outputs/charts/exp2_overload_analysis.png) & [exp2_overload_tasks.csv](outputs/tables/exp2_overload_tasks.csv) |
| **Exp 3: Unauthorized Access** | Tenant `tenant_traffic` queries private records of `tenant_health`. | Access denied with `403 Forbidden` and logged in security audit trail. | [exp3_security_audit_log.csv](outputs/tables/exp3_security_audit_log.csv) |
| **Exp 4: Parameter Tuning** | Edge node upgraded from 4 to 8 CPU cores and latency tuned from 10ms to 5ms. | More latency-sensitive tasks hosted on Edge; cluster-wide average latency drops. | [exp4_node_scaling_comparison.png](outputs/charts/exp4_node_scaling_comparison.png) & [exp4_sensitivity_comparison.csv](outputs/tables/exp4_sensitivity_comparison.csv) |

---

## 📁 Repository Structure

```text
cdef/
│
├── core/
│   ├── __init__.py
│   ├── models.py          # ComputeNode, Task, VirtualMachine models
│   ├── placement.py       # Latency-First & Capacity-Aware placement algorithms
│   ├── security.py        # RBAC, tenant isolation & audit logging
│   └── simulator.py       # Core orchestrator managing workloads & QoS
│
├── experiments/
│   ├── __init__.py
│   ├── default_tasks.py   # Benchmark and overload task definitions
│   └── runner.py          # Automated runner for all 4 experiments
│
├── outputs/               # Deliverables for Project Report & Presentation
│   ├── charts/            # High-resolution PNG graphs
│   └── tables/            # Exported CSV and JSON results
│
├── app.py                 # Streamlit web dashboard
├── main.py                # Interactive CLI application
├── requirements.txt       # Python package dependencies
└── README.md              # Documentation and execution guide
```

---

## 👥 Team Contribution (For Viva & Rubric Section 6)

- **Harshit Negi:** System architecture design, implementation of simulation engine, placement algorithms, multi-tenant security gateway, Streamlit UI, and automated experiment scripts.
- **Priya Chaurasia:** Project report (5–8 pages), PowerPoint presentation deck (5–7 slides), architectural diagrams, experimental evidence compilation, and evaluation documentation.
