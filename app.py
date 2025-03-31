from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from config import config
import reddit_api
import os
import logging
import time
from flask_session import Session

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear la aplicación Flask
app = Flask(__name__)

# Cargar configuración
config_name = os.environ.get('FLASK_CONFIG', 'default')
app.config.from_object(config[config_name])
config[config_name].init_app(app)

# Configurar sesión del lado del servidor
Session(app)

# Rutas principales
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/galeria')
def galeria():
    return render_template('galeria.html')

@app.route('/reddit')
def reddit():
    # Verificar si hay mensajes de error o éxito en los parámetros
    error = request.args.get('error')
    success = request.args.get('success')
    
    return render_template('reddit.html', error=error, success=success)

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    """Maneja la página de contacto y el envío del formulario"""
    # Si es una solicitud POST, procesar el formulario
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.form.get('nombre')
            email = request.form.get('email')
            asunto = request.form.get('asunto')
            mensaje = request.form.get('mensaje')
            newsletter = 'yes' if request.form.get('newsletter') else 'no'
            
            # Validar datos
            if not all([nombre, email, asunto, mensaje]):
                flash('Por favor completa todos los campos requeridos', 'error')
                return redirect(url_for('contacto'))
            
            # Aquí puedes añadir código para guardar en una base de datos o enviar email
            # Por ahora, solo registramos el contacto
            logger.info(f"Nuevo contacto de {nombre} ({email}): {asunto}")
            
            # Mensaje de éxito
            flash('¡Gracias por tu mensaje! Te responderemos lo antes posible.', 'success')
            return redirect(url_for('contacto'))
            
        except Exception as e:
            logger.error(f"Error al procesar formulario de contacto: {str(e)}")
            flash('Hubo un error al enviar tu mensaje. Por favor, intenta de nuevo más tarde.', 'error')
            return redirect(url_for('contacto'))
    
    # Si es una solicitud GET, mostrar la página de contacto
    return render_template('contacto.html')

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

# Rutas para la API de Reddit
@app.route('/api/reddit/auth-url')
def get_reddit_auth_url():
    """Devuelve la URL para autenticación de Reddit"""
    try:
        auth_url = reddit_api.get_auth_url()
        return jsonify({'success': True, 'auth_url': auth_url})
    except Exception as e:
        logger.error(f"Error al generar URL de autenticación: {str(e)}")
        return jsonify({'success': False, 'error': 'Error al generar URL de autenticación'})

@app.route('/reddit-callback')
def reddit_callback():
    """Maneja la redirección después de la autenticación de Reddit"""
    error = request.args.get('error')
    if error:
        logger.warning(f"Error en callback de Reddit: {error}")
        return redirect(url_for('reddit', error=error))
    
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        return redirect(url_for('reddit', error='no_code'))
    
    # Intercambiar código por token
    token_data = reddit_api.exchange_code_for_token(code, state)
    if not token_data:
        return redirect(url_for('reddit', error='token_exchange_failed'))
    
    return redirect(url_for('reddit', success='authenticated'))

@app.route('/api/reddit/user')
def get_reddit_user():
    """Devuelve información del usuario autenticado"""
    access_token = session.get('reddit_access_token')
    token_expiry = session.get('reddit_token_expiry')
    
    # Verificar si el token ha expirado
    if token_expiry and float(token_expiry) < time.time():
        # Intentar refrescar el token
        if session.get('reddit_refresh_token'):
            refresh_result = reddit_api.refresh_access_token()
            if not refresh_result.get('success'):
                return jsonify({'authenticated': False, 'error': 'Sesión expirada'})
        else:
            return jsonify({'authenticated': False})
    
    if not access_token:
        return jsonify({'authenticated': False})
    
    username = session.get('reddit_username')
    return jsonify({
        'authenticated': True,
        'username': username
    })

@app.route('/api/reddit/posts/<subreddit>')
def get_reddit_posts(subreddit):
    """Obtiene publicaciones de un subreddit"""
    try:
        posts_data = reddit_api.get_subreddit_posts(subreddit)
        if not posts_data:
            return jsonify({'success': False, 'error': 'Error al obtener publicaciones'})
        
        return jsonify({'success': True, 'data': posts_data})
    except Exception as e:
        logger.error(f"Error al obtener publicaciones: {str(e)}")
        return jsonify({'success': False, 'error': 'Error interno del servidor'})

@app.route('/api/reddit/submit', methods=['POST'])
def submit_reddit_post():
    """Envía una publicación a Reddit"""
    if not session.get('reddit_access_token'):
        return jsonify({'success': False, 'error': 'No estás autenticado'})
    
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'Datos no válidos'})
        
        subreddit = data.get('subreddit')
        title = data.get('title')
        post_type = data.get('type')
        
        # Validar campos requeridos
        if not subreddit or not title or not post_type:
            return jsonify({'success': False, 'error': 'Faltan campos requeridos'})
        
        kind = 'self'  # Por defecto, publicación de texto
        content = None
        url = None
        
        if post_type == 'text':
            kind = 'self'
            content = data.get('content')
        elif post_type == 'link':
            kind = 'link'
            url = data.get('url')
            if not url:
                return jsonify({'success': False, 'error': 'URL requerida para publicaciones de tipo enlace'})
        else:
            return jsonify({'success': False, 'error': 'Tipo de publicación no válido'})
        
        result = reddit_api.submit_post(subreddit, title, kind, content, url)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error al enviar publicación: {str(e)}")
        return jsonify({'success': False, 'error': 'Error interno del servidor'})

@app.route('/api/reddit/logout', methods=['POST'])
def logout_reddit():
    """Cierra la sesión de Reddit"""
    try:
        session.pop('reddit_access_token', None)
        session.pop('reddit_refresh_token', None)
        session.pop('reddit_token_expiry', None)
        session.pop('reddit_username', None)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error al cerrar sesión: {str(e)}")
        return jsonify({'success': False, 'error': 'Error al cerrar sesión'})

# Manejador de errores
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"Error 500: {str(e)}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Verificar que las variables de entorno necesarias estén configuradas
    if not app.config.get('REDDIT_CLIENT_ID') or not app.config.get('REDDIT_CLIENT_SECRET'):
        logger.warning("⚠️ Faltan credenciales de Reddit en el archivo .env")
        print("⚠️ ADVERTENCIA: Faltan credenciales de Reddit en el archivo .env")
    
    app.run(debug=app.config['DEBUG'])
