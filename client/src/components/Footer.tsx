export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer>
      <div className="footer-container">
        <div className="footer-column">
          <h3>PASTE DENTAL</h3>
          <p>Professional dental care in the heart of Toronto, providing comprehensive services with a focus on patient comfort and satisfaction.</p>
          <div className="footer-social">
            <a href="#" aria-label="Facebook">FB</a>
            <a href="#" aria-label="Instagram">IG</a>
            <a href="#" aria-label="Twitter">TW</a>
            <a href="#" aria-label="LinkedIn">LI</a>
          </div>
        </div>

        <div className="footer-column">
          <h3>Our Services</h3>
          <ul className="footer-links">
            <li><a href="#">General Dentistry</a></li>
            <li><a href="#">Cosmetic Dentistry</a></li>
            <li><a href="#">Restorative Dentistry</a></li>
            <li><a href="#">Emergency Dental Care</a></li>
            <li><a href="#">Pediatric Dentistry</a></li>
          </ul>
        </div>

        <div className="footer-column">
          <h3>Working Hours</h3>
          <ul className="footer-links">
            <li>Monday - Friday: 9:00 AM - 6:00 PM</li>
            <li>Saturday: 9:00 AM - 4:00 PM</li>
            <li>Sunday: Closed</li>
            <li>Emergency: 24/7 Available</li>
          </ul>
        </div>

        <div className="footer-column">
          <h3>Contact Us</h3>
          <ul className="footer-links">
            <li className="contact-detail">
              <span className="contact-icon">📍</span>
              <span>123 Dental St, Toronto, ON</span>
            </li>
            <li className="contact-detail">
              <span className="contact-icon">📞</span>
              <span>(123) 456-7890</span>
            </li>
            <li className="contact-detail">
              <span className="contact-icon">✉️</span>
              <span>contact@pastedental.com</span>
            </li>
          </ul>
        </div>
      </div>
      
      <div className="footer-bottom">
        <p>&copy; {currentYear} Paste Dental. All rights reserved.</p>
      </div>
    </footer>
  );
}
