import { useState } from 'react';

const PREFERENCE_OPTIONS = [
  { value: 'history', label: '🏛️ History', color: '#f59e0b' },
  { value: 'food', label: '🍽️ Food', color: '#ef4444' },
  { value: 'photography', label: '📸 Photography', color: '#8b5cf6' },
  { value: 'adventure', label: '🏔️ Adventure', color: '#10b981' },
  { value: 'culture', label: '🎭 Culture', color: '#ec4899' },
  { value: 'nature', label: '🌿 Nature', color: '#22c55e' },
  { value: 'shopping', label: '🛍️ Shopping', color: '#f97316' },
  { value: 'nightlife', label: '🌙 Nightlife', color: '#6366f1' },
  { value: 'relaxation', label: '🧘 Relaxation', color: '#14b8a6' },
  { value: 'spiritual', label: '🕉️ Spiritual', color: '#a855f7' },
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
    <form className="trip-form" onSubmit={handleSubmit} id="trip-form">
      <div className="form-header">
        <h2>Plan Your Trip</h2>
        <p className="form-subtitle">Tell us about your dream journey</p>
      </div>

      <div className="form-grid">
        {/* Destination */}
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

        {/* Days */}
        <div className="form-group">
          <label htmlFor="days">Days</label>
          <div className="stepper">
            <button
              type="button"
              className="stepper-btn"
              onClick={() => setFormData((p) => ({ ...p, days: Math.max(1, p.days - 1) }))}
            >
              −
            </button>
            <span className="stepper-value">{formData.days}</span>
            <button
              type="button"
              className="stepper-btn"
              onClick={() => setFormData((p) => ({ ...p, days: Math.min(14, p.days + 1) }))}
            >
              +
            </button>
          </div>
        </div>

        {/* Travelers */}
        <div className="form-group">
          <label htmlFor="travelers">Travelers</label>
          <div className="stepper">
            <button
              type="button"
              className="stepper-btn"
              onClick={() => setFormData((p) => ({ ...p, travelers: Math.max(1, p.travelers - 1) }))}
            >
              −
            </button>
            <span className="stepper-value">{formData.travelers}</span>
            <button
              type="button"
              className="stepper-btn"
              onClick={() => setFormData((p) => ({ ...p, travelers: Math.min(20, p.travelers + 1) }))}
            >
              +
            </button>
          </div>
        </div>

        {/* Budget */}
        <div className="form-group full-width">
          <label htmlFor="budget">
            Budget <span className="budget-display">₹{formData.budget.toLocaleString('en-IN')}</span>
          </label>
          <input
            type="range"
            id="budget"
            min="5000"
            max="100000"
            step="1000"
            value={formData.budget}
            onChange={(e) => setFormData((p) => ({ ...p, budget: Number(e.target.value) }))}
            className="budget-slider"
          />
          <div className="budget-range">
            <span>₹5,000</span>
            <span>₹1,00,000</span>
          </div>
        </div>

        {/* Preferences */}
        <div className="form-group full-width">
          <label>Interests & Preferences</label>
          <div className="preferences-grid">
            {PREFERENCE_OPTIONS.map((pref) => (
              <button
                key={pref.value}
                type="button"
                id={`pref-${pref.value}`}
                className={`pref-chip ${formData.preferences.includes(pref.value) ? 'active' : ''}`}
                onClick={() => togglePreference(pref.value)}
                style={{
                  '--chip-color': pref.color,
                }}
              >
                {pref.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <button
        type="submit"
        id="submit-trip"
        className="submit-btn"
        disabled={isLoading || !formData.destination}
      >
        {isLoading ? (
          <span className="btn-loading">
            <span className="spinner"></span>
            Planning your trip...
          </span>
        ) : (
          '✨ Generate Itinerary'
        )}
      </button>
    </form>
  );
}
