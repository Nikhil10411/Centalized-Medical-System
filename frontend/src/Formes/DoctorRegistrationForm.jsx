import React, { useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import './DoctorRegistrationForm.css'; // Import the CSS file

function DoctorRegistrationForm() {
  const [formData, setFormData] = useState({
    doctorName: '',
    doctorAge: '',
    gender: '',
    doctorPhoneNumber: '',
    doctorAltPhoneNumber: '',
    aadhaarNumber: '',
    doctorPhoto: null,
    doctorCity: '',
    cityPinCode: '',
    degreePassOutYear: null, // Initialize with null for date picker
    regulatoryBody: '',
    areaOfPractice: '',
    licenseFile: null,
    houseAddress: '',
    hospitalName: '',
    hospitalCity: '',
    hospitalPinCode: '',
    hospitalAddress: '',
  });

  const handleFileUpload = (event) => {
    setFormData({
      ...formData,
      [event.target.name]: event.target.files[0],
    });
  };

  const handleChange = (event) => {
    setFormData({
      ...formData,
      [event.target.name]: event.target.value,
    });
  };

  const handleDateChange = (date) => {
    setFormData({
      ...formData,
      degreePassOutYear: date,
    });
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    // Handle form submission
    console.log(formData);
  };

  return (
    <div className="form-container">
      <form onSubmit={handleSubmit} className="doctor-registration-form">
        <h2 className="form-heading">Register as a Doctor</h2> {/* Heading */}
        <input type="text" name="doctorName" placeholder="Doctor Name" onChange={handleChange} />

        <select name="doctorAge" onChange={handleChange}>
          <option value="">Select Age</option>
          {Array.from({ length: 83 }, (_, i) => (
            <option key={i + 18} value={i + 18}>
              {i + 18}
            </option>
          ))}
        </select>

        <select name="gender" onChange={handleChange}>
          <option value="">Select Gender</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
          <option value="preferNotToSay">Prefer not to say</option>
        </select>

        <input type="text" name="doctorPhoneNumber" placeholder="Doctor Phone Number" onChange={handleChange} />
        <input type="text" name="doctorAltPhoneNumber" placeholder="Alternative Phone Number" onChange={handleChange} />
        <input type="text" name="aadhaarNumber" placeholder="Aadhaar Number" onChange={handleChange} />

        <input type="file" name="doctorPhoto" accept=".jpeg, .jpg" onChange={handleFileUpload} />

        <select name="doctorCity" onChange={handleChange}>
          <option value="">Select City of Residence</option>
          <option value="mumbai">Mumbai</option>
          <option value="delhi">Delhi</option>
          <option value="bangalore">Bangalore</option>
          <option value="chennai">Chennai</option>
          <option value="kolkata">Kolkata</option>
          <option value="hyderabad">Hyderabad</option>
          <option value="pune">Pune</option>
          {/* Add more cities as needed */}
        </select>

        <input type="number" name="cityPinCode" placeholder="City Pin Code" onChange={handleChange} />

        <DatePicker
          selected={formData.degreePassOutYear}
          onChange={handleDateChange}
          showYearPicker
          dateFormat="yyyy"
          placeholderText="Select Degree Pass-out Year"
        />

        <select name="regulatoryBody" onChange={handleChange}>
          <option value="">Select Regulatory Body</option>
          <option value="mci">Medical Council of India (MCI)</option>
          <option value="dci">Dental Council of India (DCI)</option>
          <option value="inc">Indian Nursing Council (INC)</option>
          <option value="pci">Pharmacy Council of India (PCI)</option>
          {/* Add more options as needed */}
        </select>

        <select name="areaOfPractice" onChange={handleChange}>
          <option value="">Select Area of Practice</option>
          <option value="general">General Practice</option>
          <option value="cardiology">Cardiology</option>
          <option value="dermatology">Dermatology</option>
          <option value="pediatrics">Pediatrics</option>
          <option value="neurology">Neurology</option>
          {/* Add more options as needed */}
        </select>

        <input type="file" name="licenseFile" accept=".jpeg, .jpg" onChange={handleFileUpload} />

        <input type="text" name="houseAddress" placeholder="House Address" onChange={handleChange} />
        <input type="text" name="hospitalName" placeholder="Hospital/Clinic Name" onChange={handleChange} />

        <select name="hospitalCity" onChange={handleChange}>
          <option value="">Select Hospital City</option>
          <option value="mumbai">Mumbai</option>
          <option value="delhi">Delhi</option>
          <option value="bangalore">Bangalore</option>
          <option value="chennai">Chennai</option>
          <option value="kolkata">Kolkata</option>
          <option value="hyderabad">Hyderabad</option>
          <option value="pune">Pune</option>
          {/* Add more cities as needed */}
        </select>

        <input type="number" name="hospitalPinCode" placeholder="Hospital Pin Code" onChange={handleChange} />
        <input type="text" name="hospitalAddress" placeholder="Hospital Address" onChange={handleChange} />

        <button type="submit">Register Doctor</button>
      </form>
    </div>
  );
}

export default DoctorRegistrationForm;
