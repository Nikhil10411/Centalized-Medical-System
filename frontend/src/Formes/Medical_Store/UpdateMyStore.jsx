import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate, useLocation } from "react-router-dom"; // Import necessary hooks
import "./UpdateMyStore.css";
import Notification from "../../Notification/Notification";

const UpdateMyStore = () => {
  // --- Form State ---
  const [formData, setFormData] = useState({
    store_name: "",
    owner_name: "",
    age: "",
    gender: "",
    store_type: "",
    address: "",
    city: "",
    locality: "",
    pin_code: "",
    phone: "",
    email: "",
    open_hours: "",
    delivery_radius_km: "",
    latitude: "",
    longitude: "",
  });

  // --- File State ---
  const [licenseDocument, setLicenseDocument] = useState(null);
  const [storePhoto, setStorePhoto] = useState(null);
  const [licenseDocPreview, setLicenseDocPreview] = useState(null);
  const [storePhotoPreview, setStorePhotoPreview] = useState(null);

  // --- UI/Control State ---
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState({ message: "", type: "" });
  const [redirectPending, setRedirectPending] = useState(false); // New state for redirect

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
    setNotification({
      message: "⚠️ Please log in first to manage your store. Redirecting...",
      type: "warning",
    });
    setRedirectPending(true); // Triggers the useEffect hook
  };

  // --- Fetch current store data to prefill form and previews ---
  useEffect(() => {
    const fetchMyStore = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
            handleUnauthorized();
            return;
        }

        const res = await axios.get("http://127.0.0.1:8000/medical_store/update", {
          headers: { Authorization: `Bearer ${token}` },
        });

        // Map data to formData state
        setFormData({
          store_name: res.data.store_name || "",
          owner_name: res.data.owner_name || "",
          age: res.data.age || "",
          gender: res.data.gender || "",
          store_type: res.data.store_type || "",
          address: res.data.address || "",
          city: res.data.city || "",
          locality: res.data.locality || "",
          pin_code: res.data.pin_code || "",
          phone: res.data.phone || "",
          email: res.data.email || "",
          open_hours: res.data.open_hours || "",
          delivery_radius_km: res.data.delivery_radius_km || "",
          latitude: res.data.latitude || "",
          longitude: res.data.longitude || "",
        });

        // Set previews from base64 strings if available
        if (res.data.license_document) {
          setLicenseDocPreview(
            `data:${res.data.license_mime || 'application/pdf'};base64,${res.data.license_document}`
          );
        }
        if (res.data.store_photo) {
          setStorePhotoPreview(
            `data:${res.data.photo_mime || 'image/jpeg'};base64,${res.data.store_photo}`
          );
        }

        setNotification({ message: "Store data loaded", type: "success" });
      } catch (err) {
        if (err.response && err.response.status === 401) {
          handleUnauthorized();
          return; // Stop execution
        }
        setNotification({
          message: "⚠️ Could not fetch store details.",
          type: "warning",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchMyStore();
    // Added redirectPending to prevent fetching after starting redirect
  }, [location.pathname, redirectPending]); 

  // --- Input Change Handlers ---
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e, setter, previewSetter) => {
    const file = e.target.files[0];
    if (file) {
      setter(file);

      // Create preview for image files only
      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onloadend = () => {
          previewSetter(reader.result);
        };
        reader.readAsDataURL(file);
      } else {
        // For non-image files like license PDF, show file name or null preview
        previewSetter(file.name); 
      }
    }
  };

  // --- Location Handler ---
  const handleUseLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setFormData((prev) => ({
            ...prev,
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
          }));
          setNotification({
            message: "📍 Using your current location.",
            type: "info",
          });
        },
        () => {
          setNotification({
            message: "❌ Unable to fetch location. Please check browser permissions.",
            type: "error",
          });
        }
      );
    }
  };

  // --- Form Reset ---
  const clearForm = () => {
    // Note: Instead of clearing, a better approach after update is usually to refetch the fresh data.
    // However, sticking to your provided logic:
    // This function will cause form fields to blank out immediately after update.
    setFormData({
      store_name: "", owner_name: "", age: "", gender: "", store_type: "",
      address: "", city: "", locality: "", pin_code: "", phone: "",
      email: "", open_hours: "", delivery_radius_km: "", latitude: "",
      longitude: "",
    });
    setLicenseDocument(null);
    setStorePhoto(null);
    setLicenseDocPreview(null);
    setStorePhotoPreview(null);
  };

  // --- Submit Update Form Data ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const data = new FormData();
      Object.entries(formData).forEach(([key, value]) => {
        // Only append values that are not empty strings or null
        if (value !== "" && value !== null) {
          data.append(key, value);
        }
      });

      // Append files only if they were newly selected
      if (licenseDocument) data.append("license_document", licenseDocument);
      if (storePhoto) data.append("store_photo", storePhoto);

      const token = localStorage.getItem("access_token");
      if (!token) {
        handleUnauthorized();
        return;
      }
      
      const res = await axios.put("http://127.0.0.1:8000/medical_store/update", data, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data",
        },
      });

      setNotification({ message: "✅ Store updated successfully!", type: "success" });
      
      // OPTIONAL: Clear the form or Refetch the updated data.
      // Since clearing might be confusing, consider replacing clearForm() with a refetch or simply leaving the updated data in the form.
      // clearForm(); 

      console.log("Updated store:", res.data);

    } catch (error) {
      if (error.response && error.response.status === 401) {
        handleUnauthorized();
        return;
      }

      setNotification({
        message: error.response?.data?.detail || "❌ Error updating store.",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  // --- JSX Render ---
  return (
    <div className="update-store-container">
      <Notification
        message={notification.message}
        type={notification.type}
        onClose={() => setNotification({ message: "", type: "" })}
        // Set higher duration for redirect message
        duration={notification.type === 'warning' && redirectPending ? 3000 : 4000}
      />

      <form className="update-store-form" onSubmit={handleSubmit}>
        <h2>🏥 Update My Store</h2>

        <div className="form-grid">
          <input type="text" name="store_name" placeholder="Store Name" value={formData.store_name} onChange={handleChange} />
          <input type="text" name="owner_name" placeholder="Owner Name" value={formData.owner_name} onChange={handleChange} />
          <input type="number" name="age" placeholder="Owner Age" value={formData.age} onChange={handleChange} />

          <select name="gender" value={formData.gender} onChange={handleChange}>
            <option value="">Select Gender</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Other">Other</option>
          </select>

          <input type="text" name="store_type" placeholder="Store Type" value={formData.store_type} onChange={handleChange} />
          <input type="text" name="address" placeholder="Address" value={formData.address} onChange={handleChange} />
          <input type="text" name="city" placeholder="City" value={formData.city} onChange={handleChange} />
          <input type="text" name="locality" placeholder="Locality" value={formData.locality} onChange={handleChange} />
          <input type="text" name="pin_code" placeholder="Pin Code" value={formData.pin_code} onChange={handleChange} />
          <input type="text" name="phone" placeholder="Phone" value={formData.phone} onChange={handleChange} />
          <input type="email" name="email" placeholder="Email" value={formData.email} onChange={handleChange} />
          <input type="text" name="open_hours" placeholder="Open Hours" value={formData.open_hours} onChange={handleChange} />
          <input type="number" name="delivery_radius_km" placeholder="Delivery Radius (km)" value={formData.delivery_radius_km} onChange={handleChange} />
          <input type="text" name="latitude" placeholder="Latitude (auto-generated)" value={formData.latitude} readOnly disabled />
          <input type="text" name="longitude" placeholder="Longitude (auto-generated)" value={formData.longitude} readOnly disabled />
        </div>

        {/* File uploads and previews - ROW FORMAT */}
        <div className="file-upload-row">
          <div className="file-upload-col">
            <label>
              📄 License Document (Re-upload to change)
              <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => handleFileChange(e, setLicenseDocument, setLicenseDocPreview)} />
            </label>
            {licenseDocPreview && (
              <div className="file-preview">
                {licenseDocPreview.startsWith("data:image") ? (
                  <img src={licenseDocPreview} alt="License Document Preview" className="preview-image" />
                ) : (
                  <p className="preview-text">File Selected: {licenseDocPreview}</p> // Display file name for non-images
                )}
              </div>
            )}
          </div>

          <div className="file-upload-col">
            <label>
              🏪 Store Photo (Re-upload to change)
              <input type="file" accept=".jpg,.jpeg,.png" onChange={(e) => handleFileChange(e, setStorePhoto, setStorePhotoPreview)} />
            </label>
            {storePhotoPreview && (
              <div className="file-preview">
                {storePhotoPreview.startsWith("data:image") ? (
                    <img src={storePhotoPreview} alt="Store Photo Preview" className="preview-image" />
                ) : (
                    <p className="preview-text">File Selected: {storePhotoPreview}</p> 
                )}
              </div>
            )}
          </div>
        </div>

        <div className="location-row">
          <button type="button" className="btn-location" onClick={handleUseLocation} disabled={loading || redirectPending}>
            Use My Current Location
          </button>
        </div>

        <button type="submit" className="btn-update" disabled={loading || redirectPending}>
          {loading ? "Updating..." : "Update Store"}
        </button>
      </form>
    </div>
  );
};

export default UpdateMyStore;