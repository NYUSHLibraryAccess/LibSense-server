import os
import json
from datetime import date

# for encoding/decoding messages in base64
from base64 import urlsafe_b64encode

# for dealing with attachment MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type

# Gmail API utils
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


# Google Drive Folder ID
GDRIVE_FOLDER_ID = "16Ffwk-PefJv7MYiLEsUO7_FCcQ7B9MoV"
# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/drive"
]
LOGGEDIN = "LOGGEDIN"
LOGGEDOFF = "LOGGEDOFF"

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


class LibSenseGSuite:
    def __init__(self):
        self.status = LOGGEDOFF
        try:
            with open("configs/config.json", "r") as cfg:
                cfg_json = json.load(cfg)
                self._email = cfg_json["email_config"]["email"]
                self._password = cfg_json["email_config"]["password"]
        except (FileNotFoundError, KeyError):
            raise BaseException("Please check the config file.")

        self.date = date.today().strftime("%Y-%m-%d")
        self.creds = None
        self.instance = None

    def authenticate(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("configs/token.json"):
            creds = Credentials.from_authorized_user_file("configs/token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("configs/credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("configs/token.json", "w") as token:
                token.write(creds.to_json())
        self.creds = creds
        return True

    def initialize_mail(self):
        self.authenticate()
        try:
            # Call the Gmail API
            service = build("gmail", "v1", credentials=self.creds)
            results = service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])

            if not labels:
                print("No labels found.")
                return

            self.instance = service

        except HttpError as error:
            # TODO(developer) - Handle errors from gsuite API.
            print(f"An error occurred when getting the Gmail instance: {error}")
            return False

    def initialize_drive(self):
        self.authenticate()
        try:
            # create drive api client
            service = build('drive', 'v3', credentials=self.creds)
            self.instance = service

        except HttpError as error:
            print(F'An error occurred when getting the GDrive instance: {error}')
            return False

    def add_attachment(self, message, filename):
        content_type, encoding = guess_mime_type(filename)
        if content_type is None or encoding is not None:
            content_type = "application/octet-stream"
        main_type, sub_type = content_type.split("/", 1)
        with open(filename, "rb") as fp:
            if main_type == "text":
                msg = MIMEText(fp.read().decode(), _subtype=sub_type)
            elif main_type == "image":
                msg = MIMEImage(fp.read(), _subtype=sub_type)
            elif main_type == "audio":
                msg = MIMEAudio(fp.read(), _subtype=sub_type)
            else:
                msg = MIMEBase(main_type, sub_type)
                msg.set_payload(fp.read())
        filename = os.path.basename(filename)
        msg.add_header("Content-Disposition", "attachment;", filename=filename)
        message.attach(msg)

    def build_message(self, destination, nickname, count, attachments=None):
        if attachments is None:
            attachments = {}
        message = MIMEMultipart()
        message["to"] = destination
        message["from"] = self._email
        message["subject"] = TRACKING_EMAIL_TITLE % self.date
        body = ""
        for k, v in count.items():
            body += BODY_TEMPLATE % (k, v, self.date)
        message.attach(MIMEText(TRACKING_EMAIL_TEMPLATE % (nickname, body)))
        for filename in attachments.values():
            self.add_attachment(message, filename)
        return {"raw": urlsafe_b64encode(message.as_bytes()).decode()}

    def send_message(self, destination, nickname, count, attachments):
        return (
            self.instance.users()
            .messages()
            .send(userId="me", body=self.build_message(destination, nickname, count, attachments))
            .execute()
        )

    def flush_date(self):
        self.date = date.today().strftime("%Y-%m-%d")

    def upload_file(self, filename, filepath):
        try:
            # create drive api client
            file_metadata = {'name': filename, "parents": [GDRIVE_FOLDER_ID]}
            media = MediaFileUpload(filepath)
            # pylint: disable=maybe-no-member
            file = self.instance.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(F'File ID: {file.get("id")}')

        except HttpError as error:
            print(F'An error occurred: {error}')
            return False
        return True
