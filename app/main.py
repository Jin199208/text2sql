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
