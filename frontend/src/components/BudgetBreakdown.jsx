import { IconWallet } from './icons';

const inr = (n) =>
  n.toLocaleString('en-IN', {
    style: 'currency', currency: 'INR', maximumFractionDigits: 0,
  });

/* Category colours are drawn from the palette, not picked at random —
   clay, ochre, forest and a muted plum that still sits in the warm family. */
const CATEGORIES = [
  { key: 'accommodation', label: 'Stay',       color: '#C1502E' },
  { key: 'food',          label: 'Food',       color: '#D99A2B' },
  { key: 'transport',     label: 'Transport',  color: '#3F7D6C' },
  { key: 'activities',    label: 'Activities', color: '#9A5B6E' },
];

export default function BudgetBreakdown({ breakdown }) {
  if (!breakdown?.total_estimated) return null;

  const total = breakdown.total_estimated;
  const limit = breakdown.budget_limit;
  const remaining = breakdown.remaining;
  const within = breakdown.within_budget;
  const pct = Math.min((total / limit) * 100, 100);

  return (
    <div className="panel panel-pad" id="budget-breakdown">
      <div className="panel-head">
        <div>
          <p className="eyebrow">What it costs</p>
        </div>
      </div>

      <div className="budget-hero">
        <div>
          <div className="budget-total">{inr(total)}</div>
          <div className="budget-of">estimated against a {inr(limit)} budget</div>
        </div>
        <span className={`status-pill ${within ? 'within' : 'over'}`}>
          {within
            ? `${inr(Math.abs(remaining))} to spare`
            : `${inr(Math.abs(remaining))} over`}
        </span>
      </div>

      <div className="meter">
        <div
          className={`meter-fill ${within ? 'within' : 'over'}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="cat-list">
        {CATEGORIES.map(({ key, label, color }) => {
          const cat = breakdown[key];
          if (!cat) return null;

          const catTotal = cat.total || 0;
          const catPct = total > 0 ? (catTotal / total) * 100 : 0;

          return (
            <div className="cat" key={key} id={`budget-${key}`}>
              <span className="cat-name">
                <span className="cat-swatch" style={{ background: color }} />
                {label}
              </span>
              <span className="cat-amount">{inr(catTotal)}</span>
              <span className="cat-bar">
                <span
                  className="cat-bar-fill"
                  style={{ width: `${catPct}%`, background: color }}
                />
              </span>
              <span className="cat-detail">
                {key === 'accommodation' && cat.per_night > 0 &&
                  `${inr(cat.per_night)} a night · ${cat.nights} nights · ${cat.rooms} room(s)`}
                {key === 'food' && cat.per_day_per_person > 0 &&
                  `${inr(cat.per_day_per_person)} per person per day · ${cat.days} days`}
                {key === 'transport' && cat.per_day > 0 &&
                  `${inr(cat.per_day)} a day · ${cat.days} days`}
                {key === 'activities' && cat.items &&
                  `${cat.items.length} paid ${cat.items.length === 1 ? 'activity' : 'activities'}`}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
