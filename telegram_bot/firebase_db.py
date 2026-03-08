import json
import firebase_admin
from firebase_admin import credentials, db

raw_private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC0I8PCmwtGUrab\npj98b9Wn7GkvwWQkWq/iPTIJTIP8i/D16dX1+d7mKCv5J09hDZeXJw0oB7VY8bT8\nWSOLQr0X1/ISYZLq7gHT+UxCLF2Gee4XNJpmptHvapOquM2y0V/p0A3I5j3b/9Ui\nbBn EYAWyWILxUQ8Axxy2yvF0dWb+cfqtHi8kn3kAxqBTM6EvWlIWY8izKfdO2RiV\n3HMVEQHkjwKsroJeJl/3KYDRpxF3Dtr5Dxr4J/aUQVT TQ7ukOU/FKPfNzQli8ej+\nXwjh2AQyvu85WcCzj0XAi/5C7JKVIArMXJzxAhAxOkjVA72ssLT6EHYWOkOCQ1MB\nc90avuXBAgMBAAECg gEAUlKd3ct5JZQbO5qIHNgG7gzOLTLWDv8areuFeFZtYvaZ\nEejhDN46DTiCkAR09Ed/5WXFT2vmZlVffotGARhozgKz786Dk7VdRIADZ6Jaw1/p\nfNVfUlYeTqmH/lciOfwRNwsLoaoGzwllX6vDQskXEV/9x0Zh8tsLtkWcfrpAbTro\n8xOzetCy6l4FkRUgSjOYOwwn3uMyFvA Vs91u7m7eVG57tgcW7g7n7PDkybSfxKxy\nF6ySCqdwycMg4NKMJXE3VYAsEDqvpul1ka/IXCgnHxNaF+lAXe2uwIQCamoKWqR7\nWj0FI KPcD2Stymo9EAbGTdezh+lu+ZDEKo+qV0UEeQKBgQDhiKQyD5LA+ejnYuXq\nrJIs2LXRaVu82QEJ1cqU+7q4etY24+P2p1KfYz5pY/PNT Z5Fv9fF6vouu/E3D4T8\nnOLuacCYzTkjOG7KAnoRTwjqo83JEJL0Ubr2PrQ3EPgK1lBGzDTW+prYUT8tUl09\nZMtWt+U3omLzMHEARs jicgLANwKBgQDM18Zu8tubVQAED/34KXpKWVpywfm1yJ4D\nmsrqdbz0KlfZIZxdEZqWED6RymDNv+03l6CFa5mNpIytzxEnV+mQH4/QOF Xyfr9k\n+pVn46FpIDZs/aasl5fbNQcfrRIUyqsheITpwz78xCkm1citxM/KkXBqlBMFAcRk\nLQ9arLTdxwKBgEartX+Vje8QRIGmdSBn DfgQC3tyhH7S7FWHDHIaV7IjtW1DusMq\nIXCxed0hqF4ReJbSs0yJCAJ1szIiqA+YvFA1WGVfPwmEZJr7jhAy7EykISx2DHuv\n0G4Onw oORJ86Sbb/0bKOtt8jGh8DFQv5wS82yTjevAs1cLPTKnKTcbOfAoGBAJSU\n+wFlNTfhmuZXdz93TpX5ZCsTWn6qKzuwHvmcN1fgEuKTh6 jWaQvqcogrhLYZPgbx\n++RrHPFp5wT3ypiAIxGAYz+EbYs8trWXMaIusdjgHbpG7owIVYUSXL10O0ZLj3/y\nvG4XSmvsGXFq5mps9NAZ WLJl/7nFA2AqcxWxamvnAoGAPx3fyCoQrSWRECNK2BZX\nUKG19QHbm6JwR1VKcKp5UivE5ieYm6843cQ1Vg4phJjDQtO6slTahXNZ54lTMv73\na6JVEJbULFMXZ573OWrdYziPvDxwlfg90zfpjGYy8OVZi+NDpp2RstTmuQRYjAuc\nUbUdnL0J22IDgvU5MekWLTM=\n-----END PRIVATE KEY-----\n"

# Фикс пробелов в ключе, которые могли появиться при копировании
fixed_private_key = raw_private_key.replace("-----BEGIN PRIVATE KEY-----\n", "").replace("\n-----END PRIVATE KEY-----\n", "").replace(" ", "\n")
fixed_private_key = f"-----BEGIN PRIVATE KEY-----\n{fixed_private_key}\n-----END PRIVATE KEY-----\n"

FIREBASE_CONFIG = {
    "type": "service_account",
    "project_id": "boevik-1e8c3",
    "private_key_id": "fcfcad22f1644ab7bd27ffc632253275183516cb",
    "private_key": fixed_private_key,
    "client_email": "firebase-adminsdk-fbsvc@boevik-1e8c3.iam.gserviceaccount.com",
    "client_id": "116136449002776595932",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40boevik-1e8c3.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CONFIG)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://boevik-1e8c3-default-rtdb.europe-west1.firebasedatabase.app/'
        })

def get_db_ref(path):
    return db.reference(path)
