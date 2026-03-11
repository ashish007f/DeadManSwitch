import os
import sys
from dotenv import load_dotenv

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

from app.services.genai_service import GenAIService

def test_genai():
    service = GenAIService()
    
    if not service.api_key or service.api_key == "your_gemini_api_key_here":
        print("❌ Error: GEMINI_API_KEY not set in .env")
        return

    print("--- Testing GenAI Reminders ---")
    
    scenarios = [
        ("Ashish", "GENTLE", "due in 2 hours"),
        ("Ashish", "FIRM", "overdue by 1 hour"),
        ("Ashish", "CRITICAL", "overdue by 23 hours (Contacts will be notified in 1 hour)")
    ]
    
    for name, urgency, context in scenarios:
        print(f"\n[Scenario: {urgency}]")
        result = service.generate_reminder(name, urgency, context)
        if result:
            print(f"Result: {result}")
            print(f"Length: {len(result)} chars")
        else:
            print("Failed to generate message.")

if __name__ == "__main__":
    test_genai()
