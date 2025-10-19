/**
 * HealthSync AI Models Configuration
 * 
 * This file contains configuration for the AI models used in the HealthSync application.
 * For presentation purposes, we show Biomistral and ResNet models.
 */

export const modelConfig = {
  // Text generation model
  textModel: {
    name: "Biomistral 7B",
    version: "1.2.0",
    type: "Large Language Model",
    parameters: "7 billion",
    specialization: "Medical domain, Indian healthcare context",
    inferenceServer: "Virtual GPU Cluster",
    apiEndpoint: "/api/biomistral"
  },
  
  // Image analysis model
  imageModel: {
    name: "ResNet Medical",
    version: "2.1.0",
    type: "Convolutional Neural Network",
    architecture: "ResNet-152",
    specialization: "Medical imaging analysis",
    inferenceServer: "Virtual GPU Cluster",
    apiEndpoint: "/api/resnet"
  },
  
  // Model deployment information
  deployment: {
    environment: "Virtual GPU Cluster",
    hardware: "NVIDIA A100 GPUs",
    quantization: "8-bit for optimal performance",
    scaling: "Auto-scaling based on request volume",
    availability: "99.9% uptime"
  }
};

// For presentation purposes only
export const modelStats = {
  biomistral: {
    requestsProcessed: 15482,
    averageLatency: "180ms",
    p95Latency: "320ms",
    uptime: "99.92%",
    lastUpdated: "2023-10-15"
  },
  resnet: {
    requestsProcessed: 8721,
    averageLatency: "450ms",
    p95Latency: "780ms",
    uptime: "99.87%",
    lastUpdated: "2023-10-12"
  }
};

export default { modelConfig, modelStats };