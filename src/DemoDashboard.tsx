import React, { useState, useEffect } from 'react'
import { useTheme } from './ThemeContext'
import './styles/index.css'

type TabType = 'twin' | 'predictions'
type TwinPhase = 'upload' | 'init_nodes' | 'final_nodes' | 'live'
type PredPhase = 'live' | 'problem_finding' | 'solution_finding' | 'resolved'

interface RiskNode {
    id: string
    name: string
    riskScore: number
    status: 'High' | 'Medium' | 'Low'
}

const DemoDashboard: React.FC = () => {
    const { theme, setTheme, setAccent } = useTheme()

    // Core Layout State
    const [activeTab, setActiveTab] = useState<TabType>('twin')

    // Tab 1: Crowd Twin State (Pre-Event -> Live)
    const [twinPhase, setTwinPhase] = useState<TwinPhase>('upload')

    // Tab 2: Predictions State (Problem/Solution Finding)
    const [predPhase, setPredPhase] = useState<PredPhase>('live')
    const [simProgress, setSimProgress] = useState(0)

    // Mock Data for Right Pane
    const currentNodes: RiskNode[] = [
        { id: 'N1', name: 'South Gate Choke', riskScore: 68, status: 'Medium' },
        { id: 'E4', name: 'East Corridor', riskScore: 45, status: 'Low' },
        { id: 'N7', name: 'Main Concourse', riskScore: 82, status: 'High' },
    ].sort((a, b) => b.riskScore - a.riskScore)

    const predictedNodes: RiskNode[] = [
        { id: 'N2', name: 'North Gate Tunnel', riskScore: 92, status: 'High' },
        { id: 'E9', name: 'Stairwell B', riskScore: 88, status: 'High' },
        { id: 'N11', name: 'West Plaza Exit', riskScore: 75, status: 'Medium' },
    ].sort((a, b) => b.riskScore - a.riskScore)

    // --- Tab 1: Crowd Twin Renderers ---

    const renderTwinMain = () => {
        switch (twinPhase) {
            case 'upload':
                return (
                    <div className="upload-zone" onClick={() => setTwinPhase('init_nodes')}>
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" /></svg>
                        <h3>Upload Venue Map</h3>
                        <p>Click to process Base.jpeg</p>
                    </div>
                )
            case 'init_nodes':
                return <img src="/assets/Init Nodes and Edges.png" alt="Init Nodes" className="full-asset fade-in" onClick={() => setTwinPhase('final_nodes')} style={{ cursor: 'pointer' }} />
            case 'final_nodes':
                return <img src="/assets/Final Nodes and Edges.png" alt="Final Nodes" className="full-asset fade-in" onClick={() => setTwinPhase('live')} style={{ cursor: 'pointer' }} />
            case 'live':
                return <video src="/assets/Pre Heatmap.mp4" autoPlay loop muted className="full-asset fade-in" />
        }
    }

    const renderTwinBottom = () => {
        if (twinPhase === 'upload') return <p className="muted-text">Awaiting map upload...</p>
        if (twinPhase === 'init_nodes' || twinPhase === 'final_nodes') return (
            <div className="action-row fade-in">
                <div className="action-details">
                    <h4>Pre-Event Distribution Strategy</h4>
                    <p>AI suggests allocating 40% of personnel to {currentNodes[0].name} based on node topology.</p>
                </div>
                <button className="pro-btn primary" onClick={() => setTwinPhase(twinPhase === 'init_nodes' ? 'final_nodes' : 'live')}>
                    {twinPhase === 'init_nodes' ? 'Verify Nodes' : 'Deploy & Go Live'}
                </button>
            </div>
        )
        return (
            <div className="action-row fade-in">
                <div className="action-details">
                    <h4>Live Monitoring Active</h4>
                    <p>Current high-risk sector: {currentNodes[0].name}. Personnel are on standby.</p>
                </div>
                <button className="pro-btn secondary" onClick={() => setActiveTab('predictions')}>View Predictions</button>
            </div>
        )
    }

    // --- Tab 2: Predictions Renderers ---

    useEffect(() => {
        if (activeTab === 'predictions' && predPhase === 'solution_finding' && simProgress < 100) {
            const timer = setTimeout(() => setSimProgress(p => p + 5), 150)
            return () => clearTimeout(timer)
        }
    }, [activeTab, predPhase, simProgress])

    const renderPredMain = () => {
        switch (predPhase) {
            case 'live':
                return (
                    <div className="relative-container fade-in">
                        <video src="/assets/Pre Heatmap.mp4" autoPlay loop muted className="full-asset" />
                        <div className="sim-overlay-badge">Predictive Engine Active (15m Ahead)</div>
                    </div>
                )
            case 'problem_finding':
            case 'solution_finding':
                return (
                    <div className="relative-container fade-in">
                        <video src="/assets/Pre Heatmap.mp4" autoPlay loop muted className="full-asset opacity-50" />
                        <img src="/assets/Mishap pred alert.png" alt="Mishap Alert" className="overlay-alert pulse-fast" />
                    </div>
                )
            case 'resolved':
                return (
                    <div className="relative-container fade-in">
                        <video src="/assets/Post Heatmap.mp4" autoPlay loop muted className="full-asset" />
                        <div className="success-badge">Mishap Averted/Handled</div>
                    </div>
                )
        }
    }

    const renderPredBottom = () => {
        switch (predPhase) {
            case 'live':
                return (
                    <div className="action-row fade-in">
                        <p className="muted-text">Monitoring future states...</p>
                        <div className="btn-group">
                            <button className="pro-btn warning" onClick={() => setPredPhase('problem_finding')}>Trigger Problem (Avert)</button>
                            <button className="pro-btn danger" onClick={() => { setPredPhase('solution_finding'); setSimProgress(0); }}>Trigger Incident (Handle)</button>
                        </div>
                    </div>
                )
            case 'problem_finding':
                return (
                    <div className="action-grid fade-in">
                        <div className="action-choices">
                            <h4>Problem Detected: Avert using Suggestions</h4>
                            <div className="choice-list">
                                <button className="choice-btn" onClick={() => setPredPhase('resolved')}>
                                    <strong>Recommendation 1</strong>: Open Emergency Gate 4
                                </button>
                                <button className="choice-btn" onClick={() => setPredPhase('resolved')}>
                                    <strong>Recommendation 2</strong>: Divert to West Plaza
                                </button>
                            </div>
                        </div>
                        <div className="command-directive glass">
                            <h5>Command Centre Directive</h5>
                            <code className="green-text">DIRECT_GROUND: "Evac path clear, execute Recommendation 1."</code>
                        </div>
                    </div>
                )
            case 'solution_finding':
                return (
                    <div className="action-row fade-in">
                        <div className="sim-loader-area">
                            {simProgress < 100 ? (
                                <>
                                    <div className="spinner-small" />
                                    <span>Background Simulations Running... {simProgress}%</span>
                                </>
                            ) : (
                                <div className="action-details">
                                    <h4>Actionable Step (Post-Simulation)</h4>
                                    <p>Simulations complete. Optimal action: <strong>Halt inflows to Sector B</strong>.</p>
                                </div>
                            )}
                        </div>
                        {simProgress >= 100 && (
                            <div className="btn-group">
                                <div className="command-directive glass small">
                                    <code className="green-text">DIRECT_GROUND: "Lockdown Level 2."</code>
                                </div>
                                <button className="pro-btn success" onClick={() => setPredPhase('resolved')}>Mark as Handled</button>
                            </div>
                        )}
                    </div>
                )
            case 'resolved':
                return (
                    <div className="action-row fade-in">
                        <div className="action-details">
                            <h4 className="green-text">System Stabilized</h4>
                            <p>Intervention was successful. The post-intervention heatmap reflects current flow.</p>
                        </div>
                        <button className="pro-btn secondary" onClick={() => setPredPhase('live')}>Return to Monitoring</button>
                    </div>
                )
        }
    }

    // --- Main Render ---

    const nodesToShow = activeTab === 'twin' ? currentNodes : predictedNodes

    return (
        <div className={`app-container ${theme} redesign-layout`}>
            {/* Top Pane: Tabs & Header */}
            <header className="top-pane">
                <div className="logo-area">
                    <span className="logo-text">CrowdTwin</span>
                    <span className="version-tag">v2.0</span>
                </div>
                <div className="tab-container">
                    <button
                        className={`tab-btn ${activeTab === 'twin' ? 'active' : ''}`}
                        onClick={() => setActiveTab('twin')}
                    >
                        Crowd Twin (Current)
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'predictions' ? 'active' : ''}`}
                        onClick={() => setActiveTab('predictions')}
                    >
                        Predictions (Forecast)
                    </button>
                </div>
                <div className="theme-toggle" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
                    {theme === 'dark' ? '☀' : '☾'}
                </div>
            </header>

            {/* Content Grid */}
            <div className="main-grid">

                {/* Center Main Page: Visual Feed */}
                <div className="center-main pane-box">
                    <div className="pane-header">
                        <h2>{activeTab === 'twin' ? 'Live System Twin' : 'Predictive Engine Outlook'}</h2>
                        <span className="status-dot pulse"></span>
                    </div>
                    <div className="visual-area">
                        {activeTab === 'twin' ? renderTwinMain() : renderPredMain()}
                    </div>
                </div>

                {/* Right Pane: Risk List */}
                <div className="right-pane pane-box">
                    <div className="pane-header">
                        <h2>{activeTab === 'twin' ? 'Current Risks' : 'Forecasted Risks'}</h2>
                    </div>
                    <div className="node-list">
                        {nodesToShow.map(node => (
                            <div key={node.id} className={`node-item border-${node.status.toLowerCase()}`}>
                                <div className="node-info">
                                    <span className="node-id">{node.id}</span>
                                    <span className="node-name">{node.name}</span>
                                </div>
                                <div className={`risk-badge bg-${node.status.toLowerCase()}`}>
                                    {node.riskScore}%
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Bottom Pane: Actions */}
                <div className="bottom-pane pane-box">
                    <div className="pane-header">
                        <h2>Actionable Steps</h2>
                    </div>
                    <div className="action-area">
                        {activeTab === 'twin' ? renderTwinBottom() : renderPredBottom()}
                    </div>
                </div>

            </div>

            {/* Embedded styles for the new layout */}
            <style>{`
                .redesign-layout { display: flex; flex-direction: column; height: 100vh; background: var(--bg-main); overflow: hidden; }
                
                /* Top Pane */
                .top-pane { height: 60px; display: flex; justify-content: space-between; align-items: center; padding: 0 2rem; background: var(--card-bg); border-bottom: 1px solid var(--border-color); }
                .logo-area { display: flex; align-items: baseline; gap: 0.5rem; }
                .logo-text { font-weight: 800; font-size: 1.2rem; color: var(--primary); }
                .version-tag { font-size: 0.7rem; color: var(--text-muted); background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; }
                
                .tab-container { display: flex; gap: 1rem; height: 100%; }
                .tab-btn { background: none; border: none; color: var(--text-muted); font-weight: 600; padding: 0 1.5rem; cursor: pointer; transition: 0.2s; border-bottom: 3px solid transparent; }
                .tab-btn:hover { color: var(--text-main); background: rgba(255,255,255,0.02); }
                .tab-btn.active { color: var(--primary); border-bottom-color: var(--primary); background: rgba(71, 117, 255, 0.05); }

                /* CSS Grid Layout */
                .main-grid { flex: 1; display: grid; grid-template-columns: 1fr 350px; grid-template-rows: 1fr 200px; gap: 1rem; padding: 1rem; height: calc(100vh - 60px); }
                .center-main { grid-column: 1; grid-row: 1; display: flex; flex-direction: column; }
                .right-pane { grid-column: 2; grid-row: 1 / span 2; display: flex; flex-direction: column; }
                .bottom-pane { grid-column: 1; grid-row: 2; display: flex; flex-direction: column; }

                /* Pane Styling */
                .pane-box { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden; }
                .pane-header { padding: 0.75rem 1rem; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.2); }
                .pane-header h2 { font-size: 0.9rem; margin: 0; color: var(--text-main); text-transform: uppercase; letter-spacing: 1px; }

                /* Visual Area */
                .visual-area { flex: 1; position: relative; background: #000; display: flex; align-items: center; justify-content: center; overflow: hidden; }
                .full-asset { width: 100%; height: 100%; object-fit: contain; }
                .opacity-50 { opacity: 0.5; }
                .relative-container { position: relative; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }
                .overlay-alert { position: absolute; max-width: 80%; max-height: 80%; border-radius: 16px; box-shadow: 0 0 50px rgba(239, 68, 68, 0.6); }

                /* Badges */
                .sim-overlay-badge { position: absolute; top: 1rem; left: 1rem; background: rgba(0,0,0,0.7); color: var(--primary); padding: 0.5rem 1rem; border-radius: 8px; font-family: monospace; border: 1px solid var(--primary); }
                .success-badge { position: absolute; bottom: 2rem; background: rgba(16, 185, 129, 0.9); color: white; padding: 1rem 2rem; border-radius: 8px; font-weight: bold; font-size: 1.2rem; }

                /* Right Pane Lists */
                .node-list { flex: 1; overflow-y: auto; padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem; }
                .node-item { display: flex; justify-content: space-between; align-items: center; padding: 1rem; background: var(--bg-surface); border-radius: 8px; border-left: 4px solid transparent; }
                .border-high { border-left-color: var(--red); }
                .border-medium { border-left-color: var(--amber); }
                .border-low { border-left-color: var(--green); }
                .node-info { display: flex; flex-direction: column; gap: 0.25rem; }
                .node-id { font-family: monospace; color: var(--text-muted); font-size: 0.8rem; }
                .node-name { font-weight: 600; font-size: 0.95rem; }
                .risk-badge { padding: 0.25rem 0.75rem; border-radius: 12px; font-weight: bold; font-size: 0.85rem; color: #fff; }
                .bg-high { background: var(--red); }
                .bg-medium { background: var(--amber); color: #000; }
                .bg-low { background: var(--green); }

                /* Bottom Pane Actions */
                .action-area { flex: 1; padding: 1rem; display: flex; align-items: center; }
                .action-row { width: 100%; display: flex; justify-content: space-between; align-items: center; }
                .action-details h4 { margin: 0 0 0.25rem 0; color: var(--primary); }
                .action-details p { margin: 0; color: var(--text-main); font-size: 0.9rem; }
                .btn-group { display: flex; gap: 1rem; align-items: center; }
                
                .pro-btn { padding: 0.5rem 1.25rem; border-radius: 8px; font-weight: 600; border: none; cursor: pointer; transition: 0.2s; white-space: nowrap; }
                .pro-btn.primary { background: var(--primary); color: #fff; }
                .pro-btn.secondary { background: var(--bg-surface); border: 1px solid var(--border-color); color: var(--text-main); }
                .pro-btn.warning { background: var(--amber); color: #000; }
                .pro-btn.danger { background: var(--red); color: #fff; }
                .pro-btn.success { background: var(--green); color: #fff; }

                /* Problem Finding Actions */
                .action-grid { width: 100%; display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; align-items: center; }
                .choice-list { display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.5rem; }
                .choice-btn { text-align: left; padding: 0.75rem; background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 8px; cursor: pointer; color: var(--text-main); transition: 0.2s; }
                .choice-btn:hover { border-color: var(--primary); background: rgba(71, 117, 255, 0.1); }
                
                /* Directives */
                .command-directive { padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color); }
                .command-directive h5 { margin: 0 0 0.5rem 0; color: var(--text-muted); text-transform: uppercase; font-size: 0.75rem; }
                .green-text { color: var(--green); font-family: monospace; font-size: 0.9rem; }
                
                /* Sim Loader */
                .sim-loader-area { display: flex; align-items: center; gap: 1rem; }
                .spinner-small { width: 24px; height: 24px; border: 2px solid var(--border-color); border-top-color: var(--primary); border-radius: 50%; animation: rot 1s infinite linear; }
                @keyframes rot { to { transform: rotate(360deg); } }

                .upload-zone { border: 2px dashed var(--border-color); border-radius: 12px; padding: 3rem; text-align: center; cursor: pointer; transition: 0.2s; }
                .upload-zone:hover { border-color: var(--primary); background: rgba(71, 117, 255, 0.05); }

                /* Utilities */
                .fade-in { animation: fadeIn 0.3s ease-out; }
                @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
                .pulse-fast { animation: pulseF 1s infinite; }
                @keyframes pulseF { 0% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.02); opacity: 0.8; } 100% { transform: scale(1); opacity: 1; } }
            `}</style>
        </div>
    )
}

export default DemoDashboard
