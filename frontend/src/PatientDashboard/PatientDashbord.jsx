import React, { useState, useEffect } from "react";
import PatientProfileCard from "./PatientProfileCard";
import MedicalHistory from "./MedicalHistory";
import AppointmentSection from "./AppointmentSection";
import MicroserviceGrid from "./MicroserviceGrid";

function PatientDashboard() {
  const [patient, setPatient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPatient = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) throw new Error("Please log in to continue.");

        const response = await fetch("http://127.0.0.1:8000/api/patient", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          let message = "Failed to load patient data.";
          try {
            const errorData = await response.json();
            message = errorData.detail || message;
          } catch {
            // fallback to default message if response not JSON
          }
          throw new Error(message);
        }

        const data = await response.json();
        setPatient(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPatient();
  }, []);

  if (loading) return <div className="dashboard-status">Loading patient details...</div>;
  if (error) return <div className="dashboard-status error">Error: {error}</div>;
  if (!patient) return <div className="dashboard-status">No patient data available.</div>;

  return (
    <div className="dashboard-container">
      <PatientProfileCard patient={patient} />
      <MedicalHistory />
      <AppointmentSection />
      <MicroserviceGrid />
    </div>
  );
}

export default PatientDashboard;

