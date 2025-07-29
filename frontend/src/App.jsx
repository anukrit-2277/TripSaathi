import { useState, useEffect, useRef } from 'react';
import Hero from './components/Hero';
import TripForm from './components/TripForm';
import DestinationCard from './components/DestinationCard';
import AgentProgress from './components/AgentProgress';
import ItineraryView from './components/ItineraryView';
import BudgetBreakdown from './components/BudgetBreakdown';
import CriticStatus from './components/CriticStatus';
import { DESTINATIONS } from './data/destinations';
import { IconPin } from './components/icons';
import { planTrip } from './api/tripApi';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [tripResult, setTripResult] = useState(null);
  const [error, setError] = useState(null);
  const [stuck, setStuck] = useState(false);

  /* Form state lives here so the destination cards and the planner bar
     stay in sync — picking a card fills the bar and vice versa. */
  const [form, setForm] = useState({
    destination: '',
    days: 3,
    travelers: 2,
    budget: 15000,
    preferences: [],
  });

  const plannerRef = useRef(null);
  const resultsRef = useRef(null);

  // Frost the nav only after the page has scrolled past the hero top.
  useEffect(() => {
    const onScroll = () => setStuck(window.scrollY > 24);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const scrollToPlanner = () =>
    plannerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });

  /* Bring the progress panel into view the moment planning begins.
     This runs in an effect rather than inline in the submit handler
     because the panel does not exist in the DOM until the isLoading
     re-render has committed — scrolling before that is a no-op. */
  useEffect(() => {
    if (!isLoading) return;
    resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [isLoading]);

  const selectDestination = (name) => {
    setForm((prev) => ({ ...prev, destination: name }));
    scrollToPlanner();
  };

  const handleSubmit = async (formData) => {
    setIsLoading(true);
    setTripResult(null);
    setError(null);
    setCurrentStep(0);

    // Optimistic stepper: the backend does not stream progress, so we
    // advance on a timer that roughly matches observed agent timings.
    const progressInterval = setInterval(() => {
      setCurrentStep((prev) => (prev < 3 ? prev + 1 : prev));
    }, 8000);

    try {
      const result = await planTrip(formData);
      clearInterval(progressInterval);
      setCurrentStep(4);
      setTripResult(result);
      // Let the results paint before scrolling to them.
      requestAnimationFrame(() =>
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }),
      );
    } catch (err) {
      clearInterval(progressInterval);
      setError(err.message || 'Something went wrong. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <nav className={`nav ${stuck ? 'is-stuck' : ''}`}>
        <div className="nav-inner">
          <a className="brand" href="#top">
            <span className="brand-mark"><IconPin /></span>
            <span className="brand-name">Trip<em>Saathi</em></span>
          </a>
          <div className="nav-links">
            <a className="nav-link" href="#destinations">Destinations</a>
            <a className="nav-link" href="#how">How it works</a>
            <button type="button" className="btn-ghost" onClick={scrollToPlanner}>
              Plan a trip
            </button>
          </div>
        </div>
      </nav>

      <span id="top" />
      <Hero onStart={scrollToPlanner} />

      <div ref={plannerRef}>
        <TripForm
          form={form}
          setForm={setForm}
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </div>

      <main>
        {/* --- Live results ---
             Deliberately ABOVE the destination shelf. Progress has to
             appear directly under the planner bar the user just clicked;
             sitting below a full-height shelf of cards meant the button
             produced no visible feedback at all. */}
        <div ref={resultsRef}>
          {(isLoading || tripResult) && (
            <section className="section--tight" id="how">
              <div className="shell reveal">
                <AgentProgress
                  currentStep={isLoading ? currentStep : 4}
                  isComplete={!!tripResult}
                  revisionCount={
                    tripResult?.revision_count ? tripResult.revision_count - 1 : 0
                  }
                />
              </div>
            </section>
          )}

          {error && (
            <section className="section--tight">
              <div className="shell">
                <div className="error-card reveal" id="error-card">
                  <span className="error-icon">!</span>
                  <div className="error-body">
                    <h4>We couldn't build that plan</h4>
                    <p>{error}</p>
                  </div>
                  <button className="error-dismiss" onClick={() => setError(null)}>
                    Dismiss
                  </button>
                </div>
              </div>
            </section>
          )}

          {tripResult && (
            <>
              <section className="section--tight">
                <div className="shell reveal">
                  <BudgetBreakdown breakdown={tripResult.budget_breakdown} />
                </div>
              </section>

              <section className="section--tight">
                <div className="shell reveal">
                  <ItineraryView itinerary={tripResult.itinerary} />
                </div>
              </section>

              <section className="section--tight">
                <div className="shell reveal">
                  <CriticStatus critique={tripResult.critique} />
                </div>
              </section>
            </>
          )}
        </div>

        {/* --- Destination shelf --- */}
        <section className="section" id="destinations">
          <div className="shell">
            <div className="section-head">
              <p className="eyebrow">Where to</p>
              <h2>Five places we know deeply.</h2>
              <p className="lede">
                Each one is backed by a curated knowledge base — opening hours,
                real costs, and the walk between one place and the next.
              </p>
            </div>

            <div className="dest-grid">
              {DESTINATIONS.map((d) => (
                <DestinationCard
                  key={d.name}
                  destination={d}
                  isActive={form.destination === d.name}
                  onSelect={selectDestination}
                />
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="footer">
        <div className="shell footer-inner">
          <p>TripSaathi — multi-agent trip planning, grounded in real data.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
