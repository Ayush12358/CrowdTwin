import { useNavigate } from 'react-router-dom'
import './styles/LandingPage.css'

const founders = [
    {
        name: 'Ayush Maurya',
        role: 'Systems & Intelligence Lead',
        avatar: '/ayush.png',
        website: 'https://ayushmaurya.dev',
        accent: 'blue',
    },
    {
        name: 'Jayanth Raju Saraswathi',
        role: 'Simulation & Modelling Lead',
        avatar: '/jayanth.png',
        website: 'https://jayanth.dev',
        accent: 'purple',
    },
    {
        name: 'Prabhav',
        role: 'Product & Research Lead',
        avatar: '/prabhav.png',
        website: 'https://prabhav.dev',
        accent: 'teal',
    },
]

function LandingPage() {
    const navigate = useNavigate()

    return (
        <div className="landing-container">
            <header className="landing-nav">
                <div className="landing-logo">CROWD-TWIN</div>
                <nav className="nav-links">
                    <a href="#solution">Solution</a>
                    <a href="#tech">Technology</a>
                    <a href="#team">Team</a>
                </nav>
                <button className="nav-cta" onClick={() => navigate('/demo')}>Live Demo</button>
            </header>

            <main>
                {/* ---- HERO ---- */}
                <section className="hero">
                    <div className="hero-content">
                        <div className="badge">For PSARA-Certified Security Firms</div>
                        <h1>Predictive Command Center for Venue Security</h1>
                        <p className="hero-subtext">
                            Move from reactive monitoring to proactive control.
                            We provide a <strong>15-minute lead time</strong> to redirect
                            crowd flow before critical surges occur — no new hardware required.
                        </p>
                        <div className="cta-group">
                            <button className="primary-cta" onClick={() => navigate('/demo')}>
                                Launch Live Demo <span className="arrow">&#8594;</span>
                            </button>
                            <button className="secondary-cta">Contact Us</button>
                        </div>
                    </div>

                    <div className="hero-visual">
                        <div className="mockup-window pro-saas">
                            <div className="header-strip">
                                <div className="dots"><span /><span /><span /></div>
                                <div className="address">app.crowdtwin.com/monitor</div>
                            </div>
                            <div className="mockup-body-saas">
                                <div className="saas-header-mock">
                                    <div className="m-bar" />
                                    <div className="m-search" />
                                </div>
                                <div className="saas-stats-mock">
                                    <div className="m-card" /><div className="m-card" /><div className="m-card" />
                                </div>
                                <div className="saas-chart-mock">
                                    <div className="m-line" />
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* ---- STATS ---- */}
                <section className="stats-strip">
                    <div className="stat-item">
                        <span className="stat-num">15<small>min</small></span>
                        <span className="stat-label">Predictive Lead Time</span>
                    </div>
                    <div className="stat-divider" />
                    <div className="stat-item">
                        <span className="stat-num">7<small>p/m²</small></span>
                        <span className="stat-label">Critical Density Threshold</span>
                    </div>
                    <div className="stat-divider" />
                    <div className="stat-item">
                        <span className="stat-num">0</span>
                        <span className="stat-label">Extra Hardware Needed</span>
                    </div>
                    <div className="stat-divider" />
                    <div className="stat-item">
                        <span className="stat-num">10</span>
                        <span className="stat-label">Command Screens</span>
                    </div>
                </section>

                {/* ---- VALUE PROPS ---- */}
                <section id="solution" className="features">
                    <div className="section-header">
                        <span className="section-tag">The Problem We Solve</span>
                        <h2>From Reactive CCTV to Predictive Control</h2>
                    </div>
                    <div className="feature-grid">
                        <div className="feature-card">
                            <div className="icon">&#128065;&#65039;</div>
                            <h3>The 7 p/m² Problem</h3>
                            <p>At 7 people per square meter, crowds behave like a fluid. Physical intervention becomes impossible, and conventional CCTV only alerts you after the threshold is already breached.</p>
                        </div>
                        <div className="feature-card highlighted">
                            <div className="icon">&#9201;&#65039;</div>
                            <h3>Our Solution: 15-Min Lead Time</h3>
                            <p>We analyze existing CCTV feeds to <strong>forecast critical density 15 minutes into the future</strong>, allowing security teams to close gates or redirect flow before surges form.</p>
                        </div>
                        <div className="feature-card">
                            <div className="icon">&#129504;</div>
                            <h3>Psychological ABM</h3>
                            <p>Unlike standard fluid dynamics models, our Agent-Based Model simulates individual "virtual brains" with psychological stress responses — modeling actual human behavior.</p>
                        </div>
                    </div>
                </section>

                {/* ---- HOW IT WORKS ---- */}
                <section id="tech" className="how-it-works">
                    <div className="section-header">
                        <span className="section-tag">Technology</span>
                        <h2>How CrowdTwin Works</h2>
                    </div>
                    <div className="steps-grid">
                        <div className="step-card">
                            <div className="step-num">01</div>
                            <h4>Ingest</h4>
                            <p>Reads existing CCTV sensor data — no new hardware installation required.</p>
                        </div>
                        <div className="step-connector" />
                        <div className="step-card">
                            <div className="step-num">02</div>
                            <h4>Simulate</h4>
                            <p>Runs a Digital Twin agent-based simulation with psychological crowd behavior models.</p>
                        </div>
                        <div className="step-connector" />
                        <div className="step-card">
                            <div className="step-num">03</div>
                            <h4>Forecast</h4>
                            <p>Generates a 15-minute density forecast with bottleneck and surge identification.</p>
                        </div>
                        <div className="step-connector" />
                        <div className="step-card">
                            <div className="step-num">04</div>
                            <h4>Command</h4>
                            <p>Pushes actionable directives to security staff terminals before the situation escalates.</p>
                        </div>
                    </div>
                </section>

                {/* ---- COGNITIVE ENGINE ---- */}
                <section id="tech-deep" className="tech-showcase">
                    <div className="showcase-content">
                        <div className="showcase-text">
                            <span className="section-tag">Inside the Engine</span>
                            <h2>The Cognitive ABM Framework</h2>
                            <p>
                                Unlike traditional architectural tracers, CrowdTwin models the <strong>individual psychological response</strong> of every person in the venue.
                            </p>
                            <ul className="engine-checklist">
                                <li><strong>Vision Sensors:</strong> Virtual agents "see" density shifts.</li>
                                <li><strong>Goal Hierarchy:</strong> Agents prioritize safety over path efficiency.</li>
                                <li><strong>Stress Vectors:</strong> Modeling velocity drop-off under social pressure.</li>
                            </ul>
                        </div>
                        <div className="showcase-visual">
                            <div className="engine-viz-box">
                                <div className="viz-layer l1"><span>Virtual Brain</span></div>
                                <div className="viz-layer l2"><span>Goal Hierarchy</span></div>
                                <div className="viz-layer l3"><span>Stress Response</span></div>
                                <div className="viz-particles">
                                    {[...Array(20)].map((_, i) => <div key={i} className="particle" />)}
                                </div>
                            </div>
                            <div className="diagram-glow" />
                        </div>
                    </div>
                </section>

                {/* ---- FOUNDERS ---- */}
                <section id="team" className="team">
                    <div className="section-header">
                        <span className="section-tag">The Team</span>
                        <h2>Built by AJP Innovators</h2>
                        <p className="section-sub">Three engineers obsessed with making large events safer.</p>
                    </div>
                    <div className="founders-grid">
                        {founders.map((f) => (
                            <div className={`founder-card founder-card--${f.accent}`} key={f.name}>
                                <div className="founder-avatar-wrap">
                                    <img src={f.avatar} alt={f.name} className="founder-avatar" />
                                </div>
                                <h3 className="founder-name">{f.name}</h3>
                                <p className="founder-role">{f.role}</p>
                                <a
                                    href={f.website}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="founder-link"
                                >
                                    Portfolio &#8594;
                                </a>
                            </div>
                        ))}
                    </div>
                </section>
            </main>

            <footer className="landing-footer">
                <p className="footer-logo">CROWD-TWIN</p>
                <p>&copy; 2026 AJP Innovators. All rights reserved.</p>
                <button className="footer-demo-btn" onClick={() => navigate('/demo')}>Open Demo &#8594;</button>
            </footer>
        </div>
    )
}

export default LandingPage
