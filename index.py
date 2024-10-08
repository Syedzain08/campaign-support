from flask import Flask, request, render_template, session, redirect, url_for, flash
from dotenv import load_dotenv
from os import getenv
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from bcrypt import checkpw, hashpw, gensalt
from re import search
from smtplib import SMTP
from secrets import token_urlsafe
from flask_mail import Mail, Message
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


app = Flask(__name__, static_folder="static", static_url_path="/static")

load_dotenv()

app.secret_key = getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = True  
app.config['SESSION_COOKIE_HTTPONLY'] = True  
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

db = SQLAlchemy(app)
mail = Mail(app)
limiter = Limiter(
    get_remote_address,  
    app=app,
    storage_uri="memory://", 
    default_limits=["300 per day", "100 per hour"] 
)


class Users(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    password = db.Column(db.String, nullable=False) 
    token_store = db.Column(db.String, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)


    def set_password(password_given):
        password_hash = hashpw(password=password_given.encode("utf-8"), salt=gensalt(rounds=4))
        return password_hash.decode("utf-8")

    def check_password(password_given, password_hash):
        return checkpw(password_given.encode('utf-8'), password_hash)
    
    def check_password_criteria(password):
        has_special = bool(search(r'[!@#$%^&*()_+\-=\[\]{};:\'"\\|,.<>?]', password))
        has_number = bool(search(r'\d', password))
        has_uppercase = bool(search(r'[A-Z]', password))
        has_lowercase = bool(search(r'[a-z]', password))
        is_long_enough = 10 <= len(password) <= 100
        
        return all([has_special, has_number, has_uppercase, has_lowercase, is_long_enough])

    def check_username_criteria(username):
        # Define the criteria
        min_length = 3
        max_length = 25
        prohibited_chars = r"[!@#$%^&*()\+=\{\}\[\]|\\:;\"'<>,.?/ ]"

        if len(username) < min_length or len(username) > max_length:
            return False

        if search(prohibited_chars, username):
            return False

        if username[0] in "!@#$%^&*()-+=[]{},|\\:;\"'<>,.?/" or username[-1] in "!@#$%^&*()-+=[]{},|\\:;\"'<>,.?/":
            return False

        if search(r"[!@#$%^&*()\-+=\{\}\[\]|\\:;\"'<>,.?/]{2,}", username):
            return False

        return True
    

class MyIndexView(AdminIndexView):
    def is_accessible(self):
        if "username" not in session:
            return False
        
        current_user = Users.query.filter_by(username=session["username"]).first()
        if current_user:
            if current_user.is_admin:
                return True
            else:
                return False
        
        return False
    
    def inaccessible_callback(self, name, **kwargs):
        if "username" not in session:
            flash("Login first to access this page!")
            return redirect(url_for("login"))
        
        current_user = Users.query.filter_by(username=session["username"]).first()
        if current_user and not current_user.is_admin:
            flash("Access Denied! You do not have the clearance to view this page!")
        
        return redirect(url_for("index"))
        
class MyModelView(ModelView):
    def is_accessible(self):
        if "username" not in session:
            return False
        
        current_user = Users.query.filter_by(username=session["username"]).first()
        if current_user:
            if current_user.is_admin:
                return True
            else:
                return False
        
        return False
    
    def inaccessible_callback(self, name, **kwargs):
        if "username" not in session:
            flash("Login first to access this page!")
            return redirect(url_for("login"))
        
        current_user = Users.query.filter_by(username=session["username"]).first()
        if current_user and not current_user.is_admin:
            flash("Access Denied! You do not have the clearance to view this page!")

        return redirect(url_for("index"))


admin = Admin(app=app, index_view=MyIndexView())   
admin.add_view(MyModelView(model=Users, session=db.session))


    
@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("index"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if "username" in session:
        flash("Already logged in!")
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form["username"].lower()
        password = request.form["password"]
        current_user = Users.query.filter_by(username=username).first()
        if current_user and Users.check_password(password_given=password, password_hash=bytes(current_user.password, "utf-8")):
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
        email = request.form["Email"].lower()
        username = request.form["Username"].lower()
        password = request.form["Password"]
        confirm_password = request.form["confirm-password"]

        if not Users.check_username_criteria(username=username):
            flash("""
                    <ul>Your username must contain:</ul>
                    <li>- Between 3 and 20 characters</li>
                    <li>- No spaces or special characters, except for hyphens (-) and underscores (_)</li>
                    <li>- Cannot start or end with a special character</li>
                    <li>- No consecutive special characters</li>
                    """)
            return render_template("pages/register.html", email=email, username=username)

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
                
                server = SMTP("smtp.gmail.com", 587)
                server.starttls()
                my_password = getenv("GMAIL_SMTP_PASSWORD")
                user_email = getenv("GMAIL_USER")
                server.login(user_email, my_password)
                server.sendmail(user_email, email, msg)

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
                
                server = SMTP("smtp.gmail.com", 587)
                server.starttls()
                my_password = getenv("GMAIL_SMTP_PASSWORD")
                user_email = getenv("GMAIL_USER")
                server.login(user_email, my_password)
                server.sendmail(user_email, email, msg)


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
    
    if user is None or not Users.check_password(token, bytes(user.token_store, "utf-8")):
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
    with app.app_context():
        db.create_all()
    app.run(debug=True)
