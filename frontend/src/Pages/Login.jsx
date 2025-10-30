import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import Notification from "../Notification/Notification";
import "./Login.css";

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Get original destination path or fallback to home
  const from = location.state?.from || "/";

  const [formData, setFormData] = useState({ username: "", password: "" });
  const [notification, setNotification] = useState({ message: "", type: "" });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const encodedData = new URLSearchParams();
    encodedData.append("grant_type", "password");
    encodedData.append("username", formData.username);
    encodedData.append("password", formData.password);
    encodedData.append("scope", "");
    encodedData.append("client_id", "");
    encodedData.append("client_secret", "");

    try {
      const response = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: encodedData.toString(),
      });
      const data = await response.json();

      if (response.ok) {
        setNotification({ message: "✅ Login successful!", type: "success" });
        localStorage.setItem("access_token", data.access_token);
        setTimeout(() => {
          navigate(from, { replace: true });
        }, 1000);
      } else {
        setNotification({ message: data.detail || "❌ Login failed", type: "error" });
      }
    } catch {
      setNotification({ message: "🚨 Server error", type: "error" });
    }
  };

  return (
    <div className="login-container">
      {notification.message && (
        <Notification message={notification.message} type={notification.type} onClose={() => setNotification({ message: "", type: "" })} />
      )}
      <form className="login-form" onSubmit={handleSubmit}>
        <h2 className="login-heading">Login</h2>
        <div className="login-input-container">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            placeholder="Enter your username"
            required
          />
        </div>
        <div className="login-input-container">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Enter your password"
            required
          />
        </div>
        <button className="login-button" type="submit">
          Login
        </button>
      </form>
    </div>
  );
};

export default Login;

