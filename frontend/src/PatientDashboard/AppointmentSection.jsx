import React from "react";
import "./PatientDashboard.css";

function AppointmentSection({ onBookDoctor, onBookHospital, onBookLab, onBookDispensary }) {
  return (
    <div className="appointment-section">
      <h3>Book Appointment</h3>
      <div className="appointment-actions">
        <button className="appt-btn" onClick={onBookDoctor}>Doctor</button>
        <button className="appt-btn" onClick={onBookHospital}>Hospital</button>
        <button className="appt-btn" onClick={onBookDispensary}>Dispensary</button>
        <button className="appt-btn" onClick={onBookLab}>Lab Test</button>
      </div>
    </div>
  );
}

export default AppointmentSection;
