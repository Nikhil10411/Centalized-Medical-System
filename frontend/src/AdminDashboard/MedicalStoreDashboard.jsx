import React, { useEffect, useState } from "react";
import StatsSummary from "./StatsSummary";
import InventoryList from "./InventoryList";
import ActionButtons from "./ActionButtons";
import "./MedicalStoreDashboard.css";

function MedicalStoreDashboard() {
  const [stats, setStats] = useState(null);
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch data here or simulate with timeout
    setTimeout(() => {
      setStats({
        totalMedicines: 150,
        lowStock: 6,
        ordersToday: 12,
        pendingOrders: 4,
      });
      setInventory([
        { name: "Paracetamol", stock: 30, price: 15 },
        { name: "Amoxicillin", stock: 5, price: 40 },
        { name: "Cough Syrup", stock: 3, price: 25 },
        { name: "Ibuprofen", stock: 50, price: 18 },
      ]);
      setLoading(false);
    }, 900);
  }, []);

  if (loading) {
    return <div className="dashboard-container">Loading Medical Store Data...</div>;
  }

  return (
    <div className="dashboard-container">
      <StatsSummary stats={stats} />
      <ActionButtons />
      <InventoryList inventory={inventory} />
    </div>
  );
}

export default MedicalStoreDashboard;

