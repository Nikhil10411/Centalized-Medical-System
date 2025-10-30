import React, { useState, useEffect } from "react";
import "./PatientManagement.css";
import axios from "axios";
import Notification from "../../Notification/Notification"; // Adjust the import as needed

const API_BASE = "http://127.0.0.1:8000/api"; // Adjust if your backend runs elsewhere

const initialForm = {
  name: "",
  email: "",
  phone: "",
  age: "",
  gender: "",
  city: "",
  state: "",
  address: "",
  pin_code: "",
};

const PatientManagement = () => {
  const [patients, setPatients] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [notification, setNotification] = useState({ message: "", type: "" });

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await axios.get(`${API_BASE}/get_all_patients/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setPatients(res.data);
    } catch (err) {
      showNotification("Failed to fetch patients.", "error");
    }
  };

  const showNotification = (message, type = "info") => {
    setNotification({ message, type });
    setTimeout(() => setNotification({ message: "", type: "" }), 4000);
  };

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("access_token");
      if (editingId) {
        await axios.put(`${API_BASE}/patients/${editingId}`, form, {
          headers: { Authorization: `Bearer ${token}` },
        });
        showNotification("Patient updated successfully!", "success");
      } else {
        await axios.post(`${API_BASE}/patients/`, form, {
          headers: { Authorization: `Bearer ${token}` },
        });
        showNotification("Patient added successfully!", "success");
      }
      setForm(initialForm);
      setEditingId(null);
      fetchPatients();
    } catch (err) {
      showNotification(err.response?.data?.detail || "Operation failed.", "error");
    }
  };

  const handleEdit = (patient) => {
    setForm({
      name: patient.name || "",
      email: patient.email || "",
      phone: patient.phone || "",
      age: patient.age || "",
      gender: patient.gender || "",
      city: patient.city || "",
      state: patient.state || "",
      address: patient.address || "",
      pin_code: patient.pin_code || "",
    });
    setEditingId(patient.patient_id);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete?")) return;
    try {
      const token = localStorage.getItem("access_token");
      await axios.delete(`${API_BASE}/patients/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      showNotification("Patient deleted successfully!", "success");
      fetchPatients();
    } catch (err) {
      showNotification("Delete failed.", "error");
    }
  };

  const handleCancelEdit = () => {
    setForm(initialForm);
    setEditingId(null);
  };

  return (
    <div className="pm-container">
      <h2 className="pm-title">Patient Management</h2>
      <Notification
        type={notification.type}
        message={notification.message}
        duration={4000}
      />
      <form className="pm-form" onSubmit={handleSubmit}>
        <input
          name="name"
          placeholder="Full Name"
          value={form.name}
          onChange={handleChange}
          required
          className="pm-input"
        />
        <input
          name="email"
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={handleChange}
          className="pm-input"
        />
        <input
          name="phone"
          type="tel"
          placeholder="Phone"
          value={form.phone}
          onChange={handleChange}
          className="pm-input"
        />
        <input
          name="age"
          type="number"
          placeholder="Age"
          value={form.age}
          onChange={handleChange}
          className="pm-input"
          min="0"
        />
        <select
          name="gender"
          value={form.gender}
          onChange={handleChange}
          className="pm-input"
        >
          <option value="">Gender</option>
          <option value="female">Female</option>
          <option value="male">Male</option>
          <option value="other">Other</option>
        </select>
        <input
          name="city"
          placeholder="City"
          value={form.city}
          onChange={handleChange}
          className="pm-input"
        />
        <input
          name="state"
          placeholder="State"
          value={form.state}
          onChange={handleChange}
          className="pm-input"
        />
        <input
          name="address"
          placeholder="Address"
          value={form.address}
          onChange={handleChange}
          className="pm-input"
        />
        <input
          name="pin_code"
          placeholder="Pin Code"
          value={form.pin_code}
          onChange={handleChange}
          className="pm-input"
        />
        <button
          type="submit"
          className="pm-btn pm-btn-primary"
        >
          {editingId ? "Update" : "Create"}
        </button>
        {editingId && (
          <button
            type="button"
            className="pm-btn pm-btn-secondary"
            onClick={handleCancelEdit}
          >
            Cancel
          </button>
        )}
      </form>
      <table className="pm-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Age</th>
            <th>Gender</th>
            <th>City</th>
            <th>State</th>
            <th>Address</th>
            <th>Pin</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {patients.map((patient) => (
            <tr key={patient.patient_id}>
              <td>{patient.name}</td>
              <td>{patient.email}</td>
              <td>{patient.phone}</td>
              <td>{patient.age}</td>
              <td>{patient.gender}</td>
              <td>{patient.city}</td>
              <td>{patient.state}</td>
              <td>{patient.address}</td>
              <td>{patient.pin_code}</td>
              <td>
                <button
                  className="pm-btn pm-btn-edit"
                  onClick={() => handleEdit(patient)}
                >
                  Edit
                </button>
                <button
                  className="pm-btn pm-btn-delete"
                  onClick={() => handleDelete(patient.patient_id)}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PatientManagement;
