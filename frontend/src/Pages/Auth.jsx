import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import Notification from "../Notification/Notification";
import "./Auth.css";

const API_BASE = "http://localhost:8000/auth";

export default function Auth() {
  const navigate = useNavigate();
  const location = useLocation();
  const redirectAfterLogin = location.state?.from || "/";

  const [mode, setMode] = useState("login"); // login | signup | forgot | reset | logout
  const [notification, setNotification] = useState(null);

  const [formData, setFormData] = useState({
    username: "",
    password: "",
    confirmPassword: "",
    email: "",
    token: "",
  });

  // Detect if user is already logged in
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) setMode("logout");
  }, []);

  // Handle form input changes
  const handleChange = (e) =>
    setFormData({ ...formData, [e.target.name]: e.target.value });

  // Notification helper
  const showNotify = (type, message) =>
    setNotification({ type, message, id: Date.now() });

  // ───── Login ─────
  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const data = new URLSearchParams();
      data.append("username", formData.username);
      data.append("password", formData.password);

      const res = await axios.post(`${API_BASE}/login`, data, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      localStorage.setItem("access_token", res.data.access_token);
      showNotify("success", "Login successful!");

      setTimeout(() => navigate(redirectAfterLogin, { replace: true }), 1000);
    } catch (err) {
      showNotify(
        "error",
        err.response?.data?.detail || "Invalid username or password."
      );
    }
  };

  // ───── Signup ─────
  const handleSignup = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword)
      return showNotify("error", "Passwords do not match!");

    try {
      await axios.post(`${API_BASE}/signup`, {
        username: formData.username,
        email: formData.email,
        password: formData.password,
      });
      showNotify("success", "Signup successful! Please login.");
      setMode("login");
    } catch (err) {
      showNotify(
        "error",
        err.response?.data?.detail || "Signup failed. Try again."
      );
    }
  };

  // ───── Forgot Password ─────
  const handleForgot = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE}/forgot-password`, {
        email: formData.email,
      });
      showNotify("success", "Password reset link sent to email!");
      setMode("reset");
    } catch (err) {
      showNotify("error", err.response?.data?.detail || "Failed to send email.");
    }
  };

  // ───── Reset Password ─────
  const handleReset = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE}/reset-password`, {
        token: formData.token,
        new_password: formData.password,
      });
      showNotify("success", "Password reset successful! Please login.");
      setMode("login");
    } catch (err) {
      showNotify("error", err.response?.data?.detail || "Reset failed.");
    }
  };

  // ───── Logout ─────
  const handleLogout = async () => {
    try {
      localStorage.removeItem("access_token");
      localStorage.removeItem("userInfo");
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

  // ───── Render Form ─────
  const renderForm = () => {
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
              <span onClick={() => setMode("signup")}>Sign up</span>
            </p>
            <p>
              <span onClick={() => setMode("forgot")}>Forgot password?</span>
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
            <button type="submit">Sign Up</button>
            <p>
              Already have an account?{" "}
              <span onClick={() => setMode("login")}>Login</span>
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
              <span onClick={() => setMode("login")}>Login</span>
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
            <button type="submit">Reset Password</button>
            <p>
              Back to{" "}
              <span onClick={() => setMode("login")}>Login</span>
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
              <span onClick={() => navigate("/")}>Cancel</span>
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

