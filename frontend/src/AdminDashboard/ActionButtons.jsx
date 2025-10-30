import React from "react";

export default function ActionButtons() {
  return (
    <div className="actions-section">
      <button className="btn-action" onClick={() => alert("Add Medicine")}>
        Add Medicine
      </button>
      <button className="btn-action" onClick={() => alert("View Orders")}>
        View Orders
      </button>
      <button className="btn-action" onClick={() => alert("Generate Report")}>
        Generate Report
      </button>
    </div>
  );
}
