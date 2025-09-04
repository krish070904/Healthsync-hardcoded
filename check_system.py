#!/usr/bin/env python3
"""
HealthSync System Check
Comprehensive verification of all system components
"""

import os
import sys
import importlib

def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def check_dependencies():
    """Check all required dependencies"""
    print("\n📦 Checking dependencies...")
    dependencies = [
        "fastapi",
        "uvicorn", 
        "sqlalchemy",
        "pandas",
        "numpy",
        "scikit-learn",
        "joblib",
        "python-dotenv",
        "pydantic"
    ]
    
    missing = []
    for dep in dependencies:
        try:
            importlib.import_module(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - Missing")
            missing.append(dep)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    return True

def check_files():
    """Check if all required files exist"""
    print("\n📁 Checking files...")
    required_files = [
        "app/main.py",
        "app/models.py",
        "app/crud.py", 
        "app/schemas.py",
        "app/db.py",
        "app/routes/symptoms.py",
        "app/routes/meals.py",
        "app/routes/alerts.py",
        "data/food_sample.csv",
        "train_symptom_model.py",
        "requirements.txt"
    ]
    
    missing = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing")
            missing.append(file_path)
    
    if missing:
        print(f"\n⚠️  Missing files: {', '.join(missing)}")
        return False
    return True

def check_ai_model():
    """Check if AI model exists"""
    print("\n🤖 Checking AI model...")
    model_path = "models/symptom_model.joblib"
    if os.path.exists(model_path):
        print(f"✅ {model_path} - AI model ready")
        return True
    else:
        print(f"❌ {model_path} - AI model missing")
        print("💡 Run: python train_symptom_model.py")
        return False

def check_database():
    """Check database configuration"""
    print("\n🗄️  Checking database...")
    try:
        from app.db import engine
        print("✅ Database engine configured")
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_app_imports():
    """Check if app modules can be imported"""
    print("\n🔧 Checking app imports...")
    try:
        import app.main
        import app.models
        import app.crud
        import app.schemas
        import app.routes.symptoms
        import app.routes.meals
        import app.routes.alerts
        print("✅ All app modules import successfully")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Run comprehensive system check"""
    print("🔍 HealthSync System Check")
    print("=" * 50)
    
    checks = [
        check_python_version(),
        check_dependencies(),
        check_files(),
        check_ai_model(),
        check_database(),
        check_app_imports()
    ]
    
    print("\n" + "=" * 50)
    print("📊 System Check Summary")
    print("=" * 50)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"🎉 All {total} checks passed! System is ready.")
        print("\n🚀 To start HealthSync:")
        print("   python start_simple.py")
        print("\n🧪 To test the system:")
        print("   python test_healthsync.py")
    else:
        print(f"⚠️  {passed}/{total} checks passed")
        print("\n💡 Please fix the issues above before starting HealthSync")
    
    print("\n📚 Available commands:")
    print("   python start_simple.py     - Start with SQLite (no Docker)")
    print("   python start_healthsync.py - Start with PostgreSQL (requires Docker)")
    print("   python test_healthsync.py  - Run comprehensive test")
    print("   python train_symptom_model.py - Train AI model")

if __name__ == "__main__":
    main()
