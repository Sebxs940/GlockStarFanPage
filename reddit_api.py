import requests
import json
import time
import logging
from flask import current_app, session, abort
from functools import wraps

# Configurar logging
logger = logging.getLogger(__name__)

def token_required(f):
    """Decorador para verificar que existe un token válido"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = session.get('reddit_access_token')
        token_expiry = session.get('reddit_token_expiry')
        
        # Verificar si el token existe y no ha expirado
        if not access_token or (token_expiry and time.time() > token_expiry):
            # Intentar refrescar el token si hay un refresh_token
            if session.get('reddit_refresh_token'):
                refresh_result = refresh_access_token()
                if not refresh_result.get('success'):
                    return {'success': False, 'error': 'Sesión expirada'}
            else:
                return {'success': False, 'error': 'No estás autenticado'}
        
        return f(*args, **kwargs)
    return decorated_function

def get_auth_url():
    """Genera la URL para la autenticación OAuth de Reddit"""
    client_id = current_app.config['REDDIT_CLIENT_ID']
    redirect_uri = current_app.config['REDDIT_REDIRECT_URI']
    scope = 'identity edit submit read'
    state = generate_state_token()
    
    # Guardar el state token en la sesión para verificarlo después
    session['reddit_state'] = state
    
    auth_url = (
        f"https://www.reddit.com/api/v1/authorize"
        f"?client_id={client_id}"
        f"&response_type=code"
        f"&state={state}"
        f"&redirect_uri={redirect_uri}"
        f"&duration=permanent"
        f"&scope={scope}"
    )
    
    return auth_url

def generate_state_token():
    """Genera un token aleatorio para el parámetro state"""
    import secrets
    return secrets.token_urlsafe(32)

def verify_state_token(state):
    """Verifica que el token state coincida con el almacenado"""
    stored_state = session.pop('reddit_state', None)
    return stored_state and stored_state == state

def exchange_code_for_token(code, state=None):
    """Intercambia el código de autorización por un token de acceso"""
    # Verificar el state token si se proporciona
    if state and not verify_state_token(state):
        logger.warning("Posible ataque CSRF: state token no coincide")
        return None
    
    client_id = current_app.config['REDDIT_CLIENT_ID']
    client_secret = current_app.config['REDDIT_CLIENT_SECRET']
    redirect_uri = current_app.config['REDDIT_REDIRECT_URI']
    
    if not client_id or not client_secret:
        logger.error("Faltan credenciales de Reddit")
        return None
    
    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }
    
    headers = {
        'User-Agent': current_app.config['REDDIT_USER_AGENT']
    }
    
    try:
        response = requests.post(
            'https://www.reddit.com/api/v1/access_token',
            auth=auth,
            data=data,
            headers=headers
        )
        
        response.raise_for_status()
        token_data = response.json()
        
        # Guardar tokens en la sesión
        session['reddit_access_token'] = token_data.get('access_token')
        session['reddit_refresh_token'] = token_data.get('refresh_token')
        
        # Calcular tiempo de expiración absoluto
        expires_in = token_data.get('expires_in', 3600)
        session['reddit_token_expiry'] = time.time() + expires_in
        
        # Obtener información del usuario
        user_info = get_user_info(token_data.get('access_token'))
        if user_info:
            session['reddit_username'] = user_info.get('name')
        
        return token_data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al intercambiar código por token: {str(e)}")
        return None

def refresh_access_token():
    """Renueva el token de acceso usando el refresh token"""
    refresh_token = session.get('reddit_refresh_token')
    
    if not refresh_token:
        return {'success': False, 'error': 'No hay refresh token'}
    
    client_id = current_app.config['REDDIT_CLIENT_ID']
    client_secret = current_app.config['REDDIT_CLIENT_SECRET']
    
    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    
    headers = {
        'User-Agent': current_app.config['REDDIT_USER_AGENT']
    }
    
    try:
        response = requests.post(
            'https://www.reddit.com/api/v1/access_token',
            auth=auth,
            data=data,
            headers=headers
        )
        
        response.raise_for_status()
        token_data = response.json()
        
        # Actualizar tokens en la sesión
        session['reddit_access_token'] = token_data.get('access_token')
        
        # Calcular tiempo de expiración absoluto
        expires_in = token_data.get('expires_in', 3600)
        session['reddit_token_expiry'] = time.time() + expires_in
        
        return {'success': True}
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al refrescar token: {str(e)}")
        # Limpiar la sesión si hay un error
        session.pop('reddit_access_token', None)
        session.pop('reddit_refresh_token', None)
        session.pop('reddit_token_expiry', None)
        session.pop('reddit_username', None)
        return {'success': False, 'error': str(e)}

def get_user_info(access_token=None):
    """Obtiene información del usuario autenticado"""
    if not access_token:
        access_token = session.get('reddit_access_token')
        
    if not access_token:
        return None
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': current_app.config['REDDIT_USER_AGENT']
    }
    
    try:
        response = requests.get(
            'https://oauth.reddit.com/api/v1/me',
            headers=headers
        )
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al obtener información del usuario: {str(e)}")
        return None

def get_subreddit_posts(subreddit, limit=10):
    """Obtiene las publicaciones recientes de un subreddit"""
    # Sanitizar el nombre del subreddit
    subreddit = subreddit.strip().lower()
    if not subreddit or not subreddit.isalnum():
        return None
    
    url = f'https://www.reddit.com/r/{subreddit}/new.json?limit={limit}'
    
    headers = {
        'User-Agent': current_app.config['REDDIT_USER_AGENT']
    }
    
    # Si hay un token de acceso, usarlo para obtener más información
    access_token = session.get('reddit_access_token')
    if access_token:
        url = f'https://oauth.reddit.com/r/{subreddit}/new?limit={limit}'
        headers['Authorization'] = f'Bearer {access_token}'
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al obtener publicaciones de r/{subreddit}: {str(e)}")
        return None

@token_required
def submit_post(subreddit, title, kind, content=None, url=None):
    """Envía una publicación a Reddit"""
    access_token = session.get('reddit_access_token')
    
    # Validar parámetros
    if not subreddit or not title:
        return {'success': False, 'error': 'Faltan parámetros requeridos'}
    
    # Sanitizar el subreddit
    subreddit = subreddit.strip()
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': current_app.config['REDDIT_USER_AGENT']
    }
    
    data = {
        'sr': subreddit,
        'title': title,
        'kind': kind
    }
    
    if kind == 'self' and content:
        data['text'] = content
    elif kind == 'link' and url:
        data['url'] = url
    else:
        return {'success': False, 'error': 'Tipo de publicación no válido o faltan datos'}
    
    try:
        response = requests.post(
            'https://oauth.reddit.com/api/submit',
            headers=headers,
            data=data
        )
        
        # Verificar si la respuesta es exitosa
        if response.status_code == 200:
            try:
                response_data = response.json()
                # Verificar si hay errores en la respuesta
                if 'json' in response_data and 'errors' in response_data['json'] and response_data['json']['errors']:
                    errors = response_data['json']['errors']
                    error_msg = ', '.join([f"{e[0]}: {e[1]}" for e in errors])
                    return {'success': False, 'error': error_msg}
                
                return {'success': True, 'data': response_data}
            except ValueError:
                return {'success': True}
        else:
            logger.error(f"Error al publicar en Reddit: {response.status_code} - {response.text}")
            return {'success': False, 'error': f"Error {response.status_code}: {response.text}"}
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión al publicar en Reddit: {str(e)}")
        return {'success': False, 'error': 'Error de conexión'}
import requests
import json
import time
import logging
from flask import current_app, session, abort
from functools import wraps

# Configurar logging
logger = logging.getLogger(__name__)

def token_required(f):
    """Decorador para verificar que existe un token válido"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = session.get('reddit_access_token')
        token_expiry = session.get('reddit_token_expiry')
        
        # Verificar si el token existe y no ha expirado
        if not access_token or (token_expiry and time.time() > token_expiry):
            # Intentar refrescar el token si hay un refresh_token
            if session.get('reddit_refresh_token'):
                refresh_result = refresh_access_token()
                if not refresh_result.get('success'):
                    return {'success': False, 'error': 'Sesión expirada'}
            else:
                return {'success': False, 'error': 'No estás autenticado'}
        
        return f(*args, **kwargs)
    return decorated_function

def get_auth_url():
    """Genera la URL para la autenticación OAuth de Reddit"""
    client_id = current_app.config['REDDIT_CLIENT_ID']
    redirect_uri = current_app.config['REDDIT_REDIRECT_URI']
    scope = 'identity edit submit read'
    state = generate_state_token()
    
    # Guardar el state token en la sesión para verificarlo después
    session['reddit_state'] = state
    
    auth_url = (
        f"https://www.reddit.com/api/v1/authorize"
        f"?client_id={client_id}"
        f"&response_type=code"
        f"&state={state}"
        f"&redirect_uri={redirect_uri}"
        f"&duration=permanent"
        f"&scope={scope}"
    )
    
    return auth_url

def generate_state_token():
    """Genera un token aleatorio para el parámetro state"""
    import secrets
    return secrets.token_urlsafe(32)

def verify_state_token(state):
    """Verifica que el token state coincida con el almacenado"""
    stored_state = session.pop('reddit_state', None)
    return stored_state and stored_state == state

def exchange_code_for_token(code, state=None):
    """Intercambia el código de autorización por un token de acceso"""
    # Verificar el state token si se proporciona
    if state and not verify_state_token(state):
        logger.warning("Posible ataque CSRF: state token no coincide")
        return None
    
    client_id = current_app.config['REDDIT_CLIENT_ID']
    client_secret = current_app.config['REDDIT_CLIENT_SECRET']
    redirect_uri = current_app.config['REDDIT_REDIRECT_URI']
    
    if not client_id or not client_secret:
        logger.error("Faltan credenciales de Reddit")
        return None
    
    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }
    
    headers = {
        'User-Agent': current_app.config['REDDIT_USER_AGENT']
    }
    
    try:
        response = requests.post(
            'https://www.reddit.com/api/v1/access_token',
            auth=auth,
            data=data,
            headers=headers
        )
        
        response.raise_for_status()
        token_data = response.json()
        
        # Guardar tokens en la sesión
        session['reddit_access_token'] = token_data.get('access_token')
        session['reddit_refresh_token'] = token_data.get('refresh_token')
        
        # Calcular tiempo de expiración absoluto
        expires_in = token_data.get('expires_in', 3600)
        session['reddit_token_expiry'] = time.time() + expires_in
        
        # Obtener información del usuario
        user_info = get_user_info(token_data.get('access_token'))
        if user_info:
            session['reddit_username'] = user_info.get('name')
        
        return token_data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al intercambiar código por token: {str(e)}")
        return None

def refresh_access_token():
    """Renueva el token de acceso usando el refresh token"""
    refresh_token = session.get('reddit_refresh_token')
    
    if not refresh_token:
        return {'success': False, 'error': 'No hay refresh token'}
    
    client_id = current_app.config['REDDIT_CLIENT_ID']
    client_secret = current_app.config['REDDIT_CLIENT_SECRET']
    
    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    
    headers = {
        'User-Agent': current_app.config['REDDIT_USER_AGENT']
    }
    
    try:
        response = requests.post(
            'https://www.reddit.com/api/v1/access_token',
            auth=auth,
            data=data,
            headers=headers
        )
        
        response.raise_for_status()
        token_data = response.json()
        
        # Actualizar tokens en la sesión
        session['reddit_access_token'] = token_data.get('access_token')
        
        # Calcular tiempo de expiración absoluto
        expires_in = token_data.get('expires_in', 3600)
        session['reddit_token_expiry'] = time.time() + expires_in
        
        return {'success': True}
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al refrescar token: {str(e)}")
        # Limpiar la sesión si hay un error
        session.pop('reddit_access_token', None)
        session.pop('reddit_refresh_token', None)
        session.pop('reddit_token_expiry', None)
        session.pop('reddit_username', None)
        return {'success': False, 'error': str(e)}

def get_user_info(access_token=None):
    """Obtiene información del usuario autenticado"""
    if not access_token:
        access_token = session.get('reddit_access_token')
        
    if not access_token:
        return None
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': current_app.config['REDDIT_USER_AGENT']
    }
    
    try:
        response = requests.get(
            'https://oauth.reddit.com/api/v1/me',
            headers=headers
        )
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al obtener información del usuario: {str(e)}")
        return None

def get_subreddit_posts(subreddit, limit=10):
    """Obtiene las publicaciones recientes de un subreddit"""
    # Sanitizar el nombre del subreddit
    subreddit = subreddit.strip().lower()
    if not subreddit or not subreddit.isalnum():
        return None
    
    url = f'https://www.reddit.com/r/{subreddit}/new.json?limit={limit}'
    
    headers = {
        'User-Agent': current_app.config['REDDIT_USER_AGENT']
    }
    
    # Si hay un token de acceso, usarlo para obtener más información
    access_token = session.get('reddit_access_token')
    if access_token:
        url = f'https://oauth.reddit.com/r/{subreddit}/new?limit={limit}'
        headers['Authorization'] = f'Bearer {access_token}'
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al obtener publicaciones de r/{subreddit}: {str(e)}")
        return None

@token_required
def submit_post(subreddit, title, kind, content=None, url=None):
    """Envía una publicación a Reddit"""
    access_token = session.get('reddit_access_token')
    
    # Validar parámetros
    if not subreddit or not title:
        return {'success': False, 'error': 'Faltan parámetros requeridos'}
    
    # Sanitizar el subreddit
    subreddit = subreddit.strip()
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': current_app.config['REDDIT_USER_AGENT']
    }
    
    data = {
        'sr': subreddit,
        'title': title,
        'kind': kind
    }
    
    if kind == 'self' and content:
        data['text'] = content
    elif kind == 'link' and url:
        data['url'] = url
    else:
        return {'success': False, 'error': 'Tipo de publicación no válido o faltan datos'}
    
    try:
        response = requests.post(
            'https://oauth.reddit.com/api/submit',
            headers=headers,
            data=data
        )
        
        # Verificar si la respuesta es exitosa
        if response.status_code == 200:
            try:
                response_data = response.json()
                # Verificar si hay errores en la respuesta
                if 'json' in response_data and 'errors' in response_data['json'] and response_data['json']['errors']:
                    errors = response_data['json']['errors']
                    error_msg = ', '.join([f"{e[0]}: {e[1]}" for e in errors])
                    return {'success': False, 'error': error_msg}
                
                return {'success': True, 'data': response_data}
            except ValueError:
                return {'success': True}
        else:
            logger.error(f"Error al publicar en Reddit: {response.status_code} - {response.text}")
            return {'success': False, 'error': f"Error {response.status_code}: {response.text}"}
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión al publicar en Reddit: {str(e)}")
        return {'success': False, 'error': 'Error de conexión'}
