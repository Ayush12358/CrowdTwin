import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import LandingPage from './LandingPage'
import DemoDashboard from './DemoDashboard'

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/demo" element={<DemoDashboard />} />
            </Routes>
        </Router>
    )
}

export default App
