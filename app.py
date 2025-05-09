from flask import Flask, render_template_string, request, redirect, send_from_directory
from PIL import Image, ImageDraw, ImageFont, ImageColor
import os
import json
import random
import string
from datetime import datetime

# Configuración de la aplicación
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/history_user'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB límite

# Crear directorios necesarios
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Archivo para contador de IDs
COUNTER_FILE = 'story_counter.json'

def get_next_id():
    """Genera ID autoincremental US-001, US-002, etc."""
    try:
        with open(COUNTER_FILE, 'r') as f:
            data = json.load(f)
            count = data.get('count', 0) + 1
    except (FileNotFoundError, json.JSONDecodeError):
        count = 1
    
    with open(COUNTER_FILE, 'w') as f:
        json.dump({'count': count}, f)
    
    return f"US-{count:03d}"

def generate_story_card(data):
    """Genera la imagen de la tarjeta con formato mejorado"""
    # 1. Configuración inicial
    img = Image.new('RGB', (800, 400), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    margin = 40
    y = 30
    
    # 2. Fuentes (Arial en Windows, fallback a default)
    try:
        font_title = ImageFont.truetype("arial.ttf", 24)
        font_label = ImageFont.truetype("arial.ttf", 18, encoding="unic")
        font_value = ImageFont.truetype("arial.ttf", 18, encoding="unic")
    except:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()
        font_value = ImageFont.load_default()
    
    # 3. Colores
    blue = ImageColor.getrgb('#0052a5')
    black = (0, 0, 0)
    dark_gray = (50, 50, 50)

    # 4. Encabezado
    draw.text((margin, y), f"{data['name']}    {data['id']}", fill=black, font=font_title)
    y += 50
    
    # 5. Línea divisoria
    draw.line((margin, y, 760, y), fill=blue, width=2)
    y += 30

    # 6. Función para texto en línea
    def draw_inline(label, value, y_pos, label_color=blue):
        draw.text((margin, y_pos), label, fill=label_color, font=font_label)
        text_width = font_label.getlength(label)
        draw.text((margin + text_width + 5, y_pos), value, fill=black, font=font_value)
        return y_pos + 40

    # 7. Contenido principal
    y = draw_inline("As: ", data.get('actor', ''), y)
    y = draw_inline("I want: ", data.get('action', ''), y)
    y = draw_inline("So that: ", data.get('achievement', ''), y)
    y += 10
    
    # 8. Criterios de aceptación
    draw.text((margin, y), "Acceptance criteria:", fill=blue, font=font_label)
    y += 30
    
    criteria = data.get('criteria', '').split('\n')
    if not criteria or criteria == ['']:
        draw.text((margin + 20, y), "• (Sin criterios definidos)", fill=dark_gray, font=font_value)
        y += 30
    else:
        for line in criteria:
            if line.strip():
                draw.text((margin + 20, y), f"• {line.strip()}", fill=black, font=font_value)
                y += 25
    y += 15
    
    # 9. Sección final
    y = draw_inline("Done when: ", data.get('done_when', ''), y)
    

    # 11. Guardar imagen
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{data['id']}_{timestamp}.png"
    img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    img.save(img_path, quality=95, optimize=True)
    
    return filename

@app.route('/')
def index():
    """Muestra el formulario principal"""
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Generador de Historias</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                    color: #333;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #0052a5;
                    margin-top: 0;
                }
                .form-group {
                    margin-bottom: 20px;
                }
                label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                    color: #0052a5;
                }
                input[type="text"], textarea {
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 16px;
                    box-sizing: border-box;
                }
                textarea {
                    min-height: 100px;
                    resize: vertical;
                }
                button {
                    background-color: #0052a5;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    font-size: 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    transition: background-color 0.3s;
                }
                button:hover {
                    background-color: #003d7a;
                }
                .nav {
                    margin-top: 20px;
                }
                .nav a {
                    color: #0052a5;
                    text-decoration: none;
                    margin-right: 15px;
                }
                .nav a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Generador de Historias de Usuario</h1>
                <form action="/generate" method="post">
                    <div class="form-group">
                        <label for="name">Nombre de la historia:</label>
                        <input type="text" id="name" name="name" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="actor">Actor (quién):</label>
                        <input type="text" id="actor" name="actor" required placeholder="Ej: Usuario registrado">
                    </div>
                    
                    <div class="form-group">
                        <label for="action">Acción (qué quiere hacer):</label>
                        <input type="text" id="action" name="action" required placeholder="Ej: Iniciar sesión">
                    </div>
                    
                    <div class="form-group">
                        <label for="achievement">Objetivo (para qué):</label>
                        <input type="text" id="achievement" name="achievement" required placeholder="Ej: Acceder al sistema">
                    </div>
                    
                    <div class="form-group">
                        <label for="criteria">Criterios de aceptación (uno por línea):</label>
                        <textarea id="criteria" name="criteria" placeholder="Ej: 
1. Validar email
2. Validar contraseña
3. Mostrar mensaje de error"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="done_when">Sé que está terminado cuando:</label>
                        <input type="text" id="done_when" name="done_when" placeholder="Ej: Todos los tests pasan">
                    </div>
                    
                    <button type="submit">Generar Tarjeta</button>
                </form>
                
                <div class="nav">
                    <a href="/history">Ver historial</a>
                    <a href="/test">Generar ejemplo</a>
                </div>
            </div>
        </body>
        </html>
    ''')

@app.route('/generate', methods=['POST'])
def generate():
    """Procesa el formulario y genera la tarjeta"""
    try:
        story_data = {
            'id': get_next_id(),
            'name': request.form['name'],
            'actor': request.form['actor'],
            'action': request.form['action'],
            'achievement': request.form['achievement'],
            'criteria': request.form.get('criteria', ''),
            'done_when': request.form.get('done_when', '')
        }
        
        filename = generate_story_card(story_data)
        return redirect(f'/static/history_user/{filename}')
    except Exception as e:
        return f"Error al generar la tarjeta: {str(e)}", 500

@app.route('/history')
def history():
    """Muestra el historial de tarjetas generadas"""
    try:
        files = sorted(
            [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.png')],
            key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)),
            reverse=True
        )
        
        return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Historial</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {
                        font-family: 'Segoe UI', Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        background: white;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }
                    h1 {
                        color: #0052a5;
                        margin-top: 0;
                    }
                    .card-list {
                        display: grid;
                        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                        gap: 20px;
                    }
                    .card-item {
                        border: 1px solid #ddd;
                        padding: 15px;
                        border-radius: 5px;
                        background: white;
                    }
                    .card-item img {
                        max-width: 100%;
                        height: auto;
                        border: 1px solid #eee;
                    }
                    .card-info {
                        margin-top: 10px;
                        font-size: 14px;
                        color: #666;
                    }
                    .back-link {
                        display: inline-block;
                        margin-top: 20px;
                        color: #0052a5;
                        text-decoration: none;
                    }
                    .back-link:hover {
                        text-decoration: underline;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Historial de Tarjetas Generadas</h1>
                    <div class="card-list">
                        {% for file in files %}
                            <div class="card-item">
                                <a href="/static/history_user/{{ file }}" target="_blank">
                                    <img src="/static/history_user/{{ file }}" alt="Story Card">
                                </a>
                                <div class="card-info">
                                    {{ file.split('_')[0] }} - 
                                    {{ file.split('_')[1].split('.')[0] }}
                                </div>
                            </div>
                        {% endfor %}
                    </div>
                    <a href="/" class="back-link">← Volver al generador</a>
                </div>
            </body>
            </html>
        ''', files=files)
    except Exception as e:
        return f"Error al leer el historial: {str(e)}", 500

@app.route('/test')
def test():
    """Genera una tarjeta de ejemplo"""
    example_data = {
        'name': 'Ejemplo: Login de usuario',
        'actor': 'Usuario registrado',
        'action': 'iniciar sesión en el sistema',
        'achievement': 'acceder a mi panel personal',
        'criteria': '1. Validar formato de email\n2. Verificar contraseña\n3. Mostrar mensaje de error si falla',
        'done_when': 'todos los tests de aceptación pasan'
    }
    example_data['id'] = get_next_id()
    
    try:
        filename = generate_story_card(example_data)
        return redirect(f'/static/history_user/{filename}')
    except Exception as e:
        return f"Error al generar ejemplo: {str(e)}", 500

@app.route('/static/history_user/<filename>')
def serve_image(filename):
    """Sirve las imágenes desde el directorio history_user"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)