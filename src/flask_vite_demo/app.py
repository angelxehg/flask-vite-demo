from flask import Flask, render_template, request

from flask_vite_demo.core import init_assets, init_csp


def create_app() -> Flask:
    app = Flask(__name__)
    init_assets(app)
    init_csp(app)

    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        submitted_name = None
        if request.method == "POST":
            submitted_name = request.form.get("name")
        return render_template("contact.html", submitted_name=submitted_name)

    return app
