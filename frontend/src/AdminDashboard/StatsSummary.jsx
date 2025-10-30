import React from "react";

export default function StatsSummary({ stats }) {
  return (
    <div className="stats-section">
      <div className="stat-card">
        <h3>Total Medicines</h3>
        <p>{stats.totalMedicines}</p>
      </div>
      <div className="stat-card">
        <h3>Low Stock Items</h3>
        <p>{stats.lowStock}</p>
      </div>
      <div className="stat-card">
        <h3>Orders Today</h3>
        <p>{stats.ordersToday}</p>
      </div>
      <div className="stat-card">
        <h3>Pending Orders</h3>
        <p>{stats.pendingOrders}</p>
      </div>
    </div>
  );
}
