import "@/styles/Home.css";

interface HomeProps {
  onBookAppointment: () => void;
}

export default function Home({ onBookAppointment }: HomeProps) {
  return (
    <div>
      <header>
        <div className="header-container">
          <div className="logo">
            <h1>PASTE<span>DENTAL</span></h1>
          </div>
          <nav className="nav-links">
            <a href="#home">Home</a>
            <a href="#about">About</a>
            <a href="#services">Services</a>
            <a href="#contact">Contact</a>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className='hero' id="home">
        <img src='clinic-entrance.webp' alt='Modern Dental Clinic' />
        <div className='hero-content'>
          <div className='hero-text'>
            <p>Professional Dental Care in the Heart of Toronto</p>
            <h2>Your Smile, Our Expertise</h2>
            <button className="cta-button" onClick={onBookAppointment}>Book an Appointment</button>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section className='about-section' id="about">
        <div className="about-container">
          <div className="about-image">
            <img src='clinic-chair.jpeg' alt='Modern Dental Chair' />
          </div>
          <div className="about-content">
            <h2>Crafting Healthy Smiles One Service at a Time</h2>
            <p>
              At Paste Dental, our clients are our priority. We offer quality dental services with
              a team of specialists dedicated to providing the finest dental care in Toronto.
            </p>
            <p>
              Our modern facility features state-of-the-art equipment and a comfortable
              environment designed to make your dental experience as pleasant as possible.
              From routine check-ups to complex procedures, your smile is in good hands with our
              experienced professionals.
            </p>
            <button className="about-button">About Our Clinic</button>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className='services-section' id="services">
        <div className="services-header">
          <h2>Elevating Oral Health with Personalized Services</h2>
          <p>Discover our comprehensive range of dental treatments tailored to meet your specific needs</p>
        </div>

        <div className='services-container'>
          <div className='service-card'>
            <h3>General Dentistry</h3>
            <p>
              Regular dental checkups are essential for maintaining optimal oral health.
            </p>
            <hr />
            <ul>
              <li>Routine Check-ups & Teeth Cleaning</li>
              <li>Tooth-Colored Fillings</li>
              <li>Preventive Care & Education</li>
            </ul>
          </div>

          <div className='service-card'>
            <h3>Cosmetic Dentistry</h3>
            <p>
              Transform your smile with our professional cosmetic dental services.
            </p>
            <hr />
            <ul>
              <li>Veneers & Smile Makeovers</li>
              <li>Professional Teeth Whitening</li>
              <li>Clear Aligners & Invisalign</li>
            </ul>
          </div>

          <div className='service-card'>
            <h3>Restorative Dentistry</h3>
            <p>
              Restore function and aesthetics with our advanced restorative treatments.
            </p>
            <hr />
            <ul>
              <li>Custom Dentures & Partials</li>
              <li>Porcelain Crowns & Bridges</li>
              <li>Dental Implants & Restoration</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section className='contact-section' id="contact">
        <div className="contact-container">
          <div className="contact-image">
            <img src='clinic-desk.jpeg' alt='Dental Reception' />
          </div>
          <div className="contact-content">
            <h2>Get in Touch</h2>
            <div className="contact-details">
              <div className="contact-detail">
                <span className="contact-icon">📞</span>
                <span>(123) 456-7890</span>
              </div>
              <div className="contact-detail">
                <span className="contact-icon">✉️</span>
                <span>contact@pastedental.com</span>
              </div>
              <div className="contact-detail">
                <span className="contact-icon">📍</span>
                <span>123 Dental St, Toronto, ON M5V 2K6</span>
              </div>
              <div className="contact-detail">
                <span className="contact-icon">🕒</span>
                <span>Mon-Fri: 9am-6pm | Sat: 9am-4pm</span>
              </div>
            </div>
            <button className="cta-button" onClick={onBookAppointment}>
              Book Your Visit
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
