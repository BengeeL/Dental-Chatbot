import { useState } from "react";

export default function Chatbot() {
  const [showChatbox, setShowChatbox] = useState(false);

  return (
    <div className='chatbot'>
      {showChatbox && (
        <div className='chatbot-container'>
          <div className='chatbot-header'>
            <h3>Chat with us</h3>
            <button>Close</button>
          </div>
        </div>
      )}

      <button
        className='chatbot-chat-button'
        onClick={() => setShowChatbox(!showChatbox)}
      >
        ?
      </button>
    </div>
  );
}
