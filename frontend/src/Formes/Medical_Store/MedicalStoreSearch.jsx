import React, { useState } from "react";
import axios from "axios";
import "./MedicalStoreSearch.css";
import Notification from "../../Notification/Notification"; // global notification

const MedicalStoreSearch = () => {
  const [filters, setFilters] = useState({
    owner_name: "",
    search: "",
    city: "",
    locality: "",
    pin_code: "",
    medicine: "",
    latitude: null,
    longitude: null,
    radius_km: 5,
  });

  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState({ message: "", type: "" });

  // Handle input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({
      ...prev,
      [name]: name === "radius_km" ? Number(value) : value,
    }));
  };

  // Perform search
  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStores([]);

    try {
      // Only send non-empty filters
      const params = {};
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== "" && value !== null) {
          params[key] = value;
        }
      });

      const response = await axios.get(
        "http://127.0.0.1:8000/medical_store/get_all_store/",
        { params }
      );

      if (response.data.length === 0) {
        setNotification({
          message: "⚠️ No stores found for your search.",
          type: "warning",
        });
      } else {
        setStores(response.data);
      }
    } catch (error) {
      setNotification({
        message: error.response?.data?.detail || "❌ Error fetching stores.",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  // Use current location
  const handleUseLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setFilters((prev) => ({
            ...prev,
            latitude: Number(pos.coords.latitude),
            longitude: Number(pos.coords.longitude),
          }));
          setNotification({
            message: "📍 Using your current location.",
            type: "info",
          });
        },
        () => {
          setNotification({
            message: "❌ Unable to get location.",
            type: "error",
          });
        }
      );
    } else {
      setNotification({
        message: "❌ Geolocation not supported.",
        type: "error",
      });
    }
  };

  return (
    <div className="store-search-container">
      {/* Global Notification */}
      <Notification
        message={notification.message}
        type={notification.type}
        onClose={() => setNotification({ message: "", type: "" })}
      />

      {/* Search Form */}
      <form className="search-form" onSubmit={handleSearch}>
        <h2>🔍 Search Medical Stores</h2>

        <div className="search-grid">
          <input
            type="text"
            name="search"
            placeholder="Store Name"
            value={filters.search}
            onChange={handleChange}
          />
          <input
            type="text"
            name="owner_name"
            placeholder="Owner Name"
            value={filters.owner_name}
            onChange={handleChange}
          />
          <input
            type="text"
            name="city"
            placeholder="City"
            value={filters.city}
            onChange={handleChange}
          />
          <input
            type="text"
            name="locality"
            placeholder="Locality"
            value={filters.locality}
            onChange={handleChange}
          />
          <input
            type="text"
            name="pin_code"
            placeholder="Pin Code"
            value={filters.pin_code}
            onChange={handleChange}
          />
          <input
            type="text"
            name="medicine"
            placeholder="Medicine Name"
            value={filters.medicine}
            onChange={handleChange}
          />
        </div>

        <div className="location-row">
          <input
            type="number"
            name="radius_km"
            placeholder="Radius (km)"
            value={filters.radius_km}
            onChange={handleChange}
          />
          <button
            type="button"
            className="btn-location"
            onClick={handleUseLocation}
          >
            Use My Location
          </button>
        </div>

        <button type="submit" className="btn-search" disabled={loading}>
          {loading ? "Searching..." : "Search Stores"}
        </button>
      </form>

      {/* Results */}
      <div className="results-container">
        {stores.map((store) => (
          <div className="store-card" key={store.store_id}>
            {/* ✅ Store photo */}
            {store.store_photo ? (
              <img
                src={`data:${store.photo_mime};base64,${store.store_photo}`}
                alt={store.store_name}
                className="store-photo"
              />
            ) : (
              <div className="store-photo-placeholder">📷 No Image</div>
            )}

            <div className="store-info">
              <h3>{store.store_name}</h3>
              <p>
                <strong>Owner:</strong> {store.owner_name}
              </p>
              <p>
                <strong>City:</strong> {store.city} |{" "}
                <strong>Locality:</strong> {store.locality}
              </p>
              <p>
                <strong>Phone:</strong> {store.phone}
              </p>
              <p>
                <strong>Delivery Radius:</strong> {store.delivery_radius_km} km
              </p>
              {store.open_hours && (
                <p>
                  <strong>Open Hours:</strong> {store.open_hours}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MedicalStoreSearch;
