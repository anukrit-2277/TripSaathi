import { useState, useRef, useEffect } from 'react';
import { DESTINATIONS } from '../data/destinations';
import {
  IconPin, IconCalendar, IconUsers, IconWallet, IconSearch, IconSparkle,
} from './icons';

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

const inr = (n) =>
  n.toLocaleString('en-IN', {
    style: 'currency', currency: 'INR', maximumFractionDigits: 0,
  });

/**
 * The floating planner bar.
 *
 * Rather than stacking every control in a tall form, the bar shows four
 * summary segments (Airbnb-style). Clicking one opens a single popover
 * beneath it with the real control. This keeps the resting state calm
 * and gives each control room to breathe when it is actually in use.
 */
export default function TripForm({ form, setForm, onSubmit, isLoading }) {
  const [openPanel, setOpenPanel] = useState(null);
  const wrapRef = useRef(null);

  // Close on outside click / Escape — expected of any popover.
  useEffect(() => {
    if (!openPanel) return;

    const onDown = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpenPanel(null);
    };
    const onKey = (e) => { if (e.key === 'Escape') setOpenPanel(null); };

    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [openPanel]);

  const toggle = (panel) => setOpenPanel((cur) => (cur === panel ? null : panel));

  const set = (patch) => setForm((prev) => ({ ...prev, ...patch }));

  const togglePreference = (pref) =>
    setForm((prev) => ({
      ...prev,
      preferences: prev.preferences.includes(pref)
        ? prev.preferences.filter((p) => p !== pref)
        : [...prev.preferences, pref],
    }));

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.destination || isLoading) return;
    setOpenPanel(null);
    onSubmit(form);
  };

  const prefLabel = () => {
    if (form.preferences.length === 0) return 'Anything goes';
    return PREFERENCE_OPTIONS
      .filter((p) => form.preferences.includes(p.value))
      .map((p) => p.label)
      .join(' · ');
  };

  return (
    <div className="planner-wrap" ref={wrapRef}>
      <form className="shell" onSubmit={handleSubmit} id="trip-form">
        <div className="planner">
          <div className="planner-bar">
            <button
              type="button"
              className={`seg ${openPanel === 'dest' ? 'is-open' : ''}`}
              onClick={() => toggle('dest')}
            >
              <span className="seg-label">Where</span>
              <span className={`seg-value ${form.destination ? '' : 'is-empty'}`}>
                {form.destination || 'Pick a destination'}
              </span>
            </button>

            <button
              type="button"
              className={`seg ${openPanel === 'days' ? 'is-open' : ''}`}
              onClick={() => toggle('days')}
            >
              <span className="seg-label">How long</span>
              <span className="seg-value">
                {form.days} {form.days === 1 ? 'day' : 'days'}
              </span>
            </button>

            <button
              type="button"
              className={`seg ${openPanel === 'people' ? 'is-open' : ''}`}
              onClick={() => toggle('people')}
            >
              <span className="seg-label">Who</span>
              <span className="seg-value">
                {form.travelers} {form.travelers === 1 ? 'traveller' : 'travellers'}
              </span>
            </button>

            <button
              type="button"
              className={`seg ${openPanel === 'budget' ? 'is-open' : ''}`}
              onClick={() => toggle('budget')}
            >
              <span className="seg-label">Budget</span>
              <span className="seg-value">{inr(form.budget)}</span>
            </button>

            <button
              type="submit"
              id="submit-trip"
              className="planner-submit"
              disabled={isLoading || !form.destination}
            >
              {isLoading ? (
                <>
                  <span className="spinner-ring" style={{ borderTopColor: '#fff', borderColor: 'rgba(255,255,255,.35)' }} />
                  Planning…
                </>
              ) : (
                <>
                  <IconSearch />
                  Plan my trip
                </>
              )}
            </button>
          </div>

          {/* --- Popovers --- */}
          {openPanel === 'dest' && (
            <div className="popover">
              <p className="popover-title"><IconPin style={{ display: 'inline', width: 12, height: 12, verticalAlign: '-1px' }} /> Where are you going?</p>
              <div className="dest-options">
                {DESTINATIONS.map((d) => (
                  <button
                    key={d.name}
                    type="button"
                    id={`opt-dest-${d.name.toLowerCase()}`}
                    className={`dest-option ${form.destination === d.name ? 'active' : ''}`}
                    onClick={() => { set({ destination: d.name }); setOpenPanel(null); }}
                  >
                    <img className="dest-option-img" src={d.image} alt="" loading="lazy" />
                    <span className="dest-option-text">
                      <strong>{d.name}</strong>
                      <span>{d.region}</span>
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {openPanel === 'days' && (
            <div className="popover">
              <p className="popover-title"><IconCalendar style={{ display: 'inline', width: 12, height: 12, verticalAlign: '-1px' }} /> How many days?</p>
              <div className="stepper">
                <button type="button" className="stepper-btn" aria-label="One day fewer"
                  disabled={form.days <= 1}
                  onClick={() => set({ days: Math.max(1, form.days - 1) })}>−</button>
                <span className="stepper-center">
                  <span className="stepper-value">{form.days}</span>
                  <span className="stepper-label">{form.days === 1 ? 'day' : 'days'}</span>
                </span>
                <button type="button" className="stepper-btn" aria-label="One day more"
                  disabled={form.days >= 14}
                  onClick={() => set({ days: Math.min(14, form.days + 1) })}>+</button>
              </div>
            </div>
          )}

          {openPanel === 'people' && (
            <div className="popover">
              <p className="popover-title"><IconUsers style={{ display: 'inline', width: 12, height: 12, verticalAlign: '-1px' }} /> Who's coming?</p>
              <div className="stepper">
                <button type="button" className="stepper-btn" aria-label="One traveller fewer"
                  disabled={form.travelers <= 1}
                  onClick={() => set({ travelers: Math.max(1, form.travelers - 1) })}>−</button>
                <span className="stepper-center">
                  <span className="stepper-value">{form.travelers}</span>
                  <span className="stepper-label">{form.travelers === 1 ? 'person' : 'people'}</span>
                </span>
                <button type="button" className="stepper-btn" aria-label="One traveller more"
                  disabled={form.travelers >= 20}
                  onClick={() => set({ travelers: Math.min(20, form.travelers + 1) })}>+</button>
              </div>
            </div>
          )}

          {openPanel === 'budget' && (
            <div className="popover">
              <p className="popover-title"><IconWallet style={{ display: 'inline', width: 12, height: 12, verticalAlign: '-1px' }} /> Total trip budget</p>
              <div className="budget-head">
                <span className="budget-amount">{inr(form.budget)}</span>
                <span className="budget-per">
                  ≈ {inr(Math.round(form.budget / Math.max(1, form.travelers)))} per person
                </span>
              </div>
              <input
                type="range" id="budget" className="slider"
                min="5000" max="100000" step="1000"
                value={form.budget}
                aria-label="Total trip budget in rupees"
                onChange={(e) => set({ budget: Number(e.target.value) })}
              />
              <div className="slider-scale">
                <span>₹5,000</span>
                <span>₹1,00,000</span>
              </div>
            </div>
          )}

          {openPanel === 'interests' && (
            <div className="popover">
              <p className="popover-title"><IconSparkle style={{ display: 'inline', width: 12, height: 12, verticalAlign: '-1px' }} /> What do you enjoy?</p>
              <div className="chips">
                {PREFERENCE_OPTIONS.map((pref) => (
                  <button
                    key={pref.value}
                    type="button"
                    id={`pref-${pref.value}`}
                    className={`chip ${form.preferences.includes(pref.value) ? 'active' : ''}`}
                    aria-pressed={form.preferences.includes(pref.value)}
                    onClick={() => togglePreference(pref.value)}
                  >
                    {pref.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="planner-foot">
            <span className="planner-foot-label">Interests</span>
            <button
              type="button"
              className={`chip ${openPanel === 'interests' ? 'active' : ''}`}
              onClick={() => toggle('interests')}
            >
              {prefLabel()}
              {form.preferences.length > 0 && ` (${form.preferences.length})`}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
