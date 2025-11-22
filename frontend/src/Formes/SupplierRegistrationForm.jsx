import React, { useState } from "react";
import axios from "axios";
import { useNavigate, useLocation } from "react-router-dom";
import styles from "./SupplierRegistrationForm.module.css";
import Notification from "../Notification/Notification";

const API_BASE = "http://localhost:8000/api/medical_store";

const SupplierRegistrationForm = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [formData, setFormData] = useState({
    contact_name: "",
    phone: "",
    email: "",
    address: "",
    city: "",
    pin_code: "",
    age: "",
    gender: "",
  });

  const [notification, setNotification] = useState({
    message: "",
    type: "info",
  });

  const [loading, setLoading] = useState(false);

  const showNotification = (message, type = "info") => {
    setNotification({ message, type });
  };

  const closeNotification = () => {
    setNotification({ message: "", type: "" });
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const submitForm = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const token = localStorage.getItem("access_token");

      const res = await axios.post(`${API_BASE}/supplier`, formData, {
        headers: { Authorization: `Bearer ${token}` },
        validateStatus: () => true, // important for custom error handling
      });

      // -----------------------------
      // 🔐 Unauthorized → Redirect
      // -----------------------------
      if (res.status === 401 || res.status === 403 || res.status === 402) {
        showNotification("Session expired! Please login again.", "warning");

        setTimeout(() => {
          navigate("/login", {
            state: { from: location.pathname },
          });
        }, 1000);
        return;
      }

      // -----------------------------
      // ❌ Validation or Server Error
      // -----------------------------
      if (res.status >= 400) {
        showNotification(res.data?.detail || "Failed to register supplier!", "error");
        setLoading(false);
        return;
      }

      // -----------------------------
      // ✅ SUCCESS
      // -----------------------------
      showNotification("Supplier Registered Successfully!", "success");

      setFormData({
        contact_name: "",
        phone: "",
        email: "",
        address: "",
        city: "",
        pin_code: "",
        age: "",
        gender: "",
      });

      setTimeout(() => navigate(-1), 1200); // Go back to previous page

    } catch (err) {
      showNotification("Something went wrong!", "error");
    }

    setLoading(false);
  };

  return (
    <>
      {notification.message && (
        <Notification
          message={notification.message}
          type={notification.type}
          duration={3000}
          onClose={closeNotification}
        />
      )}

      <div className={styles.supplierWrapper}>
        <div className={styles.supplierCard}>
          <h2 className={styles.supplierTitle}>Supplier Registration</h2>

          <form className={styles.form} onSubmit={submitForm}>
            <input
              type="text"
              name="contact_name"
              placeholder="Contact Name"
              value={formData.contact_name}
              onChange={handleChange}
              required
            />

            <input
              type="text"
              name="phone"
              placeholder="Phone"
              value={formData.phone}
              onChange={handleChange}
              required
            />

            <input
              type="email"
              name="email"
              placeholder="Email ID"
              value={formData.email}
              onChange={handleChange}
              required
            />

            <input
              type="number"
              name="age"
              placeholder="Age"
              value={formData.age}
              onChange={handleChange}
              required
            />

            <select
              name="gender"
              value={formData.gender}
              onChange={handleChange}
              required
            >
              <option value="">Select Gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>

            <input
              type="text"
              name="city"
              placeholder="City"
              value={formData.city}
              onChange={handleChange}
              required
            />

            <input
              type="text"
              name="pin_code"
              placeholder="Pin Code"
              value={formData.pin_code}
              onChange={handleChange}
              required
            />

            <textarea
              name="address"
              placeholder="Full Address"
              value={formData.address}
              onChange={handleChange}
              required
            ></textarea>

            <button
              type="submit"
              className={styles.supplierBtn}
              disabled={loading}
            >
              {loading ? "Registering..." : "Register Supplier"}
            </button>
          </form>
        </div>
      </div>
    </>
  );
};

export default SupplierRegistrationForm;

