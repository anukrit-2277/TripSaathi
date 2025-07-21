const AGENT_STEPS = [
  { id: 'destination', label: 'Destination Agent', description: 'Retrieving destination info from knowledge base...' },
  { id: 'budget', label: 'Budget Agent', description: 'Estimating costs and budget allocation...' },
  { id: 'itinerary', label: 'Itinerary Agent', description: 'Creating day-by-day travel plan...' },
  { id: 'critic', label: 'Critic Agent', description: 'Reviewing itinerary quality...' },
];

export default function AgentProgress({ currentStep, isComplete, revisionCount }) {
  const getStepStatus = (index) => {
    if (isComplete) return 'done';
    if (index < currentStep) return 'done';
    if (index === currentStep) return 'active';
    return 'pending';
  };

  return (
    <div className="agent-progress glass-card" id="agent-progress">
      <h3 className="section-title">
        {isComplete ? 'Planning Complete' : 'Agents Working'}
      </h3>

      <div className="progress-steps">
        {AGENT_STEPS.map((step, index) => {
          const status = getStepStatus(index);
          return (
            <div key={step.id} className={`progress-step ${status}`} id={`step-${step.id}`}>
              <div className="step-indicator">
                {status === 'done' && (
                  <svg className="step-icon-svg done" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                )}
                {status === 'active' && <span className="step-spinner"></span>}
                {status === 'pending' && <span className="step-dot"></span>}
              </div>
              <div className="step-content">
                <span className="step-label">{step.label}</span>
                {status === 'active' && (
                  <span className="step-description">{step.description}</span>
                )}
              </div>
            </div>
          );
        })}

        {revisionCount > 0 && (
          <div className="progress-step done" id="step-revision">
            <div className="step-indicator">
              <svg className="step-icon-svg done" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <div className="step-content">
              <span className="step-label">Revision {revisionCount}</span>
              <span className="step-description">Itinerary improved based on feedback</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
