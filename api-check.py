from dotenv import load_dotenv
from google import genai
import os

load_dotenv()  # 讀取 .env 裡的 GEMINI_API_KEY

# 初始化 Gemini 客戶端
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


print("--- 可用的生成模型清單 ---")
# 列出支援生成內容（generateContent）的所有模型
for m in client.models.list():
    if "generateContent" in m.supported_actions:
        print(f"模型名稱: {m.name}")
        print(f"顯示名稱: {m.display_name}")
        print(f"描述: {m.description}")
        print("-" * 30)