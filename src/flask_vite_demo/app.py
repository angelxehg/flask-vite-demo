from flask import Flask, redirect, render_template, request

from flask_vite_demo.core import init_assets, init_csp
from flask_vite_demo.core.assets import static_url


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

    # base.html points every page at the real icon, so this is only for clients
    # that ask for the well-known path regardless. A redirect rather than the
    # bytes: the icon lives wherever the assets live, and one copy of that
    # decision is enough.
    @app.route("/favicon.ico")
    def favicon():
        return redirect(static_url("favicon.svg"))

    # Without these, a wrong URL renders Werkzeug's unstyled default page --
    # outside the site's own shell, though still with the CSP, which after_request
    # attaches to every response either way.
    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("500.html"), 500

    return app
