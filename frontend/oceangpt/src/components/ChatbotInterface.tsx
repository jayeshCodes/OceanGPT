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
import ReactMarkdown from "react-markdown";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import StyledDataGrid from "./StyledDataGrid";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface Message {
  text: string;
  sender: "user" | "bot" | "system";
  data?: any; // Changed from any[] to any to accommodate both chart and grid data
}

const ChatbotInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [file, setFile] = useState<File | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [dataGridRows, setDataGridRows] = useState<any[]>([]);
  const [dataGridColumns, setDataGridColumns] = useState<GridColDef[]>([]);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSend = async (): Promise<void> => {
    if (input.trim()) {
      setMessages([...messages, { text: input, sender: "user" }]);
      setInput("");
      setLoading(true);

      try {
        const response = await fetch("http://127.0.0.1:5000/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ prompt: input }),
          credentials: "include",
        });

        if (response.ok) {
          const data = await response.json();
          console.log("data", data);

          // Extract the bot's textual response
          const botResponse = data.response[0];

          let newMessage: Message = { text: botResponse, sender: "bot" };

          // Check if there's data for the chart or DataGrid
          if (data.response[1]) {
            newMessage.data = data.response[1];
          }

          // Add bot's response message
          setMessages((prev) => [...prev, newMessage]);
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
        setLoading(false);
      }
    }
  };

  const handleFileUpload = async (
    event: ChangeEvent<HTMLInputElement>
  ): Promise<void> => {
    const files = event.target.files;
    if (files && files[0]) {
      const uploadedFile = files[0];
      if (uploadedFile.name.endsWith(".csv")) {
        setFile(uploadedFile);
        setMessages((prev) => [
          ...prev,
          { text: `Uploading: ${uploadedFile.name}`, sender: "system" },
        ]);

        await uploadFile(uploadedFile);
      } else {
        alert("Please upload a CSV file");
      }
    }
  };

  const uploadFile = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://127.0.0.1:5000/upload_csv", {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        setMessages((prev) => [
          ...prev,
          { text: data.message, sender: "system" },
        ]);
      } else {
        const errorData = await response.json();
        setMessages((prev) => [
          ...prev,
          { text: `Error: ${errorData.error}`, sender: "system" },
        ]);
      }
    } catch (error) {
      console.error("Error uploading file:", error);
      setMessages((prev) => [
        ...prev,
        { text: "Error: Failed to connect to the server", sender: "system" },
      ]);
    }
  };

  const handleKeyPress = (event: KeyboardEvent<HTMLTextAreaElement>): void => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  const handleReset = async (): Promise<void> => {
    try {
      await fetch("http://127.0.0.1:5000/reset", {
        method: "POST",
        credentials: "include",
      });
      setMessages([]);
      setFile(null);
    } catch (error) {
      console.error("Error resetting conversation:", error);
    }
  };

  return (
    <div className="body">
      <div className="title-container">
        <div className="title">
          <h1 className="title-text">🌊 OceanGPT v0.1</h1>
        </div>
        <div className="reset-container">
          <Button onClick={handleReset}>
            <RotateCcw />
          </Button>
        </div>
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
              {message.sender === "bot" ? (
                <>
                  <ReactMarkdown>{message.text}</ReactMarkdown>

                  {/* Chart rendering */}
                  {message.data && message.data.xAxis && message.data.series ? (
                    <div
                      style={{
                        height: 400,
                        width: "100%",
                        marginTop: "20px",
                      }}
                    >
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart
                          data={
                            message.data.xAxis[0]?.data?.map(
                              (x: any, i: number) => ({
                                x: x,
                                y: message.data.series[0]?.data[i], // Use optional chaining to safely access nested data
                              })
                            ) || [] // Provide an empty array as fallback
                          }
                          margin={{
                            top: 5,
                            right: 30,
                            left: 20,
                            bottom: 5,
                          }}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="x" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Line
                            type="monotone"
                            dataKey="y"
                            stroke="#8884d8"
                            activeDot={{ r: 8 }}
                            name={message.data.series[0]?.name || "Unknown"} // Provide fallback name
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <Typography variant="body2" color="textSecondary">
                      No chart data available.
                    </Typography>
                  )}

                  {/* DataGrid rendering */}
                  {message.data &&
                  Array.isArray(message.data) &&
                  message.data.length > 0 ? (
                    <div
                      style={{
                        height: 400,
                        width: "100%",
                        marginTop: "20px",
                      }}
                    >
                      <StyledDataGrid
                        rows={message.data.map((row: any, index: any) => ({
                          id: index,
                          ...row,
                        }))}
                        columns={Object.keys(message.data[0] || {})
                          .reverse() // Reverse the keys back to the correct order
                          .map((key) => ({
                            field: key,
                            headerName:
                              key.charAt(0).toUpperCase() + key.slice(1),
                            flex: 1,
                          }))}
                        initialState={{
                          pagination: {
                            paginationModel: { pageSize: 5 },
                          },
                        }}
                        disableRowSelectionOnClick
                      />
                    </div>
                  ) : (
                    <Typography variant="body2" color="textSecondary">
                      No table data available.
                    </Typography>
                  )}
                </>
              ) : (
                <Typography variant="body1">{message.text}</Typography>
              )}{" "}
            </div>
          ))}
          {loading && (
            <div className="message bot">
              {/* <CircularProgress size={20} /> */}
              <Typography className="thinking-message" variant="body1">OceanGPT is thinking...</Typography>
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
            onKeyPress={handleKeyPress}
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
