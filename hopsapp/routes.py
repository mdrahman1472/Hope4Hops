"""Routes for flask app."""  # pylint: disable=cyclic-import
# import hashlib
from hopsapp import app
from flask import render_template, request
from flask_sqlalchemy import SQLAlchemy
from hopsapp.models import Beer, Brewery, Store, Customer, StoreOwner

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/register')
def register():
    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)
