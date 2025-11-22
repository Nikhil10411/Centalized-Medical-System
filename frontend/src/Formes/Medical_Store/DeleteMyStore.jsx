import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate, useLocation } from "react-router-dom"; // 👈 Import navigation hooks
import "./DeleteMyStore.css";
import Notification from "../../Notification/Notification";

const API_BASE = "http://localhost:8000/api/medical_store";

const DeleteMyStore = () => {
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState({ message: "", type: "" });
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [redirectPending, setRedirectPending] = useState(false); // 👈 New state for redirect

  const navigate = useNavigate();
  const location = useLocation();

  // --- Effect for Delayed Redirect (401 Handling) ---
  useEffect(() => {
    let timer;
    if (redirectPending) {
      timer = setTimeout(() => {
        // Redirect to auth page, passing current location for after login redirect
        navigate("/auth", { state: { from: location.pathname }, replace: true });
      }, 2500); // 2.5 second delay
    }
    return () => clearTimeout(timer);
  }, [redirectPending, navigate, location.pathname]);


  // --- Helper Function to Handle 401 and Redirect ---
  const handleUnauthorized = () => {
    setConfirmOpen(false); // Close modal immediately
    setNotification({
      message: "⚠️ Session expired. Please log in first to proceed. Redirecting...",
      type: "warning",
    });
    setRedirectPending(true); // Triggers the useEffect hook
  };


  // Show confirmation modal before actual delete
  const handleDeleteClick = () => {
    // Basic token check before showing modal
    if (!localStorage.getItem("access_token")) {
        handleUnauthorized();
        return;
    }
    setConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    setLoading(true);
    setNotification({ message: "", type: "" }); // Clear previous notifications

    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        handleUnauthorized();
        return;
      }
      
      const res = await axios.delete(`${API_BASE}/delete_me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      // Success: Clear token (optional, but recommended after successful profile/store deletion)
      // localStorage.removeItem("access_token"); 

      setNotification({ 
          message: res.data?.message || "✅ Store deleted successfully! You may need to log in again.", 
          type: "success" 
      });
      setConfirmOpen(false);
      
    } catch (error) {
      if (error.response && error.response.status === 401) {
        handleUnauthorized();
        return; // Stop execution
      }
      
      setNotification({ 
          message: error.response?.data?.detail || "❌ Error deleting store.", 
          type: "error" 
      });
      setConfirmOpen(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="delete-store-container">
      <Notification
        message={notification.message}
        type={notification.type}
        onClose={() => setNotification({ message: "", type: "" })}
        // Set higher duration for redirect message
        duration={notification.type === 'warning' && redirectPending ? 3000 : 4000}
      />
      
      <div className="delete-store-content">
        <h2>🗑️ Delete Your Medical Store</h2>
        <p className="delete-desc">
          Warning: Deleting your store is permanent and cannot be undone.
        </p>
        <button
          className="btn-delete-store"
          onClick={handleDeleteClick}
          disabled={loading || redirectPending} // 👈 Disable while redirecting
        >
          {loading ? "Deleting..." : "Delete Store"}
        </button>
      </div>

      {confirmOpen && (
        <div className="delete-confirm-modal">
          <div className="delete-confirm-box">
            <h4>Confirm Delete</h4>
            <p>Are you absolutely sure you want to delete your medical store? This action cannot be undone.</p>
            <button
              className="btn-confirm-delete"
              onClick={handleDeleteConfirm}
              disabled={loading}
            >
              Yes, Delete
            </button>
            <button
              className="btn-cancel-delete"
              onClick={() => setConfirmOpen(false)}
              disabled={loading}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DeleteMyStore;