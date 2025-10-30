import React from "react";
import "./PatientDashboard.css";

function PatientProfileCard({ patient, onEdit, onAddPhoto }) {
  return (
    <div className="patient-profile-card">
      <img className="patient-avatar" src={patient.image || "/default-avatar.png"} alt={patient.name} />
      <div className="patient-details">
        <h2>{patient.name}</h2>
        <p><strong>Age:</strong> {patient.age}</p>
        <p><strong>Gender:</strong> {patient.gender}</p>
        <p><strong>Address:</strong> {patient.address}</p>
      </div>
      <div className="profile-actions">
        <button onClick={onEdit} className="btn-edit">Edit</button>
        <button onClick={onAddPhoto} className="btn-photo">Add Photo</button>
      </div>
    </div>
  );
}

export default PatientProfileCard;
