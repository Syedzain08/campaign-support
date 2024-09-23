from flask import Flask, request, render_template, session, redirect, url_for

app = Flask(__name__)

app.secret_key = "your_secret_key"

users = {"user": "password", "zain": "yanzain"}


@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("index"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["username"] = username
            return redirect(url_for("index"))
        else:
            return "Invalid credentials", 401

    return render_template("layouts/login.html")


@app.route("/index")
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    return f'Hello, {session["username"]}!'


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
