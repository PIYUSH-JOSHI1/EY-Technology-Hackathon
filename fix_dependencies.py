"""
Dependency Fix Script for Tata Capital Loan Chatbot
Run this script if you encounter import issues with the Groq package.
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a command and return success status"""
    try:
        print(f"🔧 Running: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Success: {command}")
            return True
        else:
            print(f"❌ Failed: {command}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Exception running {command}: {e}")
        return False

def main():
    print("🏦 Tata Capital Loan Chatbot - Dependency Fix Tool")
    print("=" * 50)
    
    # Check current environment
    print("🔍 Checking current environment...")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    # Try to detect current groq version
    try:
        import pkg_resources
        groq_version = pkg_resources.get_distribution("groq").version
        print(f"Current Groq version: {groq_version}")
    except:
        print("Groq package not found or not properly installed")
    
    print("\n🚀 Starting dependency fixes...")
    
    # Step 1: Uninstall problematic packages
    print("\n📦 Step 1: Removing problematic packages...")
    packages_to_remove = ['groq', 'httpx']
    for package in packages_to_remove:
        run_command(f"pip uninstall {package} -y")
    
    # Step 2: Install compatible versions
    print("\n📦 Step 2: Installing compatible versions...")
    compatible_packages = [
        'httpx==0.24.1',
        'groq==0.3.0',
        'python-dotenv==1.0.0',
        'Flask==2.3.0',
        'reportlab==4.0.4'
    ]
    
    for package in compatible_packages:
        run_command(f"pip install {package}")
    
    # Step 3: Verify installation
    print("\n✅ Step 3: Verifying installation...")
    try:
        import groq
        print("✅ Groq package imported successfully")
        
        from groq import Groq
        print("✅ Groq class imported successfully")
        
        print("\n🎉 All dependencies fixed successfully!")
        print("You can now run: python app.py")
        
    except ImportError as e:
        print(f"❌ Import still failing: {e}")
        print("\n🔧 Alternative solutions:")
        print("1. Try creating a new virtual environment:")
        print("   python -m venv fresh_env")
        print("   fresh_env\\Scripts\\activate")
        print("   pip install -r requirements.txt")
        print("\n2. Use the mock mode (application will still work):")
        print("   python app.py")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
