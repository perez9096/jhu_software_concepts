from flask import Flask

from board import pages

def create_app():
    app = Flask(__name__)
    app.register_blueprint(pages.bp)
    
    # Keeping if statement to see if this will work - RP
#    if __name__ == "__main__":
#        app.run(host="0.0.0.0", port=8000, debug=True)
#    if __name__ == "__main__":
#        app.run(host="0.0.0.0", port=8080, debug=True)
    return app
    
    