import os
import firebase_admin
from firebase_admin import credentials, db

try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

def init_firebase():
    if not firebase_admin._apps:
        private_key = os.getenv("FIREBASE_PRIVATE_KEY")
        client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        database_url = os.getenv("FIREBASE_DATABASE_URL")

        if private_key and client_email and project_id:
            # Handle escaped newlines in environment variables
            formatted_key = private_key.replace('\\n', '\n')
            
            cred_dict = {
                "type": "service_account",
                "project_id": project_id,
                "private_key": formatted_key,
                "client_email": client_email,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {
                'databaseURL': database_url
            })
        else:
            # Fallback to local config if env vars are missing (for legacy support or local testing)
            # But we prefer env vars to avoid the ASN.1 parsing error
            print("Warning: Firebase environment variables missing. Bot might fail to start.")
            # You can add a fallback here if needed, but env vars are recommended.

def get_db_ref(path):
    return db.reference(path)
