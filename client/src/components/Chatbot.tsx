import { useEffect, useState, useRef, useCallback } from "react";
import "@/styles/chatbot.css";
import axios from "axios";
import config from "../config";

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
      
      const response = await axios.post(`${config.API_BASE_URL}/speech`, {
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
      const response = await axios.post(`${config.API_BASE_URL}/chat`, {
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
            console.log("Audio converted to base64, size:", base64data.length);
            
            try {
              // Send audio to transcribe endpoint
              console.log("Sending audio to transcribe endpoint...");
              const transcribeResponse = await axios.post(`${config.API_BASE_URL}/transcribe`, {
                audio: base64data,
                content_type: 'audio/webm'
              });
              
              console.log("Transcribe response:", transcribeResponse.data);
              
              if (transcribeResponse.data.text) {
                const transcribedText = transcribeResponse.data.text;
                console.log("Transcribed text:", transcribedText);
                
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
              } else if (transcribeResponse.data.error) {
                console.error("Transcription error:", transcribeResponse.data.error);
                setIsLoading(false);
                
                // Add an error message to the chat
                const errorMessage: Message = {
                  id: Date.now(),
                  text: "Sorry, I couldn't understand the audio. Please try again or type your message.",
                  time: new Date().toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  }),
                  date: new Date().toLocaleDateString(),
                  sender: "bot",
                };
                
                setMessages((prevMessages) => [...prevMessages, errorMessage]);
              } else {
                setIsLoading(false);
                console.error("Empty transcription result");
              }
            } catch (error) {
              setIsLoading(false);
              console.error("Error transcribing audio:", error);
              
              // Add an error message to the chat
              const errorMessage: Message = {
                id: Date.now(),
                text: "Sorry, there was an error processing your audio. Please try again later or type your message.",
                time: new Date().toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                }),
                date: new Date().toLocaleDateString(),
                sender: "bot",
              };
              
              setMessages((prevMessages) => [...prevMessages, errorMessage]);
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
      
      // Add visual indication that processing is happening
      setIsLoading(true);
    }
  };

  // Make saveConversation function stable with useCallback to avoid dependency issues
  const saveConversation = useCallback(async () => {
    if (messages.length > 1 && sessionId) { // Only save if there are actual messages
      try {
        await axios.post(`${config.API_BASE_URL}/save-conversation`, {
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
            <div className="chatbot-logo">
              <svg viewBox="0 0 24 24">
                <path d="M19 2H5C3.9 2 3 2.9 3 4V18C3 19.1 3.9 20 5 20H9L12 23L15 20H19C20.1 20 21 19.1 21 18V4C21 2.9 20.1 2 19 2M13.88 12.88L12 17L10.12 12.88L6 11L10.12 9.12L12 5L13.88 9.12L18 11L13.88 12.88M15.25 9.5L14.04 7.04L11.5 5.75L14.04 4.46L15.25 2L16.46 4.46L19 5.75L16.46 7.04L15.25 9.5M18.5 15.5L17.9 14.4L16.8 13.8L17.9 13.2L18.5 12L19.1 13.2L20.2 13.8L19.1 14.4L18.5 15.5Z" />
              </svg>
              <h3>Dental Assistant</h3>
            </div>
            <div className="chatbot-controls-header">
              {/* Modern toggle switch for auto-speak */}
              <label className="toggle-switch">
                <span className="toggle-switch__label">Auto-speak</span>
                <input 
                  type="checkbox" 
                  checked={autoSpeakResponses} 
                  onChange={() => setAutoSpeakResponses(!autoSpeakResponses)} 
                />
                <div className="toggle-switch__track">
                  <div className="toggle-switch__thumb"></div>
                </div>
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
                      <svg viewBox="0 0 24 24">
                        <path d="M14,3.23V5.29C16.89,6.15 19,8.83 19,12C19,15.17 16.89,17.84 14,18.7V20.77C18,19.86 21,16.28 21,12C21,7.72 18,4.14 14,3.23M16.5,12C16.5,10.23 15.5,8.71 14,7.97V16C15.5,15.29 16.5,13.76 16.5,12M3,9V15H7L12,20V4L7,9H3Z" />
                      </svg>
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
              title={isRecording ? "Stop recording" : "Start recording"}
            >
              {isRecording ? (
                <svg viewBox="0 0 24 24">
                  <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4M9,9V15H15V9" />
                </svg>
              ) : (
                <svg viewBox="0 0 24 24">
                  <path d="M12,2A3,3 0 0,1 15,5V11A3,3 0 0,1 12,14A3,3 0 0,1 9,11V5A3,3 0 0,1 12,2M19,11C19,14.53 16.39,17.44 13,17.93V21H11V17.93C7.61,17.44 5,14.53 5,11H7A5,5 0 0,0 12,16A5,5 0 0,0 17,11H19Z" />
                </svg>
              )}
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
