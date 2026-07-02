/**
 * CrowdTwin: Mock Data and Types for Clickable UI
 */

export interface Zone {
    id: string;
    name: string;
    count: number;
    density: number;
}

export interface ForecastEvent {
    type: string;
    zoneId: string;
    predictedDensity: number;
    confidence: number;
}

export interface Recommendation {
    id: string;
    action: string;
    source: string;
    target: string;
    reason: string;
}

export interface LiveDensityResponse {
    timestamp: string;
    zones: Zone[];
    venueStatus: 'Green' | 'Amber' | 'Red';
}

export interface ForecastResponse {
    predictionTime: string;
    forecastedEvents: ForecastEvent[];
    recommendations: Recommendation[];
}

export interface Story {
    id: string;
    title: string;
    objective: string;
    insight: string;
}

export const USER_STORIES: Story[] = [
    {
        id: 'safety_first',
        title: 'User Story 1: Critical Surge Details',
        objective: 'Intercept a 7.4 p/m² surge at the Felicity Ground Main Stage before it becomes a physical lock.',
        insight: 'ABM logic predicts behavioral panic based on fluid dynamics + social psychology during high-energy concerts.'
    },
    {
        id: 'structural_fix',
        title: 'User Story 2: Bottleneck Alerts',
        objective: 'Identify why Himalaya Food Court entrances fail under high capacity stress during breaks.',
        insight: 'Flow analysis shows the food stall walkway width is a physical 200p/m bottleneck.'
    },
    {
        id: 'audit_trail',
        title: 'User Story 3: Staff Terminal Sync',
        objective: 'Generate actionable, localized directives to security staff terminals in real-time.',
        insight: 'Command Center pushes localized insights directly to ground teams for pre-emptive action.'
    }
];

export const API_STUBS = {
    getLiveDensity: (): LiveDensityResponse => {
        return {
            timestamp: new Date().toISOString(),
            zones: [
                { id: "gate_1", name: "Himalaya Food Court", count: 120, density: 4.2 },
                { id: "sector_b", name: "Felicity Ground (Stage)", count: 450, density: 6.8 },
                { id: "exit_4", name: "Vindhya Pathways", count: 80, density: 1.5 },
            ],
            venueStatus: "Amber",
        };
    },

    getForecast: (): ForecastResponse => {
        return {
            predictionTime: new Date(Date.now() + 15 * 60000).toISOString(),
            forecastedEvents: [
                {
                    type: "THRESHOLD_BREACH",
                    zoneId: "sector_b",
                    predictedDensity: 7.4,
                    confidence: 0.89
                },
                {
                    type: "FLOW_BOTTLENECK",
                    zoneId: "exit_4",
                    predictedDensity: 5.1,
                    confidence: 0.95
                }
            ],
            recommendations: [
                {
                    id: "rec_001",
                    action: "REDIRECT FLOW",
                    source: "sector_b",
                    target: "exit_4",
                    reason: "Imminent surge predicted at Felicity Ground Stage; redirect via Vindhya Pathways."
                },
                {
                    id: "rec_002",
                    action: "DEPLOY BARRIERS",
                    source: "gate_1",
                    target: "all",
                    reason: "Reducing ingress at Himalaya Food Court to prevent compounding stand-still."
                }
            ]
        };
    }
};
