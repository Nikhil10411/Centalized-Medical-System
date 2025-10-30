import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SignUp.css';
import Notification from '../Notification/Notification'; // ✅ import universal notification

const SignUp = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: '',
  });

  const [notification, setNotification] = useState({ message: '', type: '' });
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      setNotification({ message: '❌ Passwords do not match!', type: 'error' });
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: formData.username,
          email: formData.email,
          password: formData.password,
          confirm_password: formData.confirmPassword,
          role: formData.role.toUpperCase(),
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setNotification({
          message: `✅ ${formData.role} signup successful! Redirecting...`,
          type: 'success',
        });

        setFormData({
          username: '',
          email: '',
          password: '',
          confirmPassword: '',
          role: '',
        });

        setTimeout(() => {
          navigate('/log-in');
        }, 1500);
      } else {
        setNotification({
          message: `❌ Signup failed: ${data.detail || 'Unknown error'}`,
          type: 'error',
        });
      }
    } catch (error) {
      console.error('Signup error:', error);
      setNotification({ message: '🚨 Server error', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="signup-container">
      <form className="signup-form" onSubmit={handleSubmit}>
        <h2 className="signup-heading">Sign Up</h2>

        <div className="signup-input-container">
          <label htmlFor="username">Username</label>
          <input type="text" id="username" name="username"
            value={formData.username} onChange={handleChange} required autoFocus />
        </div>

        <div className="signup-input-container">
          <label htmlFor="email">Email</label>
          <input type="email" id="email" name="email"
            value={formData.email} onChange={handleChange} required />
        </div>

        <div className="signup-input-container">
          <label htmlFor="password">Password</label>
          <input type="password" id="password" name="password"
            value={formData.password} onChange={handleChange} required autoComplete="new-password" />
        </div>

        <div className="signup-input-container">
          <label htmlFor="confirmPassword">Confirm Password</label>
          <input type="password" id="confirmPassword" name="confirmPassword"
            value={formData.confirmPassword} onChange={handleChange} required autoComplete="new-password" />
        </div>

        <div className="signup-input-container">
          <label htmlFor="role">Select Role</label>
          <select id="role" name="role"
            value={formData.role} onChange={handleChange} required>
            <option value="">-- Select Role --</option>
            <option value="HOSPITAL_SUPER_ADMIN">Hospital Super Admin</option>
            <option value="CLINIC_SUPER_ADMIN">Clinic Super Admin</option>
            <option value="DOCTOR">Doctor</option>
            <option value="CHEMIST">CHEMIST</option>
            <option value="PATIENT">Patient</option>
            <option value="PHARMACY_SUPER_ADMIN">Pharmacy Super Admin</option>
            <option value="CHEMIST">Chemist</option>
            <option value="DISPENSARY_SUPER_ADMIN">Dispensary Super Admin</option>
          </select>
        </div>

        <button className="signup-button" type="submit" disabled={loading}>
          {loading ? 'Signing up...' : 'Sign Up'}
        </button>
      </form>

      {/* ✅ Universal notification */}
      <Notification
        message={notification.message}
        type={notification.type}
        onClose={() => setNotification({ message: '', type: '' })}
      />
    </div>
  );
};

export default SignUp;
