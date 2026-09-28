export default function ProductTable({ products, onEvaluate, loadingProductId }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h3>Catalog</h3>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Product</th>
              <th>Category</th>
              <th>Price</th>
              <th>Stock</th>
              <th>Threshold</th>
              <th>Signals</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {products.map((product) => {
              const inventoryLow = product.stock_level < product.reorder_threshold;
              const demandRatio = product.demand_velocity / Math.max(product.category_average_demand, 1);
              const demandSpike = demandRatio >= 1.5;

              return (
                <tr key={product.id}>
                  <td>{product.id}</td>
                  <td>{product.name}</td>
                  <td>{product.category}</td>
                  <td>${Number(product.current_price).toFixed(2)}</td>
                  <td>{product.stock_level}</td>
                  <td>{product.reorder_threshold}</td>
                  <td>
                    <div className="badges">
                      {inventoryLow && <span className="badge badge-warning">Low Stock</span>}
                      {demandSpike && <span className="badge badge-info">Demand Spike</span>}
                    </div>
                  </td>
                  <td>
                    <button
                      className="secondary"
                      onClick={() => onEvaluate(product.id)}
                      disabled={loadingProductId === product.id}
                    >
                      {loadingProductId === product.id ? 'Evaluating...' : 'Evaluate'}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
