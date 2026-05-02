"""
YouTube Video Uploader — 山海電台 Vol.1
Requires: client_secrets.json from Google Cloud Console
"""
import os, sys, json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS = "/home/user/Gulas/client_secrets.json"
TOKEN_FILE     = "/home/user/Gulas/token.pickle"

VIDEO_FILE  = "/home/user/Gulas/assets/output/taiwan_mountain_radio_vol1.mp4"
THUMB_FILE  = "/home/user/Gulas/assets/thumbnail/thumbnail_vol1.png"

TITLE = "🏔️ 太魯閣峽谷晨光 1小時 — 台灣山海 Indie Folk｜讀書・工作・療癒放鬆音樂"

DESCRIPTION = """太魯閣峽谷——清晨的陽光穿透大理石峽壁，流水聲與鳥鳴聲交織，讓你的心回到最純粹的狀態。

🎵 1 小時不間斷的台灣 Indie Folk 音樂，專為深度工作、讀書專注、或純粹放鬆而設計。

──────────────────────────
🏔️ 關於山海電台
我們記錄台灣最美的山林與海岸風景，配上手工挑選的 Indie Folk 音樂，為你打造一個可以喘息的聲音空間。
新影片每週發布 · 訂閱開啟通知不錯過

🎧 最佳聆聽方式：耳機 · 音量 50~70% · 閉眼感受
──────────────────────────
#台灣音樂 #indiefolk #lofi #療癒音樂 #讀書音樂 #TarokoGorge #Taiwan"""

TAGS = [
    "台灣音樂", "indie folk", "lofi", "太魯閣峽谷", "Taroko Gorge",
    "療癒音樂", "讀書音樂", "工作音樂", "ambient music", "chill music",
    "Taiwan nature", "台灣自然風景", "folk music", "relax music",
    "study music", "acoustic guitar", "1小時音樂", "山海電台"
]

def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
            creds = flow.run_local_server(port=8080, open_browser=False)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
    return creds

def upload():
    if not os.path.exists(CLIENT_SECRETS):
        print("❌ 找不到 client_secrets.json")
        print("   請按照說明把 Google OAuth 憑證放到:")
        print(f"   {CLIENT_SECRETS}")
        sys.exit(1)

    print("🔐 取得 Google 授權...")
    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    print(f"📤 上傳影片: {VIDEO_FILE}")
    print(f"   大小: {os.path.getsize(VIDEO_FILE)/1024/1024:.0f} MB")

    body = {
        "snippet": {
            "title": TITLE,
            "description": DESCRIPTION,
            "tags": TAGS,
            "categoryId": "10",          # Music
            "defaultLanguage": "zh-TW",
            "defaultAudioLanguage": "zh-TW",
        },
        "status": {
            "privacyStatus": "private",   # 先設 private，確認OK再改public
            "selfDeclaredMadeForKids": False,
        }
    }

    media = MediaFileUpload(
        VIDEO_FILE,
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024   # 10MB chunks
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    print("上傳中... (238MB，視網速約需 2~10 分鐘)")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            print(f"\r  [{bar}] {pct}%", end="", flush=True)

    video_id = response["id"]
    print(f"\n✅ 影片上傳成功！")
    print(f"   影片 ID: {video_id}")
    print(f"   網址: https://www.youtube.com/watch?v={video_id}")

    # 上傳縮圖
    if os.path.exists(THUMB_FILE):
        print("🖼️  上傳縮圖...")
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(THUMB_FILE, mimetype="image/png")
        ).execute()
        print("   縮圖上傳完成！")

    print("\n⚠️  影片目前是「私人」狀態，請到 YouTube Studio 確認後再改為公開。")
    return video_id

if __name__ == "__main__":
    upload()
