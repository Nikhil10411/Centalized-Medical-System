const GlobalStyles = () => {
  const styles = `
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
    body {
      margin: 0;
      padding: 0;
      font-family: 'Poppins', sans-serif;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      background: linear-gradient(180deg, #f6faff 0%, #eef4f9 100%);
      min-height: 100vh;
    }
    /* Store Container */
    .store-container {
      background: linear-gradient(180deg, #f6faff 0%, #eef4f9 100%);
      min-height: 100vh;
      padding: 50px 5%;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .page-title {
      text-align: center;
      font-size: 2rem;
      font-weight: 700;
      color: #007ba7;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    /* Navigation Buttons */
    .nav-btn-cart, .nav-btn-store {
      margin-bottom: 30px;
      background: #00bcd4;
      color: #fff;
      padding: 10px 20px;
      border: none;
      border-radius: 10px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      box-shadow: 0 4px 10px rgba(0, 188, 212, 0.4);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .nav-btn-cart:hover, .nav-btn-store:hover {
      background: #00acc1;
      transform: translateY(-2px);
      box-shadow: 0 6px 15px rgba(0, 188, 212, 0.6);
    }
    .cart-message {
      text-align: center;
      color: #00796b;
      background-color: #e0f2f1;
      padding: 8px 18px;
      border-radius: 8px;
      margin-bottom: 20px;
      font-weight: 600;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
      animation: fadeIn 0.4s ease;
    }
    .product-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
      justify-content: center;
      gap: 30px;
      width: 100%;
      max-width: 1200px;
    }
    .product-card-container {
      position: relative;
      margin: 10px;
      width: 300px;
    }
    .product-card {
      position: relative;
      background-color: #1a2035;
      border: 1px solid #00d4ff;
      border-radius: 16px;
      padding: 1rem;
      width: 100%;
      box-shadow: 0 0 15px rgba(0,212,255,0.5);
      transition: all 0.3s ease-in-out;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      cursor: default;
      min-height: 400px;
    }
    .product-card:hover {
      transform: translateY(-5px) scale(1.02);
      box-shadow: 0 0 25px #00d4ff, 0 0 50px rgba(0,212,255,0.3);
    }
    .product-content {
      display: flex;
      flex-direction: column;
      gap: 10px;
      color: #ffffff;
      flex-grow: 1;
    }
    .image-wrapper {
      width: 100%;
      height: 180px;
      border-radius: 12px;
      overflow: hidden;
      margin-bottom: 10px;
      background-color: #0f172a;
    }
    .product-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.3s ease;
    }
    .product-card:hover .product-img {
      transform: scale(1.05);
    }
    .product-main-details {
      padding-bottom: 10px;
      border-bottom: 1px dashed rgba(0, 212, 255, 0.2);
      display: flex;
      flex-direction: column;
    }
    .product-name-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 5px;
    }
    .product-name {
      font-size: 1.5rem;
      font-weight: 700;
      color: #00d4ff;
      text-shadow: 0 0 5px rgba(0,212,255,0.5);
      margin: 0;
      max-width: 65%;
    }
    .details-btn {
      background-color: transparent;
      color: #ffcc00;
      border: 1px solid #ffcc00;
      padding: 5px 8px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .details-btn:hover {
      background-color: rgba(255,204,0,0.1);
      box-shadow: 0 0 5px #ffcc00;
    }
    .details-btn.active {
      background-color: #ffcc00;
      color: #1a2035;
    }
    .detail-text {
      font-size: 0.85rem;
      margin: 2px 0;
      color: #a0a8b9;
    }
    .detail-text strong {
      color: #ffffff;
    }
    .product-specs {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 15px;
      margin-top: auto;
    }
    .spec-tag {
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      background-color: rgba(0,212,255,0.1);
      color: #00d4ff;
      border: 1px solid #00d4ff;
    }
    .expiry {
      color: #ff9900;
      border-color: #ff9900;
    }
    .card-footer-actions {
      margin-top: 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0 5px;
    }
    .product-price {
      font-size: 1.5rem;
      font-weight: 800;
      color: #ffcc00;
      text-shadow: 0 0 8px rgba(255,204,0,0.5);
    }
    .add-cart-btn {
      background: linear-gradient(45deg, #00d4ff, #0077ff);
      color: #1a2035;
      padding: 10px 15px;
      border: none;
      border-radius: 8px;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 4px 15px rgba(0,119,255,0.5);
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      gap: 5px;
      z-index: 20;
    }
    .add-cart-btn:hover {
      background: linear-gradient(45deg, #00e9ff, #0088ff);
      box-shadow: 0 6px 20px rgba(0,119,255,0.7);
      transform: translateY(-2px);
    }
    .add-cart-btn svg {
      stroke: #1a2035;
    }
    .store-tooltip {
      position: absolute;
      top: 0; right: 0; bottom: 0; left: 0;
      background-color: rgba(26,32,53,0.98);
      border-radius: 16px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: flex-start;
      color: #ffffff;
      z-index: 10;
      border: 2px solid #ffcc00;
      box-shadow: inset 0 0 10px #ffcc00;
      animation: fade-in 0.3s ease-out;
    }
    .tooltip-close {
      position: absolute;
      top: 10px; right: 10px;
      background: none;
      border: none;
      color: #ffcc00;
      font-size: 1.5rem;
      cursor: pointer;
      z-index: 11;
    }
    @keyframes fade-in {
      from { opacity: 0; transform: scale(0.95); }
      to { opacity: 1; transform: scale(1); }
    }
    .tooltip-title {
      font-size: 1.3rem;
      color: #ffcc00;
      margin-bottom: 15px;
      text-shadow: 0 0 5px rgba(255,204,0,0.5);
    }
    .store-tooltip p {
      font-size: 0.9rem;
      margin: 5px 0;
      color: #a0a8b9;
    }
    .store-tooltip strong {
      color: #ffffff;
      font-weight: 600;
    }
    .tooltip-note {
      margin-top: 10px;
      font-style: italic;
      font-size: 0.75rem;
      color: #ff9900;
    }
    /* Cart View Styles */
    .cart-container {
      background: linear-gradient(180deg, #f0f7ff 0%, #dbe8f3 100%);
      min-height: 100vh;
      padding: 50px 5%;
      font-family: "Poppins", sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .overall-total {
      font-size: 1.5rem;
      color: #ff9900;
      font-weight: 700;
      margin-bottom: 30px;
      padding: 10px 20px;
      border-radius: 12px;
      background-color: #fff8e1;
      border: 2px solid #ff9900;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .empty-msg {
      color: #5f6f82;
      font-size: 1.2rem;
      margin-top: 50px;
      text-align: center;
    }
    .cart-store-section {
      background: #ffffff;
      border: 1px solid #e0e7ef;
      border-radius: 16px;
      padding: 25px;
      margin-bottom: 30px;
      width: 100%;
      max-width: 900px;
      box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08);
    }
    .store-heading {
      font-size: 1.25rem;
      color: #007ba7;
      margin-bottom: 15px;
      border-bottom: 2px solid #f0f7ff;
      padding-bottom: 10px;
    }
    .cart-table-wrapper {
      overflow-x: auto;
    }
    .cart-table {
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 20px;
      font-size: 0.95rem;
    }
    .cart-table th, .cart-table td {
      padding: 12px 15px;
      text-align: left;
      border-bottom: 1px solid #f0f7ff;
      vertical-align: middle;
    }
    .cart-table th {
      background-color: #f6faff;
      font-weight: 600;
      color: #1a223f;
    }
    .cart-table tr:hover {
      background-color: #fcfdff;
    }
    .btn-remove {
      background: #ff5252;
      color: white;
      border: none;
      border-radius: 6px;
      padding: 6px 10px;
      cursor: pointer;
      font-size: 0.85rem;
      transition: background 0.2s;
      display: flex;
      align-items: center;
      justify-content: center;
      line-height: 1;
    }
    .btn-remove:hover {
      background: #ff1744;
    }
    .checkout-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 15px;
      border-top: 1px solid #f0f7ff;
    }
    .store-total {
      font-size: 1.2rem;
      font-weight: 700;
      color: #00796b;
    }
    .btn-checkout {
      background: linear-gradient(90deg, #4caf50, #8bc34a);
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 10px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      box-shadow: 0 4px 10px rgba(76,175,80,0.4);
    }
    .btn-checkout:hover {
      background: linear-gradient(90deg, #43a047, #7cb342);
      transform: translateY(-2px);
      box-shadow: 0 6px 12px rgba(76,175,80,0.6);
    }
    @media (max-width: 768px) {
      .page-title {
        font-size: 1.8rem;
      }
      .product-grid {
        grid-template-columns: 1fr;
      }
      .cart-store-section {
        padding: 15px;
      }
      .cart-table th, .cart-table td {
        padding: 10px 8px;
      }
      .checkout-row {
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
      }
      .product-card-container {
        width: 100%;
      }
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(5px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `;
  return <style>{styles}</style>;
};

export default GlobalStyles;
