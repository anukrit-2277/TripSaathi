/**
 * Quality review.
 *
 * The score is drawn with a conic-gradient ring — no chart library, no
 * SVG arc maths, and it animates cleanly because it is one CSS variable.
 */
export default function CriticStatus({ critique }) {
  if (!critique?.status) return null;

  const score = critique.score || 0;
  const issues = critique.issues || [];
  const suggestions = critique.suggestions || [];
  const coverage = critique.preference_coverage || {};

  const ringColor =
    score >= 8 ? 'var(--ok)' : score >= 6 ? 'var(--warn)' : 'var(--bad)';

  const approved =
    critique.status === 'approved' || critique.status === 'max_revisions_reached';

  return (
    <div className="panel panel-pad" id="critic-status">
      <p className="eyebrow">Quality review</p>

      <div className="score-row" style={{ marginTop: 'var(--s-5)' }}>
        <div
          className="score-ring"
          style={{ '--pct': score * 10, '--ring-color': ringColor }}
          role="img"
          aria-label={`Quality score ${score} out of 10`}
        >
          <span className="score-inner">
            <span className="score-num">{score}</span>
            <span className="score-den">/10</span>
          </span>
        </div>

        <div className="score-text">
          <span className={`status-pill is-enum ${approved ? 'within' : 'over'}`}>
            {critique.status === 'max_revisions_reached' ? 'Accepted' : critique.status}
          </span>
          {critique.overall_assessment && (
            <p className="assessment">{critique.overall_assessment}</p>
          )}
        </div>
      </div>

      {Object.keys(coverage).length > 0 && (
        <div className="sub-block">
          <p className="sub-head">Your interests</p>
          <div className="chips">
            {Object.entries(coverage).map(([pref, covered]) => (
              <span key={pref} className={`cov-tag ${covered ? 'yes' : 'no'}`}>
                {pref}
              </span>
            ))}
          </div>
        </div>
      )}

      {issues.length > 0 && (
        <div className="sub-block">
          <p className="sub-head">Notes ({issues.length})</p>
          <div>
            {issues.map((issue, i) => (
              <div className="issue" key={i}>
                <span className={`issue-dot ${issue.severity}`} />
                <span>{issue.issue}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {suggestions.length > 0 && (
        <div className="sub-block">
          <p className="sub-head">Suggestions</p>
          <ul className="note-list">
            {suggestions.map((s, i) => <li key={i}>{s}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
