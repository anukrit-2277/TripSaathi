export default function SourcesList({ sources }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="sources-list" id="sources-list">
      <h3 className="section-title">📚 RAG Sources Used</h3>
      <div className="sources-tags">
        {sources.map((source, idx) => (
          <span key={idx} className="source-tag">
            📄 {source}
          </span>
        ))}
      </div>
      <p className="sources-note">
        Information was retrieved from these knowledge base documents using semantic search (RAG).
      </p>
    </div>
  );
}
