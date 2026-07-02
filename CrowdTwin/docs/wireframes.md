# CrowdTwin: 10 Functional Screens

This document defines the layout and key components for the 10 functional screens identified in the scope.

## 1. Live Heatmap (Real-time monitoring)
- **Top Bar:** Venue status (Green/Amber/Red), Current time, Active Guards.
- **Main View:** Interactive 2D/3D map overlay with density gradients.
- **Side Panel:** Selected zone stats (People count, p/m²).

## 2. Predictive Mode (Lead-time forecast)
- **Overlay:** Ghost agents showing predicted movement over 15 minutes.
- **Time Slider:** Scrub through the 15-minute forecast.
- **Toggle:** Show/Hide current vs. predicted density.

## 3. Threshold Alert (Predicted 7 p/m² warning)
- **Modal/Banner:** High-priority red alert if prediction hits critical threshold.
- **Visual:** Map pans and zooms to the "Hot Zone".
- **Action:** Button to "Open Command Panel" for action.

## 4. Simulation Playback (Prediction verification)
- **View:** Split-screen or overlay comparing past predictions with actual outcomes.
- **Graph:** Accuracy score over time.
- **Purpose:** Build operator trust in the AI engine.

## 5. Command Panel (Directive entry)
- **List:** Recommended actions (e.g., "Close Gate 4", "Redeploy Sector B").
- **Execution:** Confirmation slider to broadcast directive to ground staff.
- **Impact Preview:** Small chart showing predicted density drop after action.

## 6. Staff Terminal (Mobile instructions)
- **View:** Mobile-optimized simple UI.
- **Card:** "DIRECTIVE: Close Gate 4 - ETA 2 Mins".
- **Feedback:** "Action Taken" checkbox + "Issue Encountered" report.

## 7. Outcome Forecast (Predicted success after action)
- **Post-Action View:** The "Alternative Future" if current directives are followed.
- **Comparison:** Show "Without Intervention" vs. "With Intervention" density curves.

## 8. Layout Stress-Test (Arena planning view)
- **Editor:** Drag-and-drop obstacles, gates, and stages.
- **Run Sim:** Trigger a "Max Capacity" scenario to find design flaws.
- **Heatmap:** Cumulative density over the simulated hour.

## 9. Bottleneck Analysis (Design-based heatmap)
- **View:** Static map with permanent "Design Risks" highlighted (e.g., narrow stairs).
- **Metric:** Flow rate and wait times for specific architectural bottlenecks.

## 10. Safety Analytics (Executive Incident report)
- **Dashboard:** Critical 7 p/m² events prevented vs. occurred.
- **KPIs:** Average intervention time, total density exposure.
- **Export:** PDF Generator for insurance and regulatory compliance.
