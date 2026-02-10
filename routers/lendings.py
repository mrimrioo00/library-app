from fastapi import APIRouter, HTTPException
from database import get_db
from models import LendingCreate

router = APIRouter()


@router.post("/api/books/{book_id}/lend")
def lend_book(book_id: int, lending: LendingCreate):
    """本を借りる"""
    conn = get_db()

    # 本の存在確認
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book:
        conn.close()
        raise HTTPException(status_code=404, detail="本が見つかりません")

    # 貸出中かチェック
    active_lending = conn.execute(
        "SELECT * FROM lendings WHERE book_id = ? AND returned_at IS NULL",
        (book_id,)
    ).fetchone()
    if active_lending:
        conn.close()
        raise HTTPException(status_code=409, detail="この本は現在貸出中です")

    # 借り手の存在確認
    borrower = conn.execute(
        "SELECT * FROM users WHERE id = ?", (lending.borrower_id,)
    ).fetchone()
    if not borrower:
        conn.close()
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    # 貸し出しを記録
    conn.execute(
        "INSERT INTO lendings (book_id, borrower_id, due_date) VALUES (?, ?, ?)",
        (book_id, lending.borrower_id, lending.due_date.isoformat())
    )
    conn.commit()
    conn.close()

    return {"message": "貸し出しを記録しました"}


@router.put("/api/books/{book_id}/return")
def return_book(book_id: int):
    """本を返す"""
    conn = get_db()

    # 貸出中のレコードを探す
    lending = conn.execute(
        "SELECT * FROM lendings WHERE book_id = ? AND returned_at IS NULL",
        (book_id,)
    ).fetchone()
    if not lending:
        conn.close()
        raise HTTPException(status_code=404, detail="この本は貸出中ではありません")

    # 返却日時を記録
    conn.execute(
        "UPDATE lendings SET returned_at = CURRENT_TIMESTAMP WHERE id = ?",
        (lending["id"],)
    )
    conn.commit()
    conn.close()

    return {"message": "返却を記録しました"}