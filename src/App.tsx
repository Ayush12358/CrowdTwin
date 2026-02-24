import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import LandingPage from './LandingPage'
import DemoDashboard from './DemoDashboard'
import { ThemeProvider } from './ThemeContext'

function App() {
    return (
        <ThemeProvider>
            <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
                <Routes>
                    <Route path="/" element={<LandingPage />} />
                    <Route path="/demo" element={<DemoDashboard />} />
                </Routes>
            </Router>
        </ThemeProvider>
    )
}

export default App
