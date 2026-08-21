from flask_vite_demo.app import create_app


def main() -> None:
    create_app().run(debug=True, port=8000)
