import os
import requests
import csv

from flask import Flask, session, render_template, jsonify, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

key = 'o8crVSs73jOs92D2cvLVnw'

# Index (main route)
@app.route("/")
def index():
    return render_template("index.html")

# Registration
@app.route("/registration")
def registration():
    return render_template("registration.html")

@app.route("/submit", methods=["POST"])
def submit():

    session.clear()

    if request.method == "POST":
        eInput = request.form.get("userEmail")
        pInput = request.form.get("userPw")

    if eInput == None or pInput == None:
        return render_template("error.html", message="Error, email or password is empty")

    checkAcc = db.execute("select * from account where email = :email", {"email": eInput}).fetchone()

    try:
        if checkAcc != None:
            return render_template("error.html", message="Error, email has been registered")
    except ValueError: 
            return render_template("error.html", message="An error has occured, please try again")

    session["status"] = True
    session["username"] = str(eInput)
    db.execute("insert into account (email, password) values (:email, :password)", {"email": eInput, "password": pInput})

    db.commit()

    return render_template("index.html")

#Log in
@app.route("/home", methods=["POST"])
def home():
    if request.method == "POST":
        if not request.form.get("userEmail"):
            return render_template("error.html", message="Error, email or password is empty")
        elif not request.form.get("userPw"):
            return render_template("error.html", message="Error, email or password is empty")
        else:
            eInput = request.form.get("userEmail")
            pInput = request.form.get("userPw")
            checkAcc = db.execute("SELECT * FROM account WHERE email = :eInput AND password = :pInput", {"eInput": eInput, "pInput": pInput}).fetchone()

            if checkAcc is None:
                return render_template("index.html")
            session["status"] = True
            session["username"] = str(eInput)
            return render_template("search.html")
    else:
        return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

#Log out
@app.route("/logout")
def logout():
    session.clear()
    return render_template("login.html", message="You were successful logged out")

#Search for a book
@app.route("/search", methods=["POST"])
def search():
    if request.method == "POST":
        return render_template("error.html", message="Could not find page")

    else:
        return render_template("error.html", message="Could not find page")

@app.route("/book")
def book():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("insert into books (isbn, title, author, year) values (:isbn, :title, :author, :year)", {"isbn": isbn, "title": title, "author": author, "year": year})
        db.commit()

@app.route("/result", methods=["POST"])
def result():
    if request.method != "POST":
        return render_template("search.html")

    radInput = int(request.form.get("radOption"))
    searchInput = request.form.get("sInput")

    if radInput == 1:
        uChoice = "isbn"
    elif radInput == 2:
        uChoice = "title"
    elif radInput == 3:
        uChoice = "author"
    else:
        return render_template("error.html", message="Invalid input")

    inputResult = db.execute("select * from books where lower(" + uChoice + ") like lower(:uChoice)", {"uChoice": "%" + searchInput + "%"}).fetchall()


    if inputResult is None:
        return render_template("error.html", message="Could not find")
    else:
        return render_template("result.html", results=inputResult)

@app.route("/bookReview/<bookISBN>")
def bookReview(bookISBN):
    bookInfo = db.execute("select * from books where isbn=:isbn", {"isbn": bookISBN}).fetchone()

    url = f"https://www.goodreads.com/book/review_counts.json?key={key}&isbns={bookISBN.strip()}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
    else:
        return render_template("search.html")

    reviewCount = data["books"][0]["reviews_count"]
    avgRating = data["books"][0]["average_rating"]

    reviews = db.execute("select * from reviews where isbn=:isbn", {"isbn": bookISBN}).fetchall()

    return render_template("book.html", reviewCount=reviewCount, avgRating=avgRating, bookInfo=bookInfo, reviews=reviews)

@app.route("/bookReview/<bookISBN>/success", methods= ["POST"])
def success(bookISBN):

    username = str(session.get("username"))
    userCheck = db.execute("select * from reviews where username=:username", {"username": username}).fetchone()
    if userCheck != None:
        return render_template("error.html")
    
    uReview = request.form.get("userReview")
    uRating = request.form.get("userRating")

    db.execute("insert into reviews (isbn, username, review, rating) values (:isbn, :username, :review, :rating)", {"isbn": bookISBN, "username": username, "review": uReview, "rating": uRating})

    db.commit()
    return render_template("search.html")            

@app.route("/api/book/<isbn>")
def book_api(isbn):

    book_Info = db.execute("select * from books where isbn=:isbn", {"isbn": isbn}).fetchone()
    reviewScore = db.execute("select * from reviews where isbn=:isbn", {"isbn": isbn}).fetchall()
    
    avgScore = 0
    reviewCount = 0

    if book_Info == None:
        return jsonify({"error": "Invalid isbn"}), 422

    for rate in reviewScore:
        avgScore += int(rate.rating)
        reviewCount += 1

    if reviewCount != 0:
        avgScore/=reviewCount

    return jsonify({
        "title": book_Info.title, 
        "author": book_Info.author,
        "year": book_Info.year,
        "review_count": reviewCount,
        "average_score": avgScore
    })


    





        
