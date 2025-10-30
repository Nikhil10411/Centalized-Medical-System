import React from "react";

export default function InventoryList({ inventory }) {
  return (
    <div className="inventory-section">
      <h2>Inventory</h2>
      <ul className="inventory-list">
        {inventory.map((item, index) => (
          <li key={index} className={item.stock < 10 ? "low-stock" : ""}>
            <strong>{item.name}</strong> - Stock: {item.stock} - ₹{item.price}
          </li>
        ))}
      </ul>
    </div>
  );
}
