from flask import Flask, render_template, redirect, url_for, request, session, Response
from models import Book, LibraryManager, User, CSVExporter, JSONExporter
import math

app = Flask(__name__)
app.secret_key = "supersecretkey123"

# Dữ liệu mẫu
book1 = Book("Deep Learning", "Ian Goodfellow", 450)
book2 = Book("Python Crash Course", "Eric Matthes", 300)
book3 = Book("Clean Code", "Robert C. Martin", 464)

library = LibraryManager()
library.add_item(book1)
library.add_item(book2)
library.add_item(book3)

users = [
    User("Alice", "U001", "alice123"),
    User("Bob", "U002", "bob456"),
    User("Charlie", "U003", "charlie789"),
    User("Admin","admin","admin_pass",is_admin = True)
]
 
def get_current_user():
    uid = session.get("user_id")
    for user in users:
        if user.user_id == uid:
            return user
    return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/books", methods=["GET", "POST"])
def show_books():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    keyword = request.args.get("q", "").lower()  # lấy từ khóa tìm kiếm
    available_books = [
        i["document"] for i in library.items
        if i["availability"] and (
            keyword in i["document"].title.lower() or keyword in i["document"].author.lower()
        )
    ] if keyword else [i["document"] for i in library.items if i["availability"]]

    borrowed_books = user.borrowed_items
    return render_template("books.html", books=available_books, borrowed=borrowed_books, keyword=keyword)


@app.route("/loan/<book_title>")
def loan_book(book_title):
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    for i in library.items:
        if i["document"].title == book_title:
            library.loan_item(user, i["document"])
            break
    return redirect(url_for("show_books"))

@app.route("/return/<book_title>")
def return_book(book_title):
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    for i in library.items:
        if i["document"].title == book_title:
            library.retake_item(user, i["document"])
            break
    return redirect(url_for("show_books"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_id = request.form["user_id"]
        password = request.form["password"]
        for user in users:
            if user.user_id == user_id and user.password == password:
                session["user_id"] = user.user_id  # lưu người dùng vào session
                return redirect(url_for("show_books"))
        return render_template("login.html", error="Sai ID hoặc mật khẩu.")
    return render_template("login.html", error=None)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        user_id = request.form["user_id"]
        password = request.form["password"]

        # Kiểm tra user_id đã tồn tại chưa
        for user in users:
            if user.user_id == user_id:
                return render_template("signup.html", error="ID đã tồn tại. Vui lòng chọn ID khác.")

        # Kiểm tra độ dài mật khẩu
        if len(password) < 6:
            return render_template("signup.html", error="Mật khẩu phải có ít nhất 6 ký tự.")

        # Tạo user mới và thêm vào danh sách
        new_user = User(name, user_id, password)
        users.append(new_user)
        session["user_id"] = new_user.user_id
        return redirect(url_for("show_books"))

    return render_template("signup.html", error=None)

@app.route("/admin")
def admin_panel():
    user = get_current_user()
    if not user or not user.is_admin:
        return redirect(url_for("login"))  # hoặc trả về "403 Forbidden"
    return render_template("admin.html", user=user, library=library)

@app.route("/admin/add_book", methods=["GET", "POST"])
def add_book():
    user = get_current_user()
    if not user or not user.is_admin:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        n_pages = int(request.form["n_pages"])
        new_book = Book(title, author, n_pages)
        library.add_item(new_book)
        return redirect(url_for("admin_panel"))
    return render_template("add_book.html")

@app.route("/admin/delete_book/<title>")
def delete_book(title):
    user = get_current_user()
    if not user or not user.is_admin:
        return redirect(url_for("login"))
    for i in library.items:
        if i["document"].title == title:
            if i["availability"]:  # chỉ xóa nếu chưa cho mượn
                library.items.remove(i)
                library.log(f"Admin {user.name} đã xóa sách '{title}'")
            break
    return redirect(url_for("admin_panel"))

@app.route("/admin/loan_record")
def loan_record():
    user = get_current_user()
    if not user or not user.is_admin:
        return redirect(url_for("login")) 
    return render_template("loan_record.html", records=library.loan_record)

@app.route("/admin")
def view_books_admin():
    user = get_current_user()
    if not user or not user.is_admin:
        return redirect(url_for("login"))
    return render_template("admin.html", user=user, library=library)


@app.route("/admin/users")
def view_users():
    user = get_current_user()
    if not user or not user.is_admin:
        return redirect(url_for("login"))

    # Lấy tham số truy vấn
    search = request.args.get("search", "").strip().lower()
    sort_by = request.args.get("sort_by", "name")
    order = request.args.get("order", "asc")
    page = int(request.args.get("page", 1))

    # Lọc người dùng theo từ khóa tìm kiếm
    filtered_users = [u for u in users if search in u.name.lower() or search in u.user_id.lower()]

    # Sắp xếp
    sorted_users = sorted(filtered_users, key=lambda u: getattr(u, sort_by))
    if order == "desc":
        sorted_users.reverse()

    # Phân trang
    per_page = 25
    total_users = len(sorted_users)
    total_pages = math.ceil(total_users / per_page)

    start = (page - 1) * per_page
    end = start + per_page
    paginated_users = sorted_users[start:end]

    return render_template(
        "user_list.html",
        users=paginated_users,
        sort_by=sort_by,
        order=order,
        search=search,
        page=page,
        total_pages=total_pages,
        total_users=total_users
    )



@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        old_pass = request.form["old_password"]
        new_pass = request.form["new_password"]
        confirm_pass = request.form["confirm_password"]

        if user.password != old_pass:
            return render_template("change_password.html", error="❌ Mật khẩu cũ không đúng.")
        elif new_pass != confirm_pass:
            return render_template("change_password.html", error="❌ Mật khẩu mới không khớp.")
        elif len(new_pass) < 6:
            return render_template("change_password.html", error="❌ Mật khẩu mới phải có ít nhất 6 ký tự.")
        else:
            user.password = new_pass
            return render_template("change_password.html", success="✅ Đổi mật khẩu thành công!")

    return render_template("change_password.html", error=None)

@app.route("/admin/export/<fmt>")
def export_loan_record(fmt):
    user = get_current_user()
    if not user or not user.is_admin:
        return redirect(url_for("login"))

    exporter = CSVExporter() if fmt == "csv" else JSONExporter()
    content = exporter.export_data(library.loan_record)

    mimetype = "text/csv" if fmt == "csv" else "application/json"
    filename = f"loan_record.{fmt}"

    return Response(
        content,
        mimetype=mimetype,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())

if __name__ == "__main__":
    app.run(debug=True)
