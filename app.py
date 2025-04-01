import json
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import base64
import uuid
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import reddit_api
import logging
import time
from flask_session import Session
from config import config

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

# Definir la carpeta para guardar las imágenes
UPLOAD_FOLDER = os.path.join('static', 'uploads', 'gallery')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Lista para almacenar los recuerdos (en producción usarías una base de datos)
MEMORIES_FILE = os.path.join('static', 'data', 'memories.json')
os.makedirs(os.path.dirname(MEMORIES_FILE), exist_ok=True)

# Función auxiliar para cargar recuerdos
def load_memories():
    try:
        if os.path.exists(MEMORIES_FILE):
            with open(MEMORIES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error al cargar recuerdos: {str(e)}")
        return []

# Función auxiliar para guardar recuerdos
def save_memories(memories):
    try:
        with open(MEMORIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error al guardar recuerdos: {str(e)}")
        return False

# Rutas principales
@app.route('/')
def index():
    return render_template('Index.html')

@app.route('/galeria')
def galeria():
    return render_template('Galeria.html')

@app.route('/reddit')
def reddit():
    error = request.args.get('error')
    success = request.args.get('success')
    return render_template('Reddit.html', error=error, success=success)

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre')
            email = request.form.get('email')
            asunto = request.form.get('asunto')
            mensaje = request.form.get('mensaje')
            newsletter = 'yes' if request.form.get('newsletter') else 'no'
            
            if not all([nombre, email, asunto, mensaje]):
                flash('Por favor completa todos los campos requeridos', 'error')
                return redirect(url_for('contacto'))
            
            logger.info(f"Nuevo contacto de {nombre} ({email}): {asunto}")
            flash('¡Gracias por tu mensaje! Te responderemos lo antes posible.', 'success')
            return redirect(url_for('contacto'))
        except Exception as e:
            logger.error(f"Error al procesar formulario de contacto: {str(e)}")
            flash('Hubo un error al enviar tu mensaje. Por favor, intenta de nuevo más tarde.', 'error')
            return redirect(url_for('contacto'))
    
    return render_template('Contacto.html')

@app.route('/nosotros')
def nosotros():
    return render_template('Nosotros.html')

@app.route('/api/memories', methods=['GET'])
def get_memories():
    try:
        memories = load_memories()
        return jsonify({'success': True, 'memories': memories})
    except Exception as e:
        logger.error(f"Error al obtener recuerdos: {str(e)}")
        return jsonify({'success': False, 'error': 'Error al cargar los recuerdos'})

@app.route('/api/memories', methods=['POST'])
def add_memory():
    try:
        title = request.form.get('title')
        story = request.form.get('story')
        image_data = request.form.get('image')
        
        if not all([title, story, image_data]):
            return jsonify({'success': False, 'error': 'Datos incompletos'})
        
        if image_data.startswith('data:image'):
            format_info, base64_str = image_data.split('base64,')
            image_format = 'png'
            if 'jpeg' in format_info or 'jpg' in format_info:
                image_format = 'jpg'
            
            image_bytes = base64.b64decode(base64_str)
            image_filename = f"{uuid.uuid4().hex}.{image_format}"
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)
            
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
                
            image_url = f"/static/uploads/gallery/{image_filename}"
        else:
            return jsonify({'success': False, 'error': 'Formato de imagen no válido'})
        
        memory = {
            'id': str(uuid.uuid4()),
            'title': title,
            'story': story,
            'imageUrl': image_url,
            'date': datetime.now().strftime('%d de %B, %Y')
        }
        
        memories = load_memories()
        memories.append(memory)
        
        if save_memories(memories):
            return jsonify({'success': True, 'memory': memory})
        else:
            return jsonify({'success': False, 'error': 'Error al guardar el recuerdo'})
        
    except Exception as e:
        logger.error(f"Error al añadir recuerdo: {str(e)}")
        return jsonify({'success': False, 'error': f'Error interno: {str(e)}'})

# Rutas para la API de Reddit
@app.route('/api/reddit/auth-url')
def get_reddit_auth_url():
    try:
        auth_url = reddit_api.get_auth_url()
        return jsonify({'success': True, 'auth_url': auth_url})
    except Exception as e:
        logger.error(f"Error al generar URL de autenticación: {str(e)}")
        return jsonify({'success': False, 'error': 'Error al generar URL de autenticación'})

@app.route('/reddit-callback')
def reddit_callback():
    error = request.args.get('error')
    if error:
        logger.warning(f"Error en callback de Reddit: {error}")
        return redirect(url_for('reddit', error=error))
    
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        return redirect(url_for('reddit', error='no_code'))
    
    token_data = reddit_api.exchange_code_for_token(code, state)
    if not token_data:
        return redirect(url_for('reddit', error='token_exchange_failed'))
    
    return redirect(url_for('reddit', success='authenticated'))

@app.route('/api/reddit/user')
def get_reddit_user():
    access_token = session.get('reddit_access_token')
    token_expiry = session.get('reddit_token_expiry')
    
    if token_expiry and float(token_expiry) < time.time():
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
    if not session.get('reddit_access_token'):
        return jsonify({'success': False, 'error': 'No estás autenticado'})
    
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'Datos no válidos'})
        
        subreddit = data.get('subreddit')
        title = data.get('title')
        post_type = data.get('type')
        
        if not subreddit or not title or not post_type:
            return jsonify({'success': False, 'error': 'Faltan campos requeridos'})
        
        kind = 'self'
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
    if not app.config.get('REDDIT_CLIENT_ID') or not app.config.get('REDDIT_CLIENT_SECRET'):
        logger.warning("⚠️ Faltan credenciales de Reddit en el archivo .env")
        print("⚠️ ADVERTENCIA: Faltan credenciales de Reddit en el archivo .env")
    
    app.run(debug=app.config['DEBUG'])
