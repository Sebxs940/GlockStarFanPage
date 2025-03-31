import os
from dotenv import load_dotenv
import secrets

# Cargar variables de entorno desde .env
load_dotenv()

class Config:import os
from dotenv import load_dotenv
import secrets

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    # Configuración general de Flask
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
    DEBUG = os.environ.get('FLASK_DEBUG', 'False') == 'True'
    
    # Configuración de Reddit
    REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.environ.get('REDDIT_USER_AGENT', 'GlockStar Fanpage:v1.0')
    REDDIT_REDIRECT_URI = os.environ.get('REDDIT_REDIRECT_URI')
    
    # Configuración de sesión
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hora
    
    @staticmethod
    def init_app(app):
        # Verificar que las variables críticas estén definidas
        if not app.config.get('REDDIT_CLIENT_ID') or not app.config.get('REDDIT_CLIENT_SECRET'):
            app.logger.warning("⚠️ Faltan credenciales de Reddit en el archivo .env")

class DevelopmentConfig(Config):
    DEBUG = True
    # Configuración específica para desarrollo
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    # Configuración específica para producción
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

    # Configuración general de Flask
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
DEBUG = os.environ.get('FLASK_DEBUG', 'False') == 'True'
    
    # Configuración de Reddit
REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.environ.get('REDDIT_USER_AGENT', 'GlockStar Fanpage:v1.0')
REDDIT_REDIRECT_URI = os.environ.get('REDDIT_REDIRECT_URI')
    
    # Configuración de sesión
SESSION_TYPE = 'filesystem'
SESSION_PERMANENT = False
PERMANENT_SESSION_LIFETIME = 3600  # 1 hora
    
@staticmethod
def init_app(app):
        # Verificar que las variables críticas estén definidas
        if not app.config.get('REDDIT_CLIENT_ID') or not app.config.get('REDDIT_CLIENT_SECRET'):
            app.logger.warning("⚠️ Faltan credenciales de Reddit en el archivo .env")

class DevelopmentConfig(Config):
    DEBUG = True
    # Configuración específica para desarrollo
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    # Configuración específica para producción
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
