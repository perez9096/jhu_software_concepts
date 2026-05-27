#
from board import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
# python -m flask --app board run --port 8000 --debug