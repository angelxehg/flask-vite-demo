from flask import Flask, render_template, request


def create_app() -> Flask:
    app = Flask(__name__)

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
