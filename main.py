from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from database import init_db
from routers import books, users, lendings

# アプリ作成
app = FastAPI(title="Library App")

# 静的ファイル（CSS・画像）の設定
app.mount("/static", StaticFiles(directory="static"), name="static")

# HTMLテンプレートの設定
templates = Jinja2Templates(directory="templates")

# ルーターを登録（APIのエンドポイントをアプリに接続）
app.include_router(books.router)
app.include_router(users.router)
app.include_router(lendings.router)


@app.on_event("startup")
def startup():
    """アプリ起動時にDBを初期化"""
    init_db()


@app.get("/")
def home():
    """トップページ → 本の一覧ページにリダイレクト"""
    return RedirectResponse(url="/books")


@app.get("/books")
def book_list_page(request: Request):
    """本の一覧ページを表示"""
    book_data = books.get_books()
    return templates.TemplateResponse("book_list.html", {
        "request": request,
        "books": book_data
    })


@app.get("/books/new")
def book_form_page(request: Request):
    """本の登録ページを表示"""
    return templates.TemplateResponse("book_form.html", {
        "request": request
    })


@app.get("/books/{book_id}")
def book_detail_page(request: Request, book_id: int):
    """本の詳細ページを表示"""
    book_data = books.get_book(book_id)
    return templates.TemplateResponse("book_detail.html", {
        "request": request,
        "book": book_data
    })

@app.get("/users")
def users_page(request: Request):
    """ユーザー管理ページを表示"""
    return templates.TemplateResponse("users.html", {
        "request": request
    })