import os
import requests

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

def main ():
    #open file and read
    f = open("books.csv")
    reader = csv.reader(f)
    print("Reading CSV...")
    count = 0
    for isbn, title, author, year in reader:
        if year.isdigit():
            # Insert values in database
            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {"isbn": isbn, "title": title, "author": author, "year": year})
            print(f"Added book {title} by {author}, ISBN {isbn}")
            count = count +1
        else:
            print(f"Did not add {title}. Year is not a number")
        #Commit changes
        db.commit()
    print(f"{count} books successfully imported.")

if __name__ == "__main__":
    main()