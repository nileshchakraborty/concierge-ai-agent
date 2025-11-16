
import os

from pydantic import BaseModel

class ConciergeConstants(BaseModel):
    
    SERPER_API_KEY = os.environ.get("SERPER_API_KEY")

    OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")
    
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL") 
    RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")
    SUBJECT = "Test Email from Python via smtp.dev"
    BODY = "This is a test email sent using the Python smtplib library and smtp.dev credentials."
    SMTP_SERVER = os.environ.get("SMTP_SERVER")
    SMTP_PORT = int(os.environ.get("SMTP_PORT"))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")