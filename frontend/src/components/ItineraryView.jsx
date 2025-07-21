export default function ItineraryView({ itinerary }) {
  if (!itinerary || !itinerary.days || itinerary.days.length === 0) return null;

  return (
    <div className="itinerary-view glass-card" id="itinerary-view">
      <h3 className="section-title">{itinerary.title || 'Your Itinerary'}</h3>

      <div className="days-container">
        {itinerary.days.map((day) => (
          <div key={day.day} className="day-card" id={`day-${day.day}`}>
            <div className="day-header">
              <span className="day-number">Day {day.day}</span>
              <span className="day-title">{day.title}</span>
            </div>

            <div className="day-timeline">
              {day.activities && day.activities.map((activity, idx) => (
                <div key={idx} className="timeline-item activity-item">
                  <div className="timeline-time">{activity.time}</div>
                  <div className="timeline-dot-wrap"><div className="timeline-dot activity-dot"></div></div>
                  <div className="timeline-content">
                    <h4>{activity.activity}</h4>
                    <div className="timeline-meta">
                      <span className="meta-tag duration">{activity.duration}</span>
                      {activity.cost_per_person > 0 && (
                        <span className="meta-tag cost">{activity.cost_per_person.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })}/person</span>
                      )}
                    </div>
                    {activity.notes && <p className="timeline-notes">{activity.notes}</p>}
                  </div>
                </div>
              ))}

              {day.meals && day.meals.map((meal, idx) => (
                <div key={`meal-${idx}`} className="timeline-item meal-item">
                  <div className="timeline-time">{meal.time}</div>
                  <div className="timeline-dot-wrap"><div className="timeline-dot meal-dot"></div></div>
                  <div className="timeline-content">
                    <h4>{meal.suggestion}</h4>
                    <div className="timeline-meta">
                      <span className="meta-tag cuisine">{meal.cuisine}</span>
                      <span className="meta-tag meal-type">{meal.type}</span>
                      {meal.cost_per_person > 0 && (
                        <span className="meta-tag cost">{meal.cost_per_person.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })}/person</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {day.transport_notes && (
              <div className="day-transport">
                <span className="transport-label">Transport</span>
                <span>{day.transport_notes}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {itinerary.recommendations && itinerary.recommendations.length > 0 && (
        <div className="tips-card">
          <h4>Recommendations</h4>
          <ul>{itinerary.recommendations.map((rec, idx) => <li key={idx}>{rec}</li>)}</ul>
        </div>
      )}

      {itinerary.packing_tips && itinerary.packing_tips.length > 0 && (
        <div className="tips-card">
          <h4>Packing Tips</h4>
          <ul>{itinerary.packing_tips.map((tip, idx) => <li key={idx}>{tip}</li>)}</ul>
        </div>
      )}
    </div>
  );
}
