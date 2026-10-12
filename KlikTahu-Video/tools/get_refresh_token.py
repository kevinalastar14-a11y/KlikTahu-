"""
tools/get_refresh_token.py — bikin refresh token YouTube sekali saja (lokal).

Prasyarat (sekali):
  1. Google Cloud Console -> buat project -> aktifkan "YouTube Data API v3".
  2. OAuth consent screen -> tipe "External" -> tambahkan akunmu sebagai test user.
  3. Credentials -> Create credentials -> OAuth client ID -> tipe "Desktop app".
  4. Simpan client id & client secret sebagai env var:
       export YT_CLIENT_ID="....apps.googleusercontent.com"
       export YT_CLIENT_SECRET="..."

Jalankan:
    python tools/get_refresh_token.py

Browser akan terbuka untuk login. Setelah selesai, script menampilkan
YT_REFRESH_TOKEN. Simpan sebagai secret (GitHub Actions / .env lokal), lalu
video bisa diunggah dengan tools/youtube_upload.py.
"""

from __future__ import annotations

import os
import sys

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main() -> int:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        raise SystemExit("Butuh paket: pip install google-auth-oauthlib")

    cid = os.environ.get("YT_CLIENT_ID")
    secret = os.environ.get("YT_CLIENT_SECRET")
    if not cid or not secret:
        raise SystemExit("Set dulu YT_CLIENT_ID dan YT_CLIENT_SECRET (lihat docstring).")

    flow = InstalledAppFlow.from_client_config(
        {"installed": {"client_id": cid, "client_secret": secret,
                       "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                       "token_uri": "https://oauth2.googleapis.com/token",
                       "redirect_uris": ["http://localhost"]}},
        scopes=SCOPES,
    )
    creds = flow.run_local_server(port=0, prompt="consent")
    print("\nSimpan baris berikut sebagai secret (jangan dibagikan):\n")
    print(f"YT_REFRESH_TOKEN={creds.refresh_token}")
    print("\nLalu upload:\n  python tools/youtube_upload.py --privacy private")
    return 0


if __name__ == "__main__":
    sys.exit(main())
