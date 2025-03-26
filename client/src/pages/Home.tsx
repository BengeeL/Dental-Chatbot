import "@/styles/Home.css";

export default function Home() {
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
          <button>Book an Appointment</button>
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

      <section>
        <h2>Our Services</h2>
        <ul>
          <li>General Dentistry</li>
          <li>Cosmetic Dentistry</li>
          <li>Orthodontics</li>
          <li>Oral Surgery</li>
        </ul>
      </section>

      <section>
        <h2>Contact Us</h2>
        <p>Phone: (123) 456-7890</p>
        <p>Email: contact@dentalclinic.com</p>
        <p>Address: 123 Dental St, Tooth City</p>
      </section>
    </div>
  );
}
