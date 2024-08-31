import React, { useState } from 'react';
import styles from './UserRegistrationForm.module.css'; // Import the CSS module

const UserRegistrationForm = () => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    location: '',
    aadhaar: ''
  });

  const indianCities = ['Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Kolkata', 'Pune', 'Hyderabad', 'Ahmedabad'];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log(formData);
  };

  return (
    <div className={styles.backgroundImageContainer}>
      <div className={styles.formContainer}>
        <h2>Register</h2>
        <form onSubmit={handleSubmit}>
          <input 
            type="text" 
            name="firstName" 
            placeholder="First Name" 
            value={formData.firstName} 
            onChange={handleInputChange} 
            className={styles.inputField}
            required 
          />
          <input 
            type="text" 
            name="lastName" 
            placeholder="Last Name" 
            value={formData.lastName} 
            onChange={handleInputChange} 
            className={styles.inputField}
            required 
          />
          <input 
            type="email" 
            name="email" 
            placeholder="Email Address" 
            value={formData.email} 
            onChange={handleInputChange} 
            className={styles.inputField}
            required 
          />
          <input 
            type="tel" 
            name="phone" 
            placeholder="Phone Number" 
            value={formData.phone} 
            onChange={handleInputChange} 
            className={styles.inputField}
            required 
          />
          <select 
            name="location" 
            value={formData.location} 
            onChange={handleInputChange} 
            className={styles.selectField}
            required 
          >
            <option value="">Select City</option>
            {indianCities.map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
          </select>
          <input 
            type="text" 
            name="aadhaar" 
            placeholder="Aadhaar Card Number" 
            value={formData.aadhaar} 
            onChange={handleInputChange} 
            className={styles.inputField}
            required 
          />
          <button type="submit" className={styles.submitButton}>Submit</button>
        </form>
      </div>
    </div>
  );
};

export default UserRegistrationForm;
