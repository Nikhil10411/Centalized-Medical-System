import React, { useEffect, useState, useRef, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import Notification from "../../Notification/Notification";
import styles from './PatientMedicalHistoryManagement.module.css';

const API_BASE = "http://127.0.0.1:8000/api";

// Helper to extract filename from response Content-Disposition header
const getFilenameFromResponse = (response) => {
  const contentDisposition = response.headers["content-disposition"];
  let filename = "downloaded_file";
  if (contentDisposition) {
    const filenameMatch = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
    if (filenameMatch != null && filenameMatch[1]) {
      filename = decodeURIComponent(filenameMatch[1].replace(/['"]/g, ""));
    }
  }
  return filename;
};

const downloadAuthenticatedFile = async (basePath, token, shouldDownload, onError) => {
  if (!basePath || !token) {
    onError("Cannot access file: Missing file path or authentication token.", "error");
    return;
  }
  const url = `${API_BASE}${basePath}?download=${shouldDownload}`; 
  try {
    const response = await axios.get(url, {
      headers: { Authorization: `Bearer ${token}` },
      responseType: "blob",
    });
    const mimeType = response.headers["content-type"] || "application/octet-stream";
    const filename = getFilenameFromResponse(response);
    const blob = new Blob([response.data], { type: mimeType });
    const fileURL = window.URL.createObjectURL(blob);

    if (shouldDownload) {
      const a = document.createElement("a");
      a.href = fileURL;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => window.URL.revokeObjectURL(fileURL), 100);
      onError("File download started.", "info");
    } else {
      const newWindow = window.open(fileURL, "_blank");
      if (newWindow) {
        newWindow.onload = () => window.URL.revokeObjectURL(fileURL);
        setTimeout(() => window.URL.revokeObjectURL(fileURL), 5000); 
      } else {
        window.URL.revokeObjectURL(fileURL);
        onError("File viewer pop-up was blocked. Please allow pop-ups or use download.", "warning");
      }
    }
  } catch (e) {
    console.error("File access error:", e.response || e);
    const status = e.response?.status;
    let message = "File access failed. Please try again.";
    if (status === 404) message = "File not found on the server.";
    else if (status === 403) message = "Access denied. You may not have permission to view this file.";
    else if (status === 401) message = "Authentication failed. Please log in again.";
    onError(message, status === 401 ? "error" : "warning");
    throw e;
  }
};

const handleAuthenticatedFileAction = async (fileUrl, token, action, onError) => {
  const shouldDownload = action === "download";
  try {
    await downloadAuthenticatedFile(fileUrl, token, shouldDownload, onError);
  } catch (e) {/* error handled inside */}
};

const MedicalHistoryDetailsModal = ({ history, onClose, token, onError }) => {
  if (!history) return null;

  const handleFileAction = async (type, action) => {
    const url = type === "document" ? history.document_file : history.image_file;
    if (url) await handleAuthenticatedFileAction(url, token, action, onError);
  };

  return (
    <div className={styles["modal-overlay"]} onClick={onClose}>
      <div className={styles["modal-content"]} onClick={e => e.stopPropagation()}>
        <div className={styles["modal-header"]}>
          <h2>Medical History Details</h2>
          <button className={styles["modal-close-btn"]} onClick={onClose}>&times;</button>
        </div>
        <div className={styles["modal-body"]}>
          <section className={styles["record-info"]}>
            <h3>📝 Record Information</h3>
            <p><b>Diagnosis:</b> {history.diagnosis || "N/A"}</p>
            <p><b>Medicines:</b> {history.medicines || "N/A"}</p>
            <p><b>Surgery Notes:</b> {history.surgery_notes || "N/A"}</p>
            <p><b>Test Results:</b> {history.test_results || "N/A"}</p>
            <p><b>Visit Date:</b> {history.visit_date ? new Date(history.visit_date).toLocaleDateString() : "N/A"}</p>
            <p><b>Location:</b> {history.latitude && history.longitude ? `${history.latitude}, ${history.longitude}` : "N/A"}</p>
          </section>
          <section className={styles["patient-info"]}>
            <h3>👤 Patient Information</h3>
            <p><b>Name:</b> {history.patient?.name || "N/A"}</p>
            <p><b>Age / Gender:</b> {history.patient ? `${history.patient.age || "-"} / ${history.patient.gender || "-"}` : "N/A"}</p>
            <p><b>Contact:</b> {history.patient?.email || history.patient?.phone || "N/A"}</p>
            <p><b>Address:</b> {history.patient?.address || "N/A"}</p>
          </section>
          <section className={styles["files-section"]}>
            <h3>📂 Attached Files</h3>
            <div className={styles["file-detail-group"]}>
              <b>Document File:</b>
              {history.document_file ? (
                <>
                  <button className={`${styles["file-btn"]} ${styles["file-btn-view"]}`}
                    onClick={() => handleFileAction("document", "view")}>📄 View</button>
                  <button className={`${styles["file-btn"]} ${styles["file-btn-download"]}`}
                    onClick={() => handleFileAction("document", "download")}>⬇️ Download</button>
                </>
              ) : <p className={styles["no-file-text"]}>No document file.</p>}
            </div>
            <div className={styles["file-detail-group"]}>
              <b>Image File:</b>
              {history.image_file ? (
                <>
                  <button className={`${styles["file-btn"]} ${styles["file-btn-view"]}`}
                    onClick={() => handleFileAction("image", "view")}>🖼️ View</button>
                  <button className={`${styles["file-btn"]} ${styles["file-btn-download"]}`}
                    onClick={() => handleFileAction("image", "download")}>⬇️ Download</button>
                </>
              ) : <p className={styles["no-file-text"]}>No image file.</p>}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

function PatientMedicalHistoryManagement() {
  const [histories, setHistories] = useState([]);
  const [search, setSearch] = useState("");
  const [editingHistory, setEditingHistory] = useState(null);
  const [selectedHistory, setSelectedHistory] = useState(null);
  const [formData, setFormData] = useState({
    patient_identifier: "",
    diagnosis: "", test_results: "", medicines: "",
    surgery_notes: "", latitude: "", longitude: "",
    document_file: null, image_file: null,
  });
  const [notification, setNotification] = useState(null); 
  const [isLocating, setIsLocating] = useState(false);

  const formRef = useRef(null);
  const documentFileRef = useRef(null);
  const imageFileRef = useRef(null);
  const token = localStorage.getItem("access_token");

  const navigate = useNavigate();
  const location = useLocation();

  const showNotification = useCallback((message, type = "info", duration = 3000) => {
    setNotification(null); 
    setNotification({ message, type, duration });
  }, []);
  const closeNotification = useCallback(() => { setNotification(null); }, []);

  const handleAPIError = useCallback((error, defaultMessage = "Operation failed.", successMessage = null) => {
    const status = error.response?.status;
    const message = error.response?.data?.detail || defaultMessage;
    if (status === 401) {
      localStorage.setItem('redirectPath', location.pathname + location.search);
      showNotification("Session expired. Redirecting to login...", "error", 5000);
      navigate("/auth"); 
    } else if (status >= 400 && status < 500) {
      showNotification(message, "warning");
    } else if (status >= 500) {
      showNotification(message, "error");
    } else if (successMessage) {
      showNotification(successMessage, "success");
    } else {
      showNotification(message, "error");
    }
  }, [navigate, location, showNotification]);

  useEffect(() => {
    const redirectPath = localStorage.getItem('redirectPath');
    if (token && redirectPath) { 
      localStorage.removeItem('redirectPath'); 
      navigate(redirectPath, { replace: true });
      showNotification("Login successful. Resuming session.", "success");
    }
  }, [navigate, token, showNotification]);

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      showNotification("Geolocation is not supported by your browser.", "warning");
      return;
    }
    setIsLocating(true);
    showNotification("Fetching clinic location...", "info");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setFormData((prev) => ({
          ...prev,
          latitude: position.coords.latitude.toFixed(6),
          longitude: position.coords.longitude.toFixed(6),
        }));
        setIsLocating(false);
        showNotification("Location successfully captured.", "success");
      },
      (error) => {
        setIsLocating(false);
        showNotification(`Location error: ${error.message}. Please enter manually.`, "error");
      },
      { enableHighAccuracy: false, timeout: 5000, maximumAge: 0 }
    );
  };

  const fetchHistories = async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${API_BASE}/get_all/medical_history`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setHistories(res.data);
    } catch (err) {
      handleAPIError(err, "Failed to fetch medical histories");
    }
  };

  useEffect(() => { fetchHistories(); }, [token]);

  const handleClearForm = () => {
    setEditingHistory(null);
    setFormData({
      patient_identifier: "", diagnosis: "", test_results: "", medicines: "",
      surgery_notes: "", latitude: "", longitude: "",
      document_file: null, image_file: null,
    });
    if (documentFileRef.current) documentFileRef.current.value = "";
    if (imageFileRef.current) imageFileRef.current.value = "";
  };

  const fetchSingleHistory = async (id) => {
    if (!token) return showNotification("Authentication token missing.", "warning");
    try {
      const res = await axios.get(`${API_BASE}/get_single_history/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setEditingHistory(res.data);
      formRef.current?.scrollIntoView({ behavior: "smooth" });
    } catch (error) {
      handleAPIError(error, "Failed to load history record");
    }
  };

  useEffect(() => {
    if (editingHistory) {
      setFormData({
        patient_identifier: "",
        diagnosis: editingHistory.diagnosis || "",
        test_results: editingHistory.test_results || "",
        medicines: editingHistory.medicines || "",
        surgery_notes: editingHistory.surgery_notes || "",
        latitude: editingHistory.latitude != null ? String(editingHistory.latitude) : "",
        longitude: editingHistory.longitude != null ? String(editingHistory.longitude) : "",
        document_file: null, image_file: null,
      });
      if (documentFileRef.current) documentFileRef.current.value = "";
      if (imageFileRef.current) imageFileRef.current.value = "";
    } else { handleClearForm(); }
  }, [editingHistory]);

  const handleChange = (e) => {
    const { name, value, files } = e.target;
    if (files) {
      setFormData((prev) => ({ ...prev, [name]: files[0] }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!token) return showNotification("Authentication token missing.", "error");
    const form = new FormData();
    if (!editingHistory && !formData.patient_identifier) {
      showNotification("Patient email or phone is required for new records", "warning");
      return;
    }
    Object.keys(formData).forEach((key) => {
      const value = formData[key];
      if (editingHistory && key === "patient_identifier") return;
      if (key === "document_file" || key === "image_file") {
        if (value) form.append(key, value);
      } else if (value !== null && value !== "") {
        form.append(key, value);
      }
    });
    try {
      const config = { headers: { Authorization: `Bearer ${token}` } };
      const url = editingHistory
        ? `${API_BASE}/update/${editingHistory.history_id}`
        : `${API_BASE}/create/medical_history`;
      const method = editingHistory ? axios.put : axios.post; 
      await method(url, form, config);
      showNotification(`History ${editingHistory ? "updated" : "created"} successfully!`, "success");
      handleClearForm();
      fetchHistories();
    } catch (error) {
      handleAPIError(error, "Operation failed. Check input data.");
    }
  };

  const handleDelete = async (id) => {
    if (!token) return showNotification("Authentication token missing.", "error");
    if (!window.confirm("Delete this medical history? This cannot be undone.")) return;
    try {
      await axios.delete(`${API_BASE}/delete/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      showNotification("Deleted successfully!", "success");
      fetchHistories();
    } catch (error) {
      handleAPIError(error, "Delete failed.");
    }
  };

  const handleFileAction = (baseFileUrl, action) => {
    if (!token) return showNotification("Authentication token missing.", "error");
    handleAuthenticatedFileAction(baseFileUrl, token, action, showNotification);
  };

  const filteredHistories = histories.filter((h) => {
    const lowerSearch = search.toLowerCase();
    const patientName = h.patient?.name ?? "";
    const patientId = h.patient_id ?? "";
    return (
      (h.diagnosis ?? "").toLowerCase().includes(lowerSearch) ||
      patientName.toLowerCase().includes(lowerSearch) ||
      patientId.toLowerCase().includes(lowerSearch)
    );
  });

  const handleViewDetails = (history) => setSelectedHistory(history);

  return (
    <div className={styles["history-container"]}>
      {notification && (
        <Notification {...notification} onClose={closeNotification} />
      )}

      <MedicalHistoryDetailsModal
        history={selectedHistory}
        onClose={() => setSelectedHistory(null)}
        token={token}
        onError={showNotification}
      />

      <div className={styles["content-grid"]}>
        {/* --- Form Section --- */}
        <div ref={formRef} className={`${styles["form-section"]} ${styles["card-style"]}`}>
          <h2 className={styles["text-primary-light"]}>{editingHistory ? "Update Medical History" : "Add New Medical History"}</h2>
          <form className={styles["history-form"]} onSubmit={handleSubmit}>
            <div className={styles["input-group"]}>
              {!editingHistory ? (
                <input
                  name="patient_identifier"
                  placeholder="Patient Email or Phone (Required for New)"
                  value={formData.patient_identifier}
                  onChange={handleChange}
                  className={styles["form-input-dark"]}
                  required={!editingHistory}
                />
              ) : (
                <input
                  name="patient_id_display"
                  placeholder="Patient ID"
                  value={`Patient: ${editingHistory.patient?.name || "N/A"}`}
                  className={styles["form-input-dark"]}
                  disabled
                />
              )}
              <input
                name="diagnosis"
                placeholder="Diagnosis"
                value={formData.diagnosis}
                onChange={handleChange}
                className={styles["form-input-dark"]}
              />
            </div>
            <div className={styles["input-group"]}>
              <textarea
                name="medicines"
                placeholder="Medicines Prescribed"
                value={formData.medicines}
                onChange={handleChange}
                className={styles["form-input-dark"]}
                rows={3}
              />
              <textarea
                name="surgery_notes"
                placeholder="Surgery Notes"
                value={formData.surgery_notes}
                onChange={handleChange}
                className={styles["form-input-dark"]}
                rows={3}
              />
            </div>
            <div className={styles["input-group"]}>
              <textarea
                name="test_results"
                placeholder="Test Results"
                value={formData.test_results}
                onChange={handleChange}
                className={styles["form-input-dark"]}
                rows={6}
              />
            </div>
            <div className={`${styles["input-group"]} ${styles["location-group"]}`}>
              <input
                name="latitude"
                placeholder="Latitude (Optional)"
                value={formData.latitude}
                onChange={handleChange}
                className={styles["form-input-dark"]}
                type="number"
                step="any"
              />
              <input
                name="longitude"
                placeholder="Longitude (Optional)"
                value={formData.longitude}
                onChange={handleChange}
                className={styles["form-input-dark"]}
                type="number"
                step="any"
              />
              <button
                type="button"
                onClick={handleGetLocation}
                className={styles["btn-get-location"]}
                disabled={isLocating}
              >
                {isLocating ? "Locating..." : "Get Clinic Location"}
              </button>
            </div>
            <div className={`${styles["input-group"]} ${styles["file-upload-group"]}`}>
              <div className={styles["file-section"]}>
                <label className={styles["file-label"]}>
                  Document File (PDF/Word):
                </label>
                {editingHistory?.document_file && (
                  <div className={styles["existing-file-link"]}>
                    <span>Existing Document</span>
                    <button
                      type="button"
                      className={`${styles["file-btn"]} ${styles["file-btn-view"]}`}
                      onClick={() => handleFileAction(editingHistory.document_file, "view")}
                    >📄 View</button>
                    <button
                      type="button"
                      className={`${styles["file-btn"]} ${styles["file-btn-download"]}`}
                      onClick={() => handleFileAction(editingHistory.document_file, "download")}
                    >⬇️</button>
                    <span className={styles["replace-text"]}>| Replace:</span>
                  </div>
                )}
                <input
                  type="file"
                  name="document_file"
                  onChange={handleChange}
                  ref={documentFileRef}
                />
              </div>
              <div className={styles["file-section"]}>
                <label className={styles["file-label"]}>
                  Image File (JPEG/PNG):
                </label>
                {editingHistory?.image_file && (
                  <div className={styles["existing-file-link"]}>
                    <span>Existing Image</span>
                    <button
                      type="button"
                      className={`${styles["file-btn"]} ${styles["file-btn-view"]}`}
                      onClick={() => handleFileAction(editingHistory.image_file, "view")}
                    >🖼️ View</button>
                    <button
                      type="button"
                      className={`${styles["file-btn"]} ${styles["file-btn-download"]}`}
                      onClick={() => handleFileAction(editingHistory.image_file, "download")}
                    >⬇️</button>
                    <span className={styles["replace-text"]}>| Replace:</span>
                  </div>
                )}
                <input
                  type="file"
                  name="image_file"
                  onChange={handleChange}
                  ref={imageFileRef}
                />
              </div>
            </div>
            <div className={`${styles["button-group"]} ${styles["form-actions"]}`}>
              {editingHistory && (
                <button
                  type="button"
                  onClick={handleClearForm}
                  className={styles["btn-secondary"]}
                >
                  Cancel Update
                </button>
              )}
              <button type="submit" className={styles["btn-primary"]}>
                {editingHistory ? "Update Record" : "Add Record"}
              </button>
            </div>
          </form>
        </div>
        {/* --- End Form Section --- */}

        {/* --- Table Section --- */}
        <div className={`${styles["table-section"]} ${styles["card-style"]}`}>
          <div className={styles["table-header"]}>
            <h2 className={styles["text-primary-light"]}>All Patient Records</h2>
            <input
              type="text"
              className={`${styles["search"]} ${styles["form-input-dark"]}`}
              placeholder="Search diagnosis, patient name or ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className={styles["table-wrapper"]}>
            <table className={styles["histories-table"]}>
              <thead className={styles["table-header-bg"]}>
                <tr>
                  <th>Visit Date</th>
                  <th>Diagnosis</th>
                  <th>Patient Name</th>
                  <th>Age / Gender</th>
                  <th>Medicines</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredHistories.length > 0 ? (
                  filteredHistories.map((h) => (
                    <tr key={h.history_id}>
                      <td data-label="Visit Date">{h.visit_date ? new Date(h.visit_date).toLocaleDateString() : "-"}</td>
                      <td data-label="Diagnosis">{h.diagnosis || "-"}</td>
                      <td data-label="Patient Name">{h.patient?.name || "N/A"}</td>
                      <td data-label="Age / Gender">{h.patient?.age || "-"} / {h.patient?.gender || "-"}</td>
                      <td data-label="Medicines">{h.medicines || "-"}</td>
                      <td data-label="Files" className={styles["file-action-links"]}>
                        {h.document_file && (
                          <div className={styles["file-group"]}>
                            <button className={`${styles["file-btn"]} ${styles["file-btn-view"]}`}
                              onClick={() => handleFileAction(h.document_file, "view")}>📄</button>
                            <button className={`${styles["file-btn"]} ${styles["file-btn-download"]}`}
                              onClick={() => handleFileAction(h.document_file, "download")}>⬇️</button>
                          </div>
                        )}
                        {h.image_file && (
                          <div className={styles["file-group"]}>
                            <button className={`${styles["file-btn"]} ${styles["file-btn-view"]}`}
                              onClick={() => handleFileAction(h.image_file, "view")}>🖼️</button>
                            <button className={`${styles["file-btn"]} ${styles["file-btn-download"]}`}
                              onClick={() => handleFileAction(h.image_file, "download")}>⬇️</button>
                          </div>
                        )}
                        {!h.document_file && !h.image_file && <span>-</span>}
                      </td>
                      <td data-label="Actions" className={styles["action-buttons-group"]}>
                        <button className={styles["btn-view-details"]} onClick={() => handleViewDetails(h)}>Details</button>
                        <button className={styles["btn-edit"]} onClick={() => fetchSingleHistory(h.history_id)}>Edit</button>
                        <button className={styles["btn-delete"]} onClick={() => handleDelete(h.history_id)}>Delete</button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr><td colSpan={7} className={styles["no-data-text"]}>No medical histories found.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
        {/* --- End Table Section --- */}
      </div>
    </div>
  );
}

export default PatientMedicalHistoryManagement;
