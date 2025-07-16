export default function ItineraryView({ itinerary }) {
  if (!itinerary || !itinerary.days || itinerary.days.length === 0) {
    return null;
  }

  return (
    <div className="itinerary-view" id="itinerary-view">
      <h3 className="section-title">🗺️ {itinerary.title || 'Your Itinerary'}</h3>

      <div className="days-container">
        {itinerary.days.map((day) => (
          <div key={day.day} className="day-card" id={`day-${day.day}`}>
            <div className="day-header">
              <span className="day-number">Day {day.day}</span>
              <span className="day-title">{day.title}</span>
            </div>

            <div className="day-timeline">
              {/* Activities */}
              {day.activities && day.activities.map((activity, idx) => (
                <div key={idx} className="timeline-item activity-item">
                  <div className="timeline-time">{activity.time}</div>
                  <div className="timeline-dot activity-dot"></div>
                  <div className="timeline-content">
                    <h4>{activity.activity}</h4>
                    <div className="timeline-meta">
                      <span className="meta-tag duration">⏱ {activity.duration}</span>
                      {activity.cost_per_person > 0 && (
                        <span className="meta-tag cost">₹{activity.cost_per_person}/person</span>
                      )}
                    </div>
                    {activity.notes && <p className="timeline-notes">{activity.notes}</p>}
                  </div>
                </div>
              ))}

              {/* Meals */}
              {day.meals && day.meals.map((meal, idx) => (
                <div key={`meal-${idx}`} className="timeline-item meal-item">
                  <div className="timeline-time">{meal.time}</div>
                  <div className="timeline-dot meal-dot"></div>
                  <div className="timeline-content">
                    <h4>
                      {meal.type === 'breakfast' && '🌅'}
                      {meal.type === 'lunch' && '☀️'}
                      {meal.type === 'dinner' && '🌙'}
                      {meal.type === 'snack' && '🍿'}
                      {' '}{meal.suggestion}
                    </h4>
                    <div className="timeline-meta">
                      <span className="meta-tag cuisine">{meal.cuisine}</span>
                      {meal.cost_per_person > 0 && (
                        <span className="meta-tag cost">₹{meal.cost_per_person}/person</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {day.transport_notes && (
              <div className="day-transport">
                🚗 <span>{day.transport_notes}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Recommendations */}
      {itinerary.recommendations && itinerary.recommendations.length > 0 && (
        <div className="recommendations-card">
          <h4>💡 Recommendations</h4>
          <ul>
            {itinerary.recommendations.map((rec, idx) => (
              <li key={idx}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Packing Tips */}
      {itinerary.packing_tips && itinerary.packing_tips.length > 0 && (
        <div className="recommendations-card packing-card">
          <h4>🎒 Packing Tips</h4>
          <ul>
            {itinerary.packing_tips.map((tip, idx) => (
              <li key={idx}>{tip}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
