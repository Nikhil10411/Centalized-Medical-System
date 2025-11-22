import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import Notification from "../Notification/Notification"; // Adjust path if needed
import axios from "axios";
import "./DoctorRegistrationForm.css";

const API_BASE = "http://localhost:8000/api";

function DoctorRegistrationForm() {
  const [formData, setFormData] = useState({
    name: "",
    specialization: "",
    age: "",
    gender: "",
    medical_license_number: "",
    clinic_address: "",
    contact_phone: "",
    experience_years: 0,
    education_degree: "",
    is_available: true,
    clinic_name: "",
    regulatory_body: "",
    latitude: "",
    longitude: "",
    license_photo: null,
    doctor_photo: null,
    clinic_photo: null,
  });

  const [notification, setNotification] = useState({ message: "", type: "" });
  const navigate = useNavigate();
  const location = useLocation();

  const showNotification = (msg, type = "info") => {
    setNotification({ message: msg, type });
    setTimeout(() => setNotification({ message: "", type: "" }), 5000);
  };

  const getLocation = () => {
    if (!navigator.geolocation) {
      showNotification("Geolocation is not supported by your browser", "error");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setFormData((prev) => ({
          ...prev,
          latitude: position.coords.latitude.toFixed(6),
          longitude: position.coords.longitude.toFixed(6),
        }));
        showNotification("Clinic location detected!", "success");
      },
      (error) => {
        showNotification("Error fetching location: " + error.message, "error");
      }
    );
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleDateChange = (date) => {
    setFormData((prev) => ({
      ...prev,
      experience_years: date ? date.getFullYear() : 0,
    }));
  };

  const handleFileUpload = (e) => {
    const { name } = e.target;
    const file = e.target.files[0];
    setFormData((prev) => ({ ...prev, [name]: file }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const formPayload = new FormData();
      for (const [key, val] of Object.entries(formData)) {
        if (val !== null && val !== "") {
          formPayload.append(key, val);
        }
      }
      const token = localStorage.getItem("access_token");
      await axios.post(`${API_BASE}/doctors`, formPayload, {
        headers: {
          "Content-Type": "multipart/form-data",
          Authorization: `Bearer ${token}`,
        },
      });
      showNotification("Doctor registered successfully!", "success");
      setFormData({
        name: "",
        specialization: "",
        age: "",
        gender: "",
        medical_license_number: "",
        clinic_address: "",
        contact_phone: "",
        experience_years: 0,
        education_degree: "",
        is_available: true,
        clinic_name: "",
        regulatory_body: "",
        latitude: "",
        longitude: "",
        license_photo: null,
        doctor_photo: null,
        clinic_photo: null,
      });
    } catch (err) {
      if (err.response?.status === 401) {
        showNotification("Session expired. Please login again.", "error");
        setTimeout(() => {
          navigate("/login", { state: { from: location }, replace: true });
        }, 2500);
      } else {
        const msg = err.response?.data?.detail || err.message || "Registration failed. Please try again.";
        showNotification(msg, "error");
      }
    }
  };

  return (
    <div className="form-container">
      <Notification message={notification.message} type={notification.type} />
      <form onSubmit={handleSubmit} className="doctor-registration-form" encType="multipart/form-data">
        <h2>Register as a Doctor</h2>

        <input type="text" name="name" placeholder="Doctor Name" required value={formData.name} onChange={handleChange} />
        <input type="text" name="specialization" placeholder="Specialization" required value={formData.specialization} onChange={handleChange} />
        <input type="number" name="age" placeholder="Age" min="25" max="99" required value={formData.age} onChange={handleChange} />
        <select name="gender" required value={formData.gender} onChange={handleChange}>
          <option value="">Select Gender</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
        </select>
        <input type="text" name="medical_license_number" placeholder="Medical License Number" required value={formData.medical_license_number} onChange={handleChange} />
        <input type="text" name="clinic_address" placeholder="Clinic Address" required value={formData.clinic_address} onChange={handleChange} />
        <input type="tel" name="contact_phone" placeholder="Contact Phone" value={formData.contact_phone} onChange={handleChange} />

        <label>
          Experience Years:
          <DatePicker
            selected={formData.experience_years ? new Date(formData.experience_years, 0, 1) : null}
            onChange={handleDateChange}
            showYearPicker
            dateFormat="yyyy"
            placeholderText="Select Year"
          />
        </label>

        <input type="text" name="education_degree" placeholder="Education Degree" value={formData.education_degree} onChange={handleChange} />
        <label>
          Available for Consultation:
          <input type="checkbox" name="is_available" checked={formData.is_available} onChange={handleChange} />
        </label>
        <input type="text" name="clinic_name" placeholder="Clinic Name" value={formData.clinic_name} onChange={handleChange} />
        <select name="regulatory_body" value={formData.regulatory_body} onChange={handleChange}>
          <option value="">Select Regulatory Body</option>
          <option value="mci">Medical Council of India (MCI)</option>
          <option value="dci">Dental Council of India (DCI)</option>
          <option value="inc">Indian Nursing Council (INC)</option>
          <option value="pci">Pharmacy Council of India (PCI)</option>
        </select>

        <div style={{ display: "flex", gap: "10px", marginBottom: "15px" }}>
          <input type="text" name="latitude" placeholder="Latitude" value={formData.latitude} readOnly />
          <input type="text" name="longitude" placeholder="Longitude" value={formData.longitude} readOnly />
          <button type="button" onClick={getLocation} style={{ minWidth: "140px" }}>
            Get Clinic Location
          </button>
        </div>

        <label>License Photo (Required):</label>
        <input type="file" name="license_photo" accept=".jpeg,.jpg,.png" required onChange={handleFileUpload} />
        <label>Doctor Photo (Optional):</label>
        <input type="file" name="doctor_photo" accept=".jpeg,.jpg,.png" onChange={handleFileUpload} />
        <label>Clinic Photo (Optional):</label>
        <input type="file" name="clinic_photo" accept=".jpeg,.jpg,.png" onChange={handleFileUpload} />

        <button type="submit">Register Doctor</button>
      </form>
    </div>
  );
}

export default DoctorRegistrationForm;
