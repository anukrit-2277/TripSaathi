export default function CriticStatus({ critique }) {
  if (!critique || !critique.status) return null;

  const isApproved = critique.status === 'approved' || critique.status === 'max_revisions_reached';
  const score = critique.score || 0;
  const issues = critique.issues || [];
  const suggestions = critique.suggestions || [];
  const prefCoverage = critique.preference_coverage || {};

  const getScoreColor = (s) => {
    if (s >= 8) return '#10b981';
    if (s >= 6) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="critic-status" id="critic-status">
      <h3 className="section-title">
        {isApproved ? '✅' : '❌'} Quality Review
      </h3>

      <div className="critic-header">
        <div className="score-circle" style={{ '--score-color': getScoreColor(score) }}>
          <span className="score-value">{score}</span>
          <span className="score-max">/10</span>
        </div>
        <div className="critic-summary">
          <span className={`status-badge ${isApproved ? 'approved' : 'rejected'}`}>
            {critique.status === 'max_revisions_reached' ? 'Accepted (Best Effort)' : critique.status.toUpperCase()}
          </span>
          {critique.overall_assessment && (
            <p className="assessment-text">{critique.overall_assessment}</p>
          )}
        </div>
      </div>

      {/* Preference Coverage */}
      {Object.keys(prefCoverage).length > 0 && (
        <div className="pref-coverage">
          <h4>Preference Coverage</h4>
          <div className="pref-tags">
            {Object.entries(prefCoverage).map(([pref, covered]) => (
              <span key={pref} className={`pref-tag ${covered ? 'covered' : 'missing'}`}>
                {covered ? '✓' : '✗'} {pref}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Issues */}
      {issues.length > 0 && (
        <div className="critic-issues">
          <h4>Issues Found ({issues.length})</h4>
          <div className="issues-list">
            {issues.map((issue, idx) => (
              <div key={idx} className={`issue-item severity-${issue.severity}`}>
                <span className="issue-severity">
                  {issue.severity === 'high' && '🔴'}
                  {issue.severity === 'medium' && '🟡'}
                  {issue.severity === 'low' && '🟢'}
                </span>
                <span className="issue-text">{issue.issue}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="critic-suggestions">
          <h4>Suggestions</h4>
          <ul>
            {suggestions.map((sug, idx) => (
              <li key={idx}>{sug}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
