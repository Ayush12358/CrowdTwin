/**
 * CrowdTwin: Dummy API Stubs for Hackathon Demo
 * This file provides mock data structures and endpoints to simulate 
 * the predictive crowd management engine.
 */

const API_STUBS = {
  // 1. Real-time Monitoring Data
  getLiveDensity: () => {
    return {
      timestamp: new Date().toISOString(),
      zones: [
        { id: "gate_1", name: "Main Entrance", count: 120, density: 4.2 },
        { id: "sector_b", name: "South Stand", count: 450, density: 6.8 },
        { id: "exit_4", name: "North Exit", count: 80, density: 1.5 },
      ],
      venueStatus: "Amber", // Green, Amber, Red
    };
  },

  // 2. Predictive Analytics (15-min Forecast)
  getForecast: () => {
    return {
      predictionTime: new Date(Date.now() + 15 * 60000).toISOString(),
      forecastedEvents: [
        { 
          type: "THRESHOLD_BREACH", 
          zoneId: "sector_b", 
          predictedDensity: 7.4, 
          confidence: 0.89 
        },
      ],
      recommendations: [
        { 
          id: "rec_001", 
          action: "REDIRECT", 
          source: "sector_b", 
          target: "exit_4", 
          reason: "Imminent surge predicted in Sector B" 
        },
      ]
    };
  },

  // 3. Directive Status
  getDirectiveStatus: (id) => {
    return {
      id: id,
      status: "IN_PROGRESS", // SENT, IN_PROGRESS, COMPLETED, FAILED
      staffAcknowledged: 12,
      staffRemaining: 4,
      affectedDensityReduction: -0.8 // Predicted drop in p/m^2
    };
  },

  // 4. Safety Metrics
  getSafetyKPIs: () => {
    return {
      surgesPrevented: 4,
      activeAlerts: 1,
      avgResponseTime: "2.4 mins",
      safetyScore: 92 // Out of 100
    };
  }
};

// Example usage and export for a dummy frontend
if (typeof module !== 'undefined') {
  module.exports = API_STUBS;
} else {
  window.CrowdTwinAPI = API_STUBS;
}
