from fastapi import APIRouter, HTTPException
from database import get_db
from models import UserCreate, UserResponse

router = APIRouter()


@router.get("/api/users")
def get_users():
    """ユーザー一覧を取得"""
    conn = get_db()
    users = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    conn.close()
    return [dict(user) for user in users]


@router.post("/api/users")
def create_user(user: UserCreate):
    """ユーザーを新規登録"""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, role) VALUES (?, ?)",
        (user.name, user.role)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return {"message": "ユーザーを登録しました", "id": user_id}

@router.delete("/api/users/{user_id}")
def delete_user(user_id: int):
    """ユーザーを削除"""
    conn = get_db()

    # 存在確認
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    # 貸出中の本があるかチェック
    active = conn.execute(
        "SELECT * FROM lendings WHERE borrower_id = ? AND returned_at IS NULL",
        (user_id,)
    ).fetchone()
    if active:
        conn.close()
        raise HTTPException(status_code=409, detail="貸出中の本があるため削除できません")

    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"message": "ユーザーを削除しました"}