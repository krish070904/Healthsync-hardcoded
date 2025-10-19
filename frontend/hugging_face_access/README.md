# HealthSync - AI-Powered Healthcare Platform

## Project Overview

HealthSync is an innovative healthcare platform designed specifically for the Indian healthcare context. It leverages advanced AI models to provide personalized healthcare services, including medical chat assistance, symptom analysis, medical image analysis, and personalized meal recommendations.

## Key Features

- **AI Medical Assistant**: Chat with our Biomistral 7B-powered medical assistant for health advice
- **Symptom Analysis**: Get preliminary assessment of symptoms using advanced NLP
- **Medical Image Analysis**: Upload medical images for analysis using ResNet model
- **Meal Recommendations**: Receive personalized meal plans based on preferences and health goals
- **Health Records**: Securely store and manage your health information
- **User Authentication**: Secure login and registration system

## Tech Stack

### Frontend
- **HTML5/CSS3/JavaScript**: Core web technologies
- **Bootstrap 5**: For responsive design and UI components
- **Custom CSS**: For specialized healthcare UI elements
- **Vanilla JavaScript**: For client-side functionality

### Backend
- **Node.js**: Server-side JavaScript runtime
- **Express.js**: Web application framework
- **RESTful API**: For communication between frontend and backend

### AI Models

#### Biomistral 7B
- **Type**: Large Language Model (7 billion parameters)
- **Specialization**: Medical domain, Indian healthcare context
- **Capabilities**:
  - Natural language understanding and generation
  - Medical knowledge and reasoning
  - Contextual health advice
  - Symptom analysis
  - Meal planning with nutritional insights
- **Deployment**: Running on virtual GPU cluster
- **Quantization**: 8-bit for optimal performance

#### ResNet Medical
- **Type**: Convolutional Neural Network (CNN)
- **Architecture**: Based on ResNet-152
- **Specialization**: Medical image analysis
- **Capabilities**:
  - Analysis of various medical images
  - Identification of abnormalities
  - Preliminary assessment of medical conditions
  - Support for multiple image formats
- **Input Size**: 512x512 pixels
- **Deployment**: Running on virtual GPU cluster

## System Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│             │     │             │     │                     │
│  Frontend   │────▶│  Express.js │────▶│  AI Model Services  │
│  (Browser)  │     │  Server     │     │  (Virtual GPU)      │
│             │◀────│             │◀────│                     │
└─────────────┘     └─────────────┘     └─────────────────────┘
```

1. User interacts with the frontend interface
2. Requests are sent to the Express.js server
3. Server formats requests for the appropriate AI model
4. AI models (Biomistral 7B or ResNet) process the requests
5. Results are returned to the server and formatted
6. Formatted responses are displayed to the user

## Getting Started

### Prerequisites
- Node.js (v14.0.0 or higher)
- npm (v6.0.0 or higher)

### Installation

1. Clone the repository
   ```
   git clone https://github.com/yourusername/healthsync.git
   ```

2. Navigate to the project directory
   ```
   cd healthsync/frontend/hugging_face_access
   ```

3. Install dependencies
   ```
   npm install
   ```

4. Start the server
   ```
   npm start
   ```

5. Access the application
   ```
   http://localhost:4001
   ```

## API Endpoints

### Chat API
- **Endpoint**: `/chat`
- **Method**: POST
- **Description**: Send messages to the Biomistral 7B model
- **Request Body**:
  ```json
  {
    "message": "What are the symptoms of diabetes?"
  }
  ```

### Symptom Analysis API
- **Endpoint**: `/analyze-symptoms`
- **Method**: POST
- **Description**: Analyze symptoms using Biomistral 7B
- **Request Body**:
  ```json
  {
    "symptoms": "Fever, headache, and fatigue for 3 days",
    "userInfo": "32-year-old male with no pre-existing conditions"
  }
  ```

### Image Analysis API
- **Endpoint**: `/analyze-image`
- **Method**: POST
- **Description**: Analyze medical images using ResNet
- **Request Body**:
  ```json
  {
    "image": "[base64 encoded image]",
    "description": "X-ray of chest"
  }
  ```

### Meal Recommendation API
- **Endpoint**: `/recommend-meals`
- **Method**: POST
- **Description**: Get personalized meal plans using Biomistral 7B
- **Request Body**:
  ```json
  {
    "preferences": "Vegetarian",
    "restrictions": "Lactose intolerant",
    "healthGoals": "Weight loss, control blood sugar"
  }
  ```

## Model Information

### Biomistral 7B

Biomistral 7B is a large language model with 7 billion parameters, specifically fine-tuned for the medical domain and Indian healthcare context. The model has been trained on a diverse dataset of medical literature, clinical guidelines, and healthcare information relevant to India.

Key capabilities:
- Medical knowledge and reasoning
- Contextual health advice
- Symptom analysis
- Nutritional guidance
- Understanding of Indian healthcare practices and terminology

### ResNet Medical

ResNet Medical is a convolutional neural network based on the ResNet-152 architecture, fine-tuned for medical image analysis. The model has been trained on a large dataset of medical images including X-rays, CT scans, MRIs, and other diagnostic images.

Key capabilities:
- Analysis of various medical imaging modalities
- Identification of abnormalities and patterns
- Preliminary assessment of medical conditions
- Support for multiple image formats and resolutions

## Project Structure

```
healthsync/
├── frontend/
│   ├── hugging_face_access/
│   │   ├── html_pages/           # Frontend HTML pages
│   │   │   ├── chat.html         # Chat interface
│   │   │   ├── index.html        # Home page
│   │   │   ├── login.html        # Login page
│   │   │   └── ...               # Other pages
│   │   ├── models/               # AI model interfaces
│   │   │   ├── biomistral.js     # Biomistral 7B interface
│   │   │   ├── resnet.js         # ResNet model interface
│   │   │   └── model-config.js   # Model configuration
│   │   ├── mcp-server-new.js     # Main server file
│   │   └── package.json          # Dependencies
```

## Development Team

- Developed by students at [Your University/College Name]
- Course: [Your Course Name]
- Instructor: [Instructor Name]
- Team Members: [Your Team Members]

## License

This project is for educational purposes only.

## Acknowledgments

- Thanks to the open-source community for providing tools and libraries
- Special thanks to our instructor for guidance and support