import React, { useEffect } from "react";
import AOS from "aos";
import "aos/dist/aos.css";
import "./ServiceCard.css";

const serviceCategories = [
  {
    heading: "Hospital Services",
    services: [
      { title: "Hospital Registration", desc: "Register new hospitals on the platform.", icon: "🏥", link: "/hospital-registration" },
      { title: "Hospital Staff Management", desc: "Manage hospital staff and their profiles.", icon: "👩‍⚕️", link: "/hospital-staff" },
      { title: "Room Management", desc: "Track and update hospital room availability.", icon: "🛏️", link: "/room-management" },
      { title: "Assign Doctor Duty", desc: "Schedule and assign doctor duties.", icon: "📅", link: "/assign-duty" },
    ],
  },
  {
    heading: "Doctor Services",
    services: [
      { title: "Register Doctors in Hospital", desc: "Add doctors to a specific hospital.", icon: "🩺", link: "/doctor-registration" },
      { title: "Duty Management", desc: "Manage doctor shifts and schedules.", icon: "⏰", link: "/doctor-duty" },
      { title: "Maintain Patient History", desc: "View and update patient history records.", icon: "📄", link: "/patient-medical-history" },
      { title: "Patient Management", desc: "Management patients to the system.", icon: "🧍", link: "/patient-management" },
    ],
  },
  {
    heading: "Patient Services",
    services: [
      { title: "User Registration", desc: "Register patients to the system.", icon: "🧍", link: "/patient-registration" },
      { title: "Book Appointment", desc: "Patients can book appointments online.", icon: "📅", link: "/book-appointment" },
      { title: "Upload Prescriptions", desc: "Upload prescriptions for orders.", icon: "📤", link: "/prescription-handler" },
      { title: "Patient History", desc: "View and search patient history records.", icon: "📄", link: "/patient-history" },
      { title: "Search Stores", desc: "Find stores by owner name, pin code, location, medicines, store name, city, radius.", icon: "🔍", link: "/medical-store-search" },
    ],
  },
  {
    heading: "Clinic Services",
    services: [
      { title: "Clinic Registration", desc: "Register clinics on the platform.", icon: "🏥", link: "/clinic-registration" },
      { title: "Clinic Admin Creation", desc: "Create admin panel access for clinics.", icon: "👨‍💼", link: "/clinic-admin" },
    ],
  },
  {
    heading: "Pharmacy Services",
    services: [
      { title: "Pharmacy Registration", desc: "Register new pharmacies.", icon: "💊", link: "/pharmacy-registration" },
    ],
  },
  {
    heading: "Medical Store Services",
    services: [
      { title: "Medical Store Registration", desc: "Sign up new medical stores.", icon: "🏪", link: "/medical-store-registration" },
      { title: "Inventory Management", desc: "Manage stock and medicines.", icon: "📦", link: "/inventory-management" },
      { title: "Book Medicine at Pharmacy", desc: "Book medicines from registered pharmacies.", icon: "📝", link: "/book-medicine" },
      { title: "Customers Management", desc: "Track customer orders and records.", icon: "👥", link: "/customer-management" },
      { title: "Update Medical Store Info", desc: "Edit your store profile.", icon: "✏️", link: "/medical-store-update" },
      { title: "Delete My Store", desc: "Remove your medical store from platform.", icon: "🗑️", link: "/delete-my-store" },
      {title: "Products Management",desc: "Manage products to the store inventory.",icon: "🗃️", link: "/product-management"},
      { title: "Supplier Management", desc: "Manage suppliers for your store.", icon: "🏭", link: "/supplier-management" },
      { title: "Medical Store Search", desc: "Find medical stores quickly.", icon: "🔍", link: "/medical-store-search" },
      { title: "Prescription Response", "desc": "Manage and respond to prescriptions quickly.", "icon": "💊", "link": "/prescription-response" },
      { title: "Update Customer", desc: "Edit customer profiles.", icon: "🔄", link: "/customer-update" },
      { title: "Search Customers", desc: "Find customers quickly.", icon: "🔍", link: "/customer-search" },
    
    ],
  },
    {
    heading: "Customer Services",
    services: [
      { title: "Search Stores", desc: "Find stores like patient search services.", icon: "🔎", link: "/medical-store-search" },
      { title: "Update Customer", desc: "Edit customer profiles.", icon: "🔄", link: "/customer-update" },
      { title: "Upload Prescriptions", desc: "Upload prescriptions for orders.", icon: "📤", link: "/prescription-handler" },
    ],
  },
  {
    heading: "Dispensary Services",
    services: [
      { title: "Dispensary Registration", desc: "Register a new dispensary.", icon: "🏬", link: "/dispensary-registration" },
      { title: "Search Dispensary Location", desc: "Find the nearest dispensaries.", icon: "📍", link: "/search-dispensary" },
      { title: "Book Appointment at Dispensary", desc: "Online booking for dispensaries.", icon: "🗓️", link: "/dispensary-appointment" },
    ],
  },
  {
    heading: "Lab Services",
    services: [
      { title: "Lab Registration", desc: "Register diagnostic labs.", icon: "🧪", link: "/lab-registration" },
      { title: "Maintain Online Records", desc: "Store and manage lab results.", icon: "💾", link: "/lab-records" },
      { title: "Send Reports to Doctor/Patient", desc: "Share reports securely.", icon: "📤", link: "/send-report" },
      { title: "Add Testing Facilities", desc: "List available testing services.", icon: "🧬", link: "/add-testing" },
    ],
  },
];

const ServiceCards = () => {
  useEffect(() => {
    AOS.init({ duration: 800, easing: "ease-out", once: true });
  }, []);

  return (
    <div className="services-container">
      {serviceCategories.map((category, idx) => (
        <div key={idx} className="service-category">
          <h2 className="category-heading">{category.heading}</h2>
          <div className="service-cards">
            {category.services.map((service, i) => (
              <a
                key={i}
                href={service.link}
                className="service-card"
                data-aos="fade-up"
                data-aos-delay={i * 100}
              >
                <div className="icon">{service.icon}</div>
                <h3>{service.title}</h3>
                <p>{service.desc}</p>
              </a>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ServiceCards;
