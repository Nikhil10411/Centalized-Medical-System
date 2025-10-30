import React from "react";
import "./PatientDashboard.css";

// Example medicalHistory prop format
// [{ date: "2025-08-10", note: "Blood test result normal" }, {...}]
function MedicalHistory({ medicalHistory }) {
  return (
    <div className="medical-history">
      <h3>Medical History</h3>
      <ul>
        {medicalHistory.map((entry, idx) => (
          <li key={idx}>
            <strong>{entry.date}</strong>: {entry.note}
          </li>
        ))}
        {medicalHistory.length === 0 && <li>No history available.</li>}
      </ul>
    </div>
  );
}

export default MedicalHistory;
