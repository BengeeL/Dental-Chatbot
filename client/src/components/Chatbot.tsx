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
  audio?: string; // Base64 encoded audio
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
  const [isPlayingAudio, setIsPlayingAudio] = useState<number | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Voice recording states
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  // Auto speech toggle
  const [autoSpeakResponses, setAutoSpeakResponses] = useState(false);

  // Generate or retrieve a session ID when the component mounts
  useEffect(() => {
    const storedSessionId = localStorage.getItem('dental_chat_session');
    if (storedSessionId) {
      setSessionId(storedSessionId);
    } else {
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

  // Function to convert text to speech using Amazon Polly - define BEFORE botResponse
  const textToSpeech = useCallback(async (text: string, messageId: number) => {
    try {
      setIsPlayingAudio(messageId);
      console.log("Requesting speech synthesis for:", text.substring(0, 30) + "...");
      
      const response = await axios.post("http://localhost:8000/speech", {
        text: text,
        voice: "Joanna"
      });
      
      if (response.data.audio) {
        console.log("Received audio data, length:", response.data.audio.length);
        
        // Create audio element
        const audio = new Audio(`data:audio/mp3;base64,${response.data.audio}`);
        audioRef.current = audio;
        
        // Add event listeners for debugging
        audio.oncanplay = () => console.log("Audio can play now");
        audio.onerror = (e) => console.error("Audio error:", e);
        audio.onended = () => {
          console.log("Audio playback ended");
          setIsPlayingAudio(null);
        };
        
        // Play with user interaction handling
        const playPromise = audio.play();
        
        if (playPromise !== undefined) {
          playPromise
            .then(() => {
              console.log("Audio playback started successfully");
            })
            .catch(error => {
              console.error("Playback prevented by browser:", error);
              // Reset playing state on error
              setIsPlayingAudio(null);
              
              // Alert the user about autoplay restrictions if that's the issue
              if (error.name === "NotAllowedError") {
                console.warn("Audio playback was prevented due to browser autoplay policy");
                // You could show a UI notification here if needed
              }
            });
        }
      } else {
        console.error("No audio data in response");
        setIsPlayingAudio(null);
      }
    } catch (error) {
      console.error("Error converting text to speech:", error);
      setIsPlayingAudio(null);
    }
  }, []);

  // Send message to bot and get response
  const botResponse = useCallback(async (message: string) => {
    try {
      const response = await axios.post("http://localhost:8000/chat", {
        message: message,
        session_id: sessionId
      }, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        withCredentials: false
      });
      
      let botMessage: Message;

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

        setMessages((prevMessages) => [...prevMessages, botMessage]);
        
        // Auto-speak the response if enabled - moved after adding message to state
        if (autoSpeakResponses) {
          console.log("Auto-speak is enabled, playing audio...");
          setTimeout(() => {
            textToSpeech(response.data.text, botMessage.id);
          }, 800); // Increased timeout to ensure message is rendered first
        }
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
        
        setMessages((prevMessages) => [...prevMessages, botMessage]);
      }
    } catch (error) {
      console.error("Error communicating with the server:", error);
      
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
      setIsLoading(false);
    }
  }, [sessionId, autoSpeakResponses, textToSpeech]);

  // Handle initial message if provided
  useEffect(() => {
    if (initialMessage && showChatbox && !initialMessageSentRef.current) {
      initialMessageSentRef.current = true;
      
      if (messages.length === 0) {
        const welcomeMessage = createWelcomeMessage();
        welcomeMessageRef.current = welcomeMessage;
        setMessages([welcomeMessage]);
      }
      
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
      // Save conversation before closing
      saveConversation();

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
    setIsLoading(true);
    botResponse(message);
  }

  function scrollToBottom() {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  function startNewConversation() {
    // Save current conversation first
    saveConversation();

    const newSessionId = crypto.randomUUID();
    setSessionId(newSessionId);
    localStorage.setItem('dental_chat_session', newSessionId);
    
    setMessages([]);
    setNewMessages("");
    
    const welcomeMessage = createWelcomeMessage();
    welcomeMessageRef.current = welcomeMessage;
    setMessages([welcomeMessage]);
  }

  // Function to start voice recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        
        // Convert blob to base64
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = async () => {
          const base64data = reader.result?.toString().split(',')[1];
          
          if (base64data) {
            setIsLoading(true);
            
            try {
              // Send audio to transcribe endpoint
              const transcribeResponse = await axios.post("http://localhost:8000/transcribe", {
                audio: base64data,
                content_type: 'audio/webm'
              });
              
              if (transcribeResponse.data.text) {
                const transcribedText = transcribeResponse.data.text;
                
                // Add user message with transcribed text
                const newMessage: Message = {
                  id: Date.now(),
                  text: transcribedText,
                  time: new Date().toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  }),
                  date: new Date().toLocaleDateString(),
                  sender: "user",
                  status: "sent",
                };
                
                setMessages((prevMessages) => [...prevMessages, newMessage]);
                botResponse(transcribedText);
              } else {
                setIsLoading(false);
                console.error("Could not transcribe audio");
              }
            } catch (error) {
              setIsLoading(false);
              console.error("Error transcribing audio:", error);
            }
          }
        };
        
        // Stop all tracks on the stream
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
    }
  };

  // Function to stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Make saveConversation function stable with useCallback to avoid dependency issues
  const saveConversation = useCallback(async () => {
    if (messages.length > 1 && sessionId) { // Only save if there are actual messages
      try {
        await axios.post("http://localhost:8000/save-conversation", {
          session_id: sessionId,
          messages: messages.map(msg => ({
            text: msg.text,
            time: msg.time, 
            date: msg.date,
            sender: msg.sender
          }))
        });
        console.log("Conversation saved to S3");
      } catch (error) {
        console.error("Error saving conversation:", error);
      }
    }
  }, [messages, sessionId]);

  // Clean up resources when component unmounts
  useEffect(() => {
    return () => {
      // Stop any playing audio
      if (audioRef.current) {
        audioRef.current.pause();
      }
      
      // Stop any ongoing recording
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop();
      }
      
      // Save conversation
      saveConversation();
    };
  }, [isRecording, saveConversation]);

  useEffect(() => {
    if (!showChatbox && audioRef.current) {
      audioRef.current.pause();
      setIsPlayingAudio(null);
    }
  }, [showChatbox]);

  return (
    <div className='chatbot'>
      {showChatbox && (
        <div className='chatbot-container'>
          <div className='chatbot-header'>
            <h3>Dental Assistant</h3>
            <div className="chatbot-controls-header">
              <label className="auto-speak-toggle">
                <input 
                  type="checkbox" 
                  checked={autoSpeakResponses} 
                  onChange={() => setAutoSpeakResponses(!autoSpeakResponses)} 
                />
                <span className="toggle-label">Auto-speak</span>
              </label>
              <button className='close-chat' onClick={() => updateShowChatbox(false)}>
                X
              </button>
            </div>
          </div>

          <div className='chatbot-messages'>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`message ${
                  message.sender === "user" ? "user" : "bot"
                }`}
              >
                <div className="message-text">{message.text}</div>
                <div className='message-footer'>
                  <div className='message-time'>{message.time}</div>
                  {message.sender === "bot" && (
                    <button 
                      className='listen-button'
                      onClick={() => textToSpeech(message.text, message.id)} 
                      disabled={isPlayingAudio !== null}
                      aria-label="Listen to message"
                    >
                      {isPlayingAudio === message.id ? 'Playing...' : 'Listen'}
                    </button>
                  )}
                </div>
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
              disabled={isLoading || isRecording}
            />
            <button
              className={`voice-input-button ${isRecording ? 'recording' : ''}`}
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isLoading}
            >
              {isRecording ? '🔴 Stop' : '🎤'}
            </button>
            <button
              className='send-message-button'
              onClick={addMessage}
              disabled={isLoading || isRecording}
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
