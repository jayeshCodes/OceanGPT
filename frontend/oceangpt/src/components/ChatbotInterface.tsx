"use client";

import React, { useState, ChangeEvent, KeyboardEvent, useRef, useEffect } from "react";
import {
  Button,
  TextField,
  Paper,
  List,
  ListItem,
  ListItemText,
  Typography,
  TextareaAutosize,
} from "@mui/material";
import { Input } from "@mui/base";
import { Button as BaseButton, buttonClasses } from "@mui/base/Button";
import { Send, Upload } from "lucide-react";
import "../styles/chatbotInterface.css";

interface Message {
  text: string;
  sender: "user" | "bot" | "system";
}

const ChatbotInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSend = (): void => {
    if (input.trim()) {
      setMessages([...messages, { text: input, sender: "user" }]);
      // Here you would typically send the message to your chatbot backend
      // and get a response. For this example, we'll just echo the message.
      setTimeout(() => {
        setMessages((prev) => [
          ...prev,
          { text: `You said: ${input}`, sender: "bot" },
        ]);
      }, 500);
      setInput("");
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
      handleSend();
    }
  };

  return (
    <div className="body">
      <div className="title-container">
        <h1 className="title">🌊 OceanGPT</h1>
      </div>
      <div className="chat-area">
        <Paper elevation={3} className="chat-paper">
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.sender}`}>
              <Typography variant="body1">{message.text}</Typography>
            </div>
          ))}
          <div ref={chatEndRef} />
        </Paper>
      </div>
      <div className="user-input-area">
        <div className="upload-btn-container">
          <Button component="label">
            <Upload size={20} />
            <input type="file" hidden accept=".csv" onChange={handleFileUpload} />
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
            onKeyPress={handleKeyPress}
          />
        </div>
        <div className="send-btn">
          <Button onClick={handleSend}>
            <Send size={20} />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatbotInterface;