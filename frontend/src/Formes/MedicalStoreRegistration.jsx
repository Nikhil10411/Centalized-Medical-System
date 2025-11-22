import React, { useState, useEffect } from "react";
import "./MedicalStoreRegistration.css";
import axios from "axios";
import Notification from "../Notification/Notification"; 
import { useNavigate, useLocation } from "react-router-dom";
import storeBackground from "../assets/Medical.jpeg"; 

const API_BASE = "http://localhost:8000/api/medical_store";

const MedicalStoreRegistration = () => {
  // Form state
  const [formData, setFormData] = useState({
    store_name: "",
    owner_name: "",
    age: "",
    gender: "",
    store_type: "",
    address: "",
    city: "",
    locality: "",
    pin_code: "",
    phone: "",
    open_hours: "",
    delivery_radius_km: "",
  });

  // File uploads
  const [licenseDoc, setLicenseDoc] = useState(null);
  const [storePhoto, setStorePhoto] = useState(null);

  // Notifications and errors
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("info");
  const [errors, setErrors] = useState({});
  const [redirectPending, setRedirectPending] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false); // New state to prevent double submission

  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem("access_token");

  // Helper to reset the entire form state
  const resetFormState = () => {
    setFormData({
      store_name: "",
      owner_name: "",
      age: "",
      gender: "",
      store_type: "",
      address: "",
      city: "",
      locality: "",
      pin_code: "",
      phone: "",
      open_hours: "",
      delivery_radius_km: "",
    });
    setLicenseDoc(null);
    setStorePhoto(null);
    setErrors({});
  };

  // Validation
  const validate = () => {
    const newErrors = {};
    if (!formData.store_name.trim()) newErrors.store_name = "Store Name is required.";
    if (!formData.owner_name.trim()) newErrors.owner_name = "Owner Name is required.";
    if (!formData.phone.trim() || formData.phone.trim().length < 5) newErrors.phone = "Valid phone number is required (min 5 characters).";
    if (!licenseDoc) newErrors.licenseDoc = "License Document is required for registration.";

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handlers
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: "" }));
  };

  const handleFileChange = (e, setter, name) => {
    setter(e.target.files[0]);
    setErrors((prev) => ({ ...prev, [name]: "" }));
  };

  const handleCloseNotification = () => {
    setMessage("");
    setMessageType("info");
  };

  // Redirect effect for 401 after delay
  useEffect(() => {
    let timer;
    if (redirectPending) {
      timer = setTimeout(() => {
        navigate("/auth", { state: { from: location.pathname }, replace: true });
      }, 2500);
    }
    return () => clearTimeout(timer);
  }, [redirectPending, navigate, location.pathname]);

  // ──────────────────────────────────────────────────────────────
  // Submit logic (Updated)
  // ──────────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    setMessage("");
    setMessageType("");
    setRedirectPending(false);
    if (!validate()) return;

    setIsSubmitting(true);
    
    const form = new FormData();
    Object.entries(formData).forEach(([key, value]) => {
      if (value) form.append(key, value);
    });
    if (licenseDoc) form.append("license_document", licenseDoc);
    if (storePhoto) form.append("store_photo", storePhoto);

    try {
      const response = await axios.post(
        `${API_BASE}/register`,
        form,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            Authorization: `Bearer ${token}`,
          },
        }
      );
      
      // 1. Success state cleanup and notification
      setMessage(response.data.message || "✅ Store registered successfully! Awaiting admin approval.");
      setMessageType("success");
      resetFormState(); // ✅ SUCCESS: Clean up form state
      
    } catch (error) {
      let errMsg = "❌ A connection error occurred.";
      let type = "error";

      if (error.response) {
        const status = error.response.status;
        const detail = error.response.data.detail;
        
        if (status === 400) {
          errMsg = detail || "⚠️ You are already registered or details are invalid.";
          type = "warning";
          
          // 🎯 CRITICAL FIX: If the error is 'Already Registered', 
          // we assume the first attempt succeeded and clean up the form state 
          // to prevent the user from seeing the filled form and thinking it failed.
          if (typeof detail === 'string' && detail.toLowerCase().includes("already registered")) {
             setMessage("✅ Registration confirmed. Your store is already registered.");
             setMessageType("success");
             resetFormState(); // ✅ FIX: Clean up on confirmed registration
             setIsSubmitting(false); // Ensure button state is reset
             return; 
          }
          
        } else if (status === 401) {
          errMsg = "⚠️ Session expired or not logged in. Redirecting to login page...";
          type = "warning";
          setMessage(errMsg);
          setMessageType(type);
          setRedirectPending(true);
          setIsSubmitting(false);
          return;
        } else if (typeof detail === "string") {
          errMsg = `❌ ${detail}`;
        } else if (Array.isArray(detail) && detail.length > 0) {
          errMsg = `❌ Validation Error: ${detail[0].msg} for field '${detail[0].loc.pop()}'.`;
        }
      }
      
      setMessage(errMsg);
      setMessageType(type);
      
    } finally {
      setIsSubmitting(false); // Ensure submission state is always reset
    }
  };

  // Container style with independent background image
  const containerStyle = {
    backgroundImage: `url(${storeBackground})`,
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
      <Notification
        type={messageType}
        message={message}
        onClose={handleCloseNotification}
        duration={messageType === "warning" && redirectPending ? 3000 : 4000}
      />
      <form className="store-form" onSubmit={handleSubmit}>
        <h2>Medical Store Registration</h2>

        {/* Store Name */}
        <div className="form-group">
          <label>Store Name *</label>
          <input
            type="text"
            name="store_name"
            value={formData.store_name}
            onChange={handleChange}
            className={errors.store_name ? "input-error" : ""}
          />
          {errors.store_name && <small className="error-text">{errors.store_name}</small>}
        </div>

        {/* Owner Name */}
        <div className="form-group">
          <label>Owner Name *</label>
          <input
            type="text"
            name="owner_name"
            value={formData.owner_name}
            onChange={handleChange}
            className={errors.owner_name ? "input-error" : ""}
          />
          {errors.owner_name && <small className="error-text">{errors.owner_name}</small>}
        </div>

        {/* Age and Gender */}
        <div className="form-grid">
          <div className="form-group">
            <label>Age</label>
            <input type="number" name="age" value={formData.age} onChange={handleChange} />
          </div>

          <div className="form-group">
            <label>Gender</label>
            <select name="gender" value={formData.gender} onChange={handleChange}>
              <option value="">Select</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </div>
        </div>

        {/* Other fields... */}
        <div className="form-group">
          <label>Store Type</label>
          <input type="text" name="store_type" value={formData.store_type} onChange={handleChange} />
        </div>

        <div className="form-group">
          <label>Address</label>
          <input type="text" name="address" value={formData.address} onChange={handleChange} />
        </div>

        <div className="form-grid">
          <div className="form-group">
            <label>City</label>
            <input type="text" name="city" value={formData.city} onChange={handleChange} />
          </div>

          <div className="form-group">
            <label>Locality</label>
            <input type="text" name="locality" value={formData.locality} onChange={handleChange} />
          </div>

          <div className="form-group">
            <label>Pin Code</label>
            <input type="text" name="pin_code" value={formData.pin_code} onChange={handleChange} />
          </div>
        </div>

        {/* Phone */}
        <div className="form-group">
          <label>Phone *</label>
          <input
            type="tel"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            className={errors.phone ? "input-error" : ""}
          />
          {errors.phone && <small className="error-text">{errors.phone}</small>}
        </div>

        <div className="form-group">
          <label>Open Hours</label>
          <input type="text" name="open_hours" value={formData.open_hours} onChange={handleChange} />
        </div>

        <div className="form-group">
          <label>Delivery Radius (km)</label>
          <input type="number" name="delivery_radius_km" value={formData.delivery_radius_km} onChange={handleChange} />
        </div>
        
        {/* License Document */}
        <div className="form-group">
          <label>License Document *</label>
          <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => handleFileChange(e, setLicenseDoc, 'licenseDoc')} />
          {licenseDoc && <small className="file-info">{licenseDoc.name}</small>}
          {errors.licenseDoc && <small className="error-text">{errors.licenseDoc}</small>}
        </div>

        {/* Store Photo */}
        <div className="form-group">
          <label>Store Photo</label>
          <input type="file" accept=".jpg,.jpeg,.png" onChange={(e) => handleFileChange(e, setStorePhoto, 'storePhoto')} />
          {storePhoto && <small className="file-info">{storePhoto.name}</small>}
        </div>

        <button type="submit" className="btn-submit" disabled={redirectPending || isSubmitting}>
          {redirectPending ? "Redirecting..." : isSubmitting ? "Submitting..." : "Register Store"}
        </button>
      </form>
    </div>
  );
};

export default MedicalStoreRegistration;
