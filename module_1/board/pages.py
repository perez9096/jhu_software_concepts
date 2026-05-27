from flask import Blueprint, render_template

bp = Blueprint("pages", __name__)

@bp.route("/")
def homepage():
    return render_template("pages/homepage.html")

@bp.route("/contactinfo")
def contactinfo():
    return render_template("pages/contactinfo.html")

@bp.route("/projectspage")
def projectspage():
    return render_template("pages/projectspage.html")
