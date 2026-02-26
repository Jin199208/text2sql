# 🚀 從零開始實作 Text2SQL 系統

> 🎯 **目標**：在你的 Windows 筆電上，從零開始寫一個「問問題 → 自動查資料庫」的系統  
> 💻 **環境**：本機 Windows，**不需要 GPU**  
> 🤖 **LLM**：使用 Gemini API（免費額度夠用）  
> 🗄️ **資料庫**：SQLite（輕量、不用安裝伺服器）  
> ⏱️ **預計時間**：3～5 小時完整走完

---

## 🗺️ 你要蓋什麼？

```
使用者輸入：「有哪些產品異常？」
         ↓
Step 1: 把問題送給 Gemini AI
         ↓
Step 2: AI 看懂資料庫結構，生成 SQL
         ↓  SELECT * FROM defects WHERE ...
Step 3: 用 SQL 查詢 SQLite 資料庫
         ↓  [{"id":1, "type":"尺寸異常"}, ...]
Step 4: 把結果包成 API 回傳
```

**最終成果**：一個可以用 API 呼叫的 text2sql 服務，跑在 `http://localhost:8088`

---

## 📦 第一階段：建立環境

### Step 1-1：建立專案資料夾結構

打開 PowerShell，執行：

```powershell
# 建立專案目錄
New-Item -ItemType Directory -Force -Path "C:\Users\felix_chiu\Desktop\project\text2sql"
cd "C:\Users\felix_chiu\Desktop\project\text2sql"

# 建立子資料夾
New-Item -ItemType Directory -Force -Path "app"
New-Item -ItemType Directory -Force -Path "data"
New-Item -ItemType Directory -Force -Path "tests"
```

完成後，你的結構是：

```
text2sql/
├── app/          ← 程式碼放這
├── data/         ← 資料庫放這
├── tests/        ← 測試放這
└── （之後會新增更多檔案）
```

---

### Step 1-2：安裝 uv 並建立虛擬環境

```powershell
# 安裝 uv（如果還沒裝）
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 關掉 PowerShell 重開，然後：
cd "C:\Users\felix_chiu\Desktop\project\text2sql"

# 建立虛擬環境
uv venv

# 啟動虛擬環境
.venv\Scripts\activate

# 確認有啟動（前面會出現 (.venv)）
```

---

### Step 1-3：安裝必要套件

建立 `requirements.txt` 檔案，貼入以下內容：

```
# 檔案：requirements.txt
fastapi==0.115.0
uvicorn==0.32.0
google-genai==1.10.0
python-dotenv==1.0.0
```

> 📌 **為什麼這幾個？**
> - `fastapi` + `uvicorn` → 建立 API 用的
> - `google-genai` → 呼叫 Gemini AI 用的
> - `python-dotenv` → 讀取 API Key 用的（安全存放 key）
> - `sqlite3` → Python 內建，不用安裝！

然後安裝：

```powershell
uv pip install -r requirements.txt
```

---

### Step 1-4：取得 Gemini API Key

1. 前往 [Google AI Studio](https://aistudio.google.com/app/apikey)
2. 登入 Google 帳號
3. 點「Create API Key」
4. 複製你的 API Key（長這樣：`AIzaSy...`）

在專案根目錄建立 `.env` 檔案：

```
# 檔案：.env
GEMINI_API_KEY=你的API_Key貼在這裡
```

> ⚠️ **重要**：`.env` 檔案不要傳到 GitHub！它裡面有你的 API Key。

---

## 🗄️ 第二階段：建立資料庫

### Step 2-1：建立一個練習用的假資料庫

在 `data/` 資料夾建立 `create_db.py`：

```python
# 檔案：data/create_db.py
import sqlite3
import os

# 資料庫檔案的位置
DB_PATH = os.path.join(os.path.dirname(__file__), "factory.db")

def create_database():
    """建立練習用的工廠資料庫"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 建立「異常記錄」資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS defects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_no   TEXT NOT NULL,        -- 序號，例如 CAR-001
            product     TEXT NOT NULL,        -- 產品名稱
            defect_type TEXT NOT NULL,        -- 異常類型
            found_date  TEXT NOT NULL,        -- 發現日期 (YYYY-MM-DD)
            operator    TEXT,                 -- 負責人
            status      TEXT DEFAULT '開放'  -- 狀態：開放/關閉
        )
    """)

    # 建立「產品」資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,       -- 產品名稱
            category     TEXT,               -- 產品類別
            line         TEXT                -- 生產線
        )
    """)

    # 插入假資料：異常記錄
    sample_defects = [
        ("CAR-001", "Model-X", "尺寸異常",   "2024-01-10", "張小明", "開放"),
        ("CAR-002", "Model-Y", "外觀刮傷",   "2024-01-12", "李大華", "開放"),
        ("CAR-003", "Model-X", "電氣異常",   "2024-01-15", "王阿強", "關閉"),
        ("CAR-004", "Model-Z", "尺寸異常",   "2024-01-20", "張小明", "開放"),
        ("CAR-005", "Model-Y", "包裝破損",   "2024-02-01", "陳美美", "關閉"),
        ("CAR-006", "Model-X", "功能異常",   "2024-02-05", "李大華", "開放"),
        ("CAR-007", "Model-Z", "外觀刮傷",   "2024-02-10", "張小明", "開放"),
        ("CAR-008", "Model-Y", "尺寸異常",   "2024-02-15", "王阿強", "關閉"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO defects 
        (serial_no, product, defect_type, found_date, operator, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, sample_defects)

    # 插入假資料：產品
    sample_products = [
        ("Model-X", "電子產品", "A線"),
        ("Model-Y", "機械零件", "B線"),
        ("Model-Z", "塑膠件",   "C線"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO products (product_name, category, line)
        VALUES (?, ?, ?)
    """, sample_products)

    conn.commit()
    conn.close()
    print(f"✅ 資料庫建立成功！位置：{DB_PATH}")
    print("📊 已插入測試資料：8 筆異常記錄、3 個產品")

if __name__ == "__main__":
    create_database()
```

執行它：

```powershell
python data/create_db.py
# 應該看到：✅ 資料庫建立成功！
```

---

### Step 2-2：驗證資料庫內容

```powershell
# 用 Python 快速驗證
python -c "
import sqlite3
conn = sqlite3.connect('data/factory.db')
rows = conn.execute('SELECT * FROM defects').fetchall()
print(f'共 {len(rows)} 筆資料')
for r in rows[:3]:
    print(r)
conn.close()
"
```

---

## 🤖 第三階段：接上 Gemini AI

### Step 3-1：建立 AI 連線模組

建立 `app/llm.py`：

```python
# 檔案：app/llm.py
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # 讀取 .env 裡的 GEMINI_API_KEY

# 初始化 Gemini 客戶端
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# 使用的模型（gemini-2.0-flash 免費額度大，速度快）
MODEL = "gemini-2.0-flash"


def ask_gemini(prompt: str) -> str:
    """
    送一段文字給 Gemini，回傳它的回答。
    這是最基礎的呼叫方式。
    """
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )
    return response.text


# ---- 測試用 ----
if __name__ == "__main__":
    answer = ask_gemini("用繁體中文，一句話說明什麼是 SQL")
    print(answer)
```

測試是否成功：

```powershell
python app/llm.py
# 應該看到 Gemini 的回答
```

---

### Step 3-2：建立 Text2SQL 核心邏輯

建立 `app/text2sql.py`：

```python
# 檔案：app/text2sql.py
import sqlite3
import os
from app.llm import ask_gemini

DB_PATH = os.path.join("data", "factory.db")


# ── 1. 讀取資料庫結構（告訴 AI 有哪些表格和欄位）────────────────────────

def get_schema() -> str:
    """
    讀取資料庫的表格結構，回傳給 AI 參考。
    這就是「讓 AI 知道資料庫長什麼樣子」的關鍵步驟。
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 取得所有資料表名稱
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()

    schema_text = ""
    for (table_name,) in tables:
        # 取得每個表格的欄位資訊
        columns = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
        col_defs = ", ".join(f"{col[1]} ({col[2]})" for col in columns)
        schema_text += f"資料表 {table_name}：{col_defs}\n"

    conn.close()
    return schema_text


# ── 2. 請 AI 把問題轉成 SQL ───────────────────────────────────────────────

def question_to_sql(question: str) -> str:
    """
    把使用者的自然語言問題，轉成 SQL 語句。
    核心步驟：把「資料庫結構 + 問題」都告訴 AI，叫它寫 SQL。
    """
    schema = get_schema()

    # Prompt 設計：告訴 AI 它的角色、資料庫結構、問題，叫它只回傳 SQL
    prompt = f"""你是一個 SQLite 資料庫專家。
根據以下資料庫結構，把使用者的問題轉換成一條正確的 SQLite SQL 語句。

【資料庫結構】
{schema}

【欄位中文說明】
defects 資料表：
  - serial_no：異常序號
  - product：產品名稱
  - defect_type：異常類型（例如：尺寸異常、外觀刮傷）
  - found_date：發現日期
  - operator：負責人
  - status：狀態（開放 或 關閉）

products 資料表：
  - product_name：產品名稱
  - category：產品類別
  - line：生產線

【使用者的問題】
{question}

【要求】
- 只回傳 SQL 語句，不要解釋，不要加其他文字
- SQL 結尾不需要加分號
- 使用 SQLite 語法
"""

    sql = ask_gemini(prompt)

    # 清理 AI 回傳的 SQL（有時會帶 ```sql ... ``` 包住）
    sql = sql.strip()
    if sql.startswith("```"):
        lines = sql.split("\n")
        sql = "\n".join(lines[1:-1])  # 去掉第一行和最後一行的 ```

    return sql.strip()


# ── 3. 執行 SQL，拿到資料 ─────────────────────────────────────────────────

def run_sql(sql: str) -> list[dict]:
    """
    執行 SQL 語句，回傳結果（list of dict 格式）。
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 讓結果可以用欄位名稱存取

    try:
        rows = conn.execute(sql).fetchall()
        result = [dict(row) for row in rows]
    except Exception as e:
        result = [{"error": str(e), "sql": sql}]
    finally:
        conn.close()

    return result


# ── 4. 完整流程：問題 → SQL → 結果 ───────────────────────────────────────

def text2sql(question: str) -> dict:
    """
    完整的 text2sql 流程。
    輸入：自然語言問題
    輸出：{question, sql, result}
    """
    print(f"\n🔍 問題：{question}")

    sql = question_to_sql(question)
    print(f"📝 生成的 SQL：{sql}")

    result = run_sql(sql)
    print(f"📊 查詢結果：{len(result)} 筆資料")

    return {
        "question": question,
        "sql": sql,
        "result": result,
        "count": len(result),
    }


# ───────────────── 測試用 ─────────────────────────────────────────────────
if __name__ == "__main__":
    # 測試幾個問題
    test_questions = [
        "有哪些尺寸異常的記錄？",
        "張小明負責的異常有幾筆？",
        "狀態還是開放的異常清單",
    ]

    for q in test_questions:
        output = text2sql(q)
        print(f"\n結果：{output['result'][:2]}...")  # 只印前 2 筆
        print("-" * 50)
```

測試核心邏輯：

```powershell
python app/text2sql.py
```

你應該看到 AI 生成 SQL，然後查出資料。

---

## 🌐 第四階段：包成 API

### Step 4-1：建立 FastAPI 應用

建立 `app/main.py`：

```python
# 檔案：app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.text2sql import text2sql, run_sql, question_to_sql

app = FastAPI(
    title="Text2SQL 練習系統",
    description="輸入問題，AI 自動生成 SQL 並查詢資料庫",
    version="1.0.0",
)


# ── 定義 API 的輸入/輸出格式 ──────────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str  # 使用者輸入的問題


class Text2SQLResponse(BaseModel):
    question: str
    sql: str
    result: list
    count: int


# ── API 端點 ──────────────────────────────────────────────────────────────

@app.get("/")
def root():
    """首頁：確認服務是否正常"""
    return {"message": "Text2SQL 服務正在運行 ✅", "docs": "/docs"}


@app.post("/query", response_model=Text2SQLResponse)
def query(req: QuestionRequest):
    """
    主要端點：輸入自然語言問題，回傳 SQL 和查詢結果。
    
    範例輸入：{"question": "有哪些尺寸異常？"}
    """
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="問題不能是空的")

    result = text2sql(req.question)
    return result


@app.post("/generate-sql")
def generate_sql_only(req: QuestionRequest):
    """
    只生成 SQL，不執行查詢。
    適合在你想先確認 SQL 是否正確時使用。
    """
    sql = question_to_sql(req.question)
    return {"question": req.question, "sql": sql}


@app.post("/run-sql")
def execute_sql(body: dict):
    """
    直接執行 SQL 語句（用於手動測試）。
    
    範例輸入：{"sql": "SELECT * FROM defects LIMIT 3"}
    """
    sql = body.get("sql", "")
    if not sql:
        raise HTTPException(status_code=400, detail="SQL 不能是空的")

    result = run_sql(sql)
    return {"sql": sql, "result": result, "count": len(result)}
```

---

### Step 4-2：啟動服務

```powershell
# 確保在 (.venv) 環境下，且在專案根目錄
uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload
```

> `--reload` 的意思：修改程式碼後自動重啟，開發時很方便。

成功啟動後你會看到：
```
INFO:     Uvicorn running on http://0.0.0.0:8088 (Press CTRL+C to quit)
INFO:     Started reloader process
```

---

### Step 4-3：測試 API

**方法一：瀏覽器打開 API 文件**

前往 `http://localhost:8088/docs`  
你會看到 Swagger UI，可以直接在上面測試！

---

**方法二：PowerShell 測試**（開新視窗）

```powershell
# 測試 1：問問題
$body = '{"question": "有哪些尺寸異常的記錄？"}'
Invoke-RestMethod -Uri "http://localhost:8088/query" `
  -Method POST -ContentType "application/json" -Body $body

# 測試 2：只生成 SQL（不執行）
$body = '{"question": "張小明負責的異常有幾筆？"}'
Invoke-RestMethod -Uri "http://localhost:8088/generate-sql" `
  -Method POST -ContentType "application/json" -Body $body

# 測試 3：直接執行 SQL
$body = '{"sql": "SELECT * FROM defects WHERE status = '開放'"}'
Invoke-RestMethod -Uri "http://localhost:8088/run-sql" `
  -Method POST -ContentType "application/json" -Body $body
```

---

## 📁 最終的檔案結構

```
text2sql/
├── .env                   ← API Key（不要上傳 GitHub！）
├── requirements.txt       ← 套件清單
├── app/
│   ├── main.py            ← FastAPI 入口，定義 API 端點
│   ├── text2sql.py        ← 核心邏輯：問題→SQL→結果
│   └── llm.py             ← Gemini AI 連線模組
├── data/
│   ├── create_db.py       ← 建立和填充資料庫的腳本
│   └── factory.db         ← SQLite 資料庫（執行後產生）
└── tests/
    └── （之後可以加測試）
```

---

## 🧪 練習挑戰

完成基礎版後，試試這些進階挑戰：

### 🥉 初級：讓 AI 更準確

**挑戰**：修改 `app/text2sql.py` 裡的 Prompt，加入更多範例資料讓 AI 理解

```python
# 在 Prompt 裡加入「範例 SQL」
prompt = f"""...（原本的 prompt）...

【範例】
問題：「有幾筆開放中的異常？」
SQL：SELECT COUNT(*) as 數量 FROM defects WHERE status = '開放'
"""
```

---

### 🥈 中級：加上多輪對話

**挑戰**：讓使用者可以「接著問」，AI 記得上一個問題

修改 `app/main.py`，加入 session 功能：

```python
from collections import defaultdict

# 儲存對話歷史
conversation_history = defaultdict(list)

@app.post("/chat")
def chat(req: dict):
    session_id = req.get("session_id", "default")
    question = req.get("question")
    
    history = conversation_history[session_id]
    history.append(f"使用者：{question}")
    
    # 把歷史對話也加進 Prompt...
```

---

### 🥇 進階：加上 RAG（讓 AI 更懂你的資料）

**挑戰**：用 ChromaDB 建一個向量資料庫，存入資料庫的說明文件

```powershell
uv pip install chromadb sentence-transformers
```

然後讓 AI 生成 SQL 之前，先從向量資料庫找相關的欄位說明。

---

## 🆘 常見問題

| 問題 | 可能原因 | 解法 |
|---|---|---|
| `GEMINI_API_KEY not found` | `.env` 沒建或格式錯 | 確認 `.env` 裡有 `GEMINI_API_KEY=...` |
| AI 生成的 SQL 有語法錯誤 | Prompt 不夠清楚 | 在 Prompt 加更多說明和範例 |
| `ModuleNotFoundError` | 套件未安裝 | `uv pip install -r requirements.txt` |
| API 沒反應 | 服務沒啟動 | 執行 `uvicorn app.main:app --reload` |
| 查詢結果是空的 | SQL 條件不對 | 先用 `/run-sql` 手動測試 SQL |

---

## 📌 每日工作指令

```powershell
# 每次開始工作前：
cd "C:\Users\felix_chiu\Desktop\project\text2sql"
.venv\Scripts\activate

# 啟動開發伺服器
uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload

# 另開視窗測試（快速測試用）
python app/text2sql.py
```

---

> 💡 **學習建議**：
> 1. 先讓 `app/text2sql.py` 的測試跑通
> 2. 再啟動 API，從 Swagger UI 測試
> 3. 遇到問題先看終端機的錯誤訊息
> 4. `--reload` 模式下改程式碼不用重啟！

---

*版本：2026-02-26 | 適合本機 Windows 無 GPU 環境*
