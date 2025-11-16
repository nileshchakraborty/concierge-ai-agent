
from email.message import EmailMessage
import os
import smtplib
import ssl




class SendMailClient:
    

    def send_email(to_address: str, subject: str, body: str) -> str:
        """Sends a simple plain text email using smtplib."""
        msg = EmailMessage()
        msg.set_content(BODY)
        msg["Subject"] = SUBJECT
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL

        try:
            # Create a default SSL context for security
            context = ssl.create_default_context()
            
            # Connect to the SMTP server and initiate TLS
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.ehlo()  # Optional, but good practice
                server.starttls(context=context) # Secure the connection with STARTTLS
                server.ehlo()  # Re-identify after STARTTLS
                
                # Log in using your API key as the username (and empty password if needed)
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                
                # Send the email
                server.send_message(msg)
                print("Email sent successfully!")
                
        except smtplib.SMTPAuthenticationError:
            print("Authentication failed. Check your API key and ensure it's correct.")
        except Exception as e:
            print(f"An error occurred: {e}")

        pass