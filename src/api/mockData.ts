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
        title: 'User Story 1: Critical Prevention',
        objective: 'Intercept a 7.4 p/m² surge in Sector B before it becomes a physical lock.',
        insight: 'ABM logic predicts behavioral panic based on fluid dynamics + social psychology.'
    },
    {
        id: 'structural_fix',
        title: 'User Story 2: Design Risk',
        objective: 'Identify why Exit 4 always fails under high capacity stress.',
        insight: 'Flow analysis shows stair-well width is a physical 200p/m bottleneck.'
    },
    {
        id: 'audit_trail',
        title: 'User Story 3: Post-Match Governance',
        objective: 'Generate a safety audit report verifying a 92% successful prevention rate.',
        insight: 'Safety score is calculated by Lead-Time vs Intervention Accuracy metrics.'
    }
];

export const API_STUBS = {
    getLiveDensity: (): LiveDensityResponse => {
        return {
            timestamp: new Date().toISOString(),
            zones: [
                { id: "gate_1", name: "Main Entrance", count: 120, density: 4.2 },
                { id: "sector_b", name: "South Stand", count: 450, density: 6.8 },
                { id: "exit_4", name: "North Exit", count: 80, density: 1.5 },
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
                    action: "REDIRECT",
                    source: "sector_b",
                    target: "exit_4",
                    reason: "Imminent surge predicted in Sector B; capacity available near North Exit."
                },
                {
                    id: "rec_002",
                    action: "CLOSE_GATE",
                    source: "gate_1",
                    target: "all",
                    reason: "Reducing ingress to prevent compounding stand-still at Sect B."
                }
            ]
        };
    }
};
