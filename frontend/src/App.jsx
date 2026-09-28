import { useEffect, useMemo, useState } from 'react';
import ProductTable from './components/ProductTable';
import SuggestionQueue from './components/SuggestionQueue';
import {
  acceptPricingSuggestion,
  acceptReorderSuggestion,
  getPendingSuggestions,
  getProductSummary,
  getProducts,
  rejectPricingSuggestion,
  rejectReorderSuggestion,
  triggerProductEvaluation,
} from './services/api';

const defaultSummary = { total_products: 0, low_stock_count: 0, demand_spike_count: 0, pending_suggestions: 0 };

export default function App() {
  const [products, setProducts] = useState([]);
  const [summary, setSummary] = useState(defaultSummary);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState(null);
  const [error, setError] = useState('');

  const refreshData = async () => {
    try {
      const [productsRes, summaryRes, pendingRes] = await Promise.all([
        getProducts(),
        getProductSummary(),
        getPendingSuggestions(),
      ]);
      setProducts(productsRes.data || []);
      setSummary(summaryRes.data || defaultSummary);
      const queue = [];
      (pendingRes.data?.pricing || []).forEach((item) => queue.push({ ...item, type: 'pricing' }));
      (pendingRes.data?.reorder || []).forEach((item) => queue.push({ ...item, type: 'reorder' }));
      setSuggestions(queue);
      setError('');
    } catch (err) {
      console.error(err);
      setError('Failed to load StockPulse data. Verify the FastAPI backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
    const timer = setInterval(refreshData, 3000);
    return () => clearInterval(timer);
  }, []);

  const handleEvaluate = async (productId) => {
    try {
      setProcessingId(productId);
      await triggerProductEvaluation(productId);
      await refreshData();
    } catch (err) {
      console.error(err);
      setError('Evaluation request failed.');
    } finally {
      setProcessingId(null);
    }
  };

  const handleDecision = async (type, id, decision) => {
    try {
      setProcessingId(id);
      if (type === 'pricing') {
        if (decision === 'accept') await acceptPricingSuggestion(id);
        else await rejectPricingSuggestion(id);
      } else if (decision === 'accept') {
        await acceptReorderSuggestion(id);
      } else {
        await rejectReorderSuggestion(id);
      }
      await refreshData();
    } catch (err) {
      console.error(err);
      setError('Decision update failed.');
    } finally {
      setProcessingId(null);
    }
  };

  const summaryCards = useMemo(
    () => [
      { label: 'Products', value: summary.total_products },
      { label: 'Low Stock', value: summary.low_stock_count },
      { label: 'Demand Spike', value: summary.demand_spike_count },
      { label: 'Pending', value: suggestions.length },
    ],
    [summary, suggestions.length]
  );

  if (loading) return <div className="loading-shell">Loading StockPulse...</div>;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Merchandising control</p>
          <h1>StockPulse</h1>
        </div>
        <span className="live-pill">Live</span>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="summary-grid">
        {summaryCards.map((card) => (
          <div className="summary-card" key={card.label}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
          </div>
        ))}
      </section>

      <section className="content-grid">
        <ProductTable products={products} onEvaluate={handleEvaluate} loadingProductId={processingId} />
        <SuggestionQueue suggestions={suggestions} onDecision={handleDecision} processingId={processingId} />
      </section>
    </div>
  );
}
