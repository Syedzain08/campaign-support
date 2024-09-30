from flask import Flask, request, render_template, session, redirect, url_for, flash
from dotenv import load_dotenv
from os import getenv
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from bcrypt import checkpw, hashpw, gensalt
from re import search
import smtplib
from secrets import token_urlsafe
from flask_mail import Mail, Message
from time import time

app = Flask(__name__, static_folder="static", static_url_path="/static")

load_dotenv()

app.secret_key = getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///./users.db"
db = SQLAlchemy(app)
mail = Mail(app)



class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    password = db.Column(db.LargeBinary, nullable=False) 
    token_store = db.Column(db.LargeBinary, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)


    def set_password(password_given):
        password_hash = hashpw(password=password_given.encode("utf-8"), salt=gensalt())
        return password_hash

    def check_password(password_given, password_hash):
        return checkpw(password_given.encode('utf-8'), password_hash)
    
    def check_password_criteria(password):
        has_special = bool(search(r'[!@#$%^&*()_+\-=\[\]{};:\'"\\|,.<>?]', password))
        has_number = bool(search(r'\d', password))
        has_uppercase = bool(search(r'[A-Z]', password))
        has_lowercase = bool(search(r'[a-z]', password))
        is_long_enough = 10 <= len(password) <= 100
        
        return all([has_special, has_number, has_uppercase, has_lowercase, is_long_enough])
    
    
@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("index"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        flash("Already logged in!")
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        current_user = Users.query.filter_by(username=username).first()
        if current_user and Users.check_password(password_given=password, password_hash=current_user.password):
            session["username"] = username
            return redirect(url_for("index"))
        else:
            flash(message="Invalid Credentials", category="error")
            return render_template("pages/login.html", username=username)

    return render_template("pages/login.html")

@app.route("/register", methods={"GET", "POST"})
def register():
    if "username" in session:
        flash("Logout first to register again!")
        return redirect(url_for( "index" ))
    if request.method == "POST":
        email = request.form["Email"].lower().lower()
        username = request.form["Username"]
        password = request.form["Password"]
        confirm_password = request.form["confirm-password"]

        if password != confirm_password:
            flash("Passwords don't match!")
            return render_template("pages/register.html", email=email, username=username)

        if not Users.check_password_criteria(password):
            flash("""
            <ul>Your password must contain:<ul/>
            <li>- At least 10 characters (and up to 100 characters)</li>
            <li>- At least 1 number</li>
            <li>- At least one lowercase and one uppercase character</li>
            <li>- Inclusion of at least one special character, e.g., ! @ # ?</li>
            """)

            return render_template("pages/register.html", email=email, username=username)
        
        if Users.query.filter_by(email=email).first():
            flash("Email already registered!")
            return render_template("pages/register.html", email=email, username=username)
        
        if Users.query.filter_by(username=username).first():
            flash("Username is already taken!")
            return render_template("pages/register.html", email=email, username=username)
        password_hash = Users.set_password(password_given=password)
        new_user = Users(email=email, username=username, password=password_hash)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            session["username"] = username
            session['newly_registered'] = True
            return redirect(url_for("index"))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred. Please try again. {str(e)}")
    
    return render_template("pages/register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/index")
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    if 'newly_registered' in session and session['newly_registered'] is True:
        session.pop('newly_registered', False) 
        return f"hello, {session["username"]}. Thanks for joining us!"
    username = session["username"]
    return render_template("pages/index.html", username=username)

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if 'username' in session:
        flash("Cannot perform function while signed in!")
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form["Email"].lower()
        current_user = Users.query.filter_by(email=email).first()
        if current_user:
            token = token_urlsafe(32)
            token_hash = Users.set_password(token)
            current_user.token_store = token_hash
            current_user.token_expiry = datetime.utcnow() + timedelta(minutes=15)
            
            try:
                db.session.commit()
                
                reset_link = url_for('reset_password', token=token, _external=True)
                msg = f"""Hello,

                We received a request to reset your password.
                If you did not make this request, please ignore this email.

                To reset your password, please click on the following link or copy and paste it into your browser:

                {reset_link}

                This link will expire in 15 Minutes.

                Best regards,
                Campaign Website Support Team"""
                
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                my_password = getenv("GMAIL_SMTP_PASSWORD")
                server.login("campaignwebsiteteam@gmail.com", my_password)
                server.sendmail("campaignwebsiteteam@gmail.com", email, msg)

                flash("Password reset instructions have been sent to your email.")
                return redirect(url_for("login"))
            
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred. Please try again. {str(e)}")
        else:
            flash("No account with this E-mail!")

    return render_template("pages/forgot-password.html")

@app.route("/forgot-username", methods=["GET", "POST"])
def forgot_username():
    if 'username' in session:
        flash("Cannot perform function while signed in!")
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form["Email"].lower()
        current_user = Users.query.filter_by(email=email).first()
        if current_user:
            try:
                msg = f"""Hello,

                We received a request to retrieve your username.

                Your username is: {current_user.username}

                If you did not make this request, please ignore this email or contact our support team.

                Best regards,
                Campaign Website Support Team"""
                
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                my_password = getenv("GMAIL_SMTP_PASSWORD")
                server.login("campaignwebsiteteam@gmail.com", my_password)
                server.sendmail("campaignwebsiteteam@gmail.com", email, msg)


                flash("Email Sent!")

                return redirect(url_for("login"))
            except Exception as e:
                flash(f"Could not send E-mail {e}")
                return render_template("pages/forgot-username.html", email=email)
        else:
            flash("No account with this E-mail!")
            return render_template("pages/forgot-username.html", email=email)
        
    return render_template("pages/forgot-username.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if 'username' in session:
        flash("Cannot perform function while signed in!")
        return redirect(url_for("index"))
    
    user = Users.query.filter(Users.token_store.isnot(None), Users.token_expiry > datetime.utcnow()).first()
    
    if user is None or not Users.check_password(token, user.token_store):
        flash("The password reset link is invalid or has expired.")
        return redirect(url_for("forgot_password"))
    
    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        
        if not new_password or not confirm_password:
            flash("Please provide both new password and confirmation.")
            return render_template("pages/reset-password.html", token=token)
        
        if new_password != confirm_password:
            flash("Passwords don't match!")
            return render_template("pages/reset-password.html", token=token)
        
        if not Users.check_password_criteria(new_password):
            flash("""
            <ul>Your password must contain:<ul/>
            <li>- At least 10 characters (and up to 100 characters)</li>
            <li>- At least 1 number</li>
            <li>- At least one lowercase and one uppercase character</li>
            <li>- Inclusion of at least one special character, e.g., ! @ # ?</li>
            """)
            return render_template("pages/reset-password.html", token=token)
        
        try:
            user.password = Users.set_password(new_password)
            user.token_store = None
            user.token_expiry = None
            db.session.commit()
            flash("Your password has been reset successfully. You can now log in with your new password.")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred. Please try again. {str(e)}")
    
    return render_template("pages/reset-password.html", token=token)

if __name__ == "__main__":
    app.run(debug=True)
