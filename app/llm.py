import os
import re
import time
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ClientError

load_dotenv()  # 讀取 .env 裡的 GEMINI_API_KEY

# 初始化 Gemini 客戶端
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 使用的模型（gemini-2.0-flash 免費額度大，速度快）
MODEL = "gemini-2.5-flash"


def ask_gemini(prompt: str, max_retries: int = 3) -> str:
    """
    送一段文字給 Gemini，回傳它的回答。
    遇到 rate limit (429) 時，自動等待並重試。
    """
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
            )
            return response.text

        except ClientError as e:
            error_str = str(e)

            # 只處理 429 Rate Limit，其他錯誤直接拋出
            if "429" not in error_str:
                raise

            # 從錯誤訊息裡解析建議等待秒數（例如 'retryDelay': '47s'）
            wait_sec = 65  # 預設等 65 秒
            match = re.search(r"Please retry in ([\d.]+)s", error_str)
            if match:
                wait_sec = int(float(match.group(1))) + 5  # 多等 5 秒確保恢復

            print(f"[重試] API 限速，等待 {wait_sec} 秒後重試（第 {attempt + 1}/{max_retries} 次）...")
            time.sleep(wait_sec)

    raise RuntimeError(f"已重試 {max_retries} 次，API 仍然失敗，請稍後再試。")


# ---- 測試用 ----
if __name__ == "__main__":
    answer = ask_gemini("用繁體中文，一句話說明什麼是 SQL")
    print(answer)
