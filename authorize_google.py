import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

def main():
    """
    Guides the user through authenticating their Google Account for Google Calendar.
    Saves and displays the resulting refresh tokens.
    """
    creds = None
    
    # 1. Load existing token if it exists
    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            print("Found existing token.json.")
        except Exception as e:
            print(f"Error reading existing token.json: {e}")
            
    # 2. Run local server login flow if credentials don't exist or are invalid
    if not creds or not creds.valid:
        if not os.path.exists("credentials.json"):
            print("\n❌ 錯誤：找不到 'credentials.json' 檔案！")
            print("--------------------------------------------------------------------------------")
            print("請先前往 Google Cloud Console 建立 OAuth 2.0 用戶端識別碼，並將其下載存檔為")
            print("同目錄下的 'credentials.json'。詳細操作請參閱 README.md。")
            print("--------------------------------------------------------------------------------\n")
            return
            
        print("啟動瀏覽器進行 Google 帳號授權...")
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save credentials to token.json
        with open("token.json", "w") as token_file:
            token_file.write(creds.to_json())
            
    print("\n✅ Google 行事曆授權成功！")
    print("--------------------------------------------------------------------------------")
    print("金鑰已自動儲存至 'token.json'。\n")
    print("為了在雲端環境（如 Render / Railway）部署時免去上傳檔案的繁瑣，")
    print("請複製下方 token.json 與 credentials.json 的內容並將其存於環境變數中：\n")
    
    with open("token.json", "r") as f:
        token_data = json.load(f)
        token_json_str = json.dumps(token_data)
        
    with open("credentials.json", "r") as f:
        creds_data = json.load(f)
        creds_json_str = json.dumps(creds_data)
        
    print("1️⃣ 請將以下內容設定為環境變數 GOOGLE_TOKEN_JSON 的值（單行 JSON）：")
    print(token_json_str)
    print("\n--------------------------------------------------------------------------------")
    print("2️⃣ 請將以下內容設定為環境變數 GOOGLE_CREDENTIALS_JSON 的值（單行 JSON）：")
    print(creds_json_str)
    print("--------------------------------------------------------------------------------\n")

if __name__ == "__main__":
    main()
