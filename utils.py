#  -- Contains utility functions for the application --- #

# --- Imports --- #
from bcrypt import hashpw, gensalt, checkpw
from bs4 import BeautifulSoup
from re import search
from slugify import slugify


# --- Functions --- #


# User authentication functions


def user_logged_in(session):
    if "username" not in session:
        return False
    return True


def set_password(password_given):
    password_hash = hashpw(
        password=password_given.encode("utf-8"), salt=gensalt(rounds=4)
    )
    return password_hash.decode("utf-8")


def check_password(password_given, password_hash):
    return checkpw(password_given.encode("utf-8"), password_hash)


def check_password_criteria(password):
    has_special = bool(search(r'[!@#$%^&*()_+\-=\[\]{};:\'"\\|,.<>?]', password))
    has_number = bool(search(r"\d", password))
    has_uppercase = bool(search(r"[A-Z]", password))
    has_lowercase = bool(search(r"[a-z]", password))
    is_long_enough = 10 <= len(password) <= 100

    return all([has_special, has_number, has_uppercase, has_lowercase, is_long_enough])


def check_username_criteria(username):
    min_length = 3
    max_length = 25
    prohibited_chars = r"[!@#$%^&*()\+=\{\}\[\]|\\:;\"'<>,.?/ ]"

    if len(username) < min_length or len(username) > max_length:
        return False

    if search(prohibited_chars, username):
        return False

    if (
        username[0] in "!@#$%^&*()-+=[]{},|\\:;\"'<>,.?/"
        or username[-1] in "!@#$%^&*()-+=[]{},|\\:;\"'<>,.?/"
    ):
        return False

    if search(r"[!@#$%^&*()\-+=\{\}\[\]|\\:;\"'<>,.?/]{2,}", username):
        return False

    return True


# Article utility functions


def generate_unique_slug(title, model):
    """
    Generate a unique slug for a given title by checking existing slugs

    Args:
        title (str): The original title to convert to a slug
        model (db.Model): The database model to check for existing slugs

    Returns:
        str: A unique slug
    """
    base_slug = slugify(title)

    slug = base_slug
    counter = 1

    while model.query.filter_by(slug=slug).first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


def extract_first_sentence(content):
    text = BeautifulSoup(content, "html.parser").get_text()
    match = search(r"([^.?!]*[.?!])", text)
    if match:
        return match.group(1).strip()
    return text.strip()


def extract_first_image_link(content):
    soup = BeautifulSoup(content, "html.parser")
    first_image = soup.find("img")
    if first_image and first_image.get("src"):
        return first_image["src"]
    return None
