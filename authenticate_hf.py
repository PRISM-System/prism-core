import os
from huggingface_hub import login
from dotenv import load_dotenv

def authenticate():
    """
    Logs in to the Hugging Face Hub using a token from an environment variable.
    """
    # Load environment variables from .env file for local development
    load_dotenv()
    
    token = os.getenv("HUGGING_FACE_TOKEN")
    
    if not token:
        print("Warning: HUGGING_FACE_TOKEN environment variable not found.")
        print("Proceeding without authentication. This may fail for gated models.")
        return

    print("Attempting to log in to Hugging Face Hub...")
    try:
        login(token=token, add_to_git_credential=False)
        print("Successfully logged in to Hugging Face Hub.")
    except Exception as e:
        print(f"Failed to log in to Hugging Face Hub: {e}")

if __name__ == "__main__":
    authenticate() 