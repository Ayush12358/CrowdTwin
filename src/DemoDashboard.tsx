import React, { useState, useEffect } from 'react'
import { useTheme } from './ThemeContext'
import './styles/index.css'

// Linear Operational Phases
type Phase = 'strategize' | 'monitor' | 'prevention' | 'response'

const DemoDashboard: React.FC = () => {
    const { theme, setTheme, accent, setAccent } = useTheme()
    const [currentPhase, setCurrentPhase] = useState<Phase>('strategize')
    const [subStep, setSubStep] = useState(0) // Internal step within a phase
    const [isSimulating, setIsSimulating] = useState(false)
    const [alerts, setAlerts] = useState<string[]>([])
    const [mishapResolved, setMishapResolved] = useState(false)
    const [selectedAction, setSelectedAction] = useState<string | null>(null)
    const [simProgress, setSimProgress] = useState(0)

    // Global Effect for Phase 4 Simulation
    useEffect(() => {
        if (currentPhase === 'response' && subStep === 1 && simProgress < 100) {
            const timer = setTimeout(() => setSimProgress(p => p + 5), 100)
            return () => clearTimeout(timer)
        }
    }, [currentPhase, subStep, simProgress])

    // Phase Configuration
    const phases = [
        { id: 'strategize', label: '1. STRATEGIZE', desc: 'Pre-Event Planning' },
        { id: 'monitor', label: '2. MONITOR', desc: 'Live Surveillance' },
        { id: 'prevention', label: '3. PREVENTION', desc: 'Problem Finding' },
        { id: 'response', label: '4. RESPONSE', desc: 'Solution Finding' }
    ]

    // State Transitions
    const nextStep = () => setSubStep(prev => prev + 1)
    const resetSubStep = (newPhase: Phase) => {
        setCurrentPhase(newPhase)
        setSubStep(0)
        setSimProgress(0)
        setMishapResolved(false)
        setSelectedAction(null)
    }

    // Phase 1: Strategize Sub-renders
    const renderStrategize = () => {
        switch (subStep) {
            case 0: // Upload
                return (
                    <div className="phase-card center-content">
                        <div className="upload-zone" onClick={nextStep}>
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="1.5">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" />
                            </svg>
                            <h3>Upload Venue Map (Base)</h3>
                            <p>Upload architectural layout for AI Node mapping</p>
                            <div className="pro-btn primary">Select Base Map</div>
                        </div>
                    </div>
                )
            case 1: // Base Map View
                return (
                    <div className="phase-card">
                        <div className="map-view-container">
                            <img src="/assets/Base.jpeg" alt="Base Map" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                            <div className="floating-insights glass animate-in">
                                <h4>Venue Map Ingested</h4>
                                <p>Architectural layout parsed. Ready for Node generation.</p>
                                <button className="pro-btn primary small" onClick={nextStep}>Generate Nodes & Edges</button>
                            </div>
                        </div>
                    </div>
                )
            case 2: // Init Nodes & Edges
                return (
                    <div className="phase-card">
                        <div className="map-view-container">
                            <img src="/assets/Init Nodes and Edges.png" alt="Init Nodes" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                            <div className="floating-insights glass animate-in" style={{ borderColor: 'var(--amber)' }}>
                                <h4>Initial Node Mapping</h4>
                                <p>Analyzing crowd flow vectors and junction nodes...</p>
                                <button className="pro-btn primary small" onClick={nextStep}>Finalize Netowrk</button>
                            </div>
                        </div>
                    </div>
                )
            case 3: // Final Nodes & Edges
                return (
                    <div className="phase-card">
                        <div className="map-view-container">
                            <img src="/assets/Final Nodes and Edges.png" alt="Final Nodes" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                            <div className="floating-insights glass animate-in" style={{ borderColor: 'var(--green)' }}>
                                <h4>Network Optimized</h4>
                                <p>Final nodes and paths verified for personnel distribution.</p>
                                <button className="pro-btn primary small" onClick={() => resetSubStep('monitor')}>Launch Monitoring</button>
                            </div>
                        </div>
                    </div>
                )
            default: return null
        }
    }

    // Phase 2: Monitor
    const renderMonitor = () => (
        <div className="phase-card no-padding">
            <div className="live-monitor-grid">
                <div className="video-viewport">
                    <video src="/assets/Pre Heatmap.mp4" autoPlay loop muted style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    <div className="telemetry-hud pulse-line">LIVE FEED: PSARA_STADIUM_NORTH</div>
                    <div className="corner-tag pulse">PRE-INTERVENTION MONITORING</div>
                </div>
                <div className="alerts-sidebar glass">
                    <h3>Hazard Monitoring</h3>
                    <div className="alert-item amber" onClick={() => resetSubStep('prevention')} style={{ marginBottom: '1rem' }}>
                        <div className="alert-header">POTENTIAL MISHAP (Problem Finding)</div>
                        <p>Density surge detected at Sector A Exit. Lead time: 8m.</p>
                        <small>Investigate Prevention →</small>
                    </div>
                    <div className="alert-item red" onClick={() => resetSubStep('response')}>
                        <div className="alert-header">CRITICAL MISHAP (Solution Finding)</div>
                        <p>Active incident at Stairwell 2. Immediate response required!</p>
                        <small>Deploy Solution →</small>
                    </div>
                </div>
            </div>
        </div>
    )

    // Phase 3: Prevention (Problem Finding)
    const renderPrevention = () => (
        <div className="phase-card no-padding">
            <div className="prevention-layout" style={{ display: 'flex', height: '100%' }}>
                <div className="visual-side" style={{ flex: 1, position: 'relative', background: '#000' }}>
                    <video
                        src={mishapResolved ? "/assets/Post Heatmap.mp4" : "/assets/Pre Heatmap.mp4"}
                        autoPlay loop muted
                        style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.6 }}
                    />
                    {!mishapResolved && (
                        <div className="alert-overlay animate-pulse" style={{ position: 'absolute', top: '10%', left: '10%', right: '10%', zIndex: 10 }}>
                            <img src="/assets/Mishap pred alert.png" alt="Alert" style={{ width: '100%', borderRadius: '12px', boxShadow: '0 0 40px rgba(239, 68, 68, 0.5)' }} />
                        </div>
                    )}
                    {mishapResolved && (
                        <div className="success-overlay animate-in" style={{ position: 'absolute', bottom: '2rem', left: '2rem', right: '2rem', background: 'rgba(16, 185, 129, 0.9)', padding: '1.5rem', borderRadius: '12px', color: '#fff', textAlign: 'center' }}>
                            <h2 style={{ margin: 0 }}>✓ MISHAP AVERTED</h2>
                            <p style={{ margin: '0.5rem 0' }}>Post-intervention flow stabilized. Returning to normal monitoring.</p>
                            <button className="pro-btn secondary small" style={{ color: '#000' }} onClick={() => resetSubStep('monitor')}>Resume Active Monitoring</button>
                        </div>
                    )}
                </div>
                {!mishapResolved && (
                    <div className="control-side glass" style={{ width: '400px', padding: '2rem', borderLeft: '1px solid var(--border-color)' }}>
                        <div className="header-alert red" style={{ marginBottom: '2rem' }}>
                            <h2>Mishap Prediction</h2>
                            <p>North Gate Tunnel | Risk: 92%</p>
                        </div>
                        <div className="suggestions-grid" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            <div className={`suggestion-card ${selectedAction === 'open' ? 'active' : ''}`} onClick={() => setSelectedAction('open')}>
                                <h4>Open Emergency Exit 4</h4>
                                <p>Release bottleneck flow to bypass sector B.</p>
                            </div>
                            <div className={`suggestion-card ${selectedAction === 'divert' ? 'active' : ''}`} onClick={() => setSelectedAction('divert')}>
                                <h4>Divert to West Plaza</h4>
                                <p>Reroute inflow to larger standing area.</p>
                            </div>
                        </div>
                        {selectedAction && (
                            <div className="command-directive animate-in" style={{ marginTop: '2rem' }}>
                                <h3>DIRECTIVE</h3>
                                <p className="code-font">TO_ALPHA: "Open Gate 4 now."</p>
                                <button className="pro-btn primary" style={{ width: '100%' }} onClick={() => setMishapResolved(true)}>Execute</button>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    )

    // Phase 4: Response (Solution Finding)
    const renderResponse = () => {
        switch (subStep) {
            case 0: // Detection
                return (
                    <div className="phase-card no-padding">
                        <div style={{ position: 'relative', height: '100%', background: '#000' }}>
                            <video src="/assets/Pre Heatmap.mp4" autoPlay loop muted style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.5 }} />
                            <div className="central-alert animate-in" style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: '80%', maxWidth: '600px' }}>
                                <img src="/assets/Mishap pred alert.png" alt="Critical Alert" style={{ width: '100%', borderRadius: '20px', border: '2px solid var(--red)', boxShadow: '0 0 50px var(--red)' }} />
                                <div className="overlay-desc glass" style={{ padding: '2rem', marginTop: '1rem', textAlign: 'center', borderRadius: '16px' }}>
                                    <h2 style={{ color: 'var(--red)', margin: 0 }}>CRITICAL INCIDENT IDENTIFIED</h2>
                                    <p>Automated solution simulation triggered in background.</p>
                                    <button className="pro-btn primary" style={{ marginTop: '1rem' }} onClick={nextStep}>Analyze Solutions</button>
                                </div>
                            </div>
                        </div>
                    </div>
                )
            case 1: // Simulation
                return (
                    <div className="phase-card center-content">
                        <div className="sim-loading">
                            <div className="spinner"></div>
                            <h3>AI Search in Progress...</h3>
                            <div className="progress-bar">
                                <div className="fill" style={{ width: `${simProgress}%` }}></div>
                            </div>
                            <p className="code-font" style={{ color: 'var(--amber)' }}>Parallel Sim {simProgress * 1050} agent-steps...</p>
                            {simProgress >= 100 && <button className="pro-btn primary" onClick={nextStep}>View Actionable Rescue Plan</button>}
                        </div>
                    </div>
                )
            case 2: // Result
                return (
                    <div className="phase-card">
                        <div className="solution-panel">
                            <h3>RESUE PROTOCOL OMEGA</h3>
                            <div className="action-step active">
                                <div className="step-num">DEPLOY</div>
                                <p>Team Bravo to Stairwell 2. Team Charlie to East Escapements.</p>
                            </div>
                            <div className="directive-box glass">
                                <h4>Ground Directive</h4>
                                <p className="code-font">"All units, engage Sector Delta bypass. Evacuate Section 4."</p>
                            </div>
                            <button className="pro-btn success" onClick={nextStep}>Verify Resolution</button>
                        </div>
                    </div>
                )
            case 3: // Handled
                return (
                    <div className="phase-card no-padding">
                        <div style={{ position: 'relative', height: '100%', background: '#000' }}>
                            <video src="/assets/Post Heatmap.mp4" autoPlay loop muted style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                            <div className="handled-overlay animate-in" style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center', padding: '3rem', border: '5px solid var(--green)', borderRadius: '30px', background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(20px)' }}>
                                <div className="big-check" style={{ fontSize: '100px', lineHeight: 1 }}>✓</div>
                                <h1 style={{ fontSize: '3rem', margin: '1rem 0' }}>MISHAP HANDLED</h1>
                                <p style={{ fontSize: '1.2rem', opacity: 0.8 }}>Incident resolved via post-intervention dynamics.</p>
                                <button className="pro-btn secondary" onClick={() => resetSubStep('monitor')}>Back to Watch Mode</button>
                            </div>
                        </div>
                    </div>
                )
            default: return null
        }
    }

    return (
        <div className={`app-container ${theme}`} style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
            {/* Mission Timeline Header */}
            <header className="mission-timeline">
                <div className="logo-group">
                    <div className="logo">CrowdTwin</div>
                    <div className="mission-status pulse">● LIVE_OPERATIONS</div>
                </div>
                <div className="phase-nav">
                    {phases.map(p => (
                        <div key={p.id} className={`phase-item ${currentPhase === p.id ? 'active' : ''}`} onClick={() => resetSubStep(p.id as Phase)}>
                            <div className="label">{p.label}</div>
                            <div className="desc">{p.desc}</div>
                        </div>
                    ))}
                </div>
                <div className="theme-toggle" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
                    {theme === 'dark' ? '☀' : '☾'}
                </div>
            </header>

            {/* Main Content Area */}
            <main className="operational-content" style={{ flex: 1, padding: '2rem', overflowY: 'auto', background: 'var(--bg-main)' }}>
                {currentPhase === 'strategize' && renderStrategize()}
                {currentPhase === 'monitor' && renderMonitor()}
                {currentPhase === 'prevention' && renderPrevention()}
                {currentPhase === 'response' && renderResponse()}
            </main>

            {/* Global Accent Control (Fixed at bottom) */}
            <div className="global-controls" style={{ padding: '0.5rem 2rem', background: 'var(--card-bg)', borderTop: '1px solid var(--border-color)', display: 'flex', gap: '1rem', alignItems: 'center' }}>
                <small style={{ color: 'var(--text-muted)' }}>Security Protocol HSL:</small>
                {[
                    { h: 225, s: '100%', l: '50%', label: 'Blue' },
                    { h: 158, s: '80%', l: '40%', label: 'Emerald' },
                    { h: 38, s: '90%', l: '50%', label: 'Amber' },
                    { h: 0, s: '80%', l: '50%', label: 'Red' }
                ].map(c => (
                    <div key={c.h} className="accent-dot" style={{ background: `hsl(${c.h}, ${c.s}, ${c.l})` }} onClick={() => setAccent({ h: c.h, s: c.s, l: c.l })}></div>
                ))}
                <div style={{ marginLeft: 'auto', fontSize: '0.7rem', color: 'var(--text-muted)' }}>Powered by Crowd Twin ABM Engine v1.2</div>
            </div>

            <style>{`
                .mission-timeline { display: flex; align-items: center; justify-content: space-between; padding: 1rem 2rem; background: var(--bg-surface); border-bottom: 1px solid var(--border-color); }
                .phase-nav { display: flex; gap: 3rem; }
                .phase-item { cursor: pointer; opacity: 0.4; transition: 0.3s; }
                .phase-item.active { opacity: 1; border-bottom: 2px solid var(--primary); }
                .phase-item .label { font-size: 0.7rem; font-weight: 800; color: var(--primary); }
                .phase-item .desc { font-size: 0.9rem; font-weight: 600; }
                
                .phase-card { background: var(--card-bg); border-radius: 24px; border: 1px solid var(--border-color); height: 100%; min-height: 500px; padding: 2rem; position: relative; overflow: hidden; }
                .phase-card.no-padding { padding: 0; }
                .center-content { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
                
                .upload-zone { border: 2px dashed var(--border-color); border-radius: 20px; padding: 4rem; cursor: pointer; transition: 0.3s; }
                .upload-zone:hover { border-color: var(--primary); background: var(--primary-glow); }
                
                .map-view-container { position: relative; height: 100%; display: flex; align-items: center; }
                .overlay-nodes .node { position: absolute; width: 12px; height: 12px; background: var(--primary); border-radius: 50%; box-shadow: 0 0 10px var(--primary); }
                .floating-insights { position: absolute; bottom: 2rem; right: 2rem; width: 300px; padding: 1.5rem; border-radius: 16px; border: 1px solid var(--primary); background: rgba(0,0,0,0.4); backdrop-filter: blur(10px); }
                
                .split-view { display: grid; grid-template-columns: 1fr 400px; gap: 2rem; height: 100%; }
                .personnel-dot { position: absolute; background: var(--amber); color: #000; font-size: 0.6rem; font-weight: 900; padding: 4px; border-radius: 4px; }
                
                .live-monitor-grid { display: grid; grid-template-columns: 1fr 350px; height: 100%; }
                .video-viewport { position: relative; background: #000; }
                .telemetry-hud { position: absolute; top: 1rem; left: 1rem; color: var(--primary); font-family: monospace; font-size: 0.8rem; letter-spacing: 2px; }
                
                .alerts-sidebar { padding: 1.5rem; border-left: 1px solid var(--border-color); }
                .alert-item { background: rgba(245, 158, 11, 0.1); border: 1px solid var(--amber); padding: 1rem; border-radius: 12px; cursor: pointer; transition: 0.2s; }
                .alert-item:hover { transform: scale(1.02); }
                
                .suggestion-card { background: var(--bg-surface); border: 1px solid var(--border-color); padding: 1.5rem; border-radius: 16px; cursor: pointer; }
                .suggestion-card.active { border-color: var(--primary); background: var(--primary-glow); }
                
                .command-directive { margin-top: 2rem; padding: 1.5rem; border: 1px solid var(--primary); border-radius: 16px; background: rgba(71, 117, 255, 0.05); }
                .code-font { font-family: 'Courier New', monospace; background: #000; padding: 0.5rem; border-radius: 4px; color: var(--green); margin: 0.5rem 0; }
                
                .sim-loading { width: 400px; }
                .spinner { width: 40px; height: 40px; border: 3px solid var(--border-color); border-top-color: var(--primary); border-radius: 50%; animation: rotate 1s linear infinite; margin: 0 auto 1.5rem; }
                @keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
                
                .progress-bar { height: 8px; background: var(--border-color); border-radius: 4px; margin: 1rem 0; overflow: hidden; }
                .progress-bar .fill { height: 100%; background: var(--primary); transition: width 0.3s; }
                
                .big-check { font-size: 4rem; color: var(--green); margin-bottom: 1rem; }
                .pro-btn { padding: 0.75rem 1.5rem; border-radius: 12px; font-weight: 700; cursor: pointer; border: none; transition: 0.2s; text-transform: uppercase; letter-spacing: 1px; }
                .pro-btn.primary { background: var(--primary); color: #fff; }
                .pro-btn.secondary { background: var(--card-bg); border: 1px solid var(--border-color); color: var(--text-main); }
                .pro-btn.success { background: var(--green); color: #fff; }
                
                .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); }
                .animate-in { animation: slideIn 0.4s ease-out; }
                @keyframes slideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
            `}</style>
        </div>
    )
}

export default DemoDashboard
