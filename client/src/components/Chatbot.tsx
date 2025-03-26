import { useEffect, useState, useRef } from "react";

export default function Chatbot() {
  const [showChatbox, setShowChatbox] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hi! How can we help you today?",
      sender: "bot",
      time: "12:00",
    },
    {
      id: 2,
      text: "I have a question about my appointment",
      sender: "user",
      time: "12:01",
    },
    {
      id: 3,
      text: "Sure, what would you like to know?",
      sender: "bot",
      time: "12:02",
    },
  ]);
  const [newMessages, setNewMessages] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  function updateShowChatbox() {
    setShowChatbox(!showChatbox);
    setTimeout(scrollToBottom, 100);
  }

  function addMessage() {
    if (newMessages.trim() === "") {
      return;
    }

    const newMessage = {
      id: messages.length + 1,
      text: newMessages,
      sender: "user",
      time: "12:03",
    };

    setMessages([...messages, newMessage]);
    setNewMessages("");
  }

  function botResponse() {
    const botMessage = {
      id: messages.length + 2,
      text: "I'm a bot. I don't have the answer to that question.",
      sender: "bot",
      time: "12:04",
    };

    setMessages((prevMessages) => [...prevMessages, botMessage]);
  }

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  function scrollToBottom() {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    } else {
      console.log("No ref");
    }
  }

  return (
    <div className='chatbot'>
      {showChatbox && (
        <div className='chatbot-container'>
          <div className='chatbot-header'>
            <h3>Chat with us</h3>
            <button className='close-chat' onClick={() => updateShowChatbox()}>
              X
            </button>
          </div>

          <div className='chatbot-messages'>
            <div className='welcome-message'>
              <h3>Hi! How can we help you today?</h3>
            </div>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`message ${
                  message.sender === "user" ? "user" : "bot"
                }`}
              >
                {message.text}
                <div className='message-time'>{message.time}</div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className='chatbot-input'>
            <input
              className='message-input'
              type='text'
              placeholder='Type your message...'
              value={newMessages}
              onChange={(e) => setNewMessages(e.target.value)}
              onKeyUp={(e) => {
                if (e.key === "Enter") {
                  addMessage();
                  setTimeout(botResponse, 2000);
                }
              }}
            />
            <button
              className='send-message-button'
              onClick={() => {
                addMessage();
                setTimeout(botResponse, 2000);
              }}
            >
              Send
            </button>
          </div>
        </div>
      )}

      <button
        className='chatbot-chat-button'
        onClick={() => updateShowChatbox()}
      >
        ?
      </button>
    </div>
  );
}
