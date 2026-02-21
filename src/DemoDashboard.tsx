import { useState, useEffect, useMemo } from 'react'
import { API_STUBS, Zone, ForecastEvent, Recommendation, USER_STORIES, Story } from './api/mockData'

function DemoDashboard() {
    const [activeScreen, setActiveScreen] = useState('heatmap')
    const [activeStoryId, setActiveStoryId] = useState<string | null>(null)
    const [showObjective, setShowObjective] = useState(false)
    const [liveData, setLiveData] = useState(API_STUBS.getLiveDensity())
    const [forecast, setForecast] = useState(API_STUBS.getForecast())
    const [executedRecs, setExecutedRecs] = useState<string[]>([])

    // Active story metadata
    const activeStory = useMemo(() =>
        USER_STORIES.find(s => s.id === activeStoryId),
        [activeStoryId])

    // Simulate live updates
    useEffect(() => {
        const interval = setInterval(() => {
            setLiveData(API_STUBS.getLiveDensity())
        }, 5000)
        return () => clearInterval(interval)
    }, [])

    const handleExecute = (id: string) => {
        setExecutedRecs(prev => [...prev, id])
        // If it's the first story, move to staff terminal after execution
        if (activeStoryId === 'safety_first') {
            setTimeout(() => setActiveScreen('staff'), 1000)
        }
    }

    const selectStory = (id: string) => {
        setActiveStoryId(id)
        setShowObjective(true)
        // Auto-navigate to starting screen if needed
        if (id === 'safety_first') setActiveScreen('heatmap')
        if (id === 'structural_fix') setActiveScreen('stress')
        if (id === 'audit_trail') setActiveScreen('safety')
    }

    const renderAgents = (zoneId: string, count: number) => {
        const agents = []
        const isRed = zoneId === 'sector_b' && activeStoryId === 'safety_first'
        for (let i = 0; i < count / 10; i++) {
            const style = {
                top: `${Math.random() * 80 + 10}%`,
                left: `${Math.random() * 80 + 10}%`,
                animationDelay: `${Math.random() * 2}s`
            }
            agents.push(
                <div
                    key={i}
                    className={`agent-dot ${isRed ? 'red' : 'amber'}`}
                    style={style}
                />
            )
        }
        return agents
    }

    const renderScreen = () => {
        switch (activeScreen) {
            case 'heatmap':
                return (
                    <div className="screen-heatmap">
                        <div className="map-placeholder high-fidelity" style={{ backgroundImage: `url('/assets/heatmap_v2.png')`, backgroundSize: 'cover' }}>
                            {liveData.zones.map(zone => (
                                <div key={zone.id} className="zone-visual" style={{ position: 'absolute', inset: 0 }}>
                                    {renderAgents(zone.id, zone.count)}
                                </div>
                            ))}
                            <div className="zone-indicator" style={{ top: '35%', left: '45%', background: 'var(--amber)' }}>
                                <span>Sector B: 6.8 p/m² (Surge Imminent)</span>
                            </div>
                            <div className="zone-indicator" style={{ top: '15%', left: '70%', background: 'var(--green)' }}>
                                <span>Gate A: 4.2 p/m²</span>
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
                            <p>Predicting critical density surge in <strong>Sector B</strong></p>
                            <div className="confidence-meter">
                                <div className="meter-fill" style={{ width: '89%' }}></div>
                                <span>89% Confidence</span>
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
                                    <h4>{event.type.replace('_', ' ')}</h4>
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
                                    {executedRecs.includes(rec.id) ? (
                                        <span className="execute-status">EXECUTED</span>
                                    ) : (
                                        <button className="confirm-btn" onClick={() => handleExecute(rec.id)}>Execute</button>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )
            case 'staff':
                return (
                    <div className="screen-staff">
                        <div className="mobile-view">
                            <div className="mobile-header">STAFF TERMINAL (Zone B)</div>
                            <div className="mobile-content">
                                {executedRecs.length > 0 ? (
                                    <div className="directive-notice">
                                        <h3>NEW DIRECTIVE</h3>
                                        <p>Redirect flow from Sector B to North Exit immediately.</p>
                                        <button className="ack-btn" onClick={() => setActiveScreen('forecast')}>Acknowledge & Sync</button>
                                    </div>
                                ) : (
                                    <div style={{ textAlign: 'center', opacity: 0.5, marginTop: '4rem' }}>
                                        No active directives...
                                    </div>
                                )}
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
                                <div className="outcome-label">7.4 p/m²</div>
                            </div>
                            <div className="view-pane">
                                <h4>With Directive</h4>
                                <div className="graph-bar green" style={{ height: '40%' }}></div>
                                <div className="outcome-label">4.2 p/m²</div>
                                <div className="outcome-delta">↓ 43% Prediction Error Reduction</div>
                            </div>
                        </div>
                    </div>
                )
            case 'stress':
                return (
                    <div className="screen-stress">
                        <div className="placeholder-card">
                            <h2>Full Capacity Stress Test</h2>
                            <p>Simulating 50,000 agents attempting to exit South Stand simultaneously.</p>
                            <button className="confirm-btn" style={{ marginTop: '2rem' }} onClick={() => setActiveScreen('bottleneck')}>
                                Run Simulation
                            </button>
                        </div>
                    </div>
                )
            case 'bottleneck':
                return (
                    <div className="screen-bottleneck">
                        <div className="analysis-card high-fidelity">
                            <div className="mockup-header-lite">3D STRUCTURAL ANALYSIS</div>
                            <div className="analysis-visual">
                                <img src="/assets/security_dashboard_mockup.png" alt="3D Bottleneck Mockup" className="bottleneck-img" />
                                <div className="analysis-overlay">
                                    <div className="alert-header" style={{ color: 'var(--red)' }}>STRUCTURAL BOTTLENECK DETECTED</div>
                                    <h3>Exit 4 Stairwell</h3>
                                    <p>Physical Capacity: 200 p/m</p>
                                    <p>Peak Simulated Demand: 350 p/m</p>
                                </div>
                            </div>
                            <div className="insight-banner" style={{ marginTop: '2rem' }}>
                                <h4>Simulation Insight</h4>
                                <p>Agents exhibit "Stairwell Hesitation" behavior, reducing effective width by 20%.</p>
                            </div>
                        </div>
                    </div>
                )
            case 'safety':
                return (
                    <div className="screen-safety">
                        <div className="kpi-dashboard">
                            <div className="kpi-card"><h3>4</h3><p>Surges Prevented</p></div>
                            <div className="kpi-card"><h3>92%</h3><p>Safety Score</p></div>
                            <div className="kpi-card"><h3>11m</h3><p>Avg Lead Time</p></div>
                        </div>
                    </div>
                )
            case 'playback':
                return (
                    <div className="screen-playback">
                        <div className="video-placeholder">SIMULATION REPLAY: 18:00 (Incident ID #82)</div>
                        <div className="accuracy-label" style={{ marginTop: '1rem', textAlign: 'center' }}>
                            Prediction Accuracy: 94.2% based on agent deviation.
                        </div>
                    </div>
                )
            default:
                return <div>Select a screen</div>
        }
    }

    return (
        <div className="app-container">
            <nav className="sidebar">
                <div className="logo" onClick={() => window.location.href = '/'}>CROWD-TWIN</div>
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
                {/* STORY SELECTOR */}
                <div className="story-selector">
                    {USER_STORIES.map(story => (
                        <button
                            key={story.id}
                            className={`story-btn ${activeStoryId === story.id ? 'active' : ''}`}
                            onClick={() => selectStory(story.id)}
                        >
                            {story.title}
                        </button>
                    ))}
                </div>

                {/* OBJECTIVE OVERLAY */}
                {showObjective && activeStory && (
                    <div className="objective-overlay">
                        <h2>Objective</h2>
                        <p>{activeStory.objective}</p>
                        <button onClick={() => setShowObjective(false)}>Start Story Flow</button>
                    </div>
                )}

                <header>
                    <div>
                        <h1>{activeScreen.replace(/^\w/, (c) => c.toUpperCase()).replace(/([A-Z])/g, ' $1').trim()}</h1>
                        {activeStory && (
                            <span style={{ color: 'var(--primary)', fontSize: '0.8rem', fontWeight: 700 }}>
                                ACTIVE STORY: {activeStory.title}
                            </span>
                        )}
                    </div>
                    <div className={`status-indicator ${liveData.venueStatus === 'Red' ? 'red' : 'amber'}`}>
                        {liveData.venueStatus === 'Red' ? 'CRITICAL SURGE' : 'MONITORING LEAD TIME'}
                    </div>
                </header>

                {/* INSIGHT BANNER */}
                {activeStory && !showObjective && (
                    <div className="insight-banner">
                        <h4>Functional Insight</h4>
                        <p>{activeStory.insight}</p>
                    </div>
                )}

                <div className="screen-container">
                    {renderScreen()}
                </div>
            </main>
        </div>
    )
}

export default DemoDashboard
