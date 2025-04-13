import "@/styles/Home.css";

interface HomeProps {
  onBookAppointment: () => void;
}

export default function Home({ onBookAppointment }: HomeProps) {
  return (
    <div>
      <header>
        <h1>
          PASTE
          <br />
          DENTAL
        </h1>
      </header>

      <section className='hero'>
        <div className='hero-text'>
          <p>Dental Care Expert Located in the Heart of Toronto</p>
          <h2>
            Dental
            <br />
            Care
          </h2>
          <button onClick={onBookAppointment}>Book an Appointment</button>
        </div>
        <img src='clinic-entrance.webp' alt='Clinic Entrance' />
      </section>

      <section className='healthy-smile'>
        <img
          src='clinic-chair.jpeg'
          alt='Smiling Patient
        '
        />

        <div className='healthy-smile-text'>
          <h2>Crafting Healthy Smiles One Service at a Time</h2>
          <p>
            Our clients are our priority, we offer quality dental services with
            a team of specialist. We provide the best dental care in the city
            with a team of experienced professionals. Your smile is our
            priority.
          </p>
          <button>About Clinic</button>
        </div>
      </section>

      <section className='oral-health'>
        <img src='dental-tools.webp' alt='Dental Tools' />
        <h2>Elevating Oral Health with Personalized Services</h2>

        <div className='services'>
          <div className='service'>
            <h3>General Dentistry</h3>
            <p>
              Regular dental checkups are essential for maintaining oral health.
            </p>
            <hr />
            <li>Routine Check-ups & Teeth Cleaning</li>
            <li>Tooth-Colored Fillings</li>
            <li>Preventive Care</li>
          </div>

          <div className='service'>
            <h3>Cosmetic Dentistry</h3>
            <p>
              Get a brighter smile with our professional teeth whitening
              services.
            </p>
            <hr />
            <li>Veneers & Smile Makeovers</li>
            <li>Teeth Whitening</li>
            <li>Invisalign</li>
          </div>

          <div className='service'>
            <h3>Restorative Dentistry</h3>
            <p>
              Professional dental cleaning helps prevent gum disease and tooth
              decay.
            </p>
            <hr />
            <li>Dentures & Partials</li>
            <li>Crowns & Bridges</li>
            <li>Dental Implants</li>
          </div>
        </div>
      </section>

      <section className='contact'>
        <div className='text'>
          <h2>Contact Us</h2>
          <p>Phone: (123) 456-7890</p>
          <p>Email: contact@dentalclinic.com</p>
          <p>Address: 123 Dental St, Tooth City</p>
        </div>
        <img src='clinic-desk.jpeg' alt='Contact Us' />
      </section>
    </div>
  );
}
