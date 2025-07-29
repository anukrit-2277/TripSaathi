import { IconCheck } from './icons';

const AGENT_STEPS = [
  { id: 'destination', label: 'Destination', description: 'Searching the knowledge base for places worth your time.' },
  { id: 'budget',      label: 'Budget',      description: 'Costing stay, food, transport and entry fees.' },
  { id: 'itinerary',   label: 'Itinerary',   description: 'Laying out the day-by-day plan.' },
  { id: 'critic',      label: 'Review',      description: 'Checking pacing, budget and your interests.' },
];

export default function AgentProgress({ currentStep, isComplete, revisionCount }) {
  const statusOf = (i) => {
    if (isComplete || i < currentStep) return 'done';
    if (i === currentStep) return 'active';
    return 'pending';
  };

  return (
    <div className="panel progress-panel" id="agent-progress">
      <div className="panel-head">
        <div>
          <p className="eyebrow">{isComplete ? 'Done' : 'Working'}</p>
          <h3 style={{ marginTop: 'var(--s-3)' }}>
            {isComplete ? 'Your plan is ready' : 'Building your trip'}
          </h3>
          {!isComplete && (
            <p className="panel-sub">This usually takes about a minute.</p>
          )}
        </div>
      </div>

      <div className="progress-rail">
        {AGENT_STEPS.map((step, i) => {
          const status = statusOf(i);
          return (
            <div className={`pstep ${status}`} key={step.id} id={`step-${step.id}`}>
              <div className="pstep-top">
                <span className="pstep-mark">
                  {status === 'done' && <IconCheck />}
                  {status === 'active' && <span className="spinner-ring" />}
                  {status === 'pending' && <span className="dot-idle" />}
                </span>
                <span className="pstep-name">{step.label}</span>
              </div>
              {status === 'active' && (
                <p className="pstep-desc">{step.description}</p>
              )}
            </div>
          );
        })}

        {revisionCount > 0 && (
          <div className="pstep done" id="step-revision">
            <div className="pstep-top">
              <span className="pstep-mark"><IconCheck /></span>
              <span className="pstep-name">Revision {revisionCount}</span>
            </div>
            <p className="pstep-desc">Improved after review feedback.</p>
          </div>
        )}
      </div>
    </div>
  );
}
