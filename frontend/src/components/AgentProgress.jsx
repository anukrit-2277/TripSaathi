const AGENT_STEPS = [
  { id: 'destination', label: 'Destination Agent', description: 'Retrieving destination info from RAG...', icon: '🔍' },
  { id: 'budget', label: 'Budget Agent', description: 'Estimating costs and budget...', icon: '💰' },
  { id: 'itinerary', label: 'Itinerary Agent', description: 'Creating day-by-day plan...', icon: '📝' },
  { id: 'critic', label: 'Critic Agent', description: 'Reviewing itinerary quality...', icon: '🔍' },
];

export default function AgentProgress({ currentStep, isComplete, revisionCount }) {
  const getStepStatus = (index) => {
    if (isComplete) return 'done';
    if (index < currentStep) return 'done';
    if (index === currentStep) return 'active';
    return 'pending';
  };

  return (
    <div className="agent-progress" id="agent-progress">
      <h3 className="progress-title">
        {isComplete ? '✅ Planning Complete' : '🤖 Agents Working...'}
      </h3>

      <div className="progress-steps">
        {AGENT_STEPS.map((step, index) => {
          const status = getStepStatus(index);
          return (
            <div key={step.id} className={`progress-step ${status}`} id={`step-${step.id}`}>
              <div className="step-indicator">
                {status === 'done' && <span className="step-icon done">✓</span>}
                {status === 'active' && <span className="step-icon active spinner-icon">↻</span>}
                {status === 'pending' && <span className="step-icon pending">○</span>}
              </div>
              <div className="step-content">
                <span className="step-label">{step.icon} {step.label}</span>
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
              <span className="step-icon done">✓</span>
            </div>
            <div className="step-content">
              <span className="step-label">🔄 Revision {revisionCount}</span>
              <span className="step-description">Itinerary improved based on feedback</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
