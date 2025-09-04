#!/usr/bin/env python3
"""
HealthSync Simple Startup Script
Quick start without Docker - uses SQLite database
"""

import subprocess
import sys
import time
import os
import requests

def check_python_dependencies():
    """Check if Python dependencies are installed"""
    print("🔍 Checking Python dependencies...")
    try:
        import fastapi
        import sqlalchemy
        import pandas
        import sklearn
        import joblib
        print("✅ All required Python packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing Python package: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False

def wait_for_service(url, service_name, max_attempts=30):
    """Wait for a service to become available"""
    print(f"⏳ Waiting for {service_name} to start...")
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name} is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"   Attempt {attempt + 1}/{max_attempts}...")
        time.sleep(2)
    
    print(f"❌ {service_name} failed to start within {max_attempts * 2} seconds")
    return False

def main():
    """Main startup function"""
    print("🚀 HealthSync AI Health Assistant - Simple Start")
    print("=" * 60)
    print("💡 Using SQLite database - no Docker required")
    print("=" * 60)
    
    # Check prerequisites
    if not check_python_dependencies():
        print("❌ Python dependencies are missing. Please install them first.")
        sys.exit(1)
    
    # Step 1: Train AI model (if not already done)
    print("\n🤖 Step 1: Checking AI model...")
    if not os.path.exists("models/symptom_model.joblib"):
        print("   Training AI symptom classification model...")
        try:
            result = subprocess.run("python train_symptom_model.py", shell=True, check=True, capture_output=True, text=True)
            print("✅ AI model trained successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to train AI model: {e}")
            print("💡 Continuing anyway...")
    else:
        print("✅ AI model already exists")
    
    # Step 2: Start FastAPI server
    print("\n🌐 Step 2: Starting HealthSync API server...")
    print("💡 Starting uvicorn server...")
    
    # Start the server in background
    try:
        server_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        if not wait_for_service("http://localhost:8000/health", "HealthSync API", max_attempts=20):
            print("❌ API server failed to start. Check the logs.")
            server_process.terminate()
            sys.exit(1)
        
        # Step 3: Load sample data
        print("\n📋 Step 3: Loading sample food data...")
        try:
            response = requests.post("http://localhost:8000/food/load_sample", timeout=10)
            if response.status_code == 200:
                print("✅ Sample food data loaded successfully")
            else:
                print(f"⚠️  Warning: Failed to load sample data: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Warning: Could not load sample data: {e}")
        
        # Success message
        print("\n" + "=" * 60)
        print("🎉 HealthSync AI Health Assistant is now running!")
        print("=" * 60)
        print(f"🌐 API Server: http://localhost:8000")
        print(f"📚 API Documentation: http://localhost:8000/docs")
        print(f"🔍 Interactive Explorer: http://localhost:8000/redoc")
        print(f"📊 Database: SQLite (healthsync.db)")
        print("\n💡 To test the system, run: python test_healthsync.py")
        print("💡 To stop the server, press Ctrl+C")
        print("=" * 60)
        
        # Keep the server running
        try:
            server_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down HealthSync...")
            server_process.terminate()
            print("✅ HealthSync stopped successfully")
    
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
