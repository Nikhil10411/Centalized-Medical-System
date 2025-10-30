import React, { useEffect } from "react";
import "./Notification.css";

const Notification = ({ message, type = "info", duration = 3000, onClose }) => {
  useEffect(() => {
    if (!message) return;
    const timer = setTimeout(() => onClose && onClose(), duration);
    return () => clearTimeout(timer);
  }, [message, duration, onClose]);

  if (!message) return null;

  return (
    <div className={`notification notification-${type}`}>
      <span>{message}</span>
      <button className="close-btn" onClick={onClose}>
        ×
      </button>
    </div>
  );
};

export default Notification;
