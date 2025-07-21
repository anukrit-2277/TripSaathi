export default function BudgetBreakdown({ breakdown }) {
  if (!breakdown || !breakdown.total_estimated) return null;

  const categories = [
    { key: 'accommodation', label: 'Accommodation', color: '#7c5cfc' },
    { key: 'food', label: 'Food & Dining', color: '#f59e0b' },
    { key: 'transport', label: 'Transport', color: '#10b981' },
    { key: 'activities', label: 'Activities', color: '#ec4899' },
  ];

  const total = breakdown.total_estimated;
  const budgetLimit = breakdown.budget_limit;
  const remaining = breakdown.remaining;
  const withinBudget = breakdown.within_budget;
  const percentage = Math.min((total / budgetLimit) * 100, 100);

  return (
    <div className="budget-breakdown glass-card" id="budget-breakdown">
      <h3 className="section-title">Budget Breakdown</h3>

      <div className="budget-meter">
        <div className="meter-header">
          <span className="meter-label">
            {total.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })} of {budgetLimit.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })}
          </span>
          <span className={`meter-status ${withinBudget ? 'within' : 'over'}`}>
            {withinBudget
              ? `${Math.abs(remaining).toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })} remaining`
              : `${Math.abs(remaining).toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })} over budget`}
          </span>
        </div>
        <div className="meter-bar">
          <div className={`meter-fill ${withinBudget ? 'within' : 'over'}`} style={{ width: `${percentage}%` }}></div>
        </div>
      </div>

      <div className="budget-categories">
        {categories.map(({ key, label, color }) => {
          const cat = breakdown[key];
          if (!cat) return null;
          const catTotal = cat.total || 0;
          const catPercent = total > 0 ? (catTotal / total) * 100 : 0;
          return (
            <div key={key} className="budget-category" id={`budget-${key}`}>
              <div className="category-header">
                <div className="category-color" style={{ backgroundColor: color }}></div>
                <span className="category-label">{label}</span>
                <span className="category-amount">{catTotal.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })}</span>
              </div>
              <div className="category-bar">
                <div className="category-fill" style={{ width: `${catPercent}%`, backgroundColor: color }}></div>
              </div>
              <div className="category-detail">
                {key === 'accommodation' && cat.per_night > 0 && <span>{cat.per_night.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })}/night &middot; {cat.nights} nights &middot; {cat.rooms} room(s)</span>}
                {key === 'food' && cat.per_day_per_person > 0 && <span>{cat.per_day_per_person.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })}/day/person &middot; {cat.days} days &middot; {cat.travelers} people</span>}
                {key === 'transport' && cat.per_day > 0 && <span>{cat.per_day.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })}/day &middot; {cat.days} days</span>}
                {key === 'activities' && cat.items && <span>{cat.items.length} paid activities</span>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
