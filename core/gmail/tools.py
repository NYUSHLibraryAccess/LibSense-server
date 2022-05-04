import os
import json
from datetime import date
# Gmail API utils
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type

# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']
LOGGEDIN = 'LOGGEDIN'
LOGGEDOFF = 'LOGGEDOFF'

TRACKING_EMAIL_TITLE = "LibSense - Tracking Report %s"
TRACKING_EMAIL_TEMPLATE = """
Hi %s,

Here are the information about the orders that needs to be tracked:

%s

The detailed order report is attached to this email.

------------------------------------------------------------------------
LibSense

"""
BODY_TEMPLATE = """
---------------------
Report Type: %s
Number of Orders: %d
Generated Date: %s
---------------------
"""


class LibSenseEmail():
    def __init__(self):
        self.status = LOGGEDOFF
        try:
            with open("configs/config.json", "r")  as cfg:
                cfg_json = json.load(cfg)
                self._email = cfg_json["email_config"]["email"]
                self._password = cfg_json["email_config"]["password"]
        except (FileNotFoundError, KeyError) as e:
            raise BaseException("Please check the config file.")
        
        self.service = self.authenticate()
        self.date = date.today().strftime("%Y-%m-%d")
        
    def authenticate(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('configs/token.json'):
            creds = Credentials.from_authorized_user_file('configs/token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'configs/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('configs/token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            # Call the Gmail API
            service = build('gmail', 'v1', credentials=creds)
            results = service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])

            if not labels:
                print('No labels found.')
                return
            
            return service

        except HttpError as error:
            # TODO(developer) - Handle errors from gmail API.
            print(f'An error occurred: {error}')
            return False
    
    def add_attachment(self, message, filename):
        content_type, encoding = guess_mime_type(filename)
        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        fp = open(filename, 'rb')
        if main_type == 'text':
            msg = MIMEText(fp.read().decode(), _subtype=sub_type)
        elif main_type == 'image':
            msg = MIMEImage(fp.read(), _subtype=sub_type)
        elif main_type == 'audio':
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
        else:
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
        fp.close()
        filename = os.path.basename(filename)
        msg.add_header('Content-Disposition', 'attachment;', filename=filename)
        message.attach(msg)

    def build_message(self, destination, nickname, count, attachments={}):
        message = MIMEMultipart()
        message['to'] = destination
        message['from'] = self._email
        message['subject'] = TRACKING_EMAIL_TITLE % self.date
        body = ""
        for k, v in count.items():
            body += BODY_TEMPLATE % (k, v, self.date)
        message.attach(MIMEText(TRACKING_EMAIL_TEMPLATE % (nickname, body)))
        for key, filename in attachments.items():
            self.add_attachment(message, filename)
        return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}

    def send_message(self, destination, nickname, count, attachments):
        return self.service.users().messages().send(
            userId="me",
            body=self.build_message(destination, nickname, count, attachments)).execute()
    
    def flush_date(self):
        self.date = date.today().strftime("%Y-%m-%d")
