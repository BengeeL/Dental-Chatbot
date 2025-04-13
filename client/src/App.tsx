import "@/styles/global.css";
import { useState, useEffect } from "react";
import Home from "./pages/Home";
import Footer from "./components/Footer";
import Chatbot from "./components/Chatbot";

function App() {
  const [openChatbot, setOpenChatbot] = useState(false);
  
  // Handle the book appointment action - open the chatbot
  const handleBookAppointment = () => {
    // Simply open the chatbot
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
    <div className='page'>
      <div className='page-content'>
        <Home onBookAppointment={handleBookAppointment} />
        <Chatbot open={openChatbot} />
      </div>

      <Footer />
    </div>
  );
}

export default App;
