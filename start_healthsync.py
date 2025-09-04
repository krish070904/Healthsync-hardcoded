#!/usr/bin/env python3
"""
HealthSync Startup Script
Automates the startup process for the HealthSync AI health assistant.
"""

import subprocess
import sys
import time
import os
import requests
from pathlib import Path

def run_command(command, description, check=True):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False

def check_docker():
    """Check if Docker is running"""
    print("🔍 Checking Docker status...")
    try:
        result = subprocess.run("docker --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is available")
            return True
        else:
            print("❌ Docker is not available")
            return False
    except FileNotFoundError:
        print("❌ Docker is not installed")
        return False

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

def wait_for_service(url, service_name, max_attempts=30, is_db=False):
    """Wait for a service to become available"""
    print(f"⏳ Waiting for {service_name} to start...")
    for attempt in range(max_attempts):
        try:
            if is_db:
                result = subprocess.run(
                    "docker exec healthsync-db-1 pg_isready -U hs_user -d healthsync_db",
                    shell=True, capture_output=True, text=True
                )
                if result.returncode == 0:
                    print(f"✅ {service_name} is ready!")
                    return True
            else:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {service_name} is ready!")
                    return True
        except (requests.exceptions.RequestException, subprocess.CalledProcessError):
            pass
        
        print(f"   Attempt {attempt + 1}/{max_attempts}...")
        time.sleep(2)
    
    print(f"❌ {service_name} failed to start within {max_attempts * 2} seconds")
    return False

def main():
    """Main startup function"""
    print("🚀 HealthSync AI Health Assistant - Startup Script")
    print("=" * 60)
    
    # Check prerequisites
    if not check_docker():
        print("❌ Docker is required but not available. Please install Docker first.")
        sys.exit(1)
    
    if not check_python_dependencies():
        print("❌ Python dependencies are missing. Please install them first.")
        sys.exit(1)
    
    # Step 1: Start PostgreSQL database
    print("\n📊 Step 1: Starting PostgreSQL database...")
    if not run_command("docker-compose up -d db", "Starting PostgreSQL database"):
        print("❌ Failed to start database. Exiting.")
        sys.exit(1)
    
    # Wait for database to be ready
    if not wait_for_service(None, "PostgreSQL database", max_attempts=15, is_db=True):
        print("❌ Database failed to start. Check Docker logs.")
        sys.exit(1)
    
    # Step 2: Train AI model
    print("\n🤖 Step 2: Training AI symptom classification model...")
    if not run_command("python train_symptom_model.py", "Training AI model"):
        print("❌ Failed to train AI model. Exiting.")
        sys.exit(1)
    
    # Step 3: Start FastAPI server
    print("\n🌐 Step 3: Starting HealthSync API server...")
    print("💡 Starting uvicorn server in background...")
    
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
        
        # Step 4: Load sample data
        print("\n📋 Step 4: Loading sample food data...")
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
        print(f"📊 Database: PostgreSQL on localhost:5432")
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
