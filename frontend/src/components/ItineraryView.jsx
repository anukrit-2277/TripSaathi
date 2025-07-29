import { useState } from 'react';
import { IconChevron, IconClock, IconCar, IconFork, IconPin, IconWallet } from './icons';

const inr = (n) =>
  n.toLocaleString('en-IN', {
    style: 'currency', currency: 'INR', maximumFractionDigits: 0,
  });

/**
 * "09:00 AM" -> 540 (minutes past midnight), for sorting.
 *
 * The model is asked for 12-hour times but is not perfectly consistent,
 * so this tolerates 24-hour, missing meridiem, and dotted forms. Anything
 * unparseable sorts to the end rather than throwing the day away.
 */
function toMinutes(raw) {
  if (!raw) return Number.MAX_SAFE_INTEGER;
  const m = String(raw).trim().match(/^(\d{1,2})[:.]?(\d{2})?\s*([ap])?\.?m?\.?$/i);
  if (!m) return Number.MAX_SAFE_INTEGER;

  let hours = parseInt(m[1], 10);
  const mins = m[2] ? parseInt(m[2], 10) : 0;
  const meridiem = m[3]?.toLowerCase();

  if (meridiem === 'p' && hours !== 12) hours += 12;
  if (meridiem === 'a' && hours === 12) hours = 0;

  return hours * 60 + mins;
}

/**
 * Interleave activities and meals into one chronological rail.
 *
 * The API returns them as two separate arrays. Rendering them as two
 * separate lists (as the first version did) means a reader sees lunch
 * listed after dinner-time sightseeing — the single most confusing thing
 * about the old view. One sorted timeline reads like an actual day.
 */
function buildTimeline(day) {
  const activities = (day.activities || []).map((a) => ({
    kind: 'activity',
    time: a.time,
    at: toMinutes(a.time),
    name: a.activity,
    duration: a.duration,
    cost: a.cost_per_person,
    note: a.notes,
  }));

  const meals = (day.meals || []).map((m) => ({
    kind: 'meal',
    time: m.time,
    at: toMinutes(m.time),
    name: m.suggestion,
    mealType: m.type,
    cuisine: m.cuisine,
    cost: m.cost_per_person,
  }));

  return [...activities, ...meals].sort((a, b) => a.at - b.at);
}

function DayCard({ day, defaultOpen }) {
  const [open, setOpen] = useState(defaultOpen);
  const items = buildTimeline(day);
  const activityCount = (day.activities || []).length;
  const mealCount = (day.meals || []).length;

  const dayCost = items.reduce((sum, i) => sum + (Number(i.cost) || 0), 0);

  return (
    <article className={`day ${open ? 'is-open' : ''}`} id={`day-${day.day}`}>
      <button
        type="button"
        className="day-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-controls={`day-body-${day.day}`}
      >
        <span className="day-num">
          <small>Day</small>
          <strong>{day.day}</strong>
        </span>

        <span className="day-heading">
          <h4>{day.title}</h4>
          <span className="day-counts">
            <span><IconPin /> {activityCount} {activityCount === 1 ? 'stop' : 'stops'}</span>
            <span className="sep">·</span>
            <span><IconFork /> {mealCount} {mealCount === 1 ? 'meal' : 'meals'}</span>
            {dayCost > 0 && (
              <>
                <span className="sep">·</span>
                <span><IconWallet /> {inr(dayCost)}/person</span>
              </>
            )}
          </span>
        </span>

        <span className="day-caret"><IconChevron /></span>
      </button>

      <div className="day-body" id={`day-body-${day.day}`}>
        <div>
          <div className="day-inner">
            <ol className="timeline">
              {items.map((item, idx) => (
                <li className="tl-item" key={`${item.kind}-${idx}`}>
                  <span className="tl-time">{item.time}</span>
                  <span className="tl-mark">
                    <span className={`tl-dot ${item.kind === 'meal' ? 'meal' : ''}`} />
                  </span>
                  <span className="tl-body">
                    <span className="tl-name">{item.name}</span>
                    <span className="tags">
                      {item.duration && (
                        <span className="tag"><IconClock /> {item.duration}</span>
                      )}
                      {item.mealType && (
                        <span className="tag meal">{item.mealType}</span>
                      )}
                      {item.cuisine && (
                        <span className="tag cuisine">{item.cuisine}</span>
                      )}
                      {item.cost > 0 && (
                        <span className="tag cost">{inr(item.cost)}/person</span>
                      )}
                    </span>
                    {item.note && <span className="tl-note">{item.note}</span>}
                  </span>
                </li>
              ))}
            </ol>

            {day.transport_notes && (
              <div className="day-transport">
                <IconCar />
                <span>
                  <strong>Getting around</strong>
                  {day.transport_notes}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}

export default function ItineraryView({ itinerary }) {
  if (!itinerary?.days?.length) return null;

  const totalStops = itinerary.days.reduce(
    (n, d) => n + (d.activities?.length || 0), 0,
  );

  return (
    <div className="panel panel-pad" id="itinerary-view">
      <p className="eyebrow">Your itinerary</p>
      <h3 className="itin-title">{itinerary.title || 'Your Itinerary'}</h3>
      <p className="itin-meta">
        {itinerary.days.length} {itinerary.days.length === 1 ? 'day' : 'days'} ·{' '}
        {totalStops} stops · tap any day to expand
      </p>

      <div className="days">
        {itinerary.days.map((day, i) => (
          /* Day 1 opens by default: the reader gets substance immediately
             without facing a wall of expanded detail for a 14-day trip. */
          <DayCard key={day.day ?? i} day={day} defaultOpen={i === 0} />
        ))}
      </div>

      {(itinerary.recommendations?.length > 0 || itinerary.packing_tips?.length > 0) && (
        <div className="notes-grid">
          {itinerary.recommendations?.length > 0 && (
            <div className="note-card">
              <h4>Good to know</h4>
              <ul className="note-list">
                {itinerary.recommendations.map((rec, i) => <li key={i}>{rec}</li>)}
              </ul>
            </div>
          )}
          {itinerary.packing_tips?.length > 0 && (
            <div className="note-card is-tips">
              <h4>Worth packing</h4>
              <ul className="note-list">
                {itinerary.packing_tips.map((tip, i) => <li key={i}>{tip}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
