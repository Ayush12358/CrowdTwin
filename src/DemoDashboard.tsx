import { useState, useEffect } from 'react'
import { API_STUBS, Zone, ForecastEvent, Recommendation } from './api/mockData'

function DemoDashboard() {
    const [activeScreen, setActiveScreen] = useState('heatmap')
    const [liveData, setLiveData] = useState(API_STUBS.getLiveDensity())
    const [forecast, setForecast] = useState(API_STUBS.getForecast())

    // Simulate live updates
    useEffect(() => {
        const interval = setInterval(() => {
            setLiveData(API_STUBS.getLiveDensity())
        }, 5000)
        return () => clearInterval(interval)
    }, [])

    const renderScreen = () => {
        switch (activeScreen) {
            case 'heatmap':
                return (
                    <div className="screen-heatmap">
                        <div className="map-placeholder">
                            <div className="zone-indicator" style={{ top: '30%', left: '40%', background: 'var(--amber)' }}>
                                <span>{liveData.zones[1]?.name}: {liveData.zones[1]?.density} p/m²</span>
                            </div>
                            <div className="zone-indicator" style={{ top: '60%', left: '20%', background: 'var(--green)' }}>
                                <span>{liveData.zones[0]?.name}: {liveData.zones[0]?.density} p/m²</span>
                            </div>
                        </div>
                        <div className="stats-grid">
                            {liveData.zones.map(zone => (
                                <div key={zone.id} className="stat-card">
                                    <h3>{zone.name}</h3>
                                    <div className="stat-value">{zone.density} <small>p/m²</small></div>
                                    <div className="stat-label">{zone.count} People</div>
                                </div>
                            ))}
                        </div>
                    </div>
                )
            case 'predictive':
                return (
                    <div className="screen-predictive">
                        <div className="prediction-alert">
                            <div className="alert-header">15-MINUTE LEAD TIME FORECAST</div>
                            <p>Predicting critical density surge in <strong>{forecast.forecastedEvents[0]?.zoneId}</strong></p>
                            <div className="confidence-meter">
                                <div className="meter-fill" style={{ width: `${(forecast.forecastedEvents[0]?.confidence || 0) * 100}%` }}></div>
                                <span>{(forecast.forecastedEvents[0]?.confidence || 0) * 100}% Confidence</span>
                            </div>
                        </div>
                        <div className="timeline">
                            <div className="time-point">Now</div>
                            <div className="time-line"></div>
                            <div className="time-point active">+15m</div>
                        </div>
                    </div>
                )
            case 'alerts':
                return (
                    <div className="screen-alerts">
                        {forecast.forecastedEvents.map((event, i) => (
                            <div key={i} className="alert-item critical">
                                <div className="alert-icon">⚠️</div>
                                <div className="alert-body">
                                    <h4>{event.type}</h4>
                                    <p>Predicted density: {event.predictedDensity} p/m² (Threshold: 7.0)</p>
                                    <button onClick={() => setActiveScreen('command')}>Take Action</button>
                                </div>
                            </div>
                        ))}
                    </div>
                )
            case 'command':
                return (
                    <div className="screen-command">
                        <h3>Recommended Directives</h3>
                        <div className="directives-list">
                            {forecast.recommendations.map(rec => (
                                <div key={rec.id} className="directive-card">
                                    <div className="dir-action">{rec.action}</div>
                                    <div className="dir-details">
                                        <p><strong>Source:</strong> {rec.source} ➔ <strong>Target:</strong> {rec.target}</p>
                                        <small>{rec.reason}</small>
                                    </div>
                                    <button className="confirm-btn">Execute</button>
                                </div>
                            ))}
                        </div>
                    </div>
                )
            case 'staff':
                return (
                    <div className="screen-staff">
                        <div className="mobile-view">
                            <div className="mobile-header">STAFF TERMINAL</div>
                            <div className="mobile-content">
                                <div className="directive-notice">
                                    <h3>NEW DIRECTIVE</h3>
                                    <p>Redirect flow from Sector B to East Exit.</p>
                                    <button className="ack-btn">Acknowledge</button>
                                </div>
                            </div>
                        </div>
                    </div>
                )
            case 'forecast':
                return (
                    <div className="screen-outcome">
                        <div className="comparison-view">
                            <div className="view-pane">
                                <h4>Without Action</h4>
                                <div className="graph-bar red" style={{ height: '80%' }}></div>
                                <p>7.4 p/m²</p>
                            </div>
                            <div className="view-pane">
                                <h4>With Directive</h4>
                                <div className="graph-bar green" style={{ height: '40%' }}></div>
                                <p>4.2 p/m²</p>
                            </div>
                        </div>
                    </div>
                )
            case 'stress':
                return (
                    <div className="screen-stress">
                        <div className="stress-controls">
                            <button className="run-btn">Run Capacity Stress Test</button>
                        </div>
                        <div className="bottleneck-list">
                            <div className="bottleneck-item">
                                <span>Gate 4 Stairs</span>
                                <span className="risk-high">HIGH RISK</span>
                            </div>
                        </div>
                    </div>
                )
            case 'bottleneck':
                return (
                    <div className="screen-bottleneck">
                        <div className="analysis-card">
                            <h3>Design Flow Analysis</h3>
                            <p>Exit 4 capacity: 200 persons/min</p>
                            <p>Current projected demand: 350 persons/min</p>
                            <div className="warning">STRUCTURAL BOTTLENECK DETECTED</div>
                        </div>
                    </div>
                )
            case 'safety':
                return (
                    <div className="screen-safety">
                        <div className="kpi-dashboard">
                            <div className="kpi-card"><h3>4</h3><p>Surges Prevented</p></div>
                            <div className="kpi-card"><h3>92%</h3><p>Safety Score</p></div>
                            <div className="kpi-card"><h3>2.4m</h3><p>Avg Lead Time</p></div>
                        </div>
                    </div>
                )
            case 'playback':
                return (
                    <div className="screen-playback">
                        <div className="video-placeholder">SIMULATION REPLAY: 18:00 - 18:15</div>
                        <div className="accuracy-label">Prediction Accuracy: 94.2%</div>
                    </div>
                )
            default:
                return <div>Select a screen</div>
        }
    }

    return (
        <div className="app-container">
            <nav className="sidebar">
                <div className="logo">CROWD-TWIN</div>
                <ul>
                    <li className={activeScreen === 'heatmap' ? 'active' : ''} onClick={() => setActiveScreen('heatmap')}>Live Heatmap</li>
                    <li className={activeScreen === 'predictive' ? 'active' : ''} onClick={() => setActiveScreen('predictive')}>Predictive Mode</li>
                    <li className={activeScreen === 'alerts' ? 'active' : ''} onClick={() => setActiveScreen('alerts')}>Safety Alerts</li>
                    <li className={activeScreen === 'command' ? 'active' : ''} onClick={() => setActiveScreen('command')}>Command Panel</li>
                    <li className={activeScreen === 'staff' ? 'active' : ''} onClick={() => setActiveScreen('staff')}>Staff Terminal</li>
                    <li className={activeScreen === 'forecast' ? 'active' : ''} onClick={() => setActiveScreen('forecast')}>Outcome Forecast</li>
                    <li className={activeScreen === 'stress' ? 'active' : ''} onClick={() => setActiveScreen('stress')}>Stress Test</li>
                    <li className={activeScreen === 'bottleneck' ? 'active' : ''} onClick={() => setActiveScreen('bottleneck')}>Bottleneck Analysis</li>
                    <li className={activeScreen === 'safety' ? 'active' : ''} onClick={() => setActiveScreen('safety')}>Safety Analytics</li>
                    <li className={activeScreen === 'playback' ? 'active' : ''} onClick={() => setActiveScreen('playback')}>Sim Playback</li>
                </ul>
            </nav>
            <main className="content">
                <header>
                    <h1>{activeScreen.replace(/^\w/, (c) => c.toUpperCase()).replace(/([A-Z])/g, ' $1').trim()}</h1>
                    <div className={`status-indicator ${liveData.venueStatus === 'Red' ? 'red' : 'amber'}`}>
                        {liveData.venueStatus === 'Red' ? 'CRITICAL SURGE' : 'MONITORING LEAD TIME'}
                    </div>
                </header>
                <div className="screen-container">
                    {renderScreen()}
                </div>
            </main>
        </div>
    )
}

export default DemoDashboard
