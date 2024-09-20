"use client";

import React, {
  useState,
  ChangeEvent,
  KeyboardEvent,
  useRef,
  useEffect,
} from "react";
import {
  Button,
  Paper,
  Typography,
  TextareaAutosize,
  CircularProgress,
} from "@mui/material";
import { Send, Upload, RotateCcw, Settings } from "lucide-react";
import "../styles/chatbotInterface.css";

interface Message {
  text: string;
  sender: "user" | "bot" | "system";
}

const ChatbotInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false); // New loading state
  const [file, setFile] = useState<File | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSend = async (): Promise<void> => {
    if (input.trim()) {
      // Append user's message to the chat
      setMessages([...messages, { text: input, sender: "user" }]);
      setInput(""); // Clear the input after sending the message

      setLoading(true); // Set loading to true when request starts

      try {
        // Send the message to the Flask backend
        const response = await fetch("http://127.0.0.1:5000/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ prompt: input }), // send the input as prompt
          credentials: "include",
        });

        // Handle backend response
        if (response.ok) {
          const data = await response.json();
          const botResponse = data.response; // The response from the backend

          // Append bot's response to the chat
          setMessages((prev) => [
            ...prev,
            { text: botResponse, sender: "bot" },
          ]);
        } else {
          console.error("Failed to fetch response from the backend");
          setMessages((prev) => [
            ...prev,
            {
              text: "Error: Failed to get a response from the server",
              sender: "system",
            },
          ]);
        }
      } catch (error) {
        console.error("Error while sending message:", error);
        setMessages((prev) => [
          ...prev,
          { text: "Error: Failed to connect to the server", sender: "system" },
        ]);
      } finally {
        setLoading(false); // Set loading to false once the request completes
      }
    }
  };

  const handleFileUpload = (event: ChangeEvent<HTMLInputElement>): void => {
    const files = event.target.files;
    if (files && files[0]) {
      const uploadedFile = files[0];
      if (uploadedFile.name.endsWith(".csv")) {
        setFile(uploadedFile);
        setMessages((prev) => [
          ...prev,
          { text: `Uploaded: ${uploadedFile.name}`, sender: "system" },
        ]);
      } else {
        alert("Please upload a CSV file");
      }
    }
  };

  const handleKeyPress = (event: KeyboardEvent<HTMLTextAreaElement>): void => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend(); // Simulate clicking the send button on Enter
    }
  };

  const handleReset = async (): Promise<void> => {
    try {
      await fetch("http://127.0.0.1:5000/reset", {
        method: "POST",
        credentials: "include",
      });
      setMessages([]); // Clear the messages on the frontend
    } catch (error) {
      console.error("Error resetting conversation:", error);
    }
  };

  return (
    <div className="body">
      <div className="title-container">
        {/* App title */}
        <div className="title">
          <h1 className="title-text">🌊 OceanGPT</h1>
        </div>
        {/* Reset button */}
        <div className="reset-container">
          <Button onClick={handleReset}>
            <RotateCcw />
          </Button>
        </div>
        {/* Settings button */}
        <div className="settings-container">
          <Button>
            <Settings />
          </Button>
        </div>
      </div>
      <div className="chat-area">
        <Paper elevation={3} className="chat-paper">
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.sender}`}>
              <Typography variant="body1">{message.text}</Typography>
            </div>
          ))}

          {/* Show a loading text when waiting for the bot's response */}
          {loading && (
            <div className="message bot">
              <CircularProgress size={20} />{" "}
              {/* Replace this with a loading spinner */}
            </div>
          )}

          <div ref={chatEndRef} />
        </Paper>
      </div>
      <div className="user-input-area">
        <div className="upload-btn-container">
          <Button component="label">
            <Upload size={20} />
            <input
              type="file"
              hidden
              accept=".csv"
              onChange={handleFileUpload}
            />
          </Button>
        </div>
        <div className="user-input">
          <TextareaAutosize
            className="custom-textarea"
            minRows={1}
            maxRows={4}
            placeholder="Type your message..."
            value={input}
            onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
              setInput(e.target.value)
            }
            onKeyPress={handleKeyPress} // Handle key press event here
          />
        </div>
        <div className="send-btn">
          <Button onClick={handleSend} disabled={loading}>
            <Send size={20} />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatbotInterface;
