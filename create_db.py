import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "factory.db")




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

    # 插入假資料：異常記錄（共 40 筆）
    sample_defects = [
        # 2024 Q1
        ("CAR-001", "Model-X", "尺寸異常",   "2024-01-10", "張小明", "開放"),
        ("CAR-002", "Model-Y", "外觀刮傷",   "2024-01-12", "李大華", "開放"),
        ("CAR-003", "Model-X", "電氣異常",   "2024-01-15", "王阿強", "關閉"),
        ("CAR-004", "Model-Z", "尺寸異常",   "2024-01-20", "張小明", "開放"),
        ("CAR-005", "Model-Y", "包裝破損",   "2024-02-01", "陳美美", "關閉"),
        ("CAR-006", "Model-X", "功能異常",   "2024-02-05", "李大華", "開放"),
        ("CAR-007", "Model-Z", "外觀刮傷",   "2024-02-10", "張小明", "開放"),
        ("CAR-008", "Model-Y", "尺寸異常",   "2024-02-15", "王阿強", "關閉"),
        ("CAR-009", "Model-A", "焊接不良",   "2024-02-20", "林志偉", "關閉"),
        ("CAR-010", "Model-B", "原料汙染",   "2024-02-28", "黃雅婷", "開放"),
        # 2024 Q2
        ("CAR-011", "Model-A", "尺寸異常",   "2024-03-05", "張小明", "關閉"),
        ("CAR-012", "Model-B", "外觀刮傷",   "2024-03-10", "李大華", "開放"),
        ("CAR-013", "Model-C", "功能異常",   "2024-03-15", "陳美美", "開放"),
        ("CAR-014", "Model-X", "包裝破損",   "2024-03-22", "王阿強", "關閉"),
        ("CAR-015", "Model-Y", "電氣異常",   "2024-04-01", "林志偉", "開放"),
        ("CAR-016", "Model-Z", "尺寸異常",   "2024-04-07", "黃雅婷", "關閉"),
        ("CAR-017", "Model-A", "外觀刮傷",   "2024-04-18", "張小明", "開放"),
        ("CAR-018", "Model-B", "焊接不良",   "2024-04-25", "李大華", "關閉"),
        ("CAR-019", "Model-C", "原料汙染",   "2024-05-03", "王阿強", "開放"),
        ("CAR-020", "Model-X", "功能異常",   "2024-05-15", "陳美美", "關閉"),
        # 2024 Q3
        ("CAR-021", "Model-Y", "尺寸異常",   "2024-06-04", "張小明", "開放"),
        ("CAR-022", "Model-Z", "外觀刮傷",   "2024-06-18", "林志偉", "關閉"),
        ("CAR-023", "Model-A", "包裝破損",   "2024-07-02", "黃雅婷", "開放"),
        ("CAR-024", "Model-B", "電氣異常",   "2024-07-14", "李大華", "關閉"),
        ("CAR-025", "Model-C", "尺寸異常",   "2024-07-29", "王阿強", "開放"),
        ("CAR-026", "Model-X", "焊接不良",   "2024-08-06", "張小明", "關閉"),
        ("CAR-027", "Model-Y", "功能異常",   "2024-08-19", "陳美美", "開放"),
        ("CAR-028", "Model-Z", "原料汙染",   "2024-09-03", "林志偉", "開放"),
        ("CAR-029", "Model-A", "尺寸異常",   "2024-09-17", "黃雅婷", "關閉"),
        ("CAR-030", "Model-B", "外觀刮傷",   "2024-09-30", "張小明", "開放"),
        # 2024 Q4
        ("CAR-031", "Model-C", "電氣異常",   "2024-10-08", "李大華", "開放"),
        ("CAR-032", "Model-X", "包裝破損",   "2024-10-22", "王阿強", "關閉"),
        ("CAR-033", "Model-Y", "功能異常",   "2024-11-05", "陳美美", "開放"),
        ("CAR-034", "Model-Z", "焊接不良",   "2024-11-18", "林志偉", "關閉"),
        ("CAR-035", "Model-A", "尺寸異常",   "2024-12-02", "張小明", "開放"),
        # 2025 Q1
        ("CAR-036", "Model-B", "外觀刮傷",   "2025-01-07", "黃雅婷", "開放"),
        ("CAR-037", "Model-C", "原料汙染",   "2025-01-20", "李大華", "開放"),
        ("CAR-038", "Model-X", "尺寸異常",   "2025-02-03", "王阿強", "關閉"),
        ("CAR-039", "Model-Y", "功能異常",   "2025-02-14", "陳美美", "開放"),
        ("CAR-040", "Model-Z", "電氣異常",   "2025-02-26", "張小明", "開放"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO defects 
        (serial_no, product, defect_type, found_date, operator, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, sample_defects)

    # 插入假資料：產品（共 6 個）
    sample_products = [
        ("Model-X", "電子產品", "A線"),
        ("Model-Y", "機械零件", "B線"),
        ("Model-Z", "塑膠件",   "C線"),
        ("Model-A", "精密零件", "D線"),
        ("Model-B", "鈑金件",   "E線"),
        ("Model-C", "複合材料", "F線"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO products (product_name, category, line)
        VALUES (?, ?, ?)
    """, sample_products)

    conn.commit()
    conn.close()
    print(f"✅ 資料庫建立成功！位置：{DB_PATH}")
    print("📊 已插入測試資料：40 筆異常記錄、6 個產品")

if __name__ == "__main__":
    create_database()