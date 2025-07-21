import { useState } from 'react';
import TripForm from './components/TripForm';
import AgentProgress from './components/AgentProgress';
import ItineraryView from './components/ItineraryView';
import BudgetBreakdown from './components/BudgetBreakdown';
import CriticStatus from './components/CriticStatus';
import SourcesList from './components/SourcesList';
import { planTrip } from './api/tripApi';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [tripResult, setTripResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (formData) => {
    setIsLoading(true);
    setTripResult(null);
    setError(null);
    setCurrentStep(0);

    const progressInterval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < 3) return prev + 1;
        return prev;
      });
    }, 8000);

    try {
      const result = await planTrip(formData);
      clearInterval(progressInterval);
      setCurrentStep(4);
      setTripResult(result);
    } catch (err) {
      clearInterval(progressInterval);
      setError(err.message || 'Something went wrong. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="hero">
        <div className="hero-orbs">
          <div className="orb orb-1"></div>
          <div className="orb orb-2"></div>
          <div className="orb orb-3"></div>
        </div>
        <div className="hero-content">
          <p className="hero-eyebrow">AI-Powered Travel Planning</p>
          <h1 className="hero-title">TripSaathi</h1>
          <p className="hero-subtitle">
            Intelligent multi-agent system that crafts personalized itineraries using RAG and LangGraph
          </p>
          <div className="hero-badges">
            <span className="hero-badge">LangChain</span>
            <span className="hero-badge">LangGraph</span>
            <span className="hero-badge">RAG</span>
            <span className="hero-badge">Multi-Agent</span>
          </div>
        </div>
      </header>

      <main className="main-content">
        <section className="section form-section">
          <TripForm onSubmit={handleSubmit} isLoading={isLoading} />
        </section>

        {(isLoading || tripResult) && (
          <section className="section">
            <AgentProgress
              currentStep={isLoading ? currentStep : 4}
              isComplete={!!tripResult}
              revisionCount={tripResult?.revision_count ? tripResult.revision_count - 1 : 0}
            />
          </section>
        )}

        {error && (
          <section className="section">
            <div className="error-card" id="error-card">
              <div className="error-icon">!</div>
              <div>
                <h3>Request Failed</h3>
                <p>{error}</p>
              </div>
              <button onClick={() => setError(null)} className="error-dismiss">
                Dismiss
              </button>
            </div>
          </section>
        )}

        {tripResult && (
          <>
            <section className="section">
              <BudgetBreakdown breakdown={tripResult.budget_breakdown} />
            </section>

            <section className="section">
              <ItineraryView itinerary={tripResult.itinerary} />
            </section>

            <div className="results-grid">
              <section className="section">
                <CriticStatus critique={tripResult.critique} />
              </section>

              <section className="section">
                <SourcesList sources={tripResult.sources} />
              </section>
            </div>
          </>
        )}
      </main>

      <footer className="footer">
        <p>Built with LangChain, LangGraph, RAG, FastAPI & React</p>
      </footer>
    </div>
  );
}

export default App;
