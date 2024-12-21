from flask import session, flash, redirect, url_for
from flask_admin import Admin, AdminIndexView
from models import Users


class MyIndexView(AdminIndexView):
    def is_accessible(self):
        if "username" not in session:
            return False

        current_user = Users.query.filter_by(username=session["username"]).first()
        if current_user:
            return current_user.is_admin

        return False

    def inaccessible_callback(self, name, **kwargs):
        if "username" not in session:
            flash("Login first to access this page!")
            return redirect(url_for("login"))

        current_user = Users.query.filter_by(username=session["username"]).first()
        if current_user and not current_user.is_admin:
            flash("Access Denied! You do not have the clearance to view this page!")

        return redirect(url_for("index"))


# Initialize Flask-Admin
def setup_admin(app):
    admin = Admin(app, index_view=MyIndexView(name="Home"))
    return admin
