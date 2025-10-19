import { GoogleGenerativeAI } from "@google/generative-ai";

// Initialize API with the provided key
const API_KEY = "AIzaSyAgM-gZoER1piwlNMIxISCkLEj0EIv3t4k";
const genAI = new GoogleGenerativeAI(API_KEY);

// Function to list available models
async function listModels() {
  try {
    // List available models
    console.log("Available Gemini models:");
    const result = await genAI.getModels();
    result.models.forEach(model => {
      console.log(`- ${model.name}`);
    });
  } catch (error) {
    console.error("Error listing models:", error);
  }
}

// Run the function
listModels();
