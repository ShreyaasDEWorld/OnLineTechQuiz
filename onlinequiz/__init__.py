import os
from flask import Flask
from flask_login import LoginManager
from .config import Config
from .models.user import User

login_manager = LoginManager()
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "..", "templates"),
        static_folder=os.path.join(base_dir, "..", "static"),
    )

    app.config.from_object(Config)

    login_manager.init_app(app)

    from .routes.auth_routes import auth_bp
    from .routes.admin_routes import admin_bp
    from .routes.quiz_routes import quiz_bp
    from .routes.dashboard_routes import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(dashboard_bp)

    return app
