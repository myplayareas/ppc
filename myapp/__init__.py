import os
from flask import Flask
from myapp.config import db
from myapp.control import main

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "myapp.sqlite"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/")
    def index():
        return '<p> Bem vindo ao teste de análise de repositórios usando produtor/consumidor e threads'

    db.init_app(app)

    app.register_blueprint(main.bp)

    # Define a rota principal da aplicacao
    app.add_url_rule("/", endpoint="index")

    return app