import { useEffect, useState, useRef } from "react";
import "@/styles/Chatbot.css";
import axios from "axios";

interface Message {
  id: number;
  text: string;
  time: string;
  date: string;
  sender: "user" | "bot";
  status?: "sent" | "received" | "seen" | "ok";
}

export default function Chatbot() {
  const [showChatbox, setShowChatbox] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
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

    const newMessage: Message = {
      id: Date.now(), // Use a unique timestamp as the ID
      text: newMessages,
      time: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      date: new Date().toLocaleDateString(),
      sender: "user",
      status: "sent",
    };

    setMessages([...messages, newMessage]);
    const message = newMessages;
    setNewMessages("");
    setTimeout(() => {
      botResponse(message);
    }, 2000);
  }

  async function botResponse(message: string) {
    const response = await axios.post("http://localhost:8085/chat", {
      message: message,
    });
    let botMessage: Message;

    if (response.data.status === "ok") {
      botMessage = {
        id: Date.now() + 1, // Ensure a unique ID for the bot message
        text: response.data.text,
        time: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        date: new Date().toLocaleDateString(),
        sender: "bot",
      };
    } else {
      console.error("Error: ", response.data.text);
      botMessage = {
        id: Date.now() + 1, // Ensure a unique ID for the bot message
        text: "Sorry, I couldn't understand your message.",
        time: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        date: new Date().toLocaleDateString(),
        sender: "bot",
      };
    }

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
                }
              }}
            />
            <button
              className='send-message-button'
              onClick={() => {
                addMessage();
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
