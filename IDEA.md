# Crowd-Twin: Auditable Predictive Command & Safety Compliance Center

## 1. Executive Summary & Value Proposition
For event security firms and stadium operators, **chaos is both a safety risk and a legal liability**. Traditional crowd management tools are passive and siloed: CCTV feeds show incidents only *after* they occur, and offline design models are useless during live operations. Furthermore, modern safety regulations (such as **SASREA** in South Africa and **Martyn's Law** in the UK) impose strict personal liability on venue directors to maintain time-stamped, auditable safety logs and structured incident escalation plans.

**Crowd-Twin** is a predictive, closed-loop command and safety compliance platform. By feeding live CCTV tracks into a GPU-accelerated **Psychological Agent-Based Model (ABM)**, Crowd-Twin provides a **15-minute predictive lead time** to resolve density bottlenecks. Crucially, the platform bridges the gap between monitoring and operations by generating **verifiable, time-stamped compliance audit logs** for regulators and insurers, moving venues from reactive response to auditable proactive control.

---

## 2. Core Industry Gaps Resolved

| Existing Product Gaps | The Crowd-Twin Solution | Business Value |
|---|---|---|
| **Siloed Dashboards**: Heatmaps warn of surges but don't connect to ground dispatch. | **Closed-Loop Dispatch**: Command panel broadcasts directives directly to mobile terminals, tracking staff acknowledgement and execution latency. | Reduces incident response lag; optimizes ground security staff deployment. |
| **Passive Counting**: Turnstiles and cameras count people but cannot predict flow coordinates. | **Psychological ABM Projection**: Simulates agent routing, stress factors, and exit selection to predict crowd trajectories 15 minutes ahead. | Prevents critical exit bottlenecks before they occur physically. |
| **Unverifiable Audits**: Venues lack time-stamped proof of safety compliance for incidents. | **Automated Compliance Logs**: Automatically generates time-stamped JSON audits of surges predicted, directives issued, and actual density drops. | Protects venue directors from personal liability; slashes insurance premiums. |
| **Raw Density Metrics ($p/m^2$)**: Fails to capture compression forces and personal space violations. | **Pairwise Proximity Clustering**: Constructs live graphs of agent distances, classifying risk by average connection degree (Clustering vs. Free-Flow). | Triggers earlier alerts based on group compression dynamics rather than flat headcounts. |

---

## 3. Product Features & Operations

### A. Real-Time Proximity Clustering
Instead of simply counting agents in a grid cell, Crowd-Twin maps agents as nodes in a graph. An edge is created if the distance between two agents is $< 1.5\text{ meters}$.
* **Low Congestion**: Nodes are sparsely connected (average node degree $< 1.5$).
* **Surge Flow**: Agents move along parallel chains (low variance in velocity direction, moderate node degree).
* **Compression Risk**: Nodes form fully connected components (average node degree $> 5.0$, velocities near zero). The command center is alerted instantly of active crush potential.

### B. Closed-Loop Command Dispatch
1. **Surge Predicted**: The system flags a bottleneck at Exit 4 in 15 minutes.
2. **Directive Evaluated**: The operator selects "Open Exit Gate 4" on the Command Panel. The simulator runs a parallel "what-if" NumPy/pyflamegpu projection, showing a predicted density drop.
3. **Staff Dispatched**: The directive is pushed to the target staff's mobile terminal. The staff member clicks "Acknowledge" (logging timestamp) and "Action Completed" (logging execution timestamp).
4. **Execution Verified**: The system monitors the physical exit area via CCTV, verifying the actual density reduction.

### C. Automated Safety Compliance Logging
Every operational cycle is written to a tamper-resistant JSON compliance log.
* **Audit Fields**: Event UUID, Timestamp, Alert Type, Predicted Density, Directive Issued, Staff Acknowledged Time, Action Completed Time, Verification Outcome (Success/Fail).
* **Compliance Export**: A one-click PDF/CSV export is available for safety audits, local fire marshals, and insurance compliance evaluations.

---

## 4. Key Target Markets & Personas

### Target Customer Segments
* **PSARA-Certified Security Firms (India)**: Legally contracted security agencies managing stadium events.
* **SASREA-Compliant Venues (South Africa)**: Stadiums with capacities $> 2,000$ required by law to maintain time-stamped entry/exit records and safety plan audits.
* **Martyn's Law Premises (UK)**: Public spaces with capacity $> 800$ required to demonstrate active risk planning and emergency escalation training.

### User Personas
* **Chief Safety/Security Officer (CSO) [Buyer]**: Focuses on liability reduction and insurance compliance. Wants structured reports to prove due diligence.
* **Command Room Operator [Tactical User]**: Focuses on live monitoring. Wants high-fidelity predictive alerts and a direct, simple dispatch panel.
* **Ground Security Lead [Ground User]**: Focuses on action execution. Wants simple, clear mobile instructions on terminal screens.

---

## 5. Competitive Landscape

* **Legion / MassMotion**: Static, offline design tools. Cannot import real-time camera data or support live command dispatch.
* **Reactive Video Analytics (Briefcam)**: Good for historical search or static alarms, but lacks forward-simulating projection.
* **Hardware Count Systems (WiFi/Sensors)**: Expensive to scale, high latency, and zero predictive capability.

---

## 6. Key Risks & Mitigation Metrics

* **Calibration Accuracy**: Variable camera perspectives distort coordinate accuracy.
  * *Mitigation*: Homography projection calibration mapping bottom-center bounding box foot anchors to real-world floor plans.
* **Operator Alert Fatigue**: Excessive notifications leading to skipped warnings.
  * *Mitigation*: Triggering alerts only on topological graph compression metrics (average neighbor degree) rather than raw grid cell counts.
* **Success Metric**: Maintain a Mean Absolute Percentage Error (MAPE) of under 12% on 15-minute crowd projections, with an target system response latency of under 100ms.
