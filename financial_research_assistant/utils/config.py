import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
# This is useful for local development.
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env') # Points to the .env file in the root directory
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY") # As per .env.example

# You can add other configurations here if needed, for example:
# TAVILY_API_URL = "https://api.tavily.com/search"
# GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"

# Basic check to ensure API keys are loaded (optional, but good for early warning)
# if not GOOGLE_API_KEY:
#     print("Warning: GOOGLE_API_KEY is not set.")
# if not TAVILY_API_KEY:
#     print("Warning: TAVILY_API_KEY is not set.")
