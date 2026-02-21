import { useNavigate } from 'react-router-dom'
import './styles/LandingPage.css'

function LandingPage() {
    const navigate = useNavigate()

    return (
        <div className="landing-container">
            <header className="landing-nav">
                <div className="landing-logo">CROWD-TWIN</div>
                <div className="nav-links">
                    <a href="#problem">The Problem</a>
                    <a href="#solution">How it Works</a>
                    <a href="#tech">Technology</a>
                </div>
                <button className="nav-cta" onClick={() => navigate('/demo')}>View Demo</button>
            </header>

            <main>
                <section className="hero">
                    <div className="hero-content">
                        <div className="badge">For PSARA-Certified Security Firms</div>
                        <h1>Predictive Command Center for Venue Security</h1>
                        <p className="hero-subtext">
                            Move from reactive monitoring to proactive control. We provide a <strong>15-minute lead time</strong> to redirect crowd flow before critical surges occur.
                        </p>
                        <div className="cta-group">
                            <button className="primary-cta" onClick={() => navigate('/demo')}>
                                Launch Live Demo <span className="arrow">→</span>
                            </button>
                            <button className="secondary-cta">Contact Sales</button>
                        </div>
                    </div>
                    <div className="hero-visual">
                        <div className="mockup-window">
                            <div className="mockup-header">
                                <span className="dot red"></span>
                                <span className="dot amber"></span>
                                <span className="dot green"></span>
                            </div>
                            <div className="mockup-body">
                                <div className="heat-map-sim">
                                    <div className="pulse-zone"></div>
                                    <div className="prediction-overlay">
                                        <span>15m Forecast: 7.4 p/m²</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <section id="problem" className="features">
                    <div className="feature-grid">
                        <div className="feature-card">
                            <div className="icon">👁️</div>
                            <h3>The 7 p/m² Problem</h3>
                            <p>At 7 people per square meter, crowds behave like a fluid. Physical intervention by guards becomes impossible. CCTV only alerts you after this threshold is hit.</p>
                        </div>
                        <div className="feature-card highlighted">
                            <div className="icon">⏱️</div>
                            <h3>Our Solution: 15-Min Lead Time</h3>
                            <p>We analyze existing CCTV feeds to forecast critical density 15 minutes into the future, allowing you to close gates or redirect flow before surges form.</p>
                        </div>
                        <div className="feature-card">
                            <div className="icon">🧠</div>
                            <h3>Psychological ABM</h3>
                            <p>Unlike standard fluid dynamics models, our Agent-Based Model simulates how individual "virtual brains" react to stress, modeling actual human behavior.</p>
                        </div>
                    </div>
                </section>
            </main>

            <footer className="landing-footer">
                <p>&copy; 2026 AJP Innovators. All rights reserved.</p>
            </footer>
        </div>
    )
}

export default LandingPage
