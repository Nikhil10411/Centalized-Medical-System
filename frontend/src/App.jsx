import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import NavBar from './NavComponents/NavBar';

import Home from './Pages/Home';
import About from './Pages/AboutUsComponents/About';
import Contact from './Pages/Contact';
import Services from './Pages/Services';
import Auth from './Pages/Auth';
import PatientDashboard from './PatientDashboard/PatientDashbord';
import Footer from './Footer/Footer';
import MedicalStoreDashboard from './AdminDashboard/MedicalStoreDashboard';
import MedicalStoreRegistration from './Formes/MedicalStoreRegistration';
import MedicalStoreSearch from './Formes/Medical_Store/MedicalStoreSearch';
import UpdateMyStore from './Formes/Medical_Store/UpdateMyStore';
import DeleteMyStore from './Formes/Medical_Store/DeleteMyStore';
import InventoryManagement from './Formes/Medical_Store/InventoryManagement';
import CustomerManagement from './Formes/Medical_Store/CustomerManagement';
import SupplierManagement from './Formes/Medical_Store/SupplierManagement';
import ProductManagement from './Formes/Medical_Store/ProductManagement';
import PrescriptionHandler from './Formes/Medical_Store/PrescriptionHandler';
import PrescriptionResponse from './Formes/Medical_Store/PrescriptionResponse';
import PatientManagement from './Formes/Patients/PatientManagement';
import DoctorRegistrationForm from './Formes/DoctorRegistrationForm';
import PatientRegistrationForm from './Formes/PatientRegistrationForm';
import PatientMedicalHistoryManagement from './Formes/Doctors/PatientMedicalHistoryManagement';
import PatientMedicalHistory from './Formes/Patients/PatientMedicalHistory';
import ProductList from './Pages/ViewProducts/ProductList';
import CartView from './Pages/ViewProducts/CartView';
import SupplierRegistrationForm from './Formes/SupplierRegistrationForm';

const App = () => (
  <div className="app-layout">
    <NavBar />
    <div className="main-content">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/home" element={<Navigate to="/" replace />} />
        <Route path="/about" element={<About />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/services" element={<Services />} />
        <Route path="/auth" element={<Auth />} />
        <Route path="/patient-dashboard" element={<PatientDashboard />} />
        <Route path="/medical-store-registration" element={<MedicalStoreRegistration />} />
        <Route path="/medical-store-search" element={<MedicalStoreSearch />} />
        <Route path="/medical-store-update" element={<UpdateMyStore />} />
        <Route path="/delete-my-store" element={<DeleteMyStore />} />
        <Route path="/inventory-management" element={<InventoryManagement />} />
        <Route path="/customer-management" element={<CustomerManagement />} />
        <Route path="/supplier-management" element={<SupplierManagement />} />
        <Route path="/product-management" element={<ProductManagement />} />
        <Route path="/prescription-handler" element={<PrescriptionHandler />} />
        <Route path="/prescription-response" element={<PrescriptionResponse />} />
        <Route path="/patient-management" element={<PatientManagement />} />
        <Route path="/patient-registration" element={<PatientRegistrationForm />} />
        <Route path="/patient-history" element={<PatientMedicalHistory />} />
        <Route path="/patient-medical-history" element={<PatientMedicalHistoryManagement />} />
        <Route path="/doctor-registration" element={<DoctorRegistrationForm />} />
        <Route path="/medical-store-dashboard" element={<MedicalStoreDashboard />} />
         <Route path="/supplier-registration" element={<SupplierRegistrationForm/>} />
        <Route path="/products" element={<ProductList />} />
        <Route path="/cart" element={<CartView />} />
        {/* 404 */}
        <Route
          path="*"
          element={
            <div
              style={{
                textAlign: "center",
                marginTop: "3rem",
                fontSize: "2rem",
                color: "#00d8ff",
                fontWeight: "bold"
              }}
            >
              404 - Page Not Found
            </div>
          }
        />
      </Routes>
    </div>
    <Footer />
  </div>
);

export default App;

