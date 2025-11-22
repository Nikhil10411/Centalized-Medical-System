import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import Notification from "../Notification/Notification";
import "./Auth.css";

const API_BASE = "http://localhost:8000/auth";
const API_ME = "http://localhost:8000/auth/me"; // Assuming /auth/me returns user data

export default function Auth() {
  const navigate = useNavigate();
  const location = useLocation();
  const redirectAfterLogin = location.state?.from || "/";

  const [mode, setMode] = useState("login");
  const [notification, setNotification] = useState(null);

  const [formData, setFormData] = useState({
    username: "",
    password: "",
    confirmPassword: "",
    email: "",
    token: "",
    role: "PATIENT", 
  });

  const roleOptions = [
    { value: "DOCTOR", label: "Doctor" },
    { value: "CHEMIST", label: "Chemist" },
    { value: "PATIENT", label: "Patient" },
    { value: "SUPPLIER", label: "Supplier (e.g., Pharmacy Admin)" },
    { value: "CUSTOMER", label: "Customer" },
  ];

  // Detect if user is already logged in
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) setMode("logout");
  }, []);

  const handleChange = (e) =>
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const showNotify = (type, message) =>
    setNotification({ type, message, id: Date.now() });

  // ──────────────────────────────────────────────────────────────
  // CORE LOGIC: Redirection Handler
  // ──────────────────────────────────────────────────────────────

  const handleRedirect = (userInfo) => {
    const role = userInfo.role.toUpperCase();

    // Check if the user is *not* fully registered based on the role
    if (role === 'DOCTOR' && !userInfo.is_doctor_registered) {
      return navigate("/doctor-registration", { replace: true });
    }
    if (role === 'PATIENT' && !userInfo.is_patient_registered) {
      return navigate("/patient-registration", { replace: true });
    }
    // Assuming CHEMIST/SUPPLIER/CUSTOMER uses MedicalStoreRegistration or similar logic
    if (role === 'CHEMIST' && !userInfo.is_medical_store_registered) {
        return navigate("/medical-store-registration", { replace: true });
    }
    
    // Default: Redirect to the intended page or homepage
    navigate(redirectAfterLogin, { replace: true });
  };
  
  // ──────────────────────────────────────────────────────────────
  // Fetch User Info Handler (Runs after successful token acquisition)
  // ──────────────────────────────────────────────────────────────
  const fetchAndRedirectUser = async (token) => {
      try {
          const res = await axios.get(API_ME, {
              headers: { "Authorization": `Bearer ${token}` }
          });
          
          const userInfo = res.data;
          
          // CRITICAL: Save user data for future checks and redirect
          localStorage.setItem("userInfo", JSON.stringify(userInfo));
          handleRedirect(userInfo);
          
      } catch (err) {
          showNotify("error", "Login successful but failed to fetch user details. Please refresh.");
          // Still redirect to home to prevent being stuck, but log error
          navigate(redirectAfterLogin, { replace: true }); 
      }
  }


  // ──────────────────────────────────────────────────────────────
  // 1. Login Handler (Updated to use fetchAndRedirectUser)
  // ──────────────────────────────────────────────────────────────
  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const data = new URLSearchParams();
      data.append("username", formData.username);
      data.append("password", formData.password);

      const res = await axios.post(`${API_BASE}/login`, data, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      const token = res.data.access_token;
      localStorage.setItem("access_token", token);
      showNotify("success", "Login successful! Checking profile status...");
      
      // Fetch user details and handle redirection
      await fetchAndRedirectUser(token);
      
    } catch (err) {
      showNotify(
        "error",
        err.response?.data?.detail || "Invalid username or password."
      );
    }
  };

  // ──────────────────────────────────────────────────────────────
  // 2. Signup Handler (Updated to use fetchAndRedirectUser)
  // ──────────────────────────────────────────────────────────────
  const handleSignup = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword)
      return showNotify("error", "Passwords do not match!");

    try {
      const payload = {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        confirm_password: formData.confirmPassword,
        role: formData.role.toLowerCase(),
      };

      const res = await axios.post(`${API_BASE}/signup`, payload);
      
      const token = res.data.access_token;
      localStorage.setItem("access_token", token);
      showNotify("success", "Signup successful! Checking profile status...");
      
      // Clear fields used in signup form
      setFormData((prev) => ({
        ...prev, username: "", password: "", confirmPassword: "", email: "", role: "PATIENT",
      }));
      
      // Fetch user details and handle redirection
      await fetchAndRedirectUser(token);
      
    } catch (err) {
      const errorDetail = err.response?.data?.detail 
                        || "Signup failed. Try again.";
      showNotify("error", errorDetail);
    }
  };

  // ──────────────────────────────────────────────────────────────
  // 5. Logout Handler (Updated to clear userInfo)
  // ──────────────────────────────────────────────────────────────
  const handleLogout = async () => {
    try {
      // NOTE: Call backend /logout for token invalidation if implemented
      localStorage.removeItem("access_token");
      localStorage.removeItem("userInfo"); // <-- CRITICAL: Clear saved info
      delete axios.defaults.headers.common["Authorization"];
      showNotify("success", "You’ve logged out successfully!");
      setTimeout(() => {
        setMode("login");
        navigate("/login", { replace: true });
        window.location.reload();
      }, 1000);
    } catch (err) {
      showNotify("error", "Logout failed. Try again.");
    }
  };

  // ... (handleForgot, handleReset, and renderForm are unchanged)

  // ──────────────────────────────────────────────────────────────
  // Render Forms (Unchanged)
  // ──────────────────────────────────────────────────────────────
  const renderForm = () => {
    // ... (Your login, signup, forgot, reset, and logout forms)
    // NOTE: For brevity, the renderForm function is omitted here, but remains the same as your input.
    // ... (Your login, signup, forgot, reset, and logout forms)
    switch (mode) {
      case "login":
        return (
          <form onSubmit={handleLogin}>
            <h2>Login</h2>
            <input
              type="text"
              name="username"
              placeholder="Username or Email"
              value={formData.username}
              onChange={handleChange}
              required
            />
            <input
              type="password"
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              required
            />
            <button type="submit">Login</button>
            <p>
              Don’t have an account?{" "}
              <span className="auth-link" onClick={() => setMode("signup")}>Sign up</span>
            </p>
            <p>
              <span className="auth-link" onClick={() => setMode("forgot")}>Forgot password?</span>
            </p>
          </form>
        );

      case "signup":
        return (
          <form onSubmit={handleSignup}>
            <h2>Sign Up</h2>
            <input
              type="text"
              name="username"
              placeholder="Username"
              value={formData.username}
              onChange={handleChange}
              required
            />
            <input
              type="email"
              name="email"
              placeholder="Email"
              value={formData.email}
              onChange={handleChange}
              required
            />
            <input
              type="password"
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              required
            />
            <input
              type="password"
              name="confirmPassword"
              placeholder="Confirm Password"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
            />
            <select
              name="role"
              value={formData.role}
              onChange={handleChange}
              required
              className="role-select"
            >
              <option value="" disabled>
                -- Select Role --
              </option>
              {roleOptions.map(option => (
                <option key={option.value} value={option.value}>
                    {option.label}
                </option>
              ))}
            </select>
            <button type="submit">Sign Up</button>
            <p>
              Already have an account?{" "}
              <span className="auth-link" onClick={() => setMode("login")}>Login</span>
            </p>
          </form>
        );

      case "forgot":
        return (
          <form onSubmit={handleForgot}>
            <h2>Forgot Password</h2>
            <input
              type="email"
              name="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={handleChange}
              required
            />
            <button type="submit">Send Reset Link</button>
            <p>
              Remembered your password?{" "}
              <span className="auth-link" onClick={() => setMode("login")}>Login</span>
            </p>
          </form>
        );

      case "reset":
        return (
          <form onSubmit={handleReset}>
            <h2>Reset Password</h2>
            <input
              type="text"
              name="token"
              placeholder="Enter reset token"
              value={formData.token}
              onChange={handleChange}
              required
            />
            <input
              type="password"
              name="password"
              placeholder="New password"
              value={formData.password}
              onChange={handleChange}
              required
            />
            <input
              type="password"
              name="confirmPassword"
              placeholder="Confirm new password"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
            />
            <button type="submit">Reset Password</button>
            <p>
              Back to{" "}
              <span className="auth-link" onClick={() => setMode("login")}>Login</span>
            </p>
          </form>
        );

      case "logout":
        return (
          <div className="logout-card">
            <h2>Logout</h2>
            <p>You’re currently logged in. Do you want to log out?</p>
            <button onClick={handleLogout} className="logout-btn">
              Logout
            </button>
            <p>
              <span className="auth-link" onClick={() => navigate("/")}>Cancel</span>
            </p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="auth-container">
      {notification && (
        <Notification
          key={notification.id}
          type={notification.type}
          message={notification.message}
          onClose={() => setNotification(null)}
        />
      )}
      <div className="auth-card">{renderForm()}</div>
    </div>
  );
}