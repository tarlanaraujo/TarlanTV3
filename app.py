import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.INFO) # Nível de log INFO é mais apropriado para produção

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
# É crucial que SESSION_SECRET seja uma variável de ambiente forte em produção!
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key_change_in_production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///iptv_manager.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to create tables
    import models  # noqa: F401
    db.create_all()

# Import and register routes
import routes  # noqa: F401

# --- Configuração de Execução (para produção e desenvolvimento) ---
if __name__ == '__main__':
    # Para desenvolvimento local, você ainda pode usar o modo debug
    # Mas em produção, o Gunicorn é quem vai iniciar a aplicação
    # O Railway (ou sua plataforma) injetará a variável de ambiente PORT.
    # O 'if __name__ == "__main__":' não será executado quando o Gunicorn for usado.

    # Abaixo, apenas para testar localmente com a porta do ambiente
    # ou com 5000 se a variável PORT não estiver definida.
    # Em produção, o Gunicorn usará 0.0.0.0:$PORT conforme o Procfile.
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False) # Removido debug=True para produção

