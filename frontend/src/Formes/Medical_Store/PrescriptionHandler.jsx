import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { useNavigate, useLocation } from "react-router-dom";
import {
  FileText,
  Store,
  Upload,
  Eye,
  Trash2,
  CheckCircle,
  Loader2,
} from "lucide-react";
import Notification from "../../Notification/Notification";
import "./PrescriptionHandler.css";

const API_BASE = "http://localhost:8000/api/medical_store";

const getAuthHeaders = () => {
  const token = localStorage.getItem("access_token");
  return {
    headers: { Authorization: `Bearer ${token}` },
  };
};

const PrescriptionHandler = () => {
  const [activeTab, setActiveTab] = useState("upload");
  const [responses, setResponses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [doctorName, setDoctorName] = useState("");
  const [notes, setNotes] = useState("");
  const [file, setFile] = useState(null);
  const [creating, setCreating] = useState(false);
  const [notification, setNotification] = useState({
    message: "",
    type: "info",
  });
  const navigate = useNavigate();
  const location = useLocation();

  // --- Axios 401 Interceptor (setup on mount only once) ---
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response && error.response.status === 401) {
          setNotification({ message: "Session expired. Please login again.", type: "warning" });
          localStorage.setItem("redirectAfterLogin", location.pathname);
          localStorage.removeItem("access_token"); // Optional: clear expired
          setTimeout(() => {
            navigate("/auth", { state: { from: location } });
          }, 1400); // Show warning briefly before redirect
        }
        return Promise.reject(error);
      }
    );
    return () => axios.interceptors.response.eject(interceptor);
  }, [navigate, location]);

  // --- Notification Handler ---
  const showNotification = useCallback((message, type = "info") => {
    setNotification({ message, type });
  }, []);

  // --- Fetch prescription responses ---
  useEffect(() => {
    const fetchResponses = async () => {
      setLoading(true);
      try {
        const res = await axios.get(
          `${API_BASE}/all_chemist/my_responses`,
          getAuthHeaders()
        );
        setResponses(res.data || []);
      } catch (err) {
        showNotification("Failed to fetch responses.", "error");
      } finally {
        setLoading(false);
      }
    };
    fetchResponses();
  }, [showNotification]);

  // --- Create Prescription ---
  const handleCreatePrescription = async (e) => {
    e.preventDefault();
    if (!file) {
      showNotification("Please upload a prescription file.", "warning");
      return;
    }

    const formData = new FormData();
    formData.append("doctor_name", doctorName);
    formData.append("notes", notes);
    formData.append("file", file);

    setCreating(true);
    try {
      await axios.post(`${API_BASE}/prescription`, formData, {
        ...getAuthHeaders(),
        headers: {
          ...getAuthHeaders().headers,
          "Content-Type": "multipart/form-data",
        },
      });
      showNotification("✅ Prescription uploaded successfully!", "success");
      setDoctorName("");
      setNotes("");
      setFile(null);
      setActiveTab("responses");
      setTimeout(() => window.location.reload(), 1000); // Wait for user to read notification
    } catch (err) {
      showNotification("❌ Failed to upload prescription. Try again.", "error");
    } finally {
      setCreating(false);
    }
  };

  // --- View prescription file ---
  const handleViewPrescription = (prescription_id) => {
    const token = localStorage.getItem("access_token");
    const url = `${API_BASE}/prescription/${prescription_id}/document?token=${token}`;
    window.open(url, "_blank");
  };

  // --- Assign Store ---
  const handleAssignStore = async (prescriptionId, storeId) => {
    try {
      await axios.post(
        `${API_BASE}/assign-store?prescription_id=${prescriptionId}&store_id=${storeId}`,
        null,
        getAuthHeaders()
      );
      showNotification("🏪 Store assigned successfully!", "success");
      setResponses((prev) =>
        prev.map((r) =>
          r.prescription_id === prescriptionId ? { ...r, status: "ASSIGNED" } : r
        )
      );
    } catch (err) {
      showNotification(
        err.response?.data?.detail || "❌ Failed to assign store.",
        "error"
      );
    }
  };

  // --- Delete Prescription ---
  const handleDeletePrescription = async (prescription_id) => {
    if (!window.confirm("Delete this prescription permanently?")) return;
    try {
      await axios.delete(
        `${API_BASE}/prescription_delete/${prescription_id}`,
        getAuthHeaders()
      );
      showNotification("🗑️ Prescription deleted!", "success");
      setResponses((prev) =>
        prev.filter((r) => r.prescription_id !== prescription_id)
      );
    } catch (err) {
      showNotification(
        err.response?.data?.detail || "❌ Failed to delete prescription.",
        "error"
      );
    }
  };

  if (loading)
    return (
      <div className="loader">
        <Loader2 className="spin" /> Loading prescriptions...
      </div>
    );

  return (
    <div className="prescription-container">
      <Notification
        message={notification.message}
        type={notification.type}
        onClose={() => setNotification({ message: "", type: "info" })}
      />

      <h1 className="page-title">
        <FileText size={26} /> Prescription Portal
      </h1>

      {/* Tabs */}
      <div className="tabs">
        <button
          className={activeTab === "upload" ? "tab active" : "tab"}
          onClick={() => setActiveTab("upload")}
        >
          <Upload size={18} /> Upload Prescription
        </button>
        <button
          className={activeTab === "responses" ? "tab active" : "tab"}
          onClick={() => setActiveTab("responses")}
        >
          <Store size={18} /> Store Responses
        </button>
      </div>

      {/* Upload Tab */}
      {activeTab === "upload" && (
        <div className="tab-content fade-in">
          <form className="upload-form" onSubmit={handleCreatePrescription}>
            <h2>
              <Upload size={20} /> Upload New Prescription
            </h2>
            <input
              type="text"
              placeholder="Doctor Name"
              value={doctorName}
              onChange={(e) => setDoctorName(e.target.value)}
              required
            />
            <textarea
              placeholder="Notes for the chemist..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows="3"
            />
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={(e) => setFile(e.target.files[0])}
              required
            />
            <button type="submit" disabled={creating}>
              {creating ? <Loader2 className="spin" /> : "Submit Prescription"}
            </button>
          </form>
        </div>
      )}

      {/* Responses Tab */}
      {activeTab === "responses" && (
        <div className="tab-content fade-in">
          {responses.length === 0 ? (
            <p className="no-data">No store responses yet.</p>
          ) : (
            <div className="response-grid">
              {responses.map((res) => (
                <div className="response-card" key={res.response_id}>
                  <div className="card-header">
                    <Store size={20} />
                    <h3>{res.store?.store_name || "Unknown Store"}</h3>
                  </div>

                  <p>
                    <strong>Owner:</strong> {res.store?.owner_name || "N/A"}
                  </p>
                  <p>
                    <strong>City:</strong> {res.store?.city || "N/A"}
                  </p>
                  <p>
                    <strong>Status:</strong>{" "}
                    <span
                      className={
                        res.status === "CONFIRMED"
                          ? "status-confirmed"
                          : "status-pending"
                      }
                    >
                      {res.status}
                    </span>
                  </p>
                  <p>
                    <strong>Message:</strong> {res.message || "No message"}
                  </p>
                  <p>
                    <strong>Items:</strong>{" "}
                    {res.available_items_json || "No details"}
                  </p>

                  <div className="btn-row">
                    <button
                      className="btn-view"
                      onClick={() =>
                        handleViewPrescription(res.prescription_id)
                      }
                    >
                      <Eye size={15} /> View
                    </button>
                    <button
                      className="btn-assign"
                      onClick={() =>
                        handleAssignStore(res.prescription_id, res.store_id)
                      }
                    >
                      <CheckCircle size={15} /> Assign
                    </button>
                    <button
                      className="btn-delete"
                      onClick={() =>
                        handleDeletePrescription(res.prescription_id)
                      }
                    >
                      <Trash2 size={15} /> Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PrescriptionHandler;
