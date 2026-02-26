import sqlite3
import os
import time
from llm import ask_gemini
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
- 除非使用者明確要求「只要一筆」或「TOP 1」，否則不要加 LIMIT
- 需要排名或比較時，回傳全部分組結果並排序，讓後續程式自行判斷
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




# ── 4. 把查詢結果轉成自然語言回答 ────────────────────────────────────────────

def result_to_natural_language(question: str, result: list[dict]) -> str:
    """
    把 SQL 查詢結果，請 AI 整理成一段自然語言的摘要回答。
    """
    if not result:
        return "查詢結果為空，沒有符合條件的資料。"

    prompt = f"""使用者問了：「{question}」
查詢到的資料如下：
{result}

請用繁體中文，簡短且清楚地回答使用者的問題。
不要列出 SQL，直接根據資料說明結果。
"""
    return ask_gemini(prompt)


# ── 5. 完整流程：問題 → SQL → 結果 → 自然語言回答 ────────────────────────────

def text2sql(question: str) -> dict:
    """
    完整的 text2sql 流程。
    輸入：自然語言問題
    輸出：{question, sql, result, count, answer}
    """
    print(f"\n[問題] {question}")

    sql = question_to_sql(question)
    print(f"[SQL] {sql}")

    result = run_sql(sql)
    print(f"[結果] {len(result)} 筆資料")

    answer = result_to_natural_language(question, result)
    print(f"[回答] {answer}")

    return {
        "question": question,
        "sql": sql,
        "result": result,
        "count": len(result),
        "answer": answer,
    }



# ───────────────── 測試用 ─────────────────────────────────────────────────
if __name__ == "__main__":
    # 測試幾個問題
    test_questions = [
        "2024 年第三季哪種異常最多ㄚㄚㄚㄚ啊??"
            ]

    for i, q in enumerate(test_questions):
        output = text2sql(q)
        print("-" * 50)
        # 避免觸發 rate limit，每題間隔 30 秒（最後一題不用等）
        if i < len(test_questions) - 1:
            print("等待 10 秒避免 API 限速...")
            time.sleep(10)