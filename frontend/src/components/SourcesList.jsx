import { IconDoc } from './icons';

export default function SourcesList({ sources }) {
  if (!sources?.length) return null;

  return (
    <div className="panel panel-pad" id="sources-list">
      <p className="eyebrow">Sources</p>
      <div className="chips" style={{ marginTop: 'var(--s-5)' }}>
        {sources.map((source, i) => (
          <span className="source-tag" key={i}>
            <IconDoc />
            {source}
          </span>
        ))}
      </div>
      <p className="sources-note">
        Retrieved from the travel knowledge base by semantic search, then used
        as grounding context for every agent in the workflow.
      </p>
    </div>
  );
}
