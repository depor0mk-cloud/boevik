import json
import firebase_admin
from firebase_admin import credentials, db

raw_private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCwz0tKbuAsSr8B\n5wut4v2iPFEBs7A349qnpNJnj8Z148CmF4B849+r4tGJrSogU+KX2qCpIEuBNl5i\nO3fy2yqDLxF0pilHlTjHZJY4m25SedUihF156wivNICVi/g5+oHgeGDDZ02RZTtt\nozMZf7z+UpNZ8Xs51o2kkPLEAY+IpAINe+mp4E/h10eOa4f8VwOpmJhGaG6p4/9B\nMgGOnlLigpHUaKAOQZpFfL7XxQbbVhR4B3of4bUXpi5ML1C9O6nUzh1Pt+TlVpp2\nsWcWP+Oy4LdENP0FWvUlGvib97tI2v1eEpCBREtwTmDoGDT0d39m216O09B34Fw6\nq1bswADlAgMBAAECggEAQ/muTJOMA/tIrAaT6upV8MWXrzvSB+rF6aXoboBMII7L\nRg/LCjjhiUfOn0u/4mXdu9wF4H/WB3tLliCe4PN5yK2T3HD1ddvc1GvLhT/cjkDg\nvEB/X5wI3rMkrFn/uOqifBZLvVQ98iQlUOVpg+gkVPKSTAYXBgmCsz421zxyXmlr\n4uxcRdhLyeePNyGY5pjpbphS7LOg8Uzarp1BHy0Z/tf1Xvqi5o5JBSPw8oKuUHmK\nOCBO2riAFGAxLIx8n4TFOIQ1OJNZ7iZfEfWzyUnIMu11Pmn2VnIjjWxv9xwEBIBh\no/q9/K0N4in4Fvn2kERuCWAqxr/VEG485SUSDOyPkQKBgQDb5QtDY5ClPPGEiIWb\nx1S20Oof2BRVJnD8ZdUUixYjBJna8hUU0sCGcLCbgfgiYRYL1ttcKjiMgMi2/X6A\n2WLoWvTUD8wWW72+bB2VYebV0vopA6QJhzXXqjn/ZsdakevEXnLEaoInjB97HHoN\nddRWzTej8P/VAqTCkEMPpQAHdwKBgQDN1zxu+uACFP43bug9KabQ75Xd8VSSFkSu\nIAHFGX8SR8z0Q2sjLayRaz30C1lhnvNluNcv2gf8sA9bn4JtqOcN0/oQ6ayf6BXR\nwXSrjXAp/cFTkT9V7AjO9x6cwNU6Ym/fGJ1hIHDU2hCjNxfmciFJN4JHkmGejJFr\n3n1Wvo8JgwKBgEZQKxXVVH9ByYizjuWNC42ZqAOeuIGx1RcgCM6U2vM/mWLlXdBW\nw7E5f396Q7naiY4nmeUSqxpiY8v/qt/Qo0vhKcBVfND5bObi82K8928QE2XiACX7\n0j+v8vO0DbLsThNwkAo2dH/o0ngvVufO8aL/4/bMLUITolOEha0O+b9pAoGBAIwk\n2tSEojdIq7x6GkxqK1VdiZ/OS1IbLy+OQyY6sbV0hSpZLHyLAE8RwOCDSZuZaQX8\nzyWZQI7eH9a1x0t6D7XuePdC4XENxq1FFXYnmhI83n9TCNgrF+Qxg/odoA9cLear\nD5utRqTkwyccv3z6f4cl7+Fi3GviMLBMjvGcVC6ZAoGBAKYitsJEEkr3pwXEQTot\n2wBiAbJGep3nk7Vx8t9FfKHuOTcaISJlPEEzj37LtS+s0deJg/UcjE0n2zMMOHTq\nN4oCxFVD3bMDIoLtYuJnGXI+zkLrsEWeATTv7lEUEuNq2f3gsk+nwSBVo880TrRd\nX7oRjawE5ZZtHEe3Mi2sv8DW\n-----END PRIVATE KEY-----\n"

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
