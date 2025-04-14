import "@/styles/global.css";
import { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Footer from "./components/Footer";
import Chatbot from "./components/Chatbot";
import Authentication from "./pages/Authentication";
import Dashboard from "./pages/Dashboard";

function App() {
  const [openChatbot, setOpenChatbot] = useState(false);

  // Handle the book appointment action - open the chatbot
  const handleBookAppointment = () => {
    setOpenChatbot(true);
  };

  // Reset the openChatbot state after some time to allow re-opening
  useEffect(() => {
    if (openChatbot) {
      const timer = setTimeout(() => {
        setOpenChatbot(false);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [openChatbot]);

  return (
    <Router>
      <div className='page'>
        <div className='page-content'>
          <Routes>
            {/* Home route */}
            <Route
              path='/'
              element={<Home onBookAppointment={handleBookAppointment} />}
            />

            {/* Authentication route */}
            <Route path='/auth' element={<Authentication />} />

            <Route path='dashboard' element={<Dashboard />} />

            {/* 404 Not Found route */}
            <Route
              path='*'
              element={
                <div className='not-found'>
                  <h1>404 Not Found</h1>
                  <p>The page you are looking for does not exist.</p>
                  <a href='/'>Go back to Home</a>
                </div>
              }
            />
          </Routes>

          {/* Chatbot component (always rendered) */}
          <Chatbot open={openChatbot} />
        </div>

        <Footer />
      </div>
    </Router>
  );
}

export default App;
