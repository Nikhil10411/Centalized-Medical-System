import React from "react";
import Slider from "react-slick";
import { Link } from "react-router-dom";
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";
import "./Carousel.css";

import user from "../assets/User.jpeg";
import doctor from "../assets/Doctor.jpeg";
import hospital from "../assets/Hospital.jpeg";
import lab from "../assets/Lab.jpeg";
import medical from "../assets/Medical.jpeg";
import pharmacy from "../assets/Pharmacy.jpeg";
import nurse from "../assets/Nurse3.jpeg";
import radiologist from "../assets/Radiologist4.jpeg";
import dispensary from "../assets/Nurse3.jpeg";

const slides = [
  { image: user, title: "Register as Patient", link: "/patient-registration" },
  { image: doctor, title: "Register as Doctor", link: "/doctor-registration" },
//  { image: hospital, title: "Register as Hospital", link: "/hospital-registration" },
//  { image: lab, title: "Register as Lab", link: "/lab-registration" },
  { image: medical, title: "Register as Medical Store", link: "/medical-store-registration" },
  { image: pharmacy, title: "Register as Supplier", link: "/supplier-registration" },
//  { image: nurse, title: "Register as Nurse", link: "/nurse-registration" },
//  { image: dispensary, title: "Register as Dispensary", link: "/dispensary-registration" },
//  { image: radiologist, title: "Register as Radiologist", link: "/radiologist-registration" },
];

const Carousel = () => {
  const settings = {
    dots: true,
    infinite: true,
    speed: 800,
    slidesToShow: 1,
    slidesToScroll: 1,
    autoplay: true,
    autoplaySpeed: 3500,
    arrows: true,
    pauseOnHover: true,
    fade: true,
    afterChange: () => {
      document.querySelectorAll(".slide-btn").forEach((btn) => {
        btn.style.animation = "none";
        btn.offsetHeight; // trigger reflow
        btn.style.animation = "";
      });
    },
  };

  return (
    <div className="carousel-container">
      <Slider {...settings}>
        {slides.map((slide, index) => (
          <div key={index} className="carousel-slide">
            <img src={slide.image} alt={slide.title} className="carousel-img" />
            <div className="overlay">
              <h2 className="slide-title">{slide.title}</h2>
              <Link to={slide.link}>
                <button className="slide-btn">Register</button>
              </Link>
            </div>
          </div>
        ))}
      </Slider>
    </div>
  );
};

export default Carousel;


