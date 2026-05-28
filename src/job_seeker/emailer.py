import os
import mimetypes
from O365 import Account

class EmailClient:
    def __init__(self, logger):
        self.logger = logger
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        
        if self.is_configured():
            # Azure 'Mobile and desktop applications' are Public Clients and cannot send a secret
            credentials = (self.client_id, "")
            # The library will save the token in o365_token.txt by default
            self.account = Account(credentials)
        else:
            self.account = None
            
    def is_configured(self):
        return bool(self.client_id and self.client_secret)
        
    def authenticate_if_needed(self):
        """
        Ensures the user is authenticated via OAuth2.
        If this is the first run, it will print a link to the console for the user to log in.
        """
        if not self.account:
            return False
            
        if not self.account.is_authenticated:
            self.logger.info("Microsoft Graph Authentication required.")
            self.logger.info("Follow the instructions in the console to authorize the app...")
            # 'message_send' maps to Mail.Send permission in Graph
            self.account.authenticate(scopes=['basic', 'message_send'])
            self.logger.info("Successfully authenticated via Azure OAuth2!")
            
        return self.account.is_authenticated
        
    def send_application(self, to_email, subject, body, attachment_path=None):
        if not self.is_configured():
            self.logger.error("AZURE_CLIENT_ID or AZURE_CLIENT_SECRET not configured in .env. Cannot send email.")
            return False
            
        if not self.authenticate_if_needed():
            self.logger.error("Failed to authenticate with Microsoft Graph API.")
            return False
            
        self.logger.info(f"Preparing to send application email to {to_email} via Microsoft Graph API...")
        
        try:
            m = self.account.new_message()
            m.to.add(to_email)
            m.subject = subject
            m.body = body
            
            if attachment_path and os.path.exists(attachment_path):
                m.attachments.add(attachment_path)
                self.logger.info(f"Attached {os.path.basename(attachment_path)} to email.")
                
            m.send()
            self.logger.info(f"Successfully sent email to {to_email} via Azure OAuth2!")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send email via Microsoft Graph API: {e}")
            return False
