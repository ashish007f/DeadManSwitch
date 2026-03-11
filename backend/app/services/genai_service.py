import os
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class GenAIService:
    """Service for interacting with LLMs using LangChain for maximum flexibility"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_id = os.getenv("GENAI_MODEL_ID", "gemini-2.5-flash")
        
        if self.api_key:
            # Currently configured for Google, but easy to add others
            self.llm = ChatGoogleGenerativeAI(
                model=self.model_id,
                google_api_key=self.api_key,
                temperature=0.8, # More creative responses
                timeout=10.0, # Fail fast if LLM is slow
                max_retries=1  # Don't waste time on retries
            )
        else:
            self.llm = None

    def generate_reminder(self, display_name: str, urgency: str, time_context: str) -> Optional[str]:
        """
        Generates a personalized check-in reminder using LangChain.
        """
        if not self.llm:
            return None

        prompt = ChatPromptTemplate.from_template("""
        Generate a short, personal safety check-in reminder for a user named {name}.
        The urgency level is: {urgency}.
        Context: Their check-in is {context}.
        
        Tone guidelines based on urgency:
        - GENTLE: Friendly, casual, "just checking in" vibe.
        - FIRM: Serious, direct, "please take action" vibe.
        - CRITICAL: Urgent, high-stakes, "final warning before alerting contacts" vibe.
        
        STRICT CONSTRAINTS:
        - Must be under 100 characters.
        - Do not use hashtags or emojis.
        - Output ONLY the message text.
        """)

        chain = prompt | self.llm | StrOutputParser()

        try:
            response = chain.invoke({
                "name": display_name,
                "urgency": urgency,
                "context": time_context
            })
            return response.strip().replace('"', '')
        except Exception as e:
            print(f"⚠ LangChain Generation Error: {e}")
            return None
