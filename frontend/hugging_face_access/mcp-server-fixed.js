import express from "express";
import fs from "fs/promises";
import path from "path";
import cors from "cors";
import bodyParser from "body-parser";
import { GoogleGenerativeAI } from "@google/generative-ai";

const app = express();
app.use(cors());
app.use(bodyParser.json({ limit: '50mb' }));
app.use(bodyParser.urlencoded({ limit: '50mb', extended: true }));

const BASE_DIR = path.resolve("./html_pages");
// Serve static files from the html_pages directory
app.use(express.static('./html_pages'));
// Serve static files from the project root directory
app.use(express.static('.'));
// Serve components directly
app.use('/components', express.static('./html_pages/components'));

// Initialize Gemini API
const API_KEY = "AIzaSyCMGyhoZaFuPT2mUVDEZd2t7tKmutahmF4";
const genAI = new GoogleGenerativeAI(API_KEY);

// Function to format the response text for better readability
function formatResponse(text) {
  // Handle bold text with proper HTML formatting
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Replace bullet points with proper HTML formatting
  text = text.replace(/\*\s(.*?)\n/g, '<p>• $1</p>');
  
  // Format headings
  text = text.replace(/###\s(.*?)\n/g, '<h3>$1</h3>');
  text = text.replace(/##\s(.*?)\n/g, '<h2>$1</h2>');
  text = text.replace(/#\s(.*?)\n/g, '<h1>$1</h1>');
  
  // Format numbered lists
  text = text.replace(/(\d+)\.\s(.*?)\n/g, '<p>$1. $2</p>');
  
  // Add paragraph tags to regular text blocks
  text = text.replace(/([^\n<>][^\n<>]*?)\n\n/g, '<p>$1</p>');
  
  // Replace double line breaks with a single line break
  text = text.replace(/\n\n/g, '');
  
  // Replace single line breaks within paragraphs
  text = text.replace(/([^>])\n([^<])/g, '$1 $2');
  
  return text;
}

// 🧰 List all files
app.get("/list", async (req, res) => {
  try {
    const files = await fs.readdir(BASE_DIR);
    res.json({ files });
  } catch (error) {
    console.error("Error listing files:", error);
    res.status(500).json({ error: "Failed to list files" });
  }
});

// 🧰 Read file
app.get("/read/:filename", async (req, res) => {
  try {
    const filePath = path.join(BASE_DIR, req.params.filename);
    const content = await fs.readFile(filePath, "utf-8");
    res.json({ filename: req.params.filename, content });
  } catch (error) {
    console.error("Error reading file:", error);
    res.status(500).json({ error: "Failed to read file" });
  }
});

// 🧰 Create / update file
app.post("/write", async (req, res) => {
  try {
    const { filename, content } = req.body;
    const filePath = path.join(BASE_DIR, filename);
    await fs.writeFile(filePath, content, "utf-8");
    res.json({ message: `${filename} saved!` });
  } catch (error) {
    console.error("Error writing file:", error);
    res.status(500).json({ error: "Failed to write file" });
  }
});

// 🧰 Delete file
app.delete("/delete/:filename", async (req, res) => {
  try {
    const filePath = path.join(BASE_DIR, req.params.filename);
    await fs.unlink(filePath);
    res.json({ message: `${req.params.filename} deleted.` });
  } catch (error) {
    console.error("Error deleting file:", error);
    res.status(500).json({ error: "Failed to delete file" });
  }
});

// 🧰 Gemini Chat API endpoint
app.post("/chat", async (req, res) => {
  try {
    console.log("Chat request received:", req.body);
    const { message } = req.body;
    
    if (!message) {
      return res.status(400).json({ error: "Message is required" });
    }

    // Initialize the model for each request
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
    
    // Add context for Indian users
    const contextPrompt = `You are HealthSync's AI medical assistant for Indian users. Your model name is Biomistral 7B.
    Provide health advice and information relevant to Indian healthcare context. 
    Consider Indian medical practices, common health issues in India, and locally available treatments.
    
    User message: ${message}`;
    
    console.log("Sending to Gemini API...");
    const result = await model.generateContent(contextPrompt);
    const response = await result.response;
    let text = response.text();
    
    console.log("Gemini response received");
    
    // Format the response for better readability
    text = formatResponse(text);
    
    res.json({ reply: text, success: true });
  } catch (error) {
    console.error("Error with Gemini API:", error);
    res.status(500).json({ 
      error: "Failed to get response from Gemini API",
      details: error.message,
      success: false
    });
  }
});

// 🧰 Analyze symptoms endpoint
app.post("/analyze-symptoms", async (req, res) => {
  try {
    console.log("Symptom analysis request received:", req.body);
    const { symptoms, userInfo } = req.body;
    
    if (!symptoms) {
      return res.status(400).json({ error: "Symptoms description is required" });
    }

    // Initialize the model for each request
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
    
    // Create prompt for symptom analysis
    const analysisPrompt = `You are HealthSync's AI medical assistant for Indian users.
    Analyze these symptoms and provide a preliminary assessment:
    
    Symptoms: ${symptoms}
    User Info: ${userInfo || 'Not provided'}
    
    Provide a concise analysis including:
    1. Possible causes
    2. Severity assessment (mild, moderate, severe)
    3. Recommendations
    4. Whether immediate medical attention is needed
    
    Consider Indian healthcare context, common conditions in India, and locally available treatments.`;
    
    console.log("Sending to Gemini API for symptom analysis...");
    const result = await model.generateContent(analysisPrompt);
    const response = await result.response;
    const formattedResponse = formatResponse(response.text());
    
    console.log("Symptom analysis completed");
    
    res.json({ 
      analysis: formattedResponse,
      success: true 
    });
  } catch (error) {
    console.error("Error analyzing symptoms:", error);
    res.status(500).json({ 
      error: "Error analyzing symptoms", 
      message: error.message,
      success: false
    });
  }
});

// 🧰 Analyze image endpoint
app.post("/analyze-image", async (req, res) => {
  try {
    console.log("Image analysis request received");
    const { image, description } = req.body;
    
    if (!image) {
      return res.status(400).json({ error: "Image data is required" });
    }

    // Initialize the vision model for multimodal analysis
    const visionModel = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
    
    // Process the base64 image
    const imageData = image.split(',')[1]; // Remove the data:image/jpeg;base64, part
    
    // Create prompt for image analysis
    const analysisPrompt = `You are HealthSync's AI medical assistant for Indian users.
    Analyze this medical image and the provided symptoms:
    
    Symptoms description: ${description || 'Not provided'}
    
    Provide a concise analysis including:
    1. What the image shows (if visible)
    2. Possible conditions based on the image and symptoms
    3. Severity assessment (mild, moderate, severe)
    4. Recommendations
    5. Whether immediate medical attention is needed
    
    Consider Indian healthcare context and common conditions in India.`;
    
    // Create multipart request with image and text
    console.log("Sending to Gemini API for image analysis...");
    const result = await visionModel.generateContent([
      analysisPrompt,
      {
        inlineData: {
          data: imageData,
          mimeType: "image/jpeg"
        }
      }
    ]);
    
    const response = await result.response;
    const formattedResponse = formatResponse(response.text());
    
    console.log("Image analysis completed");
    
    res.json({ 
      analysis: formattedResponse,
      success: true 
    });
  } catch (error) {
    console.error("Error analyzing image:", error);
    res.status(500).json({ 
      error: "Error analyzing image", 
      message: error.message,
      success: false
    });
  }
});

// 🧰 Recommend meals endpoint
app.post("/recommend-meals", async (req, res) => {
  try {
    console.log("Meal recommendation request received:", req.body);
    const { symptoms, severity, preferences, restrictions } = req.body;
    
    if (!symptoms) {
      return res.status(400).json({ error: "Symptoms description is required" });
    }

    // Initialize the model for each request
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
    
    // Create prompt for meal recommendations
    const recommendationPrompt = `You are HealthSync's AI nutrition specialist for Indian users.
    Recommend Indian meals based on these health details:
    
    Symptoms: ${symptoms}
    Severity: ${severity || 'moderate'}
    Dietary Preferences: ${preferences || 'None specified'}
    Dietary Restrictions: ${restrictions || 'None specified'}
    
    Provide:
    1. 3 breakfast recommendations (traditional Indian dishes)
    2. 3 lunch recommendations (Indian dishes)
    3. 3 dinner recommendations (Indian dishes)
    4. 2 snack options (healthy Indian snacks)
    5. Foods to avoid based on the symptoms
    6. Ayurvedic considerations if relevant
    
    Focus on affordable, locally available Indian ingredients and traditional cooking methods.`;
    
    console.log("Sending to Gemini API for meal recommendations...");
    const result = await model.generateContent(recommendationPrompt);
    const response = await result.response;
    const formattedResponse = formatResponse(response.text());
    
    console.log("Meal recommendations completed");
    
    res.json({ 
      recommendations: formattedResponse,
      success: true 
    });
  } catch (error) {
    console.error("Error generating meal recommendations:", error);
    res.status(500).json({ 
      error: "Error generating meal recommendations", 
      message: error.message,
      success: false
    });
  }
});

// 🧰 Health Record Storage API endpoint
app.post("/save-health-record", async (req, res) => {
  try {
    const { userId, recordType, data } = req.body;
    
    if (!userId || !recordType || !data) {
      return res.status(400).json({ error: "User ID, record type, and data are required" });
    }

    // In a real implementation, this would save to a database
    console.log("Health record saved:", { userId, recordType, data });
    
    res.json({ success: true, message: "Health record saved successfully" });
  } catch (error) {
    console.error("Error saving health record:", error);
    res.status(500).json({ error: "Failed to save health record" });
  }
});

// 🧰 Health Record Retrieval API endpoint
app.get("/get-health-records/:userId", async (req, res) => {
  try {
    const { userId } = req.params;
    const { recordType } = req.query;
    
    if (!userId) {
      return res.status(400).json({ error: "User ID is required" });
    }

    // In a real implementation, this would fetch from a database
    const mockRecords = [
      {
        id: "rec123",
        date: "2023-06-15",
        type: "symptom",
        data: {
          description: "Fever and sore throat",
          severity: "moderate",
          duration: "2 days"
        }
      }
    ];
    
    const filteredRecords = recordType ? mockRecords.filter(record => record.type === recordType) : mockRecords;
    
    res.json({ records: filteredRecords });
  } catch (error) {
    console.error("Error retrieving health records:", error);
    res.status(500).json({ error: "Failed to retrieve health records" });
  }
});

// 🧰 User Authentication API endpoints
app.post("/auth/verify", async (req, res) => {
  try {
    const { email, token } = req.body;
    
    if (!email || !token) {
      return res.status(400).json({ error: "Email and verification token are required" });
    }

    // Find user in our simulated database
    if (!global.users) global.users = [];
    const userIndex = global.users.findIndex(u => u.email === email && u.verificationToken === token);
    
    if (userIndex === -1) {
      return res.status(400).json({ error: "Invalid verification token or email" });
    }
    
    // Mark user as verified
    global.users[userIndex].verified = true;
    global.users[userIndex].verificationToken = null;
    
    console.log(`User verified: ${email}`);
    
    res.json({
      success: true,
      message: "Email verification successful",
      user: {
        id: global.users[userIndex].id,
        name: global.users[userIndex].name,
        email: global.users[userIndex].email,
        role: global.users[userIndex].role
      },
      token: "verified-jwt-token-" + Date.now()
    });
  } catch (error) {
    console.error("Error during verification:", error);
    res.status(500).json({ error: "Verification failed" });
  }
});

app.post("/auth/login", async (req, res) => {
  try {
    const { email, password } = req.body;
    
    if (!email || !password) {
      return res.status(400).json({ error: "Email and password are required" });
    }

    // Find user in our simulated database
    if (!global.users) global.users = [];
    const user = global.users.find(u => u.email === email && u.password === password);
    
    if (!user) {
      return res.status(401).json({ error: "Invalid credentials" });
    }
    
    if (!user.verified) {
      return res.status(403).json({ 
        error: "Email not verified", 
        verificationRequired: true 
      });
    }

    res.json({
      success: true,
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        role: user.role
      },
      token: "auth-jwt-token-" + Date.now()
    });
  } catch (error) {
    console.error("Error during login:", error);
    res.status(500).json({ error: "Login failed" });
  }
});

app.post("/auth/register", async (req, res) => {
  try {
    const { name, email, password } = req.body;
    
    if (!name || !email || !password) {
      return res.status(400).json({ error: "Name, email, and password are required" });
    }

    // Generate verification token
    const verificationToken = Math.random().toString(36).substring(2, 15) + 
                             Math.random().toString(36).substring(2, 15) + 
                             Date.now().toString(36);
    
    const userData = {
      id: "user-" + Date.now(),
      name,
      email,
      password,
      role: "patient",
      verified: false,
      verificationToken,
      createdAt: new Date().toISOString()
    };
    
    // Store in our simulated database (in memory)
    if (!global.users) global.users = [];
    global.users.push(userData);
    
    console.log(`User registered: ${email} with verification token: ${verificationToken}`);
    console.log(`Verification link: http://localhost:4000/verify.html?email=${encodeURIComponent(email)}&token=${encodeURIComponent(verificationToken)}`);
    
    res.json({
      success: true,
      message: "Registration successful. Please verify your email.",
      verificationRequired: true
    });
  } catch (error) {
    console.error("Error during registration:", error);
    res.status(500).json({ error: "Registration failed" });
  }
});

// 🧰 Health check endpoint
app.get("/health", (req, res) => {
  res.json({ status: "ok", message: "MCP Server is running" });
});

// Start server
const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`🚀 MCP Server running on http://localhost:${PORT}`);
  console.log("💬 Gemini API integrated and ready for chat requests");
  console.log("🏥 Health endpoints available:");
  console.log("   - POST /chat");
  console.log("   - POST /analyze-symptoms");
  console.log("   - POST /analyze-image");
  console.log("   - POST /recommend-meals");
});
