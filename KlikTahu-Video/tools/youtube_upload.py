"""
tools/youtube_upload.py — upload video Short ke YouTube lewat Data API v3.

Kredensial dibaca dari environment (JANGAN pernah ditulis di kode):
    YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN

Mendapatkan refresh token sekali saja:
    python tools/get_refresh_token.py

Pemakaian:
    python tools/youtube_upload.py                       # upload sebagai 'private'
    python tools/youtube_upload.py --privacy public
    python tools/youtube_upload.py --file KlikTahu_Shorts_1080x1920.mp4 --tags editing,shorts
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from script_kliktahu import YOUTUBE_DESCRIPTION, YOUTUBE_TITLE  # noqa: E402

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CHUNK = 8 * 1024 * 1024


def build_service():
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        raise SystemExit("Butuh paket: pip install google-api-python-client google-auth-oauthlib")

    client_id = os.environ.get("YT_CLIENT_ID")
    client_secret = os.environ.get("YT_CLIENT_SECRET")
    refresh_token = os.environ.get("YT_REFRESH_TOKEN")
    missing = [k for k, v in dict(YT_CLIENT_ID=client_id, YT_CLIENT_SECRET=client_secret,
                                  YT_REFRESH_TOKEN=refresh_token).items() if not v]
    if missing:
        raise SystemExit("Environment belum lengkap: " + ", ".join(missing) +
                         "\nLihat docstring file ini untuk cara membuat refresh token.")

    creds = Credentials(None, refresh_token=refresh_token, token_uri="https://oauth2.googleapis.com/token",
                        client_id=client_id, client_secret=client_secret, scopes=SCOPES)
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload(path: Path, title: str, description: str, tags: list[str], privacy: str,
           category: str = "22") -> str:
    from googleapiclient.http import MediaFileUpload

    if not path.exists():
        raise SystemExit(f"File tidak ditemukan: {path}")
    size_mb = path.stat().st_size / 1024 / 1024
    print(f"[upload] {path.name} ({size_mb:.1f} MB) sebagai '{privacy}' ...")

    service = build_service()
    body = dict(
        snippet=dict(title=title[:100], description=description[:5000], tags=tags,
                     categoryId=category, defaultLanguage="id", defaultAudioLanguage="id"),
        status=dict(privacyStatus=privacy, selfDeclaredMadeForKids=False, embeddable=True),
    )
    media = MediaFileUpload(str(path), mimetype="video/mp4", chunksize=CHUNK, resumable=True)
    request = service.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  {int(status.progress() * 100):3d}%", flush=True)
    vid = response["id"]
    print(f"[upload] selesai: https://youtube.com/shorts/{vid}")
    return vid


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Upload Short KlikTahu ke YouTube")
    ap.add_argument("--file", default=str(ROOT / "KlikTahu_Shorts_1080x1920.mp4"))
    ap.add_argument("--title", default=YOUTUBE_TITLE)
    ap.add_argument("--description", default=YOUTUBE_DESCRIPTION)
    ap.add_argument("--tags", default="shorts,editing,video editing,retention,konten kreator")
    ap.add_argument("--privacy", default=os.environ.get("YT_PRIVACY", "private"),
                    choices=["private", "unlisted", "public"])
    args = ap.parse_args(argv)
    upload(Path(args.file), args.title, args.description,
           [t.strip() for t in args.tags.split(",") if t.strip()], args.privacy)
    return 0


if __name__ == "__main__":
    sys.exit(main())
