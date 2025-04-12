import { useEffect, useState, useRef, useCallback } from "react";
import "@/styles/chatbot.css";
import axios from "axios";

interface Message {
  id: number;
  text: string;
  time: string;
  date: string;
  sender: "user" | "bot";
  status?: "sent" | "received" | "seen" | "ok";
}

interface ChatbotProps {
  initialMessage?: string;
  open?: boolean;
}

export default function Chatbot({ initialMessage, open }: ChatbotProps) {
  const [showChatbox, setShowChatbox] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessages, setNewMessages] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const initialMessageSentRef = useRef(false);
  const welcomeMessageRef = useRef<Message | null>(null);

  // Generate or retrieve a session ID when the component mounts
  useEffect(() => {
    // Try to get existing session ID from localStorage
    const storedSessionId = localStorage.getItem('dental_chat_session');
    if (storedSessionId) {
      setSessionId(storedSessionId);
    } else {
      // Generate a new session ID
      const newSessionId = crypto.randomUUID();
      setSessionId(newSessionId);
      localStorage.setItem('dental_chat_session', newSessionId);
    }
  }, []);

  // Function to create a welcome message
  const createWelcomeMessage = useCallback((): Message => {
    return {
      id: Date.now(),
      text: "Welcome to our Dental Assistant Chatbot! I can help you with:\n\n" +
            "• Booking appointments\n" +
            "• Information about our dental services\n" +
            "• Answering questions about dental procedures\n\n" +
            "To book an appointment, simply type \"I'd like to book an appointment\" or ask me about our available services.\n\n" +
            "How can I assist you today?",
      time: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      date: new Date().toLocaleDateString(),
      sender: "bot",
    };
  }, []);

  // Open chatbox and show welcome message
  const openChatbox = useCallback(() => {
    setShowChatbox(true);
    
    // Add welcome message if there are no messages
    if (messages.length === 0) {
      const welcomeMessage = createWelcomeMessage();
      welcomeMessageRef.current = welcomeMessage;
      setMessages([welcomeMessage]);
    }
    
    setTimeout(scrollToBottom, 100);
  }, [messages, createWelcomeMessage]);

  // Handle the external open prop
  useEffect(() => {
    if (open) {
      openChatbox();
    }
  }, [open, openChatbox]);

  // Send message to bot and get response
  const botResponse = useCallback(async (message: string) => {
    try {
      // Update the axios request with proper CORS configuration
      const response = await axios.post("http://localhost:8085/chat", {
        message: message,
        session_id: sessionId
      }, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        withCredentials: false // Set to false for development
      });
      
      let botMessage: Message;

      // Update the session ID if returned
      if (response.data.session_id) {
        setSessionId(response.data.session_id);
        localStorage.setItem('dental_chat_session', response.data.session_id);
      }

      if (response.data.status === "ok") {
        botMessage = {
          id: Date.now() + 1,
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
          id: Date.now() + 1,
          text: "Sorry, I couldn't understand your message. Can you try again?",
          time: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
          date: new Date().toLocaleDateString(),
          sender: "bot",
        };
      }

      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.error("Error communicating with the server:", error);
      
      // Add an error message to the chat
      const errorMessage: Message = {
        id: Date.now() + 1,
        text: "Sorry, I'm having trouble connecting to the server. Please try again later.",
        time: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        date: new Date().toLocaleDateString(),
        sender: "bot",
      };
      
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false); // Hide loading indicator
    }
  }, [sessionId]);

  // Handle initial message if provided (e.g., from Book Appointment button)
  useEffect(() => {
    if (initialMessage && showChatbox && !initialMessageSentRef.current) {
      // Mark that we've processed this message
      initialMessageSentRef.current = true;
      
      // Make sure we have a welcome message first
      if (messages.length === 0) {
        const welcomeMessage = createWelcomeMessage();
        welcomeMessageRef.current = welcomeMessage;
        setMessages([welcomeMessage]);
      }
      
      // Add a small delay before sending the initial message to allow the welcome message to be seen
      setTimeout(() => {
        const initialUserMessage: Message = {
          id: Date.now(),
          text: initialMessage,
          time: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
          date: new Date().toLocaleDateString(),
          sender: "user",
          status: "sent",
        };
        
        setMessages(prevMessages => [...prevMessages, initialUserMessage]);
        botResponse(initialMessage);
      }, 1000);
    }
  }, [initialMessage, showChatbox, messages, createWelcomeMessage, botResponse]);

  // Reset the initialMessageSentRef when initialMessage changes or chatbox closes
  useEffect(() => {
    if (!showChatbox) {
      initialMessageSentRef.current = false;
    }
  }, [initialMessage, showChatbox]);

  function updateShowChatbox(shouldShow?: boolean) {
    const newState = shouldShow !== undefined ? shouldShow : !showChatbox;
    
    if (newState) {
      openChatbox();
    } else {
      // Clear all messages when closing the chatbox
      setShowChatbox(false);
      setMessages([]);
      setNewMessages("");
      welcomeMessageRef.current = null;
      initialMessageSentRef.current = false;
    }
  }

  function addMessage() {
    if (newMessages.trim() === "") {
      return;
    }

    const newMessage: Message = {
      id: Date.now(),
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
    setIsLoading(true); // Show loading indicator
    botResponse(message);
  }

  function scrollToBottom() {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }

  // Scroll to bottom whenever messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Function to start a new conversation
  function startNewConversation() {
    // Generate a new session ID
    const newSessionId = crypto.randomUUID();
    setSessionId(newSessionId);
    localStorage.setItem('dental_chat_session', newSessionId);
    
    // Clear all messages
    setMessages([]);
    setNewMessages("");
    
    // Add a welcome message from the bot
    const welcomeMessage = createWelcomeMessage();
    welcomeMessageRef.current = welcomeMessage;
    setMessages([welcomeMessage]);
  }

  return (
    <div className='chatbot'>
      {showChatbox && (
        <div className='chatbot-container'>
          <div className='chatbot-header'>
            <h3>Dental Assistant</h3>
            <button className='close-chat' onClick={() => updateShowChatbox(false)}>
              X
            </button>
          </div>

          <div className='chatbot-messages'>
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
            
            {isLoading && (
              <div className="message bot loading">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          <div className='chatbot-controls'>
            <button 
              className='new-conversation-button' 
              onClick={startNewConversation}
              disabled={isLoading}
            >
              Start New Conversation
            </button>
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
              disabled={isLoading}
            />
            <button
              className='send-message-button'
              onClick={addMessage}
              disabled={isLoading}
            >
              Send
            </button>
          </div>
        </div>
      )}

      <button
        className='chatbot-chat-button'
        onClick={() => updateShowChatbox(true)}
      >
        Chat with us
      </button>
    </div>
  );
}
