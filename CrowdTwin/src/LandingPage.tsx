import { useState, useRef, useEffect } from 'react'
import './styles/LandingPage.css'

const founders = [
    {
        name: 'Ayush Maurya',
        role: 'Systems & Intelligence Lead',
        avatar: '/ayush.png',
        website: 'https://github.com/Ayush12358',
        accent: 'blue',
    },
    {
        name: 'Jayanth Raju Saraswathi',
        role: 'Simulation & Modelling Lead',
        avatar: '/jayanth.png',
        website: 'https://github.com/TOMATOsJr',
        accent: 'purple',
    },
    {
        name: 'Prabhav',
        role: 'Product & Research Lead',
        avatar: '/prabhav.png',
        website: 'https://github.com/Prabhav-sai',
        accent: 'teal',
    },
]

function LandingPage() {
    const heroVideos = [
        { src: '/assets/Pre Heatmap.mp4', label: 'Live Monitoring' },
        { src: '/assets/Post Heatmap.mp4', label: 'Post Intervention' },
    ]
    const [videoIdx, setVideoIdx] = useState(0)
    const videoRefs = useRef<HTMLVideoElement[]>([])
    useEffect(() => { videoRefs.current[0]?.play() }, [])

    return (
        <div className="landing-container dashboard-layout">
            <header className="landing-nav">
                <div className="nav-left">
                    <div className="landing-brand">
                        <img src="/assets/logo_no_bg.png" alt="CrowdTwin Logo Element" className="landing-logo-img" />
                        <div className="landing-logo-text">CROWD-TWIN</div>
                    </div>
                </div>

                <div className="nav-right">
                    <div className="header-team">
                        {founders.map((f) => (
                            <img key={f.name} src={f.avatar} alt={f.name} className="header-avatar" title={`${f.name} - ${f.role}`} />
                        ))}
                    </div>
                </div>
            </header>

            <main className="dashboard-grid">
                {/* ---- HERO (Top Left) ---- */}
                <section className="dashboard-hero illustrative-hero">
                    <div className="hero-label">MISSION-CRITICAL CROWD INTELLIGENCE</div>
                    <h1 className="hero-title">
                        Avert Disaster Before<br />
                        <span className="text-gradient">It Threatens Lives</span>
                    </h1>
                    <p className="hero-description">
                        Our company is CrowdTwin,
                        we are developing a Predictive Command Center
                        to help Certified Venue Security Firms
                        with managing ground force and mitigate crowd risks.
                        To do this we use a digital twin and simulations through Agent Based Modeling.
                    </p>

                    <div className="hero-features">
                        <div className="feature-pill blue-pill">
                            <span className="pill-dot"></span>
                            <span>Digital Twin Engine</span>
                        </div>
                        <div className="feature-pill purple-pill">
                            <span className="pill-dot"></span>
                            <span>Agent Based Modeling</span>
                        </div>
                        <div className="feature-pill green-pill">
                            <span className="pill-dot"></span>
                            <span>PSARA-Certified Ready</span>
                        </div>
                    </div>
                </section>

                {/* ---- COMMAND WIDGET (Top Right) ---- */}
                <section className="dashboard-hero-graphic">
                    <div className="hero-graphic-orb"></div>

                    <div className="hero-command-widget">
                        {/* Left Column: Directives + Image */}
                        <div className="directives-panel">
                            <div className="directive-header">
                                <h3>Actionable steps</h3>
                                <div className="pulsing-alert-indicator"></div>
                            </div>

                            <div className="directives-row">
                                <div className="directive-group">
                                    <h4>Ground Force Directive:</h4>
                                    <ul>
                                        <li>Evac from gate c</li>
                                        <li>Divert crowd from ground a west side</li>
                                    </ul>
                                </div>
                                <div className="directive-group rec-group">
                                    <h4>Recommendations:</h4>
                                    <ul>
                                        <li>Open Emergency gate 5</li>
                                        <li>Divert West plaza</li>
                                    </ul>
                                </div>
                            </div>

                            <div className="widget-topology-container">
                                <img src="/assets/sample.png" alt="Digital Twin Topology" className="widget-topology-img" />
                            </div>
                        </div>

                        {/* Right Column: Gates Panel */}
                        <div className="gates-panel">
                            <div className="panel-header">
                                <h3>Active Gates</h3>
                            </div>
                            <div className="gates-table-header">
                                <span>Name</span>
                                <span>Status</span>
                            </div>
                            <div className="gates-list">
                                <div className="gate-item">
                                    <div className="gate-info">
                                        <strong>Gate A</strong>
                                        <span>Main Entrance</span>
                                    </div>
                                    <div className="gate-status st-open">
                                        <div className="status-dot"></div> Open
                                    </div>
                                    <div className="gate-toggle active"></div>
                                </div>
                                <div className="gate-item">
                                    <div className="gate-info">
                                        <strong>Gate B</strong>
                                        <span>North Wing</span>
                                    </div>
                                    <div className="gate-status st-closed">
                                        <div className="status-dot"></div> Closed
                                    </div>
                                    <div className="gate-toggle"></div>
                                </div>
                                <div className="gate-item highlighted-gate">
                                    <div className="gate-info">
                                        <strong>Gate C</strong>
                                        <span>East Plaza</span>
                                    </div>
                                    <div className="gate-status st-warning">
                                        <div className="status-dot"></div> Overcrowded
                                    </div>
                                    <div className="gate-toggle active"></div>
                                </div>
                                <div className="gate-item">
                                    <div className="gate-info">
                                        <strong>Gate D</strong>
                                        <span>VIP Access</span>
                                    </div>
                                    <div className="gate-status st-open">
                                        <div className="status-dot"></div> Open
                                    </div>
                                    <div className="gate-toggle active"></div>
                                </div>
                            </div>
                            <button className="view-all-btn">View All Gates</button>
                        </div>
                    </div>
                </section>

                {/* ---- HOW IT WORKS (Bottom Left) ---- */}
                <section className="dashboard-tech">
                    <div className="tech-header">
                        {/* <span className="section-tag">Technology</span> */}
                        <h2>How CrowdTwin Works</h2>
                    </div>
                    <div className="compact-steps-grid">
                        <div className="compact-step-card">
                            <div className="step-num">01</div>
                            <h4>Ingest</h4>
                            <p>Reads existing CCTV sensor data — no new hardware installation required.</p>
                        </div>
                        <div className="step-arrow">&#10132;</div>
                        <div className="compact-step-card">
                            <div className="step-num">02</div>
                            <h4>Simulate</h4>
                            <p>Runs a Digital Twin agent-based simulation with psychological crowd behavior models.</p>
                        </div>
                        <div className="step-arrow">&#10132;</div>
                        <div className="compact-step-card">
                            <div className="step-num">03</div>
                            <h4>Forecast</h4>
                            <p>Generates a 15-minute density forecast with bottleneck and surge identification.</p>
                        </div>
                        <div className="step-arrow">&#10132;</div>
                        <div className="compact-step-card">
                            <div className="step-num">04</div>
                            <h4>Command</h4>
                            <p>Pushes actionable directives to security staff terminals before the situation escalates.</p>
                        </div>
                    </div>
                </section>

                {/* ---- SCOPE OF LIABILITY (Bottom Right) ---- */}
                <section className="dashboard-liability-mini">
                    <div className="liability-mini-title">Scale of Averted Liability</div>
                    <div className="liability-mini-list">
                        <div className="l-mini-item"><strong>Astroworld:</strong> 4,000+ consolidated civil cases; $2B damages sought; 10 wrongful deaths settled.</div>
                        <div className="l-mini-item"><strong>Maha Kumbh:</strong> 82+ deaths; High Court ordered ₹25L per-family relief due to payout delays.</div>
                        <div className="l-mini-item"><strong>Cuscatlán:</strong> 5 Stadium Execs arrested; Forced financial restitution to victims & survivors.</div>
                    </div>
                </section>
            </main>
        </div>
    )
}

export default LandingPage
