import express from "express";
import fs from "fs/promises";
import path from "path";
import cors from "cors";
import bodyParser from "body-parser";
import { GoogleGenerativeAI } from "@google/generative-ai";

const app = express();
app.use(cors());
app.use(bodyParser.json());

const BASE_DIR = path.resolve("./html_pages");
// Serve static files from the html_pages directory
app.use(express.static('./html_pages'));
// Serve static files from the project root directory
app.use(express.static('.'));
// Serve components directly
app.use('/components', express.static('./html_pages/components'));

// Initialize Gemini API
const API_KEY = "AIzaSyDhY6dFH-RLGTfxhE7gV7E14JnhiBEKlyU";
const genAI = new GoogleGenerativeAI(API_KEY);
// Use gemini-2.5-flash for text-only requests
const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
// Use gemini-2.5-flash for multimodal capabilities (text + image)
const visionModel = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

// 🧰 List all files
app.get("/list", async (req, res) => {
  const files = await fs.readdir(BASE_DIR);
  res.json({ files });
});

// 🧰 Read file
app.get("/read/:filename", async (req, res) => {
  const filePath = path.join(BASE_DIR, req.params.filename);
  const content = await fs.readFile(filePath, "utf-8");
  res.json({ filename: req.params.filename, content });
});

// 🧰 Create / update file
app.post("/write", async (req, res) => {
  const { filename, content } = req.body;
  const filePath = path.join(BASE_DIR, filename);
  await fs.writeFile(filePath, content, "utf-8");
  res.json({ message: `${filename} saved!` });
});

// 🧰 Delete file
app.delete("/delete/:filename", async (req, res) => {
  const filePath = path.join(BASE_DIR, req.params.filename);
  await fs.unlink(filePath);
  res.json({ message: `${req.params.filename} deleted.` });
});

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

// 🧰 Gemini Chat API endpoint
app.post("/chat", async (req, res) => {
  try {
    const { message } = req.body;
    
    if (!message) {
      return res.status(400).json({ error: "Message is required" });
    }

    // Initialize the model for each request
  const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
    
    // Add context for Indian users
    const contextPrompt = `You are HealthSync's AI medical assistant for Indian users. you model name is Biomistral 7B
    Provide health advice and information relevant to Indian healthcare context. 
    Consider Indian medical practices, common health issues in India, and locally available treatments.
    
    User message: ${message}`;
    
    const result = await model.generateContent(contextPrompt);
    const response = await result.response;
    let text = response.text();
    
    // Format the response for better readability
    text = formatResponse(text);
    
    res.json({ reply: text });
  } catch (error) {
    console.error("Error with Gemini API:", error);
    res.status(500).json({ error: "Failed to get response from Gemini API" });
  }
});

// 🧰 Health check endpoint
app.get("/health", (req, res) => {
  res.json({ status: "ok", message: "MCP Server is running" });
});

// 🧰 Symptom Analysis API endpoint
app.post("/analyze-symptoms", async (req, res) => {
  try {
    const { symptoms, userInfo } = req.body;
    
    if (!symptoms) {
      return res.status(400).json({ error: "Symptoms description is required" });
    }

    // Initialize the model for each request
  const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

    // Create a prompt for the Gemini API that includes medical context
    const prompt = `You are a medical AI assistant trained on Indian healthcare data. 

Analyze these symptoms and provide possible health conditions, focusing on Indian context:
${symptoms}

User Info: ${userInfo || 'Not provided'}

Provide your analysis in this format:
1. Possible conditions (list 2-3 most likely conditions common in India)
2. Severity assessment (mild, moderate, severe)
3. Recommended next steps (considering Indian healthcare system)
4. Home care suggestions (including traditional Indian remedies if appropriate)
5. When to seek immediate medical attention
6. Ayurvedic considerations (if relevant)`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    let text = response.text();
    
    // Format the response for better readability
    text = formatResponse(text);
    
    res.json({ analysis: text });
  } catch (error) {
    console.error("Error with symptom analysis:", error);
    res.status(500).json({ error: "Failed to analyze symptoms" });
  }
});

// 🧰 Image-based Symptom Analysis API endpoint
app.post("/analyze-image", async (req, res) => {
  try {
    const { image, description } = req.body;
    
    if (!image) {
      return res.status(400).json({ error: "Image data is required" });
    }

    // Extract the base64 image data (remove the data:image/jpeg;base64, prefix)
    const base64ImageData = image.split(',')[1];
    
    // Convert base64 to buffer
    const imageBuffer = Buffer.from(base64ImageData, 'base64');
    
    // Create a multimodal prompt for Gemini with both text and image
    const prompt = `You are a medical AI assistant specialized in Indian healthcare. Analyze this medical image along with the patient's symptoms and provide an assessment relevant to Indian healthcare context.

Patient's description: ${description || 'No description provided'}

Provide your analysis in this format:
1. Visual observations from the image
2. Symptom severity assessment (mild, moderate, severe)
3. Possible conditions (list 2-3 most likely conditions common in India)
4. Recommended next steps (considering Indian healthcare system)
5. Home care suggestions (including traditional Indian remedies if appropriate)
6. When to seek immediate medical attention
7. Ayurvedic considerations (if relevant)
8. Disclaimer about the limitations of AI diagnosis

Consider Indian climate, common diseases in India, and locally available treatments.`;

    // Create parts array with both text and image
    const parts = [
      { text: prompt },
      {
        inlineData: {
          mimeType: "image/jpeg",
          data: base64ImageData
        }
      }
    ];
    
    // Generate content with multimodal input
    const result = await visionModel.generateContent({
      contents: [{ role: "user", parts }],
    });
    
    const response = await result.response;
    let text = response.text();
    
    // Format the response for better readability
    text = formatResponse(text);
    
    res.json({ analysis: text });
  } catch (error) {
    console.error("Error with image analysis:", error);
    res.status(500).json({ error: "Failed to analyze image: " + error.message });
  }
});

// 🧰 Meal Recommendation API endpoint
app.post("/meal-recommendations", async (req, res) => {
  try {
    const { healthCondition, preferences, restrictions, symptoms, severity } = req.body;
    
    if (!healthCondition && !symptoms) {
      return res.status(400).json({ error: "Health condition or symptoms are required" });
    }
    
    // Initialize the model for each request
  const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
    
    // Create a prompt for the Gemini API that includes dietary context and symptom information
    const prompt = `You are a nutritionist specializing in Indian cuisine and Ayurvedic principles.

Provide personalized Indian meal recommendations for a patient with the following information:
${healthCondition ? `Health condition: ${healthCondition}` : ''}
${symptoms ? `Symptoms: ${symptoms}` : ''}
${severity ? `Severity: ${severity}` : ''}

Dietary preferences: ${preferences || 'Not specified'}
Dietary restrictions: ${restrictions || 'None'}

Provide your recommendations in this format:
1. Breakfast options (3 traditional Indian dishes that help alleviate the symptoms)
2. Lunch options (3 Indian dishes that help alleviate the symptoms)
3. Dinner options (3 Indian dishes that help alleviate the symptoms)
4. Snacks (2 healthy Indian options that help alleviate the symptoms)
5. Nutritional benefits of these recommendations
6. How these meals specifically help with the symptoms or health condition
7. Ayurvedic considerations for the condition
8. Foods to avoid

Focus on ingredients commonly available in India and traditional Indian cooking methods.
Include regional dishes from different parts of India that are known to help with these symptoms.`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    let recommendations = response.text();
    
    // Format the response for better readability
    recommendations = formatResponse(recommendations);
    
    res.json({ recommendations });
  } catch (error) {
    console.error("Error with meal recommendations:", error);
    res.status(500).json({ error: "Failed to generate meal recommendations" });
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
    // For now, we'll simulate success
    
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
    // For now, we'll return mock data
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
      },
      {
        id: "rec124",
        date: "2023-06-10",
        type: "medication",
        data: {
          name: "Paracetamol",
          dosage: "500mg",
          frequency: "Every 6 hours"
        }
      }
    ];
    
    // Filter by record type if provided
    const filteredRecords = recordType ? mockRecords.filter(record => record.type === recordType) : mockRecords;
    
    res.json({ records: filteredRecords });
  } catch (error) {
    console.error("Error retrieving health records:", error);
    res.status(500).json({ error: "Failed to retrieve health records" });
  }
});

// 🧰 User Authentication API endpoint (simplified)
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

// 🧰 User Registration API endpoint with verification
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
    
    // In a real implementation, this would save to a MySQL database
    // For demo purposes, we'll store in memory and simulate the database
    const userData = {
      id: "user-" + Date.now(),
      name,
      email,
      password, // In production, this would be hashed
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
    
    // In production, send email with verification link
    // For demo, we'll just return success and the verification will be handled client-side
    
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

// Serve static files from html_pages directory
app.use(express.static(BASE_DIR));

// Serve components from the components directory
app.use('/components', express.static(path.join(BASE_DIR, 'components')));

// Start server
const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`🚀 MCP Server running on http://localhost:${PORT}`);
  console.log("💬 Gemini API integrated and ready for chat requests");
});
