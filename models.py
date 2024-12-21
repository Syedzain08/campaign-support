# ---Database Models For The Site--- #

# ---Imports--- #

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Database Instance #

db = SQLAlchemy()


# ---Database Models--- #


class Users(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    password = db.Column(db.String, nullable=False)
    token_store = db.Column(db.String, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    # Relationships
    articles = db.relationship("Articles", back_populates="author")


# Association Table for the Many-to-Many Relationship between Articles and Tags
article_tags = db.Table(
    "article_tags",
    db.Column("article_id", db.Integer, db.ForeignKey("articles.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)

# Association Table for the Many-to-Many Relationship between Articles and Categories
article_categories = db.Table(
    "article_categories",
    db.Column("article_id", db.Integer, db.ForeignKey("articles.id"), primary_key=True),
    db.Column(
        "category_id", db.Integer, db.ForeignKey("categories.id"), primary_key=True
    ),
)


class Articles(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    thumbnail = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    approved_at = db.Column(db.DateTime, nullable=True)

    status = db.Column(
        db.Enum("draft", "published", "private", name="article_status_enum"),
        default="draft",
        nullable=False,
    )

    is_approved = db.Column(db.Boolean, default=False, nullable=False)  # New field

    # Analytics
    view_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)

    # Relationships
    author = db.relationship("Users", back_populates="articles")

    categories = db.relationship(
        "Categories",
        secondary=article_categories,
        back_populates="articles",
    )
    tags = db.relationship(
        "Tags",
        secondary=article_tags,
        back_populates="articles",
    )


class Tags(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    # Relationships
    articles = db.relationship(
        "Articles",
        secondary=article_tags,
        back_populates="tags",
    )


class Categories(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    # Relationships
    articles = db.relationship(
        "Articles",
        secondary=article_categories,
        back_populates="categories",
    )
