import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # list of all shares current user
    index = db.execute("SELECT * FROM shares WHERE user_id is ?", session["user_id"])
    cash = db.execute("SELECT cash FROM users WHERE id is ?", session["user_id"])[0]["cash"]
    total_cash = cash
    
    # add to list names and actual prices
    for row in index:
        row["name"] = (lookup(row["shares"])["name"])
        row["price"] = (lookup(row["shares"])["price"])
        total_cash = total_cash + (row["price"] * row["amount"])

    # add information about actual amount of cash
    index.append({"shares" : "CASH", "price" : cash, "amount" : 1})

    print(index)
    
    
    
    
    return render_template("index.html", index = index, total_cash = total_cash)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        # information about share
        quote = lookup(request.form.get("symbol"))
        # amount of shares that user want to buy
        shares = request.form.get("shares")
        # cash of actual user
        cash = db.execute("SELECT cash FROM users WHERE id is ?", session["user_id"])
        

        if not quote:
            return render_template("buy.html", messege="Wrong symbol!")
        if shares.isnumeric() == False:
           return render_template("buy.html", messege="Wrong shares!")
        if (quote["price"] * float(shares)) > (cash[0]["cash"]):
            return render_template("buy.html", messege="Not have enough money.")
        
        
        # amount of this type of shares actaull owned by user
        actual_share = db.execute("SELECT amount FROM shares WHERE user_id is ? AND shares is ?", session["user_id"], quote["symbol"])
        
        # update user shares
        if not actual_share:
            db.execute("INSERT INTO shares (user_id, shares, amount) VALUES(?, ?, ?)", session["user_id"], quote["symbol"], shares)
        else:
            # amount of shares afte add currently bought shares
            db.execute("UPDATE shares SET amount = amount + ? WHERE shares is ? AND user_id is ?", shares, quote["symbol"], session["user_id"])
        
        # update cash
        # amount of cash to take from user account
        
        update_cash = cash[0]["cash"] - (quote["price"] * float(shares))
        
        db.execute("UPDATE users SET cash = ? WHERE id is ?", update_cash, session["user_id"]) 
        return redirect("/")

    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    # session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", messege="Provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", messege="Provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", messege="Invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        quote = lookup(request.form.get("symbol"))
        if not quote:
            return render_template("quote.html", messege="Wrong symbol!")
        return render_template("quoted.html", quote=quote)

    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    """Register user"""
    # list of all useres from databes to check is username is already taken
    users = []

    for user in db.execute("SELECT username FROM users"):
        users.append(user["username"])

    if request.method == "POST":
        if not request.form.get("username"):
            return render_template("register.html", messege="Please type username")

        if request.form.get("username") in users:
            return render_template("register.html", messege="Username already taken.")

        if not request.form.get("password") or len(request.form.get("password")) < 4:
            return render_template("register.html", messege="Please type Your password (minimum 4 characters")

        if not request.form.get("confirm_password"):
            return render_template("register.html", messege="Please confirm Your password.")

        if request.form.get("password") == request.form.get("confirm_password"):
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")))
            return render_template("login.html", messege="You are registered, please log in.")

        else:
            return render_template("register.html", messege="Passwords don`t match.")

    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
