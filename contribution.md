# CrowdTwin v2.0 - Hackathon Contributions

Building a predictive, agent-based command center for PSARA-certified security firms required tight collaboration. This document outlines the specific design and implementation contributions of our three-person team during the hackathon.

## The Team & Contributions

### 1. Ayush Maurya - Systems & Intelligence Lead
**Focus:** Architecture, Real-time Data Integration, and UI/UX Engineering.

*   **Design Contribution:** Designed the Dual-Tab Command Center architecture. Ayush focused on how a security operator works under pressure, moving the design from a linear setup wizard to a persistent 3-pane dashboard (Live/Predictions, Risk List, Action Center).
*   **Implementation Contribution:** 
    *   Built the core React front-end (`DemoDashboard.tsx`), implementing the complex state machine that handles the dual "Crowd Twin" and "Predictions" tabs.
    *   Engineered the dynamic risk-ranking list (Right Pane) and the contextual Command Directives (Bottom Pane).
    *   Integrated the UI theme system (Light/Dark mode + PSARA color protocol customization).
*   **Customer Specificity:** Ensured the UI matches a "Mission Control" aesthetic, stripping out unnecessary fluff to provide high-density, actionable telemetry that PSARA firms require for rapid decision-making.

### 2. Jayanth Raju Saraswathi - Simulation & Modelling Lead
**Focus:** Agent-Based Modeling, AI Network Synthesis, and Predictive Heatmaps.

*   **Design Contribution:** Designed the psychological crowd simulation logic. Instead of just treating crowds as fluid dynamics, Jayanth modeled the "virtual brains" of individuals (stress vectors, goal hierarchies) to predict crushes more accurately.
*   **Implementation Contribution:** 
    *   Developed the logic that ingests the `Base.jpeg` maps and maps out the `Final Nodes and Edges`.
    *   Generated the high-fidelity pre-intervention and post-intervention heatmaps (`Pre Heatmap.mp4`, `Post Heatmap.mp4`) that power the dashboard's visual engine.
    *   Built the background simulation engine that runs during the "Solution Finding" phase to calculate the optimal rescue steps.
*   **Customer Specificity:** Built the simulation to provide exactly a **15-minute lead time**—the specific metric security firms need to safely divert crowds before dangerous 7p/m² density thresholds are reached.

### 3. Prabhav - Product & Research Lead
**Focus:** Market Strategy, Narrative Design, and Solution Workflow.

*   **Design Contribution:** Defined the core operational story: *Strategize (Pre-Event) -> Monitor (Live) -> Problem Finding (Avert) -> Solution Finding (Handle)*. Prabhav shaped how the technology solves the actual business problem of reactive CCTV monitoring.
*   **Implementation Contribution:** 
    *   Developed the marketing narrative and structured the high-impact landing page to clearly communicate the "No New Hardware Needed" value proposition.
    *   Created the exact Command Center Directives (e.g., `TO_ALPHA: "Open Gate 4 now."`) to ensure the AI's output is immediately actionable by ground forces.
    *   Designed the predictive alert structures (`Mishap pred alert.png`) to ensure they grab operator attention without causing panic.
*   **Customer Specificity:** Tailored the product pitch strictly for PSARA-certified firms, ensuring the terminology matches industry standards and clearly demonstrates ROI by showing how the tool acts as a predictive force multiplier.

---

## Combined Impact
Together, the team transitioned CrowdTwin from a conceptual data model into a high-fidelity, interactive B2B SaaS dashboard. Every design and technical decision was ruthlessly prioritized to serve a single customer outcome: **Giving venue security teams the foresight and actionable steps required to prevent crowd disasters.**
