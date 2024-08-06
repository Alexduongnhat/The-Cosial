from flask import Flask, render_template, redirect, request, session, jsonify, make_response
from functools import *
import sqlite3

# start app
app = Flask(__name__)

# start session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

hpage = 20

# connect database
db = sqlite3.connect('database.db', check_same_thread=False)
db.row_factory = sqlite3.Row
cur = db.cursor()

def store(id):
    cookie = make_response(redirect("/"))
    cookie.set_cookie("id", str(id))

    return cookie

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.cookies.get("id") is None:
            return redirect('/login')
        return f(*args, **kwargs)
    
    return decorated_function
# homepage
@app.route("/", methods=['POST', 'GET'])
@login_required
def homepage():
    user_name = cur.execute("SELECT * FROM users WHERE id = ?", (int(request.cookies.get("id")),)).fetchall()[0]["name"]
    if request.method == "POST":
        text = request.get_json()
        text = text.get("inputValue")

        cur.execute(" INSERT INTO feeds (uploader, content) VALUES (?, ?)", (user_name, text))

        db.commit()
        return jsonify(success=True)
    else:
        
        return render_template("main.html")

# register
@app.route("/register", methods=['POST', 'GET'])
def register():

    session.clear()

    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")

        # check the name is valid
        check = cur.execute("SELECT * FROM users WHERE name = ?", (name, )).fetchall()
        if check:
            return "YOUR name is taken a"
        
        # save to db
        cur.execute(
            "INSERT INTO users (name, password) VALUES(?, ?)", (name, password)
        )

        id = cur.execute(
            "SELECT * FROM users WHERE name = ?", (name)
        )
        store(id[0]["id"])
        db.commit()

        return redirect("/")
    else:
        return render_template("register.html")
    
# log in
@app.route("/login", methods=['POST', 'GET'])
def login():

    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")

        check = cur.execute(" SELECT * FROM users WHERE name = ? and password = ?", (name, password)).fetchall()

        if not check:
            return "INVALID"


        res = store(check[0]["id"])
        return res
    else:
        return render_template("loggin.html")

@app.route("/newload", methods=["POST"])
def load():
    global hpage
    feeds = cur.execute(
            "SELECT * FROM feeds LIMIT ?", (hpage,)
        ).fetchall()
    if not feeds:
        return "no more"
    else:
        content=""
        for feed in feeds:
            content+=f"<div><h5>{feed["uploader"]}</h5><p>{feed["content"]}</p></div>"
        hpage+=2
        return content
# rerun server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

