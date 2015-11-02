import os


DB_URI = "sqlite:///" + os.path.expanduser("~/.lathermail.db")
DEBUG_MODE = False
SMTP_HOST = "127.0.0.1"
SMTP_PORT = 2525
API_HOST = "127.0.0.1"
API_PORT = 5000
SQLITE_FAST_SAVE = True
SQLALCHEMY_TRACK_MODIFICATIONS = False
