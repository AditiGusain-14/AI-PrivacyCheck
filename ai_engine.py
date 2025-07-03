import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use the available model
model = genai.GenerativeModel("models/gemini-1.5-flash")

# Core AI function
def chat_with_ai(messages):
    try:
        prompt = messages[-1]["content"]

        # Add instruction for AI to give score + summary
        full_prompt = f"""
You are AI SafeGuard, a digital privacy expert.

1. Answer the user’s question or scan their message.
2. After answering, provide:
   - A RISK SCORE from 0 (very safe) to 100 (very risky)
   - A short PRIVACY SUMMARY with 2–3 recommendations

Format your response like this (Markdown format):

**Reply:** <your main response>

**Risk Score:** <0–100>

**Privacy Summary:** 
- Tip 1
- Tip 2
        """.strip() + "\n\n" + prompt

        response = model.generate_content(full_prompt)
        return response.text.strip()

    except Exception as e:
        return f"❌ Gemini Error: {str(e)}"
