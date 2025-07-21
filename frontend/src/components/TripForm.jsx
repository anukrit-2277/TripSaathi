import { useState } from 'react';

const PREFERENCE_OPTIONS = [
  { value: 'history', label: 'History' },
  { value: 'food', label: 'Food & Cuisine' },
  { value: 'photography', label: 'Photography' },
  { value: 'adventure', label: 'Adventure' },
  { value: 'culture', label: 'Culture' },
  { value: 'nature', label: 'Nature' },
  { value: 'shopping', label: 'Shopping' },
  { value: 'nightlife', label: 'Nightlife' },
  { value: 'relaxation', label: 'Relaxation' },
  { value: 'spiritual', label: 'Spiritual' },
];

const DESTINATIONS = ['Jaipur', 'Udaipur', 'Delhi', 'Goa', 'Manali'];

export default function TripForm({ onSubmit, isLoading }) {
  const [formData, setFormData] = useState({
    destination: '',
    days: 3,
    travelers: 2,
    budget: 15000,
    preferences: [],
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.destination) return;
    onSubmit(formData);
  };

  const togglePreference = (pref) => {
    setFormData((prev) => ({
      ...prev,
      preferences: prev.preferences.includes(pref)
        ? prev.preferences.filter((p) => p !== pref)
        : [...prev.preferences, pref],
    }));
  };

  return (
    <form className="trip-form glass-card" onSubmit={handleSubmit} id="trip-form">
      <div className="form-header">
        <h2>Plan Your Journey</h2>
        <p className="form-subtitle">Tell us where you want to go and we'll handle the rest</p>
      </div>

      <div className="form-grid">
        <div className="form-group full-width">
          <label htmlFor="destination">Destination</label>
          <div className="destination-pills">
            {DESTINATIONS.map((dest) => (
              <button
                key={dest}
                type="button"
                id={`dest-${dest.toLowerCase()}`}
                className={`dest-pill ${formData.destination === dest ? 'active' : ''}`}
                onClick={() => setFormData((prev) => ({ ...prev, destination: dest }))}
              >
                {dest}
              </button>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label>Duration</label>
          <div className="stepper">
            <button type="button" className="stepper-btn" onClick={() => setFormData((p) => ({ ...p, days: Math.max(1, p.days - 1) }))}>-</button>
            <div className="stepper-center">
              <span className="stepper-value">{formData.days}</span>
              <span className="stepper-label">days</span>
            </div>
            <button type="button" className="stepper-btn" onClick={() => setFormData((p) => ({ ...p, days: Math.min(14, p.days + 1) }))}>+</button>
          </div>
        </div>

        <div className="form-group">
          <label>Travelers</label>
          <div className="stepper">
            <button type="button" className="stepper-btn" onClick={() => setFormData((p) => ({ ...p, travelers: Math.max(1, p.travelers - 1) }))}>-</button>
            <div className="stepper-center">
              <span className="stepper-value">{formData.travelers}</span>
              <span className="stepper-label">people</span>
            </div>
            <button type="button" className="stepper-btn" onClick={() => setFormData((p) => ({ ...p, travelers: Math.min(20, p.travelers + 1) }))}>+</button>
          </div>
        </div>

        <div className="form-group full-width">
          <label htmlFor="budget">
            Budget
            <span className="budget-display">{formData.budget.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })}</span>
          </label>
          <input type="range" id="budget" min="5000" max="100000" step="1000" value={formData.budget} onChange={(e) => setFormData((p) => ({ ...p, budget: Number(e.target.value) }))} className="budget-slider" />
          <div className="budget-range">
            <span>5,000</span>
            <span>1,00,000</span>
          </div>
        </div>

        <div className="form-group full-width">
          <label>Interests</label>
          <div className="preferences-grid">
            {PREFERENCE_OPTIONS.map((pref) => (
              <button
                key={pref.value}
                type="button"
                id={`pref-${pref.value}`}
                className={`pref-chip ${formData.preferences.includes(pref.value) ? 'active' : ''}`}
                onClick={() => togglePreference(pref.value)}
              >
                {pref.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <button type="submit" id="submit-trip" className="submit-btn" disabled={isLoading || !formData.destination}>
        {isLoading ? (
          <span className="btn-loading">
            <span className="spinner"></span>
            Planning your trip...
          </span>
        ) : (
          'Generate Itinerary'
        )}
      </button>
    </form>
  );
}
