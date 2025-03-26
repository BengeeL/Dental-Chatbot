import "@/styles/global.css";
import Home from "./pages/Home";
import Footer from "./components/Footer";
import Chatbot from "./components/Chatbot";

function App() {
  return (
    <div className='page'>
      <div className='page-content'>
        <Home />
        <Chatbot />
      </div>

      <Footer />
    </div>
  );
}

export default App;
