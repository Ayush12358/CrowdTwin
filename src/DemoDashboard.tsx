import { useState, useEffect, useMemo } from 'react'
import { API_STUBS, Zone, ForecastEvent, Recommendation, USER_STORIES, Story } from './api/mockData'
import { useTheme } from './ThemeContext'

function DemoDashboard() {
    const [activeScreen, setActiveScreen] = useState('overview')
    const [activeStoryId, setActiveStoryId] = useState<string | null>(null)
    const [showObjective, setShowObjective] = useState(false)
    const [liveData, setLiveData] = useState(API_STUBS.getLiveDensity())
    const [forecast, setForecast] = useState(API_STUBS.getForecast())
    const [executedRecs, setExecutedRecs] = useState<string[]>([])

    // Theme and Accent State from Global Context
    const { theme, setTheme, accent, setAccent } = useTheme()

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
        if (id === 'audit_trail') setActiveScreen('analytics')
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
            case 'overview':
                return (
                    <div className="screen-overview">
                        <div className="dashboard-header">
                            <div className="header-left">
                                <h1>Crowd-Twin Real-time Monitor</h1>
                            </div>
                            <div className="header-right">
                                <div className="search-bar">
                                    <span>🔍</span>
                                    <input type="text" placeholder="Search venues or zones..." />
                                </div>
                                <div className="user-profile">
                                    <div className="avatar"></div>
                                    <span style={{ fontWeight: 600 }}>Ayush M.</span>
                                </div>
                            </div>
                        </div>

                        <div className="stat-row">
                            <div className="pro-stat-card">
                                <div className="stat-icon-wrap">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                                </div>
                                <div className="stat-info">
                                    <h4>Max Density</h4>
                                    <div className="value">6.8 <small>p/m²</small></div>
                                </div>
                            </div>
                            <div className="pro-stat-card">
                                <div className="stat-icon-wrap">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect><line x1="9" y1="22" x2="15" y2="22"></line><line x1="9" y1="18" x2="15" y2="18"></line><line x1="9" y1="14" x2="15" y2="14"></line><line x1="9" y1="10" x2="15" y2="10"></line></svg>
                                </div>
                                <div className="stat-info">
                                    <h4>Venue Capacity</h4>
                                    <div className="value">92%</div>
                                </div>
                            </div>
                            <div className="pro-stat-card" style={{ borderLeft: '4px solid var(--amber)' }}>
                                <div className="stat-icon-wrap" style={{ color: 'var(--amber)' }}>
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
                                </div>
                                <div className="stat-info">
                                    <h4>Predicted Alerts</h4>
                                    <div className="value">3</div>
                                </div>
                            </div>
                        </div>

                        <div className="dashboard-grid">
                            <div className="forecast-card">
                                <div className="chart-header">
                                    <h3>Occupancy Forecast</h3>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                        <span style={{ marginRight: '1rem' }}>— Actual</span>
                                        <span style={{ borderBottom: '1px dashed var(--primary)' }}>- - Predicted</span>
                                    </div>
                                </div>
                                <div className="chart-viz">
                                    <svg width="100%" height="100%" viewBox="0 0 500 200" preserveAspectRatio="none">
                                        <path d="M0 180 Q100 160 200 120 T400 60" fill="none" stroke="var(--primary)" strokeWidth="3" />
                                        <path d="M0 180 Q100 160 200 120 T400 40" fill="none" stroke="var(--primary)" strokeWidth="2" strokeDasharray="5,5" opacity="0.5" />
                                        <path d="M200 120 Q300 100 500 20" fill="rgba(0,136,255,0.1)" />
                                    </svg>
                                    <div style={{ position: 'absolute', bottom: '-20px', left: 0, width: '100%', display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                                        <span>14:00</span><span>16:00</span><span>18:00</span><span>20:00</span>
                                    </div>
                                </div>
                            </div>
                            <div className="gate-table-card">
                                <h3>Active Gates</h3>
                                <table className="pro-table">
                                    <thead>
                                        <tr><th>Name</th><th>Status</th></tr>
                                    </thead>
                                    <tbody>
                                        <tr><td>Gate A (North)</td><td><span className="gate-pill open">OPEN</span></td></tr>
                                        <tr><td>Gate B (South)</td><td><span className="gate-pill closed">CLOSED</span></td></tr>
                                        <tr><td>Gate C (VIP)</td><td><span className="gate-pill open">OPEN</span></td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )
            case 'heatmap':
                return (
                    <div className="screen-heatmap pro-map">
                        <div className="map-controls-top">
                            <div className="search-bar" style={{ background: 'var(--card-bg)' }}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                                <input type="text" placeholder="Search Location..." style={{ background: 'transparent', color: 'var(--text-main)', border: 'none', outline: 'none' }} />
                            </div>
                        </div>
                        <div className="stadium-container">
                            <svg className="stadium-svg" viewBox="0 0 400 400">
                                {/* Stadium Tiers */}
                                <circle cx="200" cy="200" r="180" fill="none" stroke="#e2e8f0" strokeWidth="2" />
                                <circle cx="200" cy="200" r="140" fill="none" stroke="#e2e8f0" strokeWidth="40" />
                                <circle cx="200" cy="200" r="90" fill="none" stroke="#e2e8f0" strokeWidth="30" />
                                <circle cx="200" cy="200" r="40" fill="#f1f5f9" /> {/* Pitch */}

                                {/* Heat zones */}
                                <circle cx="300" cy="100" r="40" fill="rgba(239, 68, 68, 0.4)" /> {/* Red zone */}
                                <circle cx="100" cy="300" r="50" fill="rgba(245, 158, 11, 0.3)" /> {/* Amber zone */}

                                {/* Agents */}
                                {liveData.zones.map(zone => renderAgents(zone.id, zone.count))}
                            </svg>
                            <div className="map-legend">
                                <span>Density: <span style={{ color: 'var(--red)' }}>●</span> High <span style={{ color: 'var(--amber)' }}>●</span> Medium <span style={{ color: 'var(--green)' }}>●</span> Low</span>
                            </div>
                        </div>
                        <div className="stats-grid" style={{ marginTop: '2rem' }}>
                            {liveData.zones.map(zone => (
                                <div key={zone.id} className="pro-stat-card mini">
                                    <div className="stat-info">
                                        <h4>{zone.name}</h4>
                                        <div className="value" style={{ fontSize: '1.2rem' }}>{zone.density} <small>p/m²</small></div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )
            case 'predictive':
                return (
                    <div className="screen-predictive" style={{ padding: '2rem' }}>
                        <div className="prediction-alert">
                            <div className="alert-header">DENSITY SURGE PREDICTED (15M LEAD TIME)</div>
                            <p><strong>Sector B: Entrance 3</strong></p>
                            <p>Current: 4.8 p/m² | Expected: 7.4 p/m²</p>
                            <div className="confidence-meter">
                                <div className="meter-fill" style={{ width: '92%' }}></div>
                            </div>
                            <small>Simulation Confidence: 92% (ABM Score: 0.88)</small>
                        </div>
                        <div className="timeline">
                            <div className="time-point active">T-15m</div>
                            <div className="time-line"></div>
                            <div className="time-point">T-10m</div>
                            <div className="time-line"></div>
                            <div className="time-point">T-5m</div>
                            <div className="time-line"></div>
                            <div className="time-point">CRITICAL</div>
                        </div>
                    </div>
                )
            case 'alerts':
            case 'command':
                return (
                    <div className="screen-mission">
                        <div className="mission-grid">
                            <div className="venue-viewport">
                                <div className="viewport-header">VENUE MAP - PREDICTIVE VIEW</div>
                                <div className="isometric-map">
                                    {/* SVG Isometric representation inspired by reference */}
                                    <svg viewBox="0 0 600 400" className="iso-svg">
                                        <path d="M100 200 L300 100 L500 200 L300 300 Z" fill="none" stroke="var(--glass-border)" strokeWidth="2" />
                                        <path d="M150 220 L300 145 L450 220 L300 295 Z" fill="none" stroke="var(--glass-border)" strokeWidth="1" />
                                        {/* Surge Path */}
                                        <path d="M300 295 L300 245 L200 195 L200 145" fill="none" stroke="var(--red)" strokeWidth="4" strokeLinecap="round" className="surge-path" />
                                    </svg>
                                    <div className="map-alert-tag">
                                        <div className="tag-header">PREDICTIVE ALERT: CROWD SURGE</div>
                                        <div className="tag-time">TIME TO CRITICAL: 04:32</div>
                                    </div>
                                </div>
                            </div>
                            <div className="control-panel">
                                <div className="panel-section">
                                    <h3>ACTIVE ALERTS</h3>
                                    <div className="alert-tiles">
                                        {forecast.forecastedEvents.map((event, i) => (
                                            <div key={i} className="alert-tile critical">
                                                <div className="tile-body">
                                                    <div>PREDICTIVE ALERT: {event.type.replace('_', ' ')}</div>
                                                    <small>Time To Critical: 10:30 PM</small>
                                                </div>
                                                <div className="tile-timer">04:32</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                <div className="panel-section">
                                    <h3>RESPONSE PROTOCOLS</h3>
                                    <div className="protocol-btns">
                                        {forecast.recommendations.map(rec => (
                                            <button
                                                key={rec.id}
                                                className={`protocol-btn ${executedRecs.includes(rec.id) ? 'executed' : ''}`}
                                                onClick={() => handleExecute(rec.id)}
                                            >
                                                {rec.action}
                                                {executedRecs.includes(rec.id) && <span className="check">✓</span>}
                                            </button>
                                        ))}
                                        <button className="protocol-btn secondary">ALERTS LOG</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )
            case 'staff':
                return (
                    <div className="screen-staff">
                        <div className="mobile-view">
                            <div className="mobile-header">COMMAND TERMINAL - SECTOR B</div>
                            <div className="mobile-content">
                                {executedRecs.length > 0 ? (
                                    <div className="directive-notice">
                                        <h3>NEW DIRECTIVE</h3>
                                        <p>Redirect flow from Sector B to North Exit immediately.</p>
                                        <button className="ack-btn" onClick={() => setActiveScreen('outcome')}>Acknowledge & Sync</button>
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
            case 'outcome':
                return (
                    <div className="screen-outcome" style={{ padding: '2rem' }}>
                        <h3>Forecast Outcome: Intervention Delta</h3>
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
            case 'bottleneck':
                return (
                    <div className="screen-stress" style={{ padding: '2rem' }}>
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
            case 'analytics':
                return (
                    <div className="screen-analytics" style={{ padding: '2rem' }}>
                        <div className="kpi-dashboard">
                            <div className="kpi-card"><h3>9.8</h3><p>Safety Score</p></div>
                            <div className="kpi-card"><h3>100%</h3><p>Alert Response</p></div>
                            <div className="kpi-card"><h3>0</h3><p>Incidents</p></div>
                        </div>
                    </div>
                )
            case 'playback':
                return (
                    <div className="screen-playback" style={{ padding: '2rem' }}>
                        <div className="placeholder-card">
                            <h2>Simulation Playback</h2>
                            <p>Accuracy Score: <strong>94.2%</strong></p>
                            <div className="video-placeholder" style={{ background: '#f1f5f9', border: '1px solid #e2e8f0', color: '#64748b' }}>
                                SIMULATION REPLAY: 18:00 (Incident ID #82)
                            </div>
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
                    <li className={activeScreen === 'overview' ? 'active' : ''} onClick={() => setActiveScreen('overview')}>SaaS Overview</li>
                    <li className={activeScreen === 'heatmap' ? 'active' : ''} onClick={() => setActiveScreen('heatmap')}>Live Heatmap</li>
                    <li className={activeScreen === 'predictive' ? 'active' : ''} onClick={() => setActiveScreen('predictive')}>Predictive Mode</li>
                    <li className={activeScreen === 'alerts' ? 'active' : ''} onClick={() => setActiveScreen('alerts')}>Safety Alerts</li>
                    <li className={activeScreen === 'command' ? 'active' : ''} onClick={() => setActiveScreen('command')}>Command Panel</li>
                    <li className={activeScreen === 'staff' ? 'active' : ''} onClick={() => setActiveScreen('staff')}>Staff Terminal</li>
                    <li className={activeScreen === 'outcome' ? 'active' : ''} onClick={() => setActiveScreen('outcome')}>Outcome Forecast</li>
                    <li className={activeScreen === 'stress' ? 'active' : ''} onClick={() => setActiveScreen('stress')}>Stress Test</li>
                    <li className={activeScreen === 'bottleneck' ? 'active' : ''} onClick={() => setActiveScreen('bottleneck')}>Bottleneck Analysis</li>
                    <li className={activeScreen === 'analytics' ? 'active' : ''} onClick={() => setActiveScreen('analytics')}>Safety Analytics</li>
                    <li className={activeScreen === 'playback' ? 'active' : ''} onClick={() => setActiveScreen('playback')}>Sim Playback</li>
                </ul>

                {/* Theme & Accent Controls */}
                <div className="theme-controls" style={{ marginTop: 'auto', paddingTop: '2rem', borderTop: '1px solid var(--border-color)' }}>
                    <div style={{ marginBottom: '1rem' }}>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Theme</div>
                        <div style={{ display: 'flex', gap: '0.5rem', background: 'var(--card-bg)', padding: '0.2rem', borderRadius: '20px', border: '1px solid var(--border-color)' }}>
                            <button
                                onClick={() => setTheme('dark')}
                                style={{ flex: 1, padding: '0.5rem', borderRadius: '16px', border: 'none', background: theme === 'dark' ? 'var(--bg-main)' : 'transparent', color: theme === 'dark' ? 'var(--text-main)' : 'var(--text-muted)', cursor: 'pointer', transition: 'all 0.3s' }}
                            >
                                Dark
                            </button>
                            <button
                                onClick={() => setTheme('light')}
                                style={{ flex: 1, padding: '0.5rem', borderRadius: '16px', border: 'none', background: theme === 'light' ? 'var(--bg-main)' : 'transparent', color: theme === 'light' ? 'var(--text-main)' : 'var(--text-muted)', cursor: 'pointer', transition: 'all 0.3s' }}
                            >
                                Light
                            </button>
                        </div>
                    </div>
                    <div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Accent</div>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button onClick={() => setAccent({ h: 210, s: '100%', l: '50%' })} style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'hsl(210, 100%, 50%)', border: accent.h === 210 ? '2px solid #fff' : '2px solid transparent', cursor: 'pointer' }} title="Blue"></button>
                            <button onClick={() => setAccent({ h: 150, s: '80%', l: '40%' })} style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'hsl(150, 80%, 40%)', border: accent.h === 150 ? '2px solid #fff' : '2px solid transparent', cursor: 'pointer' }} title="Emerald"></button>
                            <button onClick={() => setAccent({ h: 280, s: '80%', l: '60%' })} style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'hsl(280, 80%, 60%)', border: accent.h === 280 ? '2px solid #fff' : '2px solid transparent', cursor: 'pointer' }} title="Purple"></button>
                        </div>
                    </div>
                </div>
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
