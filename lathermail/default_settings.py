import os

SMTP_HOST = "127.0.0.1"
SMTP_PORT = 2525
API_HOST = "127.0.0.1"
API_PORT = 5000
SQLITE_FAST_SAVE = True
SQLALCHEMY_TRACK_MODIFICATIONS = False

# This hack for tests sits here, because tests launch SMTP server subprocess
if os.getenv("LATHERMAIL_TEST_DB_TYPE", "sqlite") == "mongo":
    DB_URI = "mongodb://localhost/lathermail_test_db"
