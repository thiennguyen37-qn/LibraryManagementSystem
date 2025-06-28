from flask import Flask, render_template, redirect, url_for
from models import Book, LibraryManager, User

app = Flask(__name__)

# Dữ liệu mẫu
book1 = Book("Deep Learning", "Ian Goodfellow", 450)
book2 = Book("Python Crash Course", "Eric Matthes", 300)
book3 = Book("Clean Code", "Robert C. Martin", 464)

library = LibraryManager()
library.add_item(book1)
library.add_item(book2)
library.add_item(book3)

user = User("Alice", "U001")  

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/books")
def show_books():
    available_books = [i['document'] for i in library.items if i['availability']]
    borrowed_books = user.borrowed_items
    return render_template("books.html", books=available_books, borrowed=borrowed_books)

@app.route("/loan/<book_title>")
def loan_book(book_title):
    
    for i in library.items:
        if i["document"].title == book_title:
            library.loan_item(user, i["document"])
            break
    return redirect(url_for("show_books"))

@app.route("/return/<book_title>")
def return_book(book_title):
    for i in library.items:
        if i["document"].title == book_title:
            library.retake_item(user, i["document"])
            break
    return redirect(url_for("show_books"))

if __name__ == "__main__":
    app.run(debug=True)
