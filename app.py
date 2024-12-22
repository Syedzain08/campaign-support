# ---IMPORTS--- #

from admin import setup_admin
from cloudinary import uploader, config
from datetime import datetime, timedelta
from dotenv import load_dotenv
from email.mime.text import MIMEText
from flask import Flask, request, render_template, session, redirect, url_for, flash
from flask import jsonify, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFError
from flask_wtf.csrf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from io import BytesIO
from models import db, Users, Articles, Tags
from models import Categories, article_tags, article_categories
from os import getenv
from PIL import Image
from secrets import token_urlsafe
from smtplib import SMTP
from utils import *


# ---CONFIGURATION--- #

# App instance

app = Flask(__name__, static_folder="static", static_url_path="/static")

# Load environment variables

load_dotenv()

# App Configuration

app.secret_key = getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Initialize extensions
setup_admin(app)
db.init_app(app)
mail = Mail(app)
csrf = CSRFProtect(app)
migrate = Migrate(app, db)
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://",
    default_limits=["10000 per day", "1000 per hour"],
)

# Cloudinary Configurations
config(
    cloud_name=getenv("CLOUD_NAME"),
    api_key=getenv("API_KEY"),
    api_secret=getenv("API_SECRET"),
)

# ---CONTEXT PROCESSORS---


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": generate_csrf()}


@app.context_processor
def base():
    try:
        current_user = Users.query.filter_by(username=session["username"]).first()
        admins = Users.query.filter_by(is_admin=True).all()

        if current_user not in admins:
            is_admin = False
        else:
            is_admin = True
        return dict(is_admin=is_admin)
    except Exception:
        return dict(is_admin=False)


# ---ROUTES--- #


@app.route("/")
def home():
    if user_logged_in(session=session):
        return redirect(url_for("index"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("50 per minute")
def login():

    if user_logged_in(session=session):
        flash("Already logged in!")
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form["username"].lower()
        password = request.form["password"]

        current_user = Users.query.filter_by(username=username).first()

        if current_user and check_password(
            password_given=password, password_hash=bytes(current_user.password, "utf-8")
        ):
            session["username"] = username

            return redirect(url_for("index"))
        else:

            flash(message="Invalid Credentials", category="error")
            return render_template("pages/login.html", username=username)

    return render_template("pages/login.html")


@app.route("/register", methods={"GET", "POST"})
@limiter.limit("50 per minute")
def register():
    if user_logged_in(session=session):
        flash("Already Registered!")
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form["Email"].lower()
        username = request.form["Username"].lower()
        password = request.form["Password"]
        confirm_password = request.form["confirm-password"]

        if not check_username_criteria(username=username):
            flash(
                """
                    <ul>Your username must contain:</ul>
                    <li>- Between 3 and 20 characters</li>
                    <li>- No spaces or special characters, except for hyphens (-) and underscores (_)</li>
                    <li>- Cannot start or end with a special character</li>
                    <li>- No consecutive special characters</li>
                    """
            )
            return render_template(
                "pages/register.html", email=email, username=username
            )

        if password != confirm_password:
            flash("Passwords don't match!")
            return render_template(
                "pages/register.html", email=email, username=username
            )

        if not check_password_criteria(password):
            flash(
                """
            <ul>Your password must contain:<ul/>
            <li>- At least 10 characters (and up to 100 characters)</li>
            <li>- At least 1 number</li>
            <li>- At least one lowercase and one uppercase character</li>
            <li>- Inclusion of at least one special character, e.g., ! @ # ?</li>
            """
            )

            return render_template(
                "pages/register.html", email=email, username=username
            )

        if Users.query.filter_by(email=email).first():
            flash("Email already registered!")
            return render_template(
                "pages/register.html", email=email, username=username
            )

        if Users.query.filter_by(username=username).first():
            flash("Username is already taken!")
            return render_template(
                "pages/register.html", email=email, username=username
            )
        password_hash = set_password(password_given=password)
        new_user = Users(email=email, username=username, password=password_hash)

        try:
            db.session.add(new_user)
            db.session.commit()
            session["username"] = username
            session["newly_registered"] = True
            return redirect(url_for("index"))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred. Please try again. {str(e)}")

    return render_template("pages/register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/index", methods=["GET", "POST"])
@limiter.limit("100 per minute")
def index():
    if not user_logged_in(session=session):
        return redirect(url_for("login"))

    if "newly_registered" in session and session["newly_registered"] is True:
        session.pop("newly_registered", False)
        flash(
            f"Welcome to the Campaign Website! {session['username']} Your account has been created."
        )

        return render_template("pages/index.html")

    # Content recommendation for the user
    username = session["username"]
    latest_articles = (
        Articles.query.filter_by(status="published")
        .order_by(Articles.created_at.desc())
        .limit(9)
        .all()
    )
    popular_articles = (
        Articles.query.filter_by(status="published")
        .order_by(Articles.view_count.desc())
        .limit(9)
        .all()
    )

    for article in latest_articles:
        article.first_sentence = extract_first_sentence(article.content)
        article.first_image = (
            extract_first_image_link(article.content)
            or "https://picsum.photos/1920/1080"
        )

    return render_template(
        "pages/index.html",
        username=username,
        latest_articles=latest_articles,
        popular_articles=popular_articles,
    )


@app.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("50 per minute")
def forgot_password():

    if user_logged_in(session=session):
        flash("Cannot perform function while signed in!")
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form["Email"].lower()
        current_user = Users.query.filter_by(email=email).first()

        if current_user:
            token = token_urlsafe(32)
            token_hash = set_password(token)
            current_user.token_store = token_hash
            current_user.token_expiry = datetime.utcnow() + timedelta(minutes=15)

            try:
                db.session.commit()

                reset_link = url_for("reset_password", token=token, _external=True)
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
@limiter.limit("50 per minute")
def forgot_username():
    if user_logged_in(session=session):
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
@limiter.limit("50 per minute")
def reset_password(token):
    if user_logged_in(session=session):
        flash("Cannot perform function while signed in!")
        return redirect(url_for("index"))

    user = Users.query.filter(
        Users.token_store.isnot(None), Users.token_expiry > datetime.utcnow()
    ).first()

    if user is None or not check_password(token, bytes(user.token_store, "utf-8")):
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

        if not check_password_criteria(new_password):
            flash(
                """
            <ul>Your password must contain:<ul/>
            <li>- At least 10 characters (and up to 100 characters)</li>
            <li>- At least 1 number</li>
            <li>- At least one lowercase and one uppercase character</li>
            <li>- Inclusion of at least one special character, e.g., ! @ # ?</li>
            """
            )
            return render_template("pages/reset-password.html", token=token)

        try:
            user.password = set_password(new_password)
            user.token_store = None
            user.token_expiry = None
            db.session.commit()
            flash(
                "Your password has been reset successfully. You can now log in with your new password."
            )
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred. Please try again. {str(e)}")

    return render_template("pages/reset-password.html", token=token)


@app.route("/posts/add", methods=["GET", "POST"])
def add_post():
    if not user_logged_in(session=session):
        flash("Sign in to post!")
        return redirect(url_for("login"))

    categories = Categories.query.all()
    tags = Tags.query.all()

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("post-content")
        selected_categories = request.form.getlist("category")
        selected_tags = request.form.getlist("tags")
        thumbnail_url = request.form.get("thumbnail_url")

        if not content or not title or not selected_categories or not selected_tags:
            flash("Title, content, tags, and category are required", "error")
            return render_template(
                "pages/add-post.html", categories=categories, tags=tags
            )
        if not thumbnail_url:
            thumbnail_url = None

        try:
            slug = generate_unique_slug(title, Articles)
            current_user = Users.query.filter_by(username=session["username"]).first()

            new_article = Articles(
                title=title,
                slug=slug,
                content=content,
                author_id=current_user.id,
                status="draft",
                is_approved=False,
                thumbnail=thumbnail_url,
            )

            # Add categories
            for category_id in selected_categories:
                category = Categories.query.get(int(category_id))
                if category:
                    new_article.categories.append(category)

            # Add tags
            for tag_id in selected_tags:
                tag = Tags.query.get(int(tag_id))
                if tag:
                    new_article.tags.append(tag)
            db.session.add(new_article)
            db.session.commit()

            base_url = request.url_root

            # Compose the HTML email
            html_msg = f"""
                <html>
                <body>
                    <p>Hello {current_user.username},</p>
                    <p>
                        The article titled <strong>{title}</strong> that you submitted 
                        has been created and is awaiting approval by the ADMIN.
                        Only you  and the ADMIN can view the article until it is approved and published
                        Take a look:  <a href="{base_url}posts/{slug}" target="_blank"  rel="noopener noreferrer">{title}</a>
                    </p>
                    <p>Thank you,<br>Campaign Website Support Team</p>
                </body>
                </html>
                """

            # Create the MIMEText object with HTML content
            mime_msg = MIMEText(html_msg, "html")

            server = SMTP("smtp.gmail.com", 587)
            server.starttls()
            my_password = getenv("GMAIL_SMTP_PASSWORD")
            user_email = getenv("GMAIL_USER")
            server.login(user_email, my_password)

            mime_msg["From"] = user_email
            mime_msg["To"] = current_user.email
            mime_msg["Subject"] = "Article Approval Notification"

            server.sendmail(user_email, current_user.email, mime_msg.as_string())

            flash("Post created successfully! Awaiting admin approval.", "success")
            return redirect(url_for("index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to create post: {str(e)}", "error")
            return render_template(
                "pages/add-post.html", categories=categories, tags=tags
            )

    return render_template("pages/add-post.html", categories=categories, tags=tags)


@app.route("/posts/edit/<string:slug>", methods=["GET", "POST"])
def edit_post(slug):
    if not user_logged_in(session=session):
        flash("Sign in to edit posts!")
        return redirect(url_for("login"))

    article = Articles.query.filter_by(slug=slug).first_or_404()

    current_user = Users.query.filter_by(username=session["username"]).first()
    if article.author_id != current_user.id and not current_user.is_admin:
        flash("You do not have permission to edit this post.", "error")
        return redirect(url_for("view_post", slug=slug))

    categories = Categories.query.all()
    tags = Tags.query.all()

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("post-content")
        selected_categories = request.form.getlist("category")
        selected_tags = request.form.getlist("tags")
        thumbnail_url = request.form.get("thumbnail_url")

        thumbnail_url
        if not thumbnail_url:
            thumbnail_url = article.thumbnail

        if not title or not content:
            flash("Title and content are required", "error")
            return render_template(
                "pages/edit-post.html",
                article=article,
                categories=categories,
                tags=tags,
            )

        try:

            article.title = title
            article.content = content
            article.is_approved = False
            article.status = "draft"
            article.thumbnail = thumbnail_url

            article.categories.clear()
            article.tags.clear()

            for category_id in selected_categories:
                category = Categories.query.get(int(category_id))
                if category:
                    article.categories.append(category)

            for tag_id in selected_tags:
                tag = Tags.query.get(int(tag_id))
                if tag:
                    article.tags.append(tag)

            db.session.commit()

            flash("Post updated successfully! Awaiting admin approval.", "success")
            return redirect(url_for("index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to update post: {str(e)}", "error")
            return render_template(
                "pages/edit-post.html",
                article=article,
                categories=categories,
                tags=tags,
            )

    return render_template(
        "pages/edit-post.html",
        article=article,
        categories=categories,
        tags=tags,
    )


@app.route("/posts/<slug>", methods=["GET", "POST"])
def view_post(slug):
    if not user_logged_in(session=session):
        flash("Sign in to edit posts!")
        return redirect(url_for("login"))

    article = Articles.query.filter_by(slug=slug).first()

    if not article:
        abort(404)

    current_user = None
    if user_logged_in(session=session):
        current_user = Users.query.filter_by(username=session["username"]).first()

    is_author = current_user and current_user.username == article.author.username
    is_admin = current_user and current_user.is_admin

    if not article.is_approved and not (is_author or is_admin):
        flash("You do not have permission to view this article.", "error")
        return redirect(url_for("index"))

    if article.is_approved and f"viewed_{article.id}" not in session:
        article.view_count += 1
        db.session.commit()
        session[f"viewed_{article.id}"] = True

    categories = article.categories
    tags = article.tags

    return render_template(
        "pages/view-post.html",
        article=article,
        categories=categories,
        tags=tags,
        current_user=current_user,
    )


@app.route("/posts/delete/<string:slug>", methods=["POST"])
def delete_post(slug):
    if not user_logged_in(session=session):
        flash("Sign in to edit posts!")
        return redirect(url_for("login"))

    article = Articles.query.filter_by(slug=slug).first()

    current_user = Users.query.filter_by(username=session["username"]).first()
    if article.author_id != current_user.id and not current_user.is_admin:
        flash("You don't have clearance to delete this article!", "error")
        return redirect(url_for("view_post", slug=slug))

    if article:
        try:
            db.session.delete(article)
            db.session.commit()
            flash(f"Article: '{article.title}' deleted.")
            return redirect(url_for("index"))

        except Exception as e:
            flash(f"Could not complete action!", "error")
            return redirect(url_for("view_post", slug=slug))

    flash("Article doesn't exist!")
    return redirect(url_for("index"))


@app.route("/upload_image", methods=["POST"])
def upload_image():
    try:

        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image uploaded"}), 400

        file = request.files["image"]

        if file.filename == "":
            return jsonify({"success": False, "error": "No selected file"}), 400

        img = Image.open(file)

        img.thumbnail((1920, 1080), Image.LANCZOS)

        byte_stream = BytesIO()
        img.save(byte_stream, format="WEBP", quality=85)
        byte_stream.seek(0)

        upload_response = uploader.upload(byte_stream, format="webp")
        image_url = upload_response["secure_url"]

        return jsonify({"success": True, "link": image_url}), 200

    except Exception as e:
        app.logger.error(f"Image upload error: {str(e)}")
        return jsonify({"success": False, "error": f"Upload failed: {str(e)}"}), 500


@app.route("/upload_video", methods=["POST"])
def upload_video():
    try:
        if "video" not in request.files:
            return jsonify({"success": False, "error": "No video uploaded"}), 400

        file = request.files["video"]

        if file.filename == "":
            return jsonify({"success": False, "error": "No selected file"}), 400

        byte_stream = BytesIO(file.read())

        upload_response = uploader.upload(byte_stream, resource_type="video")
        video_url = upload_response["secure_url"]

        return jsonify({"success": True, "link": video_url}), 200

    except Exception as e:
        app.logger.error(f"Video upload error: {str(e)}")
        return jsonify({"success": False, "error": f"Upload failed: {str(e)}"}), 500


@app.route("/admin/articles/pending", methods=["GET", "POST"])
def pending_articles():
    if not user_logged_in(session=session):
        flash("Login to access this page!", "error")
        return redirect(url_for("login"))

    admins = Users.query.filter_by(is_admin=True).all()
    current_user = Users.query.filter_by(username=session["username"]).first()
    if current_user not in admins:
        flash("Access denied. Admins only.", "error")
        return redirect(url_for("index"))

    articles = Articles.query.filter_by(is_approved=False).all()

    if request.method == "POST":
        article_id = request.form.get("article_id")
        article = Articles.query.get(article_id)
        author = Users.query.filter_by(id=article.author_id).first()
        if article:
            article.is_approved = True
            article.status = "published"
            article.updated_at = datetime.utcnow()

            try:
                base_url = request.url_root

                # Compose the HTML email
                html_msg = f"""
                <html>
                <body>
                    <p>Hello {author.username},</p>
                    <p>
                        The article titled <strong>{article.title}</strong> that you submitted 
                        has been approved by the ADMIN and is now published.
                        Take a look:  <a href="{base_url}posts/{article.slug}" target="_blank" rel="noopener noreferrer">{article.title}</a>
                    </p>
                    <p>Thank you,<br>Campaign Website Support Team</p>
                </body>
                </html>
                """

                mime_msg = MIMEText(html_msg, "html")

                server = SMTP("smtp.gmail.com", 587)
                server.starttls()
                my_password = getenv("GMAIL_SMTP_PASSWORD")
                user_email = getenv("GMAIL_USER")
                server.login(user_email, my_password)

                mime_msg["From"] = user_email
                mime_msg["To"] = author.email
                mime_msg["Subject"] = "Article Approval Notification"

                server.sendmail(user_email, author.email, mime_msg.as_string())

                db.session.commit()

                flash(
                    f"Article '{article.title}' has been approved and published.",
                    "success",
                )

            except Exception as e:
                flash(f"An error occurred. Please try again. {str(e)}")
        else:
            flash("Article not found.", "error")
        return redirect(url_for("pending_articles"))

    return render_template("pages/admin_pending_articles.html", articles=articles)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = (
        request.form.get("search-query")
        if request.method == "POST"
        else request.args.get("q")
    )
    page = request.args.get("page", 1, type=int)
    per_page = 9

    if query:
        results = (
            Articles.query.join(Users, Users.id == Articles.author_id)
            .outerjoin(
                article_categories, article_categories.c.article_id == Articles.id
            )
            .outerjoin(Categories, Categories.id == article_categories.c.category_id)
            .outerjoin(article_tags, article_tags.c.article_id == Articles.id)
            .outerjoin(Tags, Tags.id == article_tags.c.tag_id)
            .filter(
                Articles.is_approved == True,
                Articles.status == "published",
                db.or_(
                    Articles.title.ilike(f"%{query}%"),
                    Articles.content.ilike(f"%{query}%"),
                    Users.username.ilike(f"%{query}%"),
                    Categories.name.ilike(f"%{query}%"),
                    Tags.name.ilike(f"%{query}%"),
                ),
            )
            .distinct()
        )

        total_results = results.count()

        paginated_results = results.paginate(
            page=page, per_page=per_page, error_out=False
        )

        for result in paginated_results.items:
            result.first_sentence = extract_first_sentence(result.content)
            result.first_image = (
                extract_first_image_link(result.content)
                or "https://picsum.photos/1920/1080"
            )

        return render_template(
            "layouts/search-results.html",
            results=paginated_results.items,
            query=query,
            pagination=paginated_results,
            total_results=total_results,
        )

    return render_template(
        "layouts/search-results.html", results=[], query=query or "", total_results=0
    )


# ---ERROR HANDLERS--- #


@app.errorhandler(404)
def page_not_found(e):
    return render_template("pages/errors/404.html"), 404


@app.errorhandler(429)
def too_many_requests(e):
    return render_template("pages/errors/429.html"), 429


@app.errorhandler(405)
def too_many_requests(e):
    return render_template("pages/errors/405.html"), 405


@app.errorhandler(500)
def too_many_requests(e):
    return render_template("pages/errors/500.html"), 500


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template("pages/errors/CSRF-error.html")


# ---MAIN--- #

if __name__ == "__main__":
    app.run()
