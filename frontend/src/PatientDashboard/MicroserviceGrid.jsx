import React from "react";
import "./PatientDashboard.css";

const microservices = [
  { label: "Search Hospital", icon: "🏥", path: "/search/hospital" },
  { label: "Search Doctor", icon: "🩺", path: "/search/doctor" },
  { label: "Search Labs", icon: "🔬", path: "/search/labs" },
  { label: "Search Medical Stores", icon: "💊", path: "/search/medical-stores" },
  { label: "Search Dispensary", icon: "💉", path: "/search/dispensary" },
  { label: "Search Medicine", icon: "🧪", path: "/search/medicine" },
  { label: "Search Clinic", icon: "🏨", path: "/search/clinic" },
  { label: "Search Nursing Home", icon: "🏠", path: "/search/nursing-home" },
];

function MicroserviceGrid({ onNavigate }) {
  return (
    <div className="microservice-grid">
      {microservices.map((svc) => (
        <button key={svc.label} className="microservice-btn" onClick={() => onNavigate(svc.path)}>
          <span className="svc-icon">{svc.icon}</span>
          {svc.label}
        </button>
      ))}
    </div>
  );
}

export default MicroserviceGrid;
