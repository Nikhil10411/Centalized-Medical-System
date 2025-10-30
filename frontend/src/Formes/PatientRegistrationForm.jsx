import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import Notification from "../Notification/Notification"; // Adjust path
import "./PatientRegistrationForm.css";
import axios from "axios";
import patientBackground from "../assets/User.jpeg"; // Adjust path to your image

const API_BASE = "http://127.0.0.1:8000/api";

function PatientRegistrationForm() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    age: "",
    gender: "",
    city: "",
    state: "",
    address: "",
    pin_code: "",
    latitude: "",
    longitude: "",
  });

  const [errors, setErrors] = useState({
    name: "",
    email: "",
    phone: "",
  });

  const [notification, setNotification] = useState({ message: "", type: "" });

  const navigate = useNavigate();
  const location = useLocation();

  const showNotification = (msg, type = "info") => {
    setNotification({ message: msg, type });
    setTimeout(() => setNotification({ message: "", type: "" }), 5000);
  };

  const validateName = (name) => name.trim().length > 0;

  const validateEmail = (email) => {
    const re = /^[\w-.]+@([\w-]+\.)+[\w-]{2,4}$/;
    if (!email) return true;
    return re.test(email);
  };

  const validatePhone = (phone) => {
    const re = /^[0-9]{10}$/;
    if (!phone) return true;
    return re.test(phone);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    if (name === "name") {
      setErrors((prev) => ({
        ...prev,
        name: validateName(value) ? "" : "Name is required.",
      }));
    } else if (name === "email") {
      setErrors((prev) => ({
        ...prev,
        email: validateEmail(value) ? "" : "Invalid email address.",
      }));
    } else if (name === "phone") {
      setErrors((prev) => ({
        ...prev,
        phone: validatePhone(value) ? "" : "Phone must be 10 digits.",
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateName(formData.name)) {
      showNotification("Please enter your name.", "error");
      return;
    }
    if (!validateEmail(formData.email)) {
      showNotification("Invalid email address.", "error");
      return;
    }
    if (!validatePhone(formData.phone)) {
      showNotification("Phone must be 10 digits.", "error");
      return;
    }
    if (errors.name || errors.email || errors.phone) {
      showNotification("Please fix all errors before submitting.", "error");
      return;
    }

    try {
      const token = localStorage.getItem("access_token");
      await axios.post(`${API_BASE}/patients/`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      showNotification("Patient registered successfully!", "success");
      setFormData({
        name: "",
        email: "",
        phone: "",
        age: "",
        gender: "",
        city: "",
        state: "",
        address: "",
        pin_code: "",
        latitude: "",
        longitude: "",
      });
      setErrors({ name: "", email: "", phone: "" });
    } catch (err) {
      if (err.response?.status === 401) {
        showNotification("Session expired. Please login again.", "error");
        setTimeout(() => {
          navigate("/login", { state: { from: location }, replace: true });
        }, 2500);
      } else {
        const msg = err.response?.data?.detail || err.message || "Registration failed.";
        showNotification(msg, "error");
      }
    }
  };

  const containerStyle = {
    backgroundImage: `url(${patientBackground})`,
    backgroundSize: "cover",
    backgroundPosition: "center",
    minHeight: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    padding: "1rem",
  };

  return (
    <div style={containerStyle}>
      <Notification message={notification.message} type={notification.type} />
      <form onSubmit={handleSubmit} className="patient-registration-form" noValidate>
        <h2>Patient Registration</h2>

        <input
          name="name"
          type="text"
          placeholder="Name"
          value={formData.name}
          onChange={handleChange}
          required
        />
        {errors.name && <small className="error-text">{errors.name}</small>}

        <input
          name="email"
          type="email"
          placeholder="Email"
          value={formData.email}
          onChange={handleChange}
        />
        {errors.email && <small className="error-text">{errors.email}</small>}

        <input
          name="phone"
          type="tel"
          placeholder="Phone"
          value={formData.phone}
          onChange={handleChange}
        />
        {errors.phone && <small className="error-text">{errors.phone}</small>}

        <input
          name="age"
          type="number"
          min="0"
          max="120"
          placeholder="Age"
          value={formData.age}
          onChange={handleChange}
        />

        <select name="gender" value={formData.gender} onChange={handleChange}>
          <option value="">Select Gender</option>
          <option value="female">Female</option>
          <option value="male">Male</option>
          <option value="other">Other</option>
        </select>

        <input name="city" type="text" placeholder="City" value={formData.city} onChange={handleChange} />

        <input name="state" type="text" placeholder="State" value={formData.state} onChange={handleChange} />

        <input name="address" type="text" placeholder="Address" value={formData.address} onChange={handleChange} />

        <input name="pin_code" type="text" placeholder="Pin Code" value={formData.pin_code} onChange={handleChange} />

        <button type="submit">Register Patient</button>
      </form>
    </div>
  );
}

export default PatientRegistrationForm;
