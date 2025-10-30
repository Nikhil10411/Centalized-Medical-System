import React, { useState } from "react";
import "./Contact.css";
import Carousel from "../Carousel/Carousel";

function Contact() {
  const [form, setForm] = useState({ name: "", email: "", message: "" });
  const [errors, setErrors] = useState({});
  const [submitted, setSubmitted] = useState(false);

  function validate() {
    let err = {};
    if (!form.name) err.name = "Name is required";
    if (!form.email) err.email = "Email is required";
    else if (!/\S+@\S+\.\S+/.test(form.email)) err.email = "Email is invalid";
    if (!form.message) err.message = "Message is required";
    return err;
  }

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: "" });
  }

  function handleSubmit(e) {
    e.preventDefault();
    const validation = validate();
    setErrors(validation);
    if (Object.keys(validation).length === 0) {
      setSubmitted(true);
      setForm({ name: "", email: "", message: "" });
      setTimeout(() => setSubmitted(false), 3500); // Hide animation after 3s
    }
  }

  return (
    <>
    <Carousel/>
    <div className="contact-container">
      <h2>Contact Us</h2>
      <form className="contact-form" onSubmit={handleSubmit} autoComplete="off">
        <input
          type="text"
          name="name"
          value={form.name}
          placeholder="Your Name"
          onChange={handleChange}
          className={errors.name ? "error" : ""}
        />
        {errors.name && <span className="error-msg">{errors.name}</span>}
        <input
          type="email"
          name="email"
          value={form.email}
          placeholder="Your Email"
          onChange={handleChange}
          className={errors.email ? "error" : ""}
        />
        {errors.email && <span className="error-msg">{errors.email}</span>}
        <textarea
          name="message"
          value={form.message}
          placeholder="Your Message"
          onChange={handleChange}
          className={errors.message ? "error" : ""}
        />
        {errors.message && <span className="error-msg">{errors.message}</span>}
        <button type="submit">Send Message</button>
      </form>
      {submitted && (
        <div className="success-animation">
          <span>✓</span> Thank you for contacting us!
        </div>
      )}
      <div className="social-links">
        <span>Connect with us: </span>
        <a href="#"><i className="fab fa-whatsapp"></i></a>
        <a href="#"><i className="fab fa-linkedin"></i></a>
        <a href="#"><i className="fab fa-instagram"></i></a>
      </div>
      {/* Embed Google Map */}
      <div className="map-container">
        <iframe
          title="Our Location"
          src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d224346.25056719397!2d77.06889928495473!3d28.527218042586856!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x390ce3a2f36be305%3A0x342d126d5ae5be8b!2sDelhi!5e0!3m2!1sen!2sin!4v1692182831187!5m2!1sen!2sin"
          width="100%"
          height="150"
          style={{ border: 0, borderRadius: "8px" }}
          allowFullScreen=""
          loading="lazy"
        />
      </div>
    </div>

    </>
  );
}

export default Contact;
