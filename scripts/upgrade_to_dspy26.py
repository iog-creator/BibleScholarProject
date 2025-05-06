#!/usr/bin/env python
"""
Upgrade Script for DSPy 2.6

This script:
1. Checks the installed DSPy version
2. Upgrades to DSPy 2.6 if needed
3. Updates key files to use the new DSPy 2.6 API
4. Disables Langfuse integration that's causing issues
"""
import os
import sys
import re
import subprocess
import importlib
import shutil
from pathlib import Path

# Files to be updated
FILES_TO_UPDATE = [
    "src/dspy_programs/huggingface_integration.py",
    "final_bible_qa_api.py",
    "src/api/dspy_api.py",
    "simple_dspy_train.py",
    "simple_dspy_api.py",
    "minimal_dspy_api.py",
]

def print_header(message):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {message}")
    print("=" * 80)

def print_step(message):
    """Print a step message."""
    print(f"\n➤ {message}")

def run_command(command):
    """Run a shell command and return the output."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result.stdout

def check_dspy_version():
    """Check the installed DSPy version."""
    try:
        # Use pip to check the installed version
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "dspy-ai"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            print("DSPy is not installed.")
            return None
        
        # Parse the version from pip output
        for line in result.stdout.splitlines():
            if line.startswith("Version: "):
                version = line.split("Version: ")[1].strip()
                print(f"Current DSPy version: {version}")
                return version
        
        print("Failed to determine DSPy version.")
        return None
    except Exception as e:
        print(f"Error checking DSPy version: {e}")
        return None

def install_dspy_26():
    """Install DSPy 2.6."""
    print_step("Installing DSPy 2.6...")
    run_command("pip install dspy-ai==2.6.0")
    
    # Verify installation
    try:
        # Use pip to check the installed version
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "dspy-ai"],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Version: "):
                    version = line.split("Version: ")[1].strip()
                    print(f"DSPy version after install: {version}")
                    break
        else:
            print("Failed to verify DSPy installation.")
    except Exception as e:
        print(f"Error verifying installation: {e}")

def backup_file(file_path):
    """Create a backup of a file."""
    backup_path = f"{file_path}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")
    return backup_path

def update_huggingface_integration():
    """Update the HuggingFace integration file."""
    file_path = "src/dspy_programs/huggingface_integration.py"
    print_step(f"Updating {file_path}...")
    
    backup_file(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace GPT3 with LM
    content = re.sub(
        r"from dspy import GPT3",
        "from dspy import LM",
        content
    )
    
    # Update configure_teacher_model function
    content = re.sub(
        r"def configure_teacher_model\(api_key, model_name=.*?\):[^\n]*\n\s+\"\"\"[^\"]*\"\"\"\n\s+if.*?lm_studio.*?:\n\s+# Use LM Studio API\n\s+return GPT3\(model=model_name, api_base=.*?\)",
        """def configure_teacher_model(api_key, model_name=None):
    \"\"\"Configure a teacher model for DSPy training, using either HuggingFace or LM Studio.\"\"\"
    if "LM_STUDIO_API_URL" in os.environ:
        # Use LM Studio API
        api_base = os.environ.get("LM_STUDIO_API_URL", "http://localhost:1234/v1")
        return LM(f"openai/{model_name}", api_base=api_base, api_key="lm-studio", model_type='chat')""",
        content
    )
    
    # Update configure_local_student_model function if it exists
    if "configure_local_student_model" in content:
        content = re.sub(
            r"def configure_local_student_model\(model_name=.*?\):[^\n]*\n\s+\"\"\"[^\"]*\"\"\"\n\s+if.*?lm_studio.*?:\n\s+# Use LM Studio API\n\s+return GPT3\(model=model_name, api_base=.*?\)",
            """def configure_local_student_model(model_name=None):
    \"\"\"Configure a local student model for DSPy training using LM Studio.\"\"\"
    if "LM_STUDIO_API_URL" in os.environ:
        # Use LM Studio API
        api_base = os.environ.get("LM_STUDIO_API_URL", "http://localhost:1234/v1")
        return LM(f"openai/{model_name}", api_base=api_base, api_key="lm-studio", model_type='text-completion')""",
            content
        )
    
    # Update dspy.settings.configure to dspy.configure
    content = re.sub(
        r"dspy\.settings\.configure\(lm=",
        "dspy.configure(lm=",
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def update_api_files():
    """Update the API files to use the new DSPy 2.6 API and disable Langfuse."""
    for file_path in FILES_TO_UPDATE:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
        
        print_step(f"Updating {file_path}...")
        backup_file(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace GPT3 with LM
        content = re.sub(
            r"from dspy import GPT3",
            "from dspy import LM",
            content
        )
        
        content = re.sub(
            r"import dspy\nfrom dspy import GPT3",
            "import dspy\nfrom dspy import LM",
            content
        )
        
        # Replace GPT3(...) with LM("openai/...")
        content = re.sub(
            r"GPT3\(model=([^,\)]+)(.+?)\)",
            r'LM(f"openai/{\1}"\2, model_type="chat")',
            content
        )
        
        # Update dspy.settings.configure to dspy.configure
        content = re.sub(
            r"dspy\.settings\.configure\(lm=",
            "dspy.configure(lm=",
            content
        )
        
        # Disable Langfuse integration (temporary fix for the NoneType has no len() error)
        if "langfuse" in content:
            print("  Disabling Langfuse integration...")
            content = re.sub(
                r"from langfuse.*?\n",
                "# Langfuse integration disabled\n",
                content
            )
            
            content = re.sub(
                r"@langfuse_decorator.*?\n",
                "# @langfuse_decorator\n",
                content
            )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

def create_test_script():
    """Create a test script to verify the DSPy 2.6 integration works."""
    file_path = "test_dspy26.py"
    print_step(f"Creating {file_path}...")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("""#!/usr/bin/env python
\"\"\"
Test script for DSPy 2.6 with LM Studio integration
\"\"\"
import os
import sys
from dotenv import load_dotenv

# Load environment variables
if os.path.exists('.env.dspy'):
    load_dotenv('.env.dspy')
    print("Loaded environment variables from .env.dspy")

import dspy
from dspy import InputField, OutputField

# Print DSPy version
print(f"DSPy version: {dspy.__version__}")

# Configure LM Studio connection
lm_studio_url = os.environ.get('LM_STUDIO_API_URL', 'http://localhost:1234/v1')
model_name = os.environ.get('LM_STUDIO_CHAT_MODEL', 'darkidol-llama-3.1-8b-instruct-1.2-uncensored')

print(f"Connecting to LM Studio at {lm_studio_url}")
print(f"Using model: {model_name}")

# Create a language model with DSPy 2.6 API
lm = dspy.LM(
    f"openai/{model_name}", 
    api_base=lm_studio_url,
    api_key="lm-studio",
    model_type='chat'
)

# Configure DSPy to use this language model
dspy.configure(lm=lm)

# Define a simple signature for testing
class SimpleQA(dspy.Signature):
    \"\"\"Answer simple questions.\"\"\"
    question = InputField(desc="The question to answer")
    answer = OutputField(desc="The answer to the question")

# Create a basic module
class SimpleQAModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.qa_model = dspy.Predict(SimpleQA)
    
    def forward(self, question):
        return self.qa_model(question=question)

# Run a simple test
print("\\nRunning test with DSPy 2.6...")
try:
    module = SimpleQAModule()
    result = module(question="What is the capital of France?")
    print(f"Question: What is the capital of France?")
    print(f"Answer: {result.answer}")
    print("\\nTest completed successfully!")
except Exception as e:
    print(f"Error during test: {e}")
""")
    
    print(f"Created test script: {file_path}")
    return file_path

def main():
    print_header("DSPy 2.6 Upgrade Script")
    
    # Check current version
    current_version = check_dspy_version()
    
    # Install DSPy 2.6 if needed
    if current_version != "2.6.0":
        install_dspy_26()
    else:
        print("DSPy 2.6.0 is already installed.")
    
    # Update files
    update_huggingface_integration()
    update_api_files()
    
    # Create test script
    test_script = create_test_script()
    
    print_header("Upgrade Complete")
    print("The upgrade to DSPy 2.6 is complete.")
    print(f"\nTo test the new installation, run: python {test_script}")
    print("\nIf everything works correctly, you can start the Bible QA API with:")
    print("python final_bible_qa_api.py")
    print("\nNote: If you encounter any issues, backups of modified files were created with .bak extension.")

if __name__ == "__main__":
    main() 