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
    }
};
