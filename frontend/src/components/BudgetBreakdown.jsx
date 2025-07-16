export default function BudgetBreakdown({ breakdown }) {
  if (!breakdown || !breakdown.total_estimated) return null;

  const categories = [
    { key: 'accommodation', label: '🏨 Accommodation', color: '#6366f1' },
    { key: 'food', label: '🍽️ Food', color: '#f59e0b' },
    { key: 'transport', label: '🚗 Transport', color: '#10b981' },
    { key: 'activities', label: '🎯 Activities', color: '#ec4899' },
  ];

  const total = breakdown.total_estimated;
  const budgetLimit = breakdown.budget_limit;
  const remaining = breakdown.remaining;
  const withinBudget = breakdown.within_budget;
  const percentage = Math.min((total / budgetLimit) * 100, 100);

  return (
    <div className="budget-breakdown" id="budget-breakdown">
      <h3 className="section-title">💰 Budget Breakdown</h3>

      {/* Budget meter */}
      <div className="budget-meter">
        <div className="meter-header">
          <span className="meter-label">
            ₹{total.toLocaleString('en-IN')} of ₹{budgetLimit.toLocaleString('en-IN')}
          </span>
          <span className={`meter-status ${withinBudget ? 'within' : 'over'}`}>
            {withinBudget ? `₹${remaining.toLocaleString('en-IN')} remaining` : `₹${Math.abs(remaining).toLocaleString('en-IN')} over budget`}
          </span>
        </div>
        <div className="meter-bar">
          <div
            className={`meter-fill ${withinBudget ? 'within' : 'over'}`}
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
      </div>

      {/* Category breakdown */}
      <div className="budget-categories">
        {categories.map(({ key, label, color }) => {
          const cat = breakdown[key];
          if (!cat) return null;
          const catTotal = cat.total || 0;
          const catPercent = total > 0 ? (catTotal / total) * 100 : 0;

          return (
            <div key={key} className="budget-category" id={`budget-${key}`}>
              <div className="category-header">
                <span className="category-label">{label}</span>
                <span className="category-amount">₹{catTotal.toLocaleString('en-IN')}</span>
              </div>
              <div className="category-bar">
                <div
                  className="category-fill"
                  style={{ width: `${catPercent}%`, backgroundColor: color }}
                ></div>
              </div>
              <div className="category-detail">
                {key === 'accommodation' && cat.per_night > 0 && (
                  <span>₹{cat.per_night}/night × {cat.nights} nights × {cat.rooms} room(s)</span>
                )}
                {key === 'food' && cat.per_day_per_person > 0 && (
                  <span>₹{cat.per_day_per_person}/day/person × {cat.days} days × {cat.travelers} people</span>
                )}
                {key === 'transport' && cat.per_day > 0 && (
                  <span>₹{cat.per_day}/day × {cat.days} days</span>
                )}
                {key === 'activities' && cat.items && (
                  <span>{cat.items.length} paid activities</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
