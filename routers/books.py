import urllib.request
import json
from fastapi import APIRouter, HTTPException
from database import get_db
from models import BookCreate, BookISBNCreate

router = APIRouter()


def fetch_book_by_isbn(isbn: str):
    """OpenBD → Google Books の順で本の情報を取得する"""
    try:
        url = f"https://api.openbd.jp/v1/get?isbn={isbn}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())

        if data and data[0]:
            summary = data[0].get("summary", {})
            title = summary.get("title", "")
            cover = summary.get("cover", "")
            description = (data[0].get("onix", {})
                .get("CollateralDetail", {})
                .get("TextContent", [{}])[0]
                .get("Text", ""))

            if title:
                if not cover:
                    cover = fetch_cover_from_google(isbn)
                return {
                    "title": title,
                    "description": description,
                    "cover_url": cover,
                }
    except Exception:
        pass

    return fetch_from_google_books(isbn)


def fetch_cover_from_google(isbn: str):
    """Google Books APIから表紙画像URLだけ取得"""
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())

        if data.get("totalItems", 0) > 0:
            volume = data["items"][0]["volumeInfo"]
            thumbnail = volume.get("imageLinks", {}).get("thumbnail", "")
            return thumbnail.replace("http://", "https://")
    except Exception:
        pass
    return ""


def fetch_from_google_books(isbn: str):
    """Google Books APIから本の情報を取得"""
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())

        if data.get("totalItems", 0) > 0:
            volume = data["items"][0]["volumeInfo"]
            thumbnail = volume.get("imageLinks", {}).get("thumbnail", "")
            return {
                "title": volume.get("title", ""),
                "description": volume.get("description", ""),
                "cover_url": thumbnail.replace("http://", "https://"),
            }
    except Exception:
        pass
    return None


@router.get("/api/books")
def get_books():
    """本の一覧を取得（貸出状態つき）"""
    conn = get_db()
    books = conn.execute("""
        SELECT
            b.*,
            u.name as owner_name,
            CASE
                WHEN l.id IS NOT NULL THEN 0
                ELSE 1
            END as is_available,
            l.borrower_id,
            bu.name as borrower_name,
            l.due_date
        FROM books b
        LEFT JOIN users u ON b.owner_id = u.id
        LEFT JOIN lendings l ON b.id = l.book_id AND l.returned_at IS NULL
        LEFT JOIN users bu ON l.borrower_id = bu.id
        ORDER BY b.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(book) for book in books]


@router.get("/api/books/{book_id}")
def get_book(book_id: int):
    """本の詳細を取得"""
    conn = get_db()
    book = conn.execute("""
        SELECT
            b.*,
            u.name as owner_name,
            CASE
                WHEN l.id IS NOT NULL THEN 0
                ELSE 1
            END as is_available,
            l.borrower_id,
            bu.name as borrower_name,
            l.due_date,
            l.id as lending_id
        FROM books b
        LEFT JOIN users u ON b.owner_id = u.id
        LEFT JOIN lendings l ON b.id = l.book_id AND l.returned_at IS NULL
        LEFT JOIN users bu ON l.borrower_id = bu.id
        WHERE b.id = ?
    """, (book_id,)).fetchone()
    conn.close()

    if not book:
        raise HTTPException(status_code=404, detail="本が見つかりません")

    return dict(book)


@router.post("/api/books")
def create_book(book: BookCreate):
    """本を手動で登録"""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO books (title, description, cover_url, owner_id) VALUES (?, ?, ?, ?)",
        (book.title, book.description, book.cover_url, book.owner_id)
    )
    conn.commit()
    book_id = cursor.lastrowid
    conn.close()
    return {"message": "本を登録しました", "id": book_id}


@router.post("/api/books/isbn")
def create_book_by_isbn(data: BookISBNCreate):
    """ISBNから本の情報を自動取得して登録"""
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM books WHERE isbn = ?", (data.isbn,)
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(
            status_code=409,
            detail="この本はすでに登録されています（" + existing["title"] + "）"
        )
    conn.close()

    book_info = fetch_book_by_isbn(data.isbn)

    if not book_info:
        raise HTTPException(
            status_code=404,
            detail="ISBNに対応する本が見つかりませんでした"
        )

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO books (isbn, title, description, cover_url, owner_id) VALUES (?, ?, ?, ?, ?)",
        (data.isbn, book_info["title"], book_info["description"],
         book_info["cover_url"], data.owner_id)
    )
    conn.commit()
    book_id = cursor.lastrowid
    conn.close()

    return {
        "message": "本を登録しました",
        "id": book_id,
        "title": book_info["title"],
        "cover_url": book_info["cover_url"],
    }


@router.delete("/api/books/{book_id}")
def delete_book(book_id: int):
    """本を削除"""
    conn = get_db()

    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book:
        conn.close()
        raise HTTPException(status_code=404, detail="本が見つかりません")

    active = conn.execute(
        "SELECT * FROM lendings WHERE book_id = ? AND returned_at IS NULL",
        (book_id,)
    ).fetchone()
    if active:
        conn.close()
        raise HTTPException(status_code=409, detail="貸出中の本は削除できません")

    conn.execute("DELETE FROM lendings WHERE book_id = ?", (book_id,))
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()

    return {"message": "本を削除しました"}