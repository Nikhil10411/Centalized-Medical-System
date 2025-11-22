import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  FileText,
  Store,
  MessageSquare,
  Trash2,
  XCircle,
  Eye,
  User,
  BriefcaseMedical,
  Edit2,
  ClipboardList,
  RefreshCw,
  Mail,
  Phone,
  Home,
} from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import styles from "./PrescriptionResponse.module.css";
import Notification from "../../Notification/Notification";

const API_BASE = "http://localhost:8000/api/medical_store";

// Create a reusable axios instance
const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

let interceptorSet = false;
const setupAxiosInterceptor = (navigate, location) => {
  if (interceptorSet) return;
  interceptorSet = true;

  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.setItem("redirectAfterLogin", location.pathname);
        localStorage.removeItem("access_token");
        navigate("/auth", { replace: true, state: { from: location } });
      }
      return Promise.reject(error);
    }
  );
};

const getAuthHeaders = () => {
  const token = localStorage.getItem("access_token");
  return {
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
  };
};

const getDocumentUrl = (prescriptionId) => {
  const token = localStorage.getItem("access_token");
  return `${API_BASE}/prescription/${prescriptionId}/document?token=${encodeURIComponent(token)}`;
};

const statusOptions = [
  { value: "CONFIRMED", label: "Confirmed" },
  { value: "PARTIAL", label: "Partial" },
  { value: "NOT AVAILABLE", label: "Not Available" },
];

const PrescriptionResponse = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [responses, setResponses] = useState([]);
  const [openRequests, setOpenRequests] = useState([]);
  const [assignedPrescriptions, setAssignedPrescriptions] = useState([]);
  const [storeId, setStoreId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeView, setActiveView] = useState("NewRequests");
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [formData, setFormData] = useState({
    prescription_id: "",
    status: "CONFIRMED",
    available_items_json: "",
    message: "",
  });
  const [pdfViewerOpen, setPdfViewerOpen] = useState(false);
  const [pdfUrlToView, setPdfUrlToView] = useState("");
  const [notification, setNotification] = useState({ message: "", type: "info" });

  useEffect(() => {
    setupAxiosInterceptor(navigate, location);
  }, [navigate, location]);

  const showNotification = (message, type = "info") => {
    setNotification({ message, type });
  };

  const handleError = (err, action) => {
    const msg = err.response?.data?.detail || `Failed to ${action}.`;
    setError(msg);
    showNotification(msg, "error");
    console.error(`${action} error:`, err.response || err);
  };

  const handleViewPdf = (id) => {
    setPdfUrlToView(getDocumentUrl(id));
    setPdfViewerOpen(true);
  };

  const fetchStoreResponses = async () => {
    try {
      setLoading(true);
      const storeRes = await api.get(`/prescriptions/assigned`, getAuthHeaders());
      const store = storeRes.data.length > 0 ? storeRes.data[0].store_id : null;
      if (store) {
        setStoreId(store);
        const res = await api.get(`/store/${store}`, getAuthHeaders());
        setResponses(res.data);
      }
    } catch (err) {
      handleError(err, "fetch store responses");
    } finally {
      setLoading(false);
    }
  };

  const fetchOpenRequests = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/chemist/open_prescriptions`, getAuthHeaders());
      setOpenRequests(res.data);
    } catch (err) {
      handleError(err, "fetch open prescriptions");
    } finally {
      setLoading(false);
    }
  };

  const fetchAssignedPrescriptions = async () => {
    try {
      const res = await api.get(`/prescriptions/assigned`, getAuthHeaders());
      setAssignedPrescriptions(res.data);
    } catch (err) {
      handleError(err, "fetch assigned prescriptions");
    }
  };

  useEffect(() => {
    if (activeView === "NewRequests") fetchOpenRequests();
    if (activeView === "MyResponses") fetchStoreResponses();
    if (activeView === "Assigned") fetchAssignedPrescriptions();
  }, [activeView]);

  const handleResponseForm = (pres) => {
    setFormData({
      prescription_id: pres.prescription_id,
      status: "CONFIRMED",
      available_items_json: "",
      message: "",
    });
    setIsFormOpen(true);
  };

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData((f) => ({ ...f, [name]: value }));
  };

  const handleSubmitResponse = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        prescription_id: formData.prescription_id,
        status: formData.status,
        available_items_json: formData.available_items_json,
        message: formData.message,
      };
      await api.post(`/response`, payload, getAuthHeaders());
      showNotification("✅ Quote submitted successfully!", "success");
      setIsFormOpen(false);
      fetchStoreResponses();
    } catch (err) {
      handleError(err, "submit response");
    }
  };

  const handleUpdateResponse = async (responseId) => {
    try {
      const payload = {
        prescription_id: formData.prescription_id,
        status: formData.status,
        available_items_json: formData.available_items_json,
        message: formData.message,
      };
      await api.put(`/response/${responseId}`, payload, getAuthHeaders());
      showNotification("✅ Response updated!", "success");
      fetchStoreResponses();
      setIsEditOpen(false);
    } catch (err) {
      handleError(err, "update response");
    }
  };

  const handleDeleteResponse = async (id) => {
    if (!window.confirm("Do you really want to delete this response?")) return;
    try {
      await api.delete(`/response/${id}`, getAuthHeaders());
      showNotification("🗑️ Response deleted successfully!", "success");
      fetchStoreResponses();
    } catch (err) {
      handleError(err, "delete response");
    }
  };

  return (
    <div className={styles.wrapper}>
      <h1 className={styles.heading}>
        <Store /> Chemist Prescription Dashboard
      </h1>

      <div className={styles.tabWrapper}>
        <button
          className={`${styles.tab} ${activeView === "NewRequests" ? styles.active : ""}`}
          onClick={() => setActiveView("NewRequests")}
        >
          New Requests ({openRequests.length})
        </button>
        <button
          className={`${styles.tab} ${activeView === "MyResponses" ? styles.active : ""}`}
          onClick={() => setActiveView("MyResponses")}
        >
          My Responses ({responses.length})
        </button>
        <button
          className={`${styles.tab} ${activeView === "Assigned" ? styles.active : ""}`}
          onClick={() => setActiveView("Assigned")}
        >
          Assigned Prescriptions ({assignedPrescriptions.length})
        </button>
      </div>

      {loading && (
        <p className={styles.loading}>
          <RefreshCw className={styles.spinner} /> Loading...
        </p>
      )}

      {error && <p className={styles.error}>{error}</p>}

      <Notification
        message={notification.message}
        type={notification.type}
        onClose={() => setNotification({ message: "", type: "info" })}
      />

      {activeView === "NewRequests" &&
        openRequests.map((r) => (
          <div key={r.prescription_id} className={styles.card}>
            <div className={styles.cardHeader}>
              <FileText /> {r.prescription_id.substring(0, 8)}...
            </div>
            <div className={styles.cardBody}>
              <p>
                <User /> <b>Patient:</b> {r.patient?.name || "Unknown"}
              </p>
              <p>
                <BriefcaseMedical /> <b>Doctor:</b> {r.doctor_name || "N/A"}
              </p>
            </div>
            <div className={styles.cardActions}>
              <button
                onClick={() => handleViewPdf(r.prescription_id)}
                className={styles.viewBtn}
              >
                <Eye size={16} /> View
              </button>
              <button
                onClick={() => handleResponseForm(r)}
                className={styles.respondBtn}
              >
                <MessageSquare size={16} /> Quote
              </button>
            </div>
          </div>
        ))}

      {activeView === "MyResponses" &&
        responses.map((res) => (
          <div key={res.response_id} className={styles.card}>
            <div className={styles.cardHeader}>
              <ClipboardList /> Response #{res.response_id.substring(0, 8)}
            </div>
            <p className={styles.message}>{res.message}</p>
            <div className={styles.cardActions}>
              <button
                onClick={() => handleDeleteResponse(res.response_id)}
                className={styles.deleteBtn}
              >
                <Trash2 size={16} /> Delete
              </button>
              <button
                onClick={() => {
                  setIsEditOpen(true);
                  // MAKE SURE ONLY THE REQUIRED RESPONSE FIELDS ARE IN THE FORM
                  setFormData({
                    prescription_id: res.prescription_id,
                    status: res.status,
                    available_items_json: res.available_items_json,
                    message: res.message
                  });
                }}
                className={styles.editBtn}
              >
                <Edit2 size={16} /> Edit
              </button>
            </div>
          </div>
        ))}

      {activeView === "Assigned" &&
        assignedPrescriptions.map((p) => (
          <div key={p.prescription_id} className={styles.card}>
            <div className={styles.cardHeader}>
              <FileText /> Prescription: {p.prescription_id.substring(0, 8)}...
            </div>
            <div className={styles.cardBody}>
              <p>
                <User /> <b>Patient:</b> {p.patient?.name || "N/A"}, Age: {p.patient?.age || "-"}, Gender: {p.patient?.gender || "-"}
              </p>
              <p>
                <BriefcaseMedical /> <b>Doctor:</b> {p.doctor_name || "N/A"}
              </p>
              <p>
                <b>Store Assigned:</b> {p.store_id || "N/A"}
              </p>
              {p.patient && (
                <div className={styles.patientDetails}>
                  <h4>Patient Details</h4>
                  <p>
                    <User /> <b>Name:</b> {p.patient.name}
                  </p>
                  <p>
                    <Mail /> <b>Email:</b> {p.patient.email}
                  </p>
                  <p>
                    <Phone /> <b>Phone:</b> {p.patient.phone}
                  </p>
                  <p>
                    <Home /> <b>Address:</b> {p.patient.address}
                  </p>
                  <p>
                    <b>Age:</b> {p.patient.age}, <b>Gender:</b> {p.patient.gender}
                  </p>
                </div>
              )}
              {p.customer && (
                <div className={styles.customerDetails}>
                  <h4>Customer Details</h4>
                  <p>
                    <User /> <b>Name:</b> {p.customer.name}
                  </p>
                  <p>
                    <Mail /> <b>Email:</b> {p.customer.email}
                  </p>
                  <p>
                    <Phone /> <b>Phone:</b> {p.customer.phone}
                  </p>
                  <p>
                    <Home /> <b>Address:</b> {p.customer.address}
                  </p>
                  <p>
                    <b>Age:</b> {p.customer.age}, <b>Gender:</b> {p.customer.gender}
                  </p>
                </div>
              )}
            </div>
            <div className={styles.cardActions}>
              <button
                onClick={() => handleViewPdf(p.prescription_id)}
                className={styles.viewBtn}
              >
                <Eye size={16} /> View PDF
              </button>
            </div>
          </div>
        ))}

      {(isFormOpen || isEditOpen) && (
        <div className={styles.modalOverlay}>
          <form
            className={styles.form}
            onSubmit={
              isFormOpen
                ? handleSubmitResponse
                : (e) => {
                    e.preventDefault();
                    handleUpdateResponse(formData.prescription_id);
                  }
            }
          >
            <button
              type="button"
              onClick={() => {
                setIsFormOpen(false);
                setIsEditOpen(false);
              }}
              className={styles.closeBtn}
            >
              <XCircle size={24} />
            </button>
            <h3>{isFormOpen ? "Submit Quote" : "Edit Response"}</h3>
            <label>
              Status:
              <select name="status" value={formData.status} onChange={handleFormChange} required>
                {statusOptions.map(opt => (
                  <option value={opt.value} key={opt.value}>{opt.label}</option>
                ))}
              </select>
            </label>
            <label>
              Available Items (as JSON):
              <textarea
                name="available_items_json"
                value={formData.available_items_json}
                onChange={handleFormChange}
                rows="4"
                required
              />
            </label>
            <label>
              Message:
              <textarea
                name="message"
                value={formData.message}
                onChange={handleFormChange}
                rows="3"
                required
              />
            </label>
            <div className={styles.formActions}>
              <button type="submit" className={styles.submitBtn}>
                {isFormOpen ? "Submit" : "Update"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsFormOpen(false);
                  setIsEditOpen(false);
                }}
                className={styles.cancelBtn}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {pdfViewerOpen && (
        <div className={styles.modalOverlay}>
          <div className={styles.pdfViewer}>
            <button
              onClick={() => setPdfViewerOpen(false)}
              className={styles.closeBtn}
            >
              <XCircle size={24} />
            </button>
            <h3 className={styles.viewerTitle}>Prescription Document</h3>
            <iframe
              src={pdfUrlToView}
              title="Prescription PDF"
              className={styles.pdfFrame}
              frameBorder="0"
            ></iframe>
          </div>
        </div>
      )}
    </div>
  );
};

export default PrescriptionResponse;
