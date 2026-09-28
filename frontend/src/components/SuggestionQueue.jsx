export default function SuggestionQueue({ suggestions, onDecision, processingId }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h3>Approval Queue</h3>
      </div>
      <div className="queue-list">
        {!suggestions.length && <div className="empty-state">No pending actions</div>}
        {suggestions.map((item) => (
          <div key={`${item.type}-${item.id}`} className="queue-item">
            <div className="queue-header">
              <div>
                <span className="item-type">{item.type === 'pricing' ? 'Pricing' : 'Reorder'}</span>
                <strong>{item.product_name || item.product_id}</strong>
              </div>
              <span className="badge badge-muted">{item.trigger_reason}</span>
            </div>
            <p>{item.rationale}</p>
            {item.ai_reasoning && <small>AI reasoning: {item.ai_reasoning}</small>}
            <div className="suggestion-details">
              {item.type === 'pricing' ? (
                <span>Suggested price: ${Number(item.suggested_price).toFixed(2)}</span>
              ) : (
                <span>Suggested quantity: {item.suggested_quantity}</span>
              )}
            </div>
            <div className="actions-row">
              <button className="success" onClick={() => onDecision(item.type, item.id, 'accept')} disabled={processingId === item.id}>
                {processingId === item.id ? 'Processing...' : 'Accept'}
              </button>
              <button className="danger" onClick={() => onDecision(item.type, item.id, 'reject')} disabled={processingId === item.id}>
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
