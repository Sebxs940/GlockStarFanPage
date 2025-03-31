// Elementos del DOM
const authButton = document.getElementById('auth-button');
const authStatus = document.getElementById('auth-status');
const authSection = document.getElementById('auth-section');
const postSection = document.getElementById('post-section');
const redditForm = document.getElementById('reddit-form');
const postTypeSelect = document.getElementById('post-type');
const textContentGroup = document.getElementById('text-content-group');
const linkContentGroup = document.getElementById('link-content-group');
const postsContainer = document.getElementById('posts-container');
const errorContainer = document.getElementById('error-container');

// Comprobar el estado de autenticación al cargar la página
function checkAuthStatus() {
    fetch('/api/reddit/user')
        .then(response => response.json())
        .then(data => {
            if (data.authenticated) {
                showAuthenticatedUI(data.username);
            } else {
                showUnauthenticatedUI();
            }
        })
        .catch(error => {
            console.error('Error al verificar autenticación:', error);
            showUnauthenticatedUI();
        });
}

// Mostrar UI para usuario autenticado
function showAuthenticatedUI(username) {
    authStatus.textContent = `Conectado como: ${username || 'Usuario de Reddit'}`;
    authButton.textContent = 'Cerrar sesión';
    authButton.removeEventListener('click', initiateRedditAuth);
    authButton.addEventListener('click', logoutFromReddit);
    postSection.style.display = 'flex';
    
    // Cargar publicaciones recientes
    fetchRedditPosts();
}

// Mostrar UI para usuario no autenticado
function showUnauthenticatedUI() {
    authStatus.textContent = 'No has iniciado sesión';
    authButton.innerHTML = '<i class="fab fa-reddit-alien"></i> Iniciar sesión con Reddit';
    authButton.removeEventListener('click', logoutFromReddit);
    authButton.addEventListener('click', initiateRedditAuth);
    postSection.style.display = 'none';
    
    // Mostrar publicaciones públicas
    fetchRedditPosts();
}

// Iniciar el proceso de autenticación de Reddit
function initiateRedditAuth() {
    fetch('/api/reddit/auth-url')
        .then(response => response.json())
        .then(data => {
            window.location.href = data.auth_url;
        })
        .catch(error => {
            console.error('Error al obtener URL de autenticación:', error);
            showError('Error al iniciar la autenticación');
        });
}

// Cerrar sesión de Reddit
function logoutFromReddit() {
    fetch('/api/reddit/logout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showUnauthenticatedUI();
        }
    })
    .catch(error => {
        console.error('Error al cerrar sesión:', error);
    });
}

// Obtener publicaciones recientes de Reddit
function fetchRedditPosts() {
    postsContainer.innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner"></i>
            <p>Cargando publicaciones...</p>
        </div>
    `;
    
    // Subreddit a consultar
    const subreddit = 'test'; // Puedes cambiarlo a 'GlockStar' o el que prefieras
    
    // Hacer la solicitud a la API
    fetch(`/api/reddit/posts/${subreddit}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayRedditPosts(data.data.data.children);
            } else {
                throw new Error(data.error || 'Error al obtener publicaciones');
            }
        })
        .catch(error => {
            postsContainer.innerHTML = `
                <div class="error-message">
                    <p>Error al cargar publicaciones: ${error.message}</p>
                </div>
                <div class="no-posts">
                    No se pudieron cargar las publicaciones. Intenta de nuevo más tarde.
                </div>
            `;
        });
}

// Mostrar las publicaciones en la interfaz
function displayRedditPosts(posts) {
    if (!posts || posts.length === 0) {
        postsContainer.innerHTML = `
            <div class="no-posts">
                No hay publicaciones recientes en este subreddit.
            </div>
        `;
        return;
    }
    
    postsContainer.innerHTML = '';
    
    posts.forEach(post => {
        const postData = post.data;
        const hasImage = postData.thumbnail && postData.thumbnail.startsWith('http');
        
        const postCard = document.createElement('div');
        postCard.className = 'post-card';
        
        postCard.innerHTML = `
            <div class="post-header">
                <span class="post-subreddit">r/${postData.subreddit}</span>
                <span class="post-author">Publicado por u/${postData.author}</span>
            </div>
            <h3 class="post-title">${postData.title}</h3>
            <div class="post-content">${postData.selftext ? formatRedditText(postData.selftext) : ''}</div>
            ${hasImage ? `<img src="${postData.thumbnail}" alt="Thumbnail" class="post-image">` : ''}
            ${postData.url && !hasImage && !postData.is_self ? `<a href="${postData.url}" target="_blank" rel="noopener noreferrer">${postData.url}</a>` : ''}
            <div class="post-footer">
                <div class="post-votes">
                    <i class="fas fa-arrow-up"></i> ${postData.ups}
                </div>
                <div class="post-comments">
                    <i class="fas fa-comment"></i> ${postData.num_comments} comentarios
                </div>
            </div>
        `;
        
        postsContainer.appendChild(postCard);
    });
}

// Formatear texto de Reddit (básico)
function formatRedditText(text) {
    if (!text) return '';
    
    // Convertir saltos de línea en <br>
    return text.replace(/\n/g, '<br>');
}

// Mostrar mensaje de error
function showError(message) {
    errorContainer.innerHTML = `
        <div class="error-message">
            <p>${message}</p>
        </div>
    `;
    
    // Ocultar el mensaje después de 5 segundos
    setTimeout(() => {
        errorContainer.innerHTML = '';
    }, 5000);
}

// Cambiar campos del formulario según el tipo de publicación
postTypeSelect.addEventListener('change', function() {
    const selectedType = this.value;
    
    // Ocultar todos los grupos
    textContentGroup.style.display = 'none';
    linkContentGroup.style.display = 'none';
    
    // Mostrar el grupo correspondiente
    if (selectedType === 'text') {
        textContentGroup.style.display = 'block';
    } else if (selectedType === 'link') {
        linkContentGroup.style.display = 'block';
    }
});

// Manejar el envío del formulario
redditForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const subreddit = document.getElementById('subreddit').value;
    const title = document.getElementById('post-title').value;
    const postType = document.getElementById('post-type').value;
    
    // Validar campos
    if (!subreddit || !title) {
        showError('Por favor completa todos los campos requeridos');
        return;
    }
    
    // Preparar datos según el tipo de publicación
    const postData = {
        subreddit: subreddit,
        title: title,
        type: postType
    };
    
    if (postType === 'text') {
        postData.content = document.getElementById('post-content').value;
    } else if (postType === 'link') {
        postData.url = document.getElementById('post-link').value;
    }
    
    // Mostrar mensaje de carga
    errorContainer.innerHTML = `
        <div class="loading" style="padding: 10px;">
            <i class="fas fa-spinner"></i>
            <span>Publicando en Reddit...</span>
        </div>
    `;
    
    // Enviar datos al servidor
    fetch('/api/reddit/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(postData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Limpiar el formulario
            redditForm.reset();
            postTypeSelect.dispatchEvent(new Event('change'));
            
            // Mostrar mensaje de éxito
            errorContainer.innerHTML = `
                <div class="error-message" style="background-color: rgba(75, 181, 67, 0.2); border-left-color: #4bb543; color: #4bb543;">
                    <p>¡Publicación creada con éxito! Tu post aparecerá pronto en r/${subreddit}.</p>
                </div>
            `;
            
            // Ocultar mensaje después de 5 segundos
            setTimeout(() => {
                errorContainer.innerHTML = '';
            }, 5000);
            
            // Recargar publicaciones
            fetchRedditPosts();
        } else {
            showError(data.error || 'Error al publicar');
        }
    })
    .catch(error => {
        console.error('Error al enviar publicación:', error);
        showError('Error al comunicarse con el servidor');
    });
});

// Inicializar la página
document.addEventListener('DOMContentLoaded', function() {
    // Comprobar estado de autenticación
    checkAuthStatus();
    
    // Configurar el selector de tipo de publicación
    postTypeSelect.dispatchEvent(new Event('change'));
    
    // Verificar si hay mensajes de error o éxito en la URL
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    const success = urlParams.get('success');
    
    if (error) {
        showError(`Error: ${error}`);
        // Limpiar parámetros de la URL
        window.history.replaceState({}, document.title, window.location.pathname);
    } else if (success === 'authenticated') {
        // Mostrar mensaje de éxito de autenticación
        errorContainer.innerHTML = `
            <div class="error-message" style="background-color: rgba(75, 181, 67, 0.2); border-left-color: #4bb543; color: #4bb543;">
                <p>¡Autenticación exitosa! Ahora puedes publicar en Reddit.</p>
            </div>
        `;
        
        // Ocultar mensaje después de 5 segundos
        setTimeout(() => {
            errorContainer.innerHTML = '';
        }, 5000);
        
        // Limpiar parámetros de la URL
        window.history.replaceState({}, document.title, window.location.pathname);
    }
});
