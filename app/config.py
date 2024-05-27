import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ.get("CLIENT_ID",None)
CLIENT_SECRET = os.environ.get("CLIENT_SECRET",None)
SECRET_KEY = os.environ.get("SECRET_KEY",None)