import React, { useEffect, useState } from "react";

// The ProductCard component is responsible for displaying a single product 
// and differentiating between store inventory and supplier products.
const ProductCard = ({ product, onAddToCart, authToken }) => {
  // --- Input Validation ---
  if (!product) {
    // Visual error card when product data is missing.
    return (
      <div className="product-card-error">
        <style>{`
          .product-card-error {
            background-color: #1a2035;
            border: 1px solid #ff0077;
            color: #ff0077;
            border-radius: 16px;
            padding: 1rem;
            width: 300px;
            margin: 10px;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 250px;
            box-shadow: 0 0 10px rgba(255, 0, 119, 0.5);
          }
        `}</style>
        Product data missing.
      </div>
    );
  }

  const PLACEHOLDER_URL = "https://placehold.co/150x150/0f172a/ffffff?text=No+Image";
  
  // --- State Management ---
  const [imageSrc, setImageSrc] = useState(PLACEHOLDER_URL);
  const [detailsVisible, setDetailsVisible] = useState(false);

  // --- Differentiation Logic ---
  const isSupplierProduct = product.type === "supplier_product";
  const productSourceLabel = isSupplierProduct ? "Supplier Item" : "Store Inventory";

  // --- Image Fetching Effect ---
  useEffect(() => {
    if (!product || !product.product_id) return;
    
    let currentImageSrc = null;

    const fetchImage = async () => {
      if (!product.product_image_url) {
        setImageSrc(PLACEHOLDER_URL);
        return;
      }
      
      // Construct the image URL based on the product ID and assumed local API endpoint
      const imageUrl = `http://127.0.0.1:8000/api/image/${product.product_id}`;
      
      try {
        // Use the provided authToken for secure image access
        const res = await fetch(imageUrl, {
          headers: { Authorization: `Bearer ${authToken}` },
        });
        if (!res.ok) throw new Error("Image not found");
        
        // Convert response to blob and create a local URL
        const blob = await res.blob();
        currentImageSrc = URL.createObjectURL(blob);
        setImageSrc(currentImageSrc);
      } catch (err) {
        console.error("🖼️ Image fetch failed:", err);
        setImageSrc(PLACEHOLDER_URL);
      }
    };
    fetchImage();
    
    // Cleanup function: revoke the object URL to prevent memory leaks
    return () => {
      if (currentImageSrc && currentImageSrc !== PLACEHOLDER_URL) {
        URL.revokeObjectURL(currentImageSrc);
      }
    };
  }, [product.product_id, product.product_image_url, authToken]);

  // --- Event Handlers ---
  const handleAddToCart = (e) => {
    e.stopPropagation();
    if (typeof onAddToCart === "function") {
      onAddToCart(product);
    } else {
      console.warn("onAddToCart is missing or invalid");
    }
  };

  const toggleDetails = (e) => {
    e.stopPropagation();
    setDetailsVisible((prev) => !prev);
  };

  // --- CSS Styles (Embedded for Single-File React Mandate) ---
  const cardStyles = `
    /* --- COMMON VARIABLES --- */
    :root {
      --card-bg: #1a2035;
      --neon-blue: #00d4ff;
      --text-light: #ffffff;
      --text-secondary: #a0a8b9;
      --shadow-color: rgba(0, 212, 255, 0.5);
      --yellow-accent: #ffcc00;
      --supplier-red: #ff3366; /* Supplier highlight color */
      --card-min-height: 400px;
    }
    
    /* --- PRODUCT CARD BASE STYLES --- */
    .product-card-container { position: relative; margin: 10px; width: 300px; }
    .product-card {
      position: relative;
      background-color: var(--card-bg);
      border: 1px solid var(--neon-blue);
      border-radius: 16px;
      padding: 1rem;
      width: 100%;
      box-shadow: 0 0 15px var(--shadow-color);
      transition: all 0.3s ease-in-out;
      display: flex; flex-direction: column;
      overflow: hidden; cursor: default; 
      min-height: var(--card-min-height);
    }
    
    /* Supplier Specific Styling */
    .product-card.supplier {
      border-color: var(--supplier-red);
      box-shadow: 0 0 15px rgba(255, 51, 102, 0.7);
    }
    .product-card.supplier:hover {
      box-shadow: 0 0 25px var(--supplier-red), 0 0 50px rgba(255, 51, 102, 0.3);
    }

    .product-card:hover {
      transform: translateY(-5px) scale(1.02);
      box-shadow: 0 0 25px var(--neon-blue), 0 0 50px rgba(0, 212, 255, 0.3);
    }
    .image-wrapper { width: 100%; height: 180px; border-radius: 12px; overflow: hidden; margin-bottom: 10px; background-color: #0f172a; }
    .product-img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease; }
    .product-card:hover .product-img { transform: scale(1.05); }
    .product-main-details { padding-bottom: 10px; border-bottom: 1px dashed rgba(0,212,255,0.2); display: flex; flex-direction: column; }
    .product-card.supplier .product-main-details { border-bottom: 1px dashed rgba(255, 51, 102, 0.5); }


    .product-name-row { 
      display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; 
      position: relative; 
    }
    .product-name { 
      font-size: 1.5rem; font-weight: 700; color: var(--neon-blue); text-shadow: 0 0 5px var(--shadow-color); margin: 0; max-width: 65%; 
    }
    .product-card.supplier .product-name { color: var(--supplier-red); text-shadow: 0 0 5px rgba(255, 51, 102, 0.5); }

    /* --- PRODUCT SOURCE TAG (RIBBON) --- */
    .product-source-tag {
      position: absolute;
      top: 5px; /* Adjusted position to be slightly more visible */
      left: 0;
      padding: 3px 10px;
      padding-left: 20px;
      font-size: 0.7rem;
      font-weight: 700;
      color: var(--card-bg);
      background-color: var(--neon-blue);
      border-radius: 0 8px 8px 0;
      z-index: 10;
      transform: translateX(-10px); /* slightly pull it back */
    }
    .product-source-tag.supplier {
      background-color: var(--supplier-red);
      color: white;
    }
    
    .details-btn { background: transparent; color: var(--yellow-accent); border: 1px solid var(--yellow-accent); padding: 5px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; cursor: pointer; transition: all 0.2s ease; }
    .details-btn:hover { background-color: rgba(255,204,0,0.1); box-shadow: 0 0 5px var(--yellow-accent); }
    .details-btn.active { background-color: var(--yellow-accent); color: var(--card-bg); }
    .detail-text { font-size: 0.85rem; margin: 2px 0; color: var(--text-secondary); }
    .detail-text strong { color: var(--text-light); }
    .product-specs { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px; margin-top: auto; }
    .spec-tag { padding: 4px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; background-color: rgba(0,212,255,0.1); color: var(--neon-blue); border: 1px solid var(--neon-blue); }
    .product-card.supplier .spec-tag { background-color: rgba(255, 51, 102, 0.1); color: var(--supplier-red); border-color: var(--supplier-red); }
    .expiry { color: #ff9900; border-color: #ff9900; }
    
    .card-footer-actions { margin-top: 10px; display: flex; justify-content: space-between; align-items: center; padding: 0 5px; }
    .product-price { font-size: 1.5rem; font-weight: 800; color: var(--yellow-accent); text-shadow: 0 0 8px rgba(255,204,0,0.5); }
    
    .add-cart-btn { background: linear-gradient(45deg,var(--neon-blue),#0077ff); color: var(--card-bg); padding: 10px 15px; border: none; border-radius: 8px; font-weight: 700; cursor: pointer; box-shadow: 0 4px 15px rgba(0,119,255,0.5); transition: all 0.3s ease; display: flex; align-items: center; gap: 5px; z-index: 20; }
    .add-cart-btn:hover { background: linear-gradient(45deg,#00e9ff,#0088ff); box-shadow: 0 6px 20px rgba(0,119,255,0.7); transform: translateY(-2px); }
    
    /* Supplier Add to Cart Button */
    .product-card.supplier .add-cart-btn { background: linear-gradient(45deg, var(--supplier-red), #cc2255); box-shadow: 0 4px 15px rgba(255, 51, 102, 0.5); }
    .product-card.supplier .add-cart-btn:hover { background: linear-gradient(45deg, #ff4477, #dd3366); box-shadow: 0 6px 20px rgba(255, 51, 102, 0.7); }
    .add-cart-btn svg { stroke: var(--card-bg); }

    /* --- DETAILS OVERLAY STYLES --- */
    .store-tooltip {
      position: absolute; top: 0; left: 0; right: 0; bottom: 0; height: 100%; width: 100%; z-index: 30; 
      background-color: rgba(10, 18, 30, 0.98); border: 2px solid var(--neon-blue); border-radius: 16px;
      box-shadow: 0 0 30px var(--shadow-color); backdrop-filter: blur(2px); padding: 1.5rem; color: var(--text-light); cursor: default;
      display: flex; flex-direction: column; align-items: flex-start; justify-content: space-between;
      transition: opacity 0.3s ease; animation: fadeIn 0.3s ease-out; 
      /* Important: Prevent scrolling issues on the overlay */
      overflow-y: hidden; 
    }
    .product-card.supplier .store-tooltip { border-color: var(--supplier-red); box-shadow: 0 0 30px rgba(255, 51, 102, 0.7); }
    
    @keyframes fadeIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
    
    .tooltip-close {
      position: absolute; top: 10px; right: 15px; background: none; border: none; color: var(--neon-blue);
      font-size: 2rem; font-weight: 300; cursor: pointer; transition: color 0.2s; line-height: 1; padding: 0;
      text-shadow: 0 0 10px var(--shadow-color); z-index: 40;
    }
    .product-card.supplier .tooltip-close { color: var(--supplier-red); text-shadow: 0 0 10px rgba(255, 51, 102, 0.7); }
    .tooltip-close:hover { color: #ff5555; text-shadow: 0 0 10px #ff5555; }

    .tooltip-title {
      font-size: 1.25rem; font-weight: 700; color: var(--yellow-accent); margin-top: 0; margin-bottom: 1rem;
      border-bottom: 1px solid rgba(255, 204, 0, 0.3); padding-bottom: 8px; width: 100%;
      text-shadow: 0 0 5px rgba(255,204,0,0.5);
    }
    .store-tooltip p { font-size: 0.95rem; margin: 6px 0; color: var(--text-secondary); word-break: break-word; }
    .store-tooltip p strong { color: var(--text-light); font-weight: 600; font-size: 1rem; }

    .tooltip-note {
      margin-top: 10px; padding-top: 10px; font-size: 0.85rem; color: var(--neon-blue);
      border-top: 1px dashed rgba(0, 212, 255, 0.2); width: 100%; flex-shrink: 0;
    }

    /* --- MOBILE STYLES (Screen size 500px or less) --- */
    @media (max-width: 500px) {
      .product-card-container { width: 95%; margin: 10px auto; }
      .product-card { padding: 0.75rem; min-height: 380px; }
      .product-name { font-size: 1.3rem; }
      .product-price { font-size: 1.3rem; }
      .add-cart-btn { padding: 8px 12px; font-size: 0.9rem; }
      .store-tooltip { padding: 1.2rem; }
      .tooltip-title { font-size: 1.1rem; }
      .store-tooltip p { font-size: 0.85rem; }
      .store-tooltip p strong { font-size: 0.9rem; }
    }
  `;

  return (
    <>
      <style>{cardStyles}</style>
      <div className="product-card-container">
        <div className={`product-card ${isSupplierProduct ? "supplier" : "inventory"}`}>
          
          {/* Product Source Tag (Ribbon visual differentiation) */}
          <span className={`product-source-tag ${isSupplierProduct ? "supplier" : ""}`}>
            {productSourceLabel}
          </span>

          {detailsVisible && (
            // --- Store/Supplier Details Overlay ---
            <div className="store-tooltip" onClick={toggleDetails}>
              <button className="tooltip-close" onClick={toggleDetails}>
                &times;
              </button>
              <h4 className="tooltip-title">
                {isSupplierProduct ? "Supplier Details" : "Store Details"}:{" "}
                {isSupplierProduct ? (product.supplier_name || "N/A") : (product.store_name || "N/A")}
              </h4>
              
              {/* Conditional Details based on product type */}
              {!isSupplierProduct ? (
                // --- Inventory Product Details ---
                <>
                  <p><strong>Store ID:</strong> {product.store_id || "N/A"}</p>
                  <p><strong>Address:</strong> {product.store_address || "N/A"}</p>
                  <p><strong>Email:</strong> {product.store_email || "N/A"}</p>
                  <p><strong>Phone:</strong> {product.store_phone_no || "N/A"}</p>
                  <p><strong>Delivery Radius:</strong> {product.delivery_radius || 0} km</p>
                  <div style={{ flexGrow: 1 }}></div> 
                  <p className="tooltip-note">Open Hours: {product.store_open_hour || "N/A"}</p>
                </>
              ) : (
                // --- Supplier Product Details (with extra supplier contact info) ---
                <>
                  <p><strong>Contact Name:</strong> {product.contact_name || "N/A"}</p>
                  <p><strong>Phone:</strong> {product.phone || "N/A"}</p>
                  <p><strong>Email:</strong> {product.email || "N/A"}</p>
                  <p><strong>City/Pin:</strong> {product.city || "N/A"} / {product.pin_code || "N/A"}</p>
                  <p><strong>Full Address:</strong> {product.address || "N/A"}</p>
                  <div style={{ flexGrow: 1 }}></div>
                  <p className="tooltip-note" style={{ color: "var(--supplier-red)" }}>
                    Lead Time: {product.lead_time_days || 0} day(s)
                  </p>
                </>
              )}
            </div>
          )}

          <div className="product-content">
            <div className="image-wrapper">
              <img
                src={imageSrc}
                alt={product.product_name || "Product"}
                className="product-img"
                onError={(e) => (e.target.src = PLACEHOLDER_URL)}
              />
            </div>

            <div className="product-main-details">
              <div className="product-name-row">
                <h3 className="product-name">{product.product_name || "Unknown Product"}</h3>
                <button
                  className={`details-btn ${detailsVisible ? "active" : ""}`}
                  onClick={toggleDetails}
                >
                  {detailsVisible ? "Hide Details" : "More Details"}
                </button>
              </div>

              <p className="detail-text">Brand: <strong>{product.brand || "N/A"}</strong></p>
              <p className="detail-text">Generic: <strong>{product.generic_name || "N/A"}</strong></p>
              <p className="detail-text">Category: <strong>{product.category || "N/A"}</strong></p>
            </div>

            {/* Product Specifications / Inventory Details */}
            <div className="product-specs">
              <span className="spec-tag">{product.dosage || "N/A"}</span>
              <span className="spec-tag">{product.form || "N/A"}</span>
              
              {isSupplierProduct ? (
                // Specs for Supplier Product
                <span className="spec-tag">Lead Time: {product.lead_time_days || "N/A"}d</span>
              ) : (
                // Specs for Inventory Product
                <>
                  <span className="spec-tag">Qty: {product.quantity || "N/A"}</span>
                  <span className="spec-tag expiry">
                    Exp: {product.expiry_date ? new Date(product.expiry_date).toLocaleDateString() : "N/A"}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* --- Footer and Action Button --- */}
        <div className="card-footer-actions">
          <span className="product-price">₹ {product.price || "0.00"}</span>
          <button className="add-cart-btn" onClick={handleAddToCart}>
            {/* Shopping Cart Icon (Lucide-react inline SVG equivalent) */}
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"
              viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-shopping-cart">
              <circle cx="8" cy="21" r="1" />
              <circle cx="19" cy="21" r="1" />
              <path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.72a2 2 0 0 0 2-1.58L23 6H6" />
            </svg>
            {isSupplierProduct ? "Order from Supplier" : "Add to Cart"}
          </button>
        </div>
      </div>
    </>
  );
};

export default ProductCard;