import React, { useEffect, useState, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import Notification from "../../Notification/Notification";
import styles from './PatientMedicalHistory.module.css';

const API_BASE = "http://localhost:8000/api";

// Util to extract filename from Content-Disposition header
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

const downloadFile = async (url, token, onError) => {
  try {
    const response = await axios.get(url, {
      headers: { Authorization: `Bearer ${token}` },
      responseType: "blob",
    });
    const filename = getFilenameFromResponse(response);
    const blob = new Blob([response.data], { type: response.headers["content-type"] });
    const fileURL = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = fileURL;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => window.URL.revokeObjectURL(fileURL), 500);
    onError("Download started", "success", 2000);
  } catch (err) {
    const code = err?.response?.status;
    if (code === 401) onError("Session expired. Redirecting to login...", "error", 4000, code);
    else onError("File could not be downloaded.", "error");
  }
};

const MedicalHistoryDetailsModal = ({ history, onClose, token, onNotify }) => {
  if (!history) return null;

  const handleFileAction = async (field, type) => {
    const fileId = history.history_id;
    let endpoint;
    if (field === "document") endpoint = `${API_BASE}/file/document/${fileId}?download=${type === "download"}`;
    else endpoint = `${API_BASE}/file/image/${fileId}?download=${type === "download"}`;
    await downloadFile(endpoint, token, onNotify);
  };

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <div style={{fontWeight:"700", color:"var(--primary-light)"}}>Medical History Details</div>
          <button className={styles.modalCloseBtn} onClick={onClose}>&times;</button>
        </div>
        <div className={styles.modalBody}>
          <section>
            <b>Diagnosis:</b> {history.diagnosis || "-"}<br/>
            <b>Medicines:</b> {history.medicines || "-"}<br/>
            <b>Surgery Notes:</b> {history.surgery_notes || "-"}<br/>
            <b>Test Results:</b> {history.test_results || "-"}<br/>
            <b>Visit Date:</b> {history.visit_date ? new Date(history.visit_date).toLocaleDateString() : "-"}<br/>
            <b>Latitude/Longitude:</b> {history.latitude}, {history.longitude}
          </section>
          <section>
            <b>Patient Name:</b> {history.patient?.name || "-"}<br/>
            <b>Patient Age/Gender:</b> {history.patient?.age || "-"} / {history.patient?.gender || "-"}<br/>
            <b>Patient Email:</b> {history.patient?.email || "-"}<br/>
            <b>Patient Phone:</b> {history.patient?.phone || "-"}<br/>
            <b>Patient Address:</b> {history.patient?.address || "-"}
          </section>
          <section>
            <b>Doctor Name:</b> {history.doctor?.name || "-"}<br/>
            <b>Doctor Specialization:</b> {history.doctor?.specialization || "-"}<br/>
            <b>Doctor Contact:</b> {history.doctor?.contact_phone || "-"}<br/>
            <b>Clinic Name:</b> {history.doctor?.clinic_name || "-"}<br/>
            <b>Clinic Address:</b> {history.doctor?.clinic_address || "-"}
          </section>
          <section className={styles.filesSection}>
            <div className={styles.fileDetailGroup}>
              <b>Document:</b>
              {history.document_file ? (
                <>
                  <button className={`${styles.fileBtn} ${styles.fileBtnView}`} onClick={() => handleFileAction("document", "view")}>View</button>
                  <button className={`${styles.fileBtn} ${styles.fileBtnDownload}`} onClick={() => handleFileAction("document", "download")}>Download</button>
                </>
              ) : <span className={styles.noFileText}>No document</span>}
            </div>
            <div className={styles.fileDetailGroup}>
              <b>Image:</b>
              {history.image_file ? (
                <>
                  <button className={`${styles.fileBtn} ${styles.fileBtnView}`} onClick={() => handleFileAction("image", "view")}>View</button>
                  <button className={`${styles.fileBtn} ${styles.fileBtnDownload}`} onClick={() => handleFileAction("image", "download")}>Download</button>
                </>
              ) : <span className={styles.noFileText}>No image</span>}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default function PatientMedicalHistory() {
  const [histories, setHistories] = useState([]);
  const [search, setSearch] = useState("");
  const [selectedHistory, setSelectedHistory] = useState(null);
  const [notification, setNotification] = useState(null);
  const token = localStorage.getItem("access_token");
  const navigate = useNavigate();
  const location = useLocation();

  // Auto-redirect after login
  useEffect(() => {
    const redirectPath = localStorage.getItem('redirectPath');
    if (token && redirectPath) {
      localStorage.removeItem('redirectPath');
      navigate(redirectPath, { replace: true });
      setNotification({ message: "Login successful. Resuming session.", type: "success" });
    }
  }, [token, navigate]);

  // Show notification and handle error/redirect
  const showNotification = useCallback((message, type = "info", duration = 3000, code = null) => {
    setNotification({ message, type, duration });
    if (code === 401) {
      setTimeout(() => {
        // Redirect after notification to login and preserve return path
        localStorage.setItem('redirectPath', location.pathname + location.search);
        navigate("/auth");
      }, 1200);
    }
  }, [navigate, location]);

  // Fetch histories with error/401 handling
  const fetchHistories = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/get_all/medical_history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHistories(res.data);
    } catch (err) {
      const code = err?.response?.status;
      if (code === 401) {
        showNotification("Session expired. Redirecting to login...", "error", 3500, code);
      } else {
        showNotification("Unable to load your medical histories.", "error");
      }
    }
  }, [token, showNotification]);

  useEffect(() => { if (token) fetchHistories(); }, [token, fetchHistories]);

  const filteredHistories = search.trim()
    ? histories.filter(h =>
      (h.diagnosis || "").toLowerCase().includes(search.toLowerCase())
      || (h.patient?.name || "").toLowerCase().includes(search.toLowerCase())
      || (h.patient?.email || "").toLowerCase().includes(search.toLowerCase())
      || (h.doctor?.name || "").toLowerCase().includes(search.toLowerCase())
      || (h.doctor?.clinic_name || "").toLowerCase().includes(search.toLowerCase()))
    : histories;

  const closeNotification = useCallback(() => setNotification(null), []);

  return (
    <div className={styles.historyContainer}>
      <div className={styles.headerTitle}>Your Medical History</div>
      {notification && (
        <Notification
          message={notification.message}
          type={notification.type}
          duration={notification.duration || 3500}
          onClose={closeNotification}
        />
      )}

      <div className={styles.tableSection}>
        <div className={styles.tableHeader}>
          <div className={styles.headerTitle}>All Records</div>
          <input
            className={styles.searchBox}
            placeholder="Search diagnosis, patient, or doctor"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div className={styles.tableWrapper}>
          <table className={styles.historiesTable}>
            <thead>
              <tr>
                <th>Visit Date</th>
                <th>Diagnosis</th>
                <th>Doctor</th>
                <th>Medicines</th>
                <th>Documents</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredHistories.length ? filteredHistories.map(h => (
                <tr key={h.history_id}>
                  <td data-label="Visit Date">{h.visit_date ? new Date(h.visit_date).toLocaleDateString() : "-"}</td>
                  <td data-label="Diagnosis">{h.diagnosis || "-"}</td>
                  <td data-label="Doctor">{h.doctor?.name || "-"}</td>
                  <td data-label="Medicines">{h.medicines || "-"}</td>
                  <td data-label="Documents">
                    <div className={styles.fileActionLinks}>
                      {h.document_file && (
                        <button className={`${styles.fileBtn} ${styles.fileBtnView}`}
                                onClick={() => downloadFile(`${API_BASE}/file/document/${h.history_id}?download=true`, token, showNotification)}>
                          PDF
                        </button>
                      )}
                      {h.image_file && (
                        <button className={`${styles.fileBtn} ${styles.fileBtnView}`}
                                onClick={() => downloadFile(`${API_BASE}/file/image/${h.history_id}?download=true`, token, showNotification)}>
                          Img
                        </button>
                      )}
                      {(!h.document_file && !h.image_file) && "-"}
                    </div>
                  </td>
                  <td data-label="Actions">
                    <div className={styles.actionButtonsGroup}>
                      <button className={`${styles.btn} ${styles.btnViewDetails}`} onClick={() => setSelectedHistory(h)}>
                        Details
                      </button>
                    </div>
                  </td>
                </tr>
              )) :
                <tr>
                  <td colSpan={6} className={styles.noDataText}>No records found</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>

      {selectedHistory && (
        <MedicalHistoryDetailsModal
          history={selectedHistory}
          onClose={() => setSelectedHistory(null)}
          token={token}
          onNotify={showNotification}
        />
      )}
    </div>
  );
}
