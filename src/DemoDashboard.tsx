import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTheme } from './ThemeContext'
import './styles/index.css'

type TabType = 'twin' | 'predictions'
type TwinPhase = 'upload' | 'init_nodes' | 'verifying_nodes' | 'final_nodes' | 'live'
type PredPhase = 'live' | 'problem_finding' | 'solution_finding' | 'resolved'

interface RiskNode {
    id: string
    name: string
    riskScore: number
    status: 'High' | 'Medium' | 'Low'
}

const DemoDashboard: React.FC = () => {
    const { theme, setTheme, setAccent } = useTheme()
    const navigate = useNavigate()

    // Core Layout State
    const [activeTab, setActiveTab] = useState<TabType>('twin')

    // Narrator drag state
    const [dragPos, setDragPos] = useState({ x: 24, y: 24 })
    const [dragging, setDragging] = useState(false)
    const dragOffset = React.useRef({ x: 0, y: 0 })

    useEffect(() => {
        if (!dragging) return
        const onMove = (e: MouseEvent) => {
            setDragPos({
                x: window.innerWidth - e.clientX - dragOffset.current.x,
                y: window.innerHeight - e.clientY - dragOffset.current.y
            })
        }
        const onUp = () => setDragging(false)
        window.addEventListener('mousemove', onMove)
        window.addEventListener('mouseup', onUp)
        return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp) }
    }, [dragging])

    // Tab 1: Crowd Twin State (Pre-Event -> Live)
    const [twinPhase, setTwinPhase] = useState<TwinPhase>('upload')
    const [twinProgress, setTwinProgress] = useState(0)

    // TTS state (declared early because progress bar effects depend on it)
    const [ttsEnabled, setTtsEnabled] = useState(true)
    const [ttsLoading, setTtsLoading] = useState(false)
    const audioRef = React.useRef<HTMLAudioElement | null>(null)
    const abortRef = React.useRef<AbortController | null>(null)

    useEffect(() => {
        if (activeTab === 'twin' && twinPhase === 'verifying_nodes') {
            // If TTS is disabled or audio not available, use a fallback timer
            if (!ttsEnabled || !audioRef.current) {
                if (twinProgress < 100) {
                    const timer = setTimeout(() => setTwinProgress(p => p + 2), 200)
                    return () => clearTimeout(timer)
                } else {
                    setTwinPhase('final_nodes')
                }
            }
        }
    }, [activeTab, twinPhase, twinProgress, ttsEnabled])

    // Tab 2: Predictions State (Problem/Solution Finding)
    const [predPhase, setPredPhase] = useState<PredPhase>('live')
    const [simProgress, setSimProgress] = useState(0)
    const [didAvertOnce, setDidAvertOnce] = useState(false)
    const [didHandleOnce, setDidHandleOnce] = useState(false)

    // Mock Data for Right Pane
    const currentNodes = ([
        { id: 'N1', name: 'South Gate Choke', riskScore: 68, status: 'Medium' },
        { id: 'E4', name: 'East Corridor', riskScore: 45, status: 'Low' },
        { id: 'N7', name: 'Main Concourse', riskScore: 82, status: 'High' },
    ] as RiskNode[]).sort((a, b) => b.riskScore - a.riskScore)

    const predictedNodes = ([
        { id: 'N2', name: 'North Gate Tunnel', riskScore: 92, status: 'High' },
        { id: 'E9', name: 'Stairwell B', riskScore: 88, status: 'High' },
        { id: 'N11', name: 'West Plaza Exit', riskScore: 75, status: 'Medium' },
    ] as RiskNode[]).sort((a, b) => b.riskScore - a.riskScore)

    // --- Tab 1: Crowd Twin Renderers ---

    const renderTwinMain = () => {
        switch (twinPhase) {
            case 'upload':
                return (
                    <div id="ct-upload" className="upload-zone" onClick={() => setTwinPhase('init_nodes')}>
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" /></svg>
                        <h3>Upload Venue Map</h3>
                        <p>Click to process Base.jpeg</p>
                    </div>
                )
            case 'init_nodes':
                return <img src="/assets/Init Nodes and Edges.png" alt="Init Nodes" className="full-asset fade-in" onClick={() => { setTwinPhase('verifying_nodes'); setTwinProgress(0); }} style={{ cursor: 'pointer' }} />
            case 'verifying_nodes':
                return (
                    <div className="relative-container fade-in">
                        <img src="/assets/Init Nodes and Edges.png" alt="Init Nodes" className="full-asset opacity-50" />
                        <div className="sim-loader-area glass" style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', flexDirection: 'column', padding: '2rem 3rem', borderRadius: '16px', border: '1px solid var(--primary)', zIndex: 5, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center' }}>
                            <div className="spinner-small" style={{ width: '40px', height: '40px', marginBottom: '1rem' }} />
                            <h3 style={{ margin: '0 0 1rem 0', color: 'var(--primary)', whiteSpace: 'nowrap' }}>Verifying Flow Topology...</h3>
                            <div className="progress-bar" style={{ width: '100%', minWidth: '250px', background: 'var(--border-color)', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                                <div className="fill" style={{ width: `${twinProgress}%`, background: 'var(--primary)', height: '100%', transition: 'width 0.1s' }}></div>
                            </div>
                        </div>
                    </div>
                )
            case 'final_nodes':
                return <img src="/assets/Final Nodes and Edges.png" alt="Final Nodes" className="full-asset fade-in" onClick={() => setTwinPhase('live')} style={{ cursor: 'pointer' }} />
            case 'live':
                return <video src="/assets/Pre Heatmap.mp4" autoPlay loop muted className="full-asset fade-in" />
        }
    }

    const renderTwinBottom = () => {
        if (twinPhase === 'upload') return <p className="muted-text">Awaiting map upload...</p>
        if (twinPhase === 'init_nodes' || twinPhase === 'verifying_nodes' || twinPhase === 'final_nodes') return (
            <div className="action-row fade-in">
                <div className="action-details">
                    <h4>Pre-Event Distribution Strategy</h4>
                    <p>AI suggests allocating 40% of personnel to {currentNodes[0]?.name} based on node topology.</p>
                </div>
                <button id="ct-verify" className="pro-btn primary" onClick={() => {
                    if (twinPhase === 'init_nodes') {
                        setTwinPhase('verifying_nodes');
                        setTwinProgress(0);
                    } else if (twinPhase === 'final_nodes') {
                        setTwinPhase('live');
                    }
                }} disabled={twinPhase === 'verifying_nodes'}>
                    {twinPhase === 'init_nodes' ? 'Verify Nodes' : twinPhase === 'verifying_nodes' ? 'Verifying...' : 'Deploy & Go Live'}
                </button>
            </div>
        )
        return (
            <div className="action-row fade-in">
                <div className="action-details">
                    <h4>Live Monitoring Active</h4>
                    <p>Current high-risk sector: {currentNodes[0]?.name}. Personnel are on standby.</p>
                </div>
                <button id="ct-pred-tab" className="pro-btn secondary" onClick={() => setActiveTab('predictions')}>View Predictions</button>
            </div>
        )
    }

    // --- Tab 2: Predictions Renderers ---

    useEffect(() => {
        if (activeTab === 'predictions' && predPhase === 'solution_finding' && simProgress < 100) {
            // If TTS is disabled or audio not available, use a fallback timer
            if (!ttsEnabled || !audioRef.current) {
                const timer = setTimeout(() => setSimProgress(p => p + 2), 200)
                return () => clearTimeout(timer)
            }
        }
    }, [activeTab, predPhase, simProgress, ttsEnabled])

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
                            <button id="ct-trigger-problem" className="pro-btn warning" onClick={() => setPredPhase('problem_finding')}>Trigger Problem (Avert)</button>
                            <button id="ct-trigger-incident" className="pro-btn danger" onClick={() => { setPredPhase('solution_finding'); setSimProgress(0); }}>Trigger Incident (Handle)</button>
                        </div>
                    </div>
                )
            case 'problem_finding':
                return (
                    <div className="action-grid fade-in">
                        <div className="action-choices">
                            <h4>Problem Detected: Avert using Suggestions</h4>
                            <div className="choice-list">
                                <button id="ct-rec1" className="choice-btn" onClick={() => { setDidAvertOnce(true); setPredPhase('resolved') }}>
                                    <strong>Recommendation 1</strong>: Open Emergency Gate 4
                                </button>
                                <button className="choice-btn" onClick={() => { setDidAvertOnce(true); setPredPhase('resolved') }}>
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
                                <div className="action-details" style={{ width: '100%' }}>
                                    <h4>Actionable Resolution Plan (Post-Simulation)</h4>
                                    <ul className="action-list" style={{ listStyleType: 'none', padding: 0, margin: '0.5rem 0', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                        <li style={{ background: 'rgba(255,255,255,0.05)', padding: '0.5rem 1rem', borderRadius: '4px', borderLeft: '3px solid var(--amber)' }}>
                                            <strong>1. Primary Halt:</strong> Halt inflows to Sector B via Central Hub.
                                        </li>
                                        <li style={{ background: 'rgba(255,255,255,0.05)', padding: '0.5rem 1rem', borderRadius: '4px', borderLeft: '3px solid var(--primary)' }}>
                                            <strong>2. Redeployment:</strong> Dispatch Alpha to clear Stairwell B.
                                        </li>
                                        <li style={{ background: 'rgba(255,255,255,0.05)', padding: '0.5rem 1rem', borderRadius: '4px', borderLeft: '3px solid var(--green)' }}>
                                            <strong>3. Evacuation Bypass:</strong> Open East Ramps for controlled egress.
                                        </li>
                                    </ul>
                                </div>
                            )}
                        </div>
                        {simProgress >= 100 && (
                            <div className="btn-group" style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                                <div className="command-directive glass small" style={{ marginBottom: '0.5rem' }}>
                                    <code className="green-text">DIRECT_GROUND: "Execute Protocol Omega."</code>
                                </div>
                                <button id="ct-return" className="pro-btn success" onClick={() => { setDidHandleOnce(true); setPredPhase('resolved') }}>Return to Monitoring</button>
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
                        <button id="ct-return-reset" className="pro-btn secondary" onClick={() => setPredPhase('live')}>Return to Monitoring</button>
                    </div>
                )
        }
    }

    // --- Narrator System ---
    const getNarratorDialogue = (): { label: string; message: string; avatar: string; name: string } => {
        if (activeTab === 'twin') {
            // Ayush narrates the pre-event setup story
            switch (twinPhase) {
                case 'upload':
                    return { label: 'Before the Event', avatar: '/ayush.png', name: 'Ayush', message: 'Welcome to the CrowdTwin Command Center. You are looking at three panes: the Main View (center) shows the simulation, the Risk List (right) ranks dangerous zones, and the Action Panel (bottom) provides next steps. To begin, click "Upload Venue Map" in the center to load the venue blueprint.' }
                case 'init_nodes':
                    return { label: 'Before the Event', avatar: '/ayush.png', name: 'Ayush', message: 'The AI has detected initial crowd-flow nodes and corridors from the map. The Risk List on the right already shows hotspots ranked by density risk. Now click "Verify Nodes" in the Action Panel at the bottom to let the AI optimize the network.' }
                case 'verifying_nodes':
                    return { label: 'Before the Event', avatar: '/ayush.png', name: 'Ayush', message: 'The system is verifying every junction and corridor. Watch the progress bar in the center -- once it reaches 100%, the optimized network will appear automatically. No action needed, just wait.' }
                case 'final_nodes':
                    return { label: 'Before the Event', avatar: '/ayush.png', name: 'Ayush', message: 'The verified network is ready -- these are the final nodes and paths our AI will monitor in real-time. The Risk List on the right shows current density levels. Click "Deploy & Go Live" in the Action Panel below to start live monitoring.' }
                case 'live':
                    return { label: 'Before the Event', avatar: '/ayush.png', name: 'Ayush', message: 'The venue is now live. The center shows the real-time heatmap feed, and the Risk List on the right updates with current crowd densities. To see what happens when our AI predicts an incident, click the "Predictions (Forecast)" tab at the top of the screen.' }
            }
        } else {
            switch (predPhase) {
                case 'live':
                    // Jayanth narrates the prediction story
                    return { label: 'During the Event', avatar: '/jayanth.png', name: 'Jayanth', message: 'You are now on the Predictions tab. The center shows the same live feed, but our engine is looking 15 minutes into the future. The Risk List on the right shows forecasted hotspots. In the Action Panel below, click "Trigger Problem (Avert)" to see how we prevent a predicted crush, or "Trigger Incident (Handle)" to simulate a real disaster.' }
                case 'problem_finding':
                    return { label: 'A Predicted Incident', avatar: '/jayanth.png', name: 'Jayanth', message: 'A potential crowd crush has been predicted at North Gate Tunnel (92% risk). The center now overlays the alert on the live feed. In the Action Panel below, you can see two AI-generated recommendations on the left and the exact radio directive for ground forces on the right. Click either "Recommendation 1" or "Recommendation 2" to avert the crisis.' }
                case 'solution_finding':
                    // Prabhav narrates the disaster response story
                    return simProgress < 100
                        ? { label: 'A Disaster Happened', avatar: '/prabhav.png', name: 'Prabhav', message: 'A critical incident has been triggered. The center shows the alert overlay, and the Action Panel below is running parallel rescue simulations. Watch the progress indicator -- once complete, the AI will present a step-by-step resolution plan. No action needed yet.' }
                        : { label: 'A Disaster Happened', avatar: '/prabhav.png', name: 'Prabhav', message: 'Simulations complete. The Action Panel below now shows three actionable steps: (1) Primary Halt, (2) Redeployment, and (3) Evacuation Bypass, along with the ground force directive. Review the steps, then click "Return to Monitoring" to see the post-intervention heatmap.' }
                case 'resolved':
                    return { label: 'Crisis Resolved', avatar: '/prabhav.png', name: 'Prabhav', message: 'The center now shows the post-intervention heatmap -- notice how crowd density has stabilized. The Action Panel confirms the system is back to normal. Click "Return to Monitoring" below to reset and try the other scenario, or switch back to the "Crowd Twin" tab at the top.' }
            }
        }
    }

    const narrator = getNarratorDialogue()

    // --- TTS (Edge TTS via /api/edge-tts proxy) ---

    const speakMessage = React.useCallback(async (text: string, voice: string) => {
        // Stop any currently playing audio
        if (audioRef.current) { audioRef.current.pause(); audioRef.current = null }
        if (abortRef.current) { abortRef.current.abort(); abortRef.current = null }

        try {
            setTtsLoading(true)
            const controller = new AbortController()
            abortRef.current = controller

            const res = await fetch(`/api/edge-tts?text=${encodeURIComponent(text)}&voice=${encodeURIComponent(voice)}`, {
                signal: controller.signal
            })

            if (!res.ok) throw new Error('TTS failed')

            const blob = await res.blob()
            const url = URL.createObjectURL(blob)
            const audio = new Audio(url)
            audioRef.current = audio

            // Drive progress bars from audio playback
            audio.ontimeupdate = () => {
                if (audio.duration > 0) {
                    const pct = Math.min(Math.floor((audio.currentTime / audio.duration) * 100), 99)
                    setTwinProgress(prev => twinPhase === 'verifying_nodes' ? pct : prev)
                    setSimProgress(prev => predPhase === 'solution_finding' ? pct : prev)
                }
            }

            audio.onended = () => {
                URL.revokeObjectURL(url)
                audioRef.current = null
                // Complete progress bars when audio finishes
                if (twinPhase === 'verifying_nodes') {
                    setTwinProgress(100)
                    setTimeout(() => setTwinPhase('final_nodes'), 300)
                }
                if (predPhase === 'solution_finding') {
                    setSimProgress(100)
                }
            }

            audio.play()
        } catch (err: any) {
            if (err.name !== 'AbortError') console.error('[TTS]', err)
        } finally {
            setTtsLoading(false)
        }
    }, [twinPhase, predPhase])

    // Speak when narrator message changes
    useEffect(() => {
        if (!ttsEnabled || !narrator?.message) return
        speakMessage(narrator.message, narrator.name.toLowerCase())
    }, [narrator?.message, narrator?.name, ttsEnabled, speakMessage])

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (audioRef.current) audioRef.current.pause()
            if (abortRef.current) abortRef.current.abort()
        }
    }, [])

    // --- Click Guide ---
    const getClickTargetId = (): string | null => {
        if (activeTab === 'twin') {
            switch (twinPhase) {
                case 'upload': return 'ct-upload'
                case 'init_nodes': return 'ct-verify'
                case 'verifying_nodes': return null // waiting
                case 'final_nodes': return 'ct-verify'
                case 'live': return 'ct-pred-tab'
            }
        } else {
            switch (predPhase) {
                case 'live': return didAvertOnce ? 'ct-trigger-incident' : 'ct-trigger-problem'
                case 'problem_finding': return 'ct-rec1'
                case 'solution_finding': return simProgress >= 100 ? 'ct-return' : null
                case 'resolved': return 'ct-return-reset'
            }
        }
    }

    const [guidePos, setGuidePos] = useState<{ x: number; y: number; w: number; h: number } | null>(null)
    const targetId = getClickTargetId()

    useEffect(() => {
        if (!targetId) { setGuidePos(null); return }
        let raf: number
        const track = () => {
            const el = document.getElementById(targetId)
            if (el) {
                const r = el.getBoundingClientRect()
                setGuidePos({ x: r.left + r.width / 2, y: r.top + r.height / 2, w: r.width, h: r.height })
            } else {
                setGuidePos(null)
            }
            raf = requestAnimationFrame(track)
        }
        // Small delay to let DOM update after phase change
        const timer = setTimeout(() => { raf = requestAnimationFrame(track) }, 200)
        return () => { clearTimeout(timer); cancelAnimationFrame(raf) }
    }, [targetId])

    // --- Story Progress ---
    const stories = [
        { label: 'Before the Event', done: twinPhase === 'live' || activeTab === 'predictions', active: activeTab === 'twin' },
        { label: 'A Predicted Incident', done: didAvertOnce, active: activeTab === 'predictions' && !didAvertOnce },
        { label: 'A Disaster Happened', done: didHandleOnce, active: activeTab === 'predictions' && didAvertOnce && !didHandleOnce },
    ]
    const allDone = stories.every(s => s.done)

    // --- Main Render ---

    const nodesToShow = activeTab === 'twin' ? currentNodes : predictedNodes

    if (allDone) {
        return (
            <div className={`app-container ${theme}`} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg-main)' }}>
                <div className="fade-in" style={{ textAlign: 'center', padding: '3rem 4rem', borderRadius: '16px', border: '1px solid var(--border-color)', background: 'var(--card-bg)', maxWidth: '560px', width: '100%' }}>
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="2" style={{ marginBottom: '1rem' }}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
                    <h2 style={{ color: 'var(--primary)', marginBottom: '0.5rem', fontSize: '1.5rem' }}>Demo Complete</h2>
                    <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '0.9rem' }}>All three scenarios have been demonstrated successfully.</p>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', marginBottom: '2rem' }}>
                        {stories.map((s, i) => (
                            <React.Fragment key={i}>
                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                                    <div style={{ width: '32px', height: '32px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.9rem', fontWeight: 700, background: 'var(--green)', color: '#fff' }}>&#10003;</div>
                                    <span style={{ fontSize: '0.75rem', color: 'var(--green)', whiteSpace: 'nowrap' }}>{s.label}</span>
                                </div>
                                {i < stories.length - 1 && <div style={{ width: '40px', height: '2px', background: 'var(--green)', marginBottom: '1.5rem' }} />}
                            </React.Fragment>
                        ))}
                    </div>
                    <button style={{ background: 'var(--primary)', color: '#fff', border: 'none', padding: '0.75rem 2rem', borderRadius: '8px', fontWeight: 600, fontSize: '0.9rem', cursor: 'pointer', marginTop: '0.5rem' }} onClick={() => {
                        setActiveTab('twin'); setTwinPhase('upload'); setTwinProgress(0);
                        setPredPhase('live'); setSimProgress(0);
                        setDidAvertOnce(false); setDidHandleOnce(false);
                        prevMessageRef.current = '';
                    }}>Restart Demo</button>
                </div>
            </div>
        )
    }

    return (
        <div className={`app-container ${theme} redesign-layout`}>
            {/* Story Progress Stepper */}
            <div className="story-progress-bar">
                {stories.map((s, i) => (
                    <div key={i} className={`sp-step ${s.done ? 'done' : s.active ? 'active' : ''}`}>
                        <div className="sp-dot">{s.done ? '\u2713' : i + 1}</div>
                        <span className="sp-label">{s.label}</span>
                        {i < stories.length - 1 && <div className={`sp-line ${s.done ? 'done' : ''}`} />}
                    </div>
                ))}
            </div>
            {/* Top Pane: Tabs & Header */}
            <header className="top-pane">
                <div className="logo-area" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
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

            {/* Narrator Character (Draggable) */}
            <div
                className="narrator-bubble fade-in"
                key={narrator.avatar + narrator.label}
                style={{ right: dragPos.x, bottom: dragPos.y, cursor: dragging ? 'grabbing' : 'grab' }}
                onMouseDown={(e) => {
                    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
                    dragOffset.current = { x: rect.right - e.clientX, y: rect.bottom - e.clientY }
                    setDragging(true)
                    e.preventDefault()
                }}
            >
                <img src={narrator.avatar} alt={narrator.name} className="narrator-avatar-img" />
                <div className="narrator-content">
                    <div className="narrator-meta">
                        <span className="narrator-name">{narrator.name}</span>
                        <span className="narrator-label">{narrator.label}</span>
                    </div>
                    <p className="narrator-text">{narrator.message}</p>
                </div>
                <button
                    className="tts-toggle"
                    onClick={(e) => {
                        e.stopPropagation()
                        if (ttsEnabled && audioRef.current) { audioRef.current.pause(); audioRef.current = null }
                        if (abortRef.current) { abortRef.current.abort(); abortRef.current = null }
                        setTtsEnabled(!ttsEnabled)
                    }}
                    title={ttsEnabled ? 'Mute narration' : 'Unmute narration'}
                >
                    {ttsLoading ? '\u{23F3}' : ttsEnabled ? '\u{1F50A}' : '\u{1F507}'}
                </button>
            </div>

            {/* Pulsating Click Guide */}
            {guidePos && (
                <div
                    className="click-guide"
                    style={{
                        left: guidePos.x,
                        top: guidePos.y,
                        width: Math.max(guidePos.w, guidePos.h) + 24,
                        height: Math.max(guidePos.w, guidePos.h) + 24,
                    }}
                />
            )}

            {/* Embedded styles for the new layout */}
            <style>{`
                .redesign-layout { display: flex; flex-direction: column; height: 100vh; background: var(--bg-main); overflow: hidden; position: relative; }
                
                /* Story Progress Stepper */
                .story-progress-bar { display: flex; align-items: center; justify-content: center; gap: 0; padding: 0.5rem 2rem; background: var(--card-bg); border-bottom: 1px solid var(--border-color); height: 40px; flex-shrink: 0; box-sizing: border-box; }
                .sp-step { display: flex; align-items: center; gap: 0.5rem; }
                .sp-dot { width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; background: var(--border-color); color: var(--text-muted); transition: 0.3s; flex-shrink: 0; }
                .sp-step.active .sp-dot { background: var(--primary); color: #fff; box-shadow: 0 0 8px rgba(71,117,255,0.4); }
                .sp-step.done .sp-dot { background: var(--green); color: #fff; }
                .sp-label { font-size: 0.75rem; color: var(--text-muted); white-space: nowrap; }
                .sp-step.active .sp-label { color: var(--primary); font-weight: 600; }
                .sp-step.done .sp-label { color: var(--green); }
                .sp-line { width: 40px; height: 2px; background: var(--border-color); margin: 0 0.75rem; flex-shrink: 0; transition: 0.3s; }
                .sp-line.done { background: var(--green); }

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
                .main-grid { flex: 1; display: grid; grid-template-columns: 1fr 350px; grid-template-rows: 1fr 200px; gap: 1rem; padding: 1rem; height: calc(100vh - 60px - 40px); min-height: 0; }
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

                /* Click Guide */
                .click-guide { position: fixed; transform: translate(-50%, -50%); border-radius: 50%; pointer-events: none; z-index: 90; border: 2px solid var(--primary); background: rgba(71, 117, 255, 0.12); animation: clickPulse 1.8s ease-in-out infinite; box-shadow: 0 0 20px rgba(71, 117, 255, 0.3), inset 0 0 20px rgba(71, 117, 255, 0.1); }
                @keyframes clickPulse { 0% { transform: translate(-50%, -50%) scale(1); opacity: 0.8; } 50% { transform: translate(-50%, -50%) scale(1.2); opacity: 0.4; } 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.8; } }

                /* Narrator */
                .narrator-bubble { position: fixed; display: flex; gap: 0.75rem; align-items: flex-start; background: var(--card-bg); border: 1px solid var(--primary); border-radius: 12px; padding: 1rem 1.25rem; max-width: 420px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); z-index: 100; backdrop-filter: blur(12px); user-select: none; }
                .narrator-avatar-img { width: 44px; height: 44px; border-radius: 50%; object-fit: cover; border: 2px solid var(--primary); flex-shrink: 0; }
                .narrator-content { display: flex; flex-direction: column; gap: 0.25rem; }
                .narrator-meta { display: flex; align-items: center; gap: 0.5rem; }
                .narrator-name { font-size: 0.85rem; font-weight: 700; color: var(--text-main); }
                .narrator-label { font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--primary); background: rgba(71, 117, 255, 0.1); padding: 2px 8px; border-radius: 4px; }
                .narrator-text { margin: 0; font-size: 0.85rem; line-height: 1.5; color: var(--text-main); }
                .tts-toggle { position: absolute; top: 0.5rem; right: 0.5rem; background: none; border: none; font-size: 1.1rem; cursor: pointer; opacity: 0.6; transition: 0.2s; padding: 2px; }
                .tts-toggle:hover { opacity: 1; }

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
