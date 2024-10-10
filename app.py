from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import pandas as pd
import subprocess

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = './uploads'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Cargar usuarios desde el CSV usando pandas
def cargar_usuarios_csv():
    df = pd.read_csv('usuarios.csv', dtype={'matricula': str})
    return df

usuarios = cargar_usuarios_csv()

# Función para obtener el nombre del usuario a partir de su matrícula
def obtener_nombre_usuario(matricula):
    # Filtrar el DataFrame por la matrícula
    usuario_filtro = usuarios[usuarios['matricula'] == matricula]
    
    # Si existe un resultado, devolver el nombre
    if not usuario_filtro.empty:
        return usuario_filtro.iloc[0]['nombre']
    return None

# Modelo de Usuario temporal
class User(UserMixin):
    def __init__(self, matricula, nombre, apellido_paterno, apellido_materno):
        self.id = matricula
        self.nombre = nombre
        self.apellido_paterno = apellido_paterno
        self.apellido_materno = apellido_materno

@login_manager.user_loader
def load_user(user_id):
    # Asegúrate de que user_id existe en los valores de la columna 'matricula'
    if user_id in usuarios['matricula'].values:
        usuario_filtro = usuarios[usuarios['matricula'] == user_id].iloc[0]
        return User(usuario_filtro['matricula'], usuario_filtro['nombre'], usuario_filtro['apellido_paterno'], usuario_filtro['apellido_materno'])
    return None




@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    matricula = current_user.id  # Puedes recibir la matrícula como argumento en la URL
    nombre_usuario = obtener_nombre_usuario(matricula)
    
    if nombre_usuario:
        saludo = f"Hola {nombre_usuario}, sube tu código para evaluación"
    else:
        saludo = "Sube tu código para evaluación"
    
    return render_template('index.html', saludo=saludo)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        matricula = request.form['matricula']
        
        # Verificar si la matrícula está en el DataFrame
        usuario_filtro = usuarios[usuarios['matricula'] == matricula]
        
        if not usuario_filtro.empty:
            user_data = usuario_filtro.iloc[0]
            user = User(matricula, user_data['nombre'], user_data['apellido_paterno'], user_data['apellido_materno'])
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Matrícula no encontrada. Por favor, contacta al administrador.", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión correctamente.", "success")
    return redirect(url_for('login'))


# Asegurarse de que exista la carpeta de uploads
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Ruta para subir código y evaluarlo
@app.route('/submit_code', methods=['POST'])
@login_required
def submit_code():
    if 'code_file' not in request.files:
        flash("No se ha subido ningún archivo", "danger")
        return redirect(url_for('index'))
    
    file = request.files['code_file']
    
    if file.filename == '':
        flash("No se ha seleccionado ningún archivo", "danger")
        return redirect(url_for('index'))

    if file:
        # Guardar el archivo en la carpeta 'uploads'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        # Ejecutar el código de manera segura y obtener el resultado
        result = execute_code(file_path)
        
        # Evaluar el código en función del resultado obtenido
        score, feedback = evaluate_code(result)
        
        flash(f"Calificación: {score}, Comentarios: {feedback}", "success")
        return redirect(url_for('index'))

# Función para ejecutar el código de manera segura
def execute_code(file_path):
    try:
        # Usar subprocess para ejecutar el código y capturar la salida
        result = subprocess.run(
            ['python', file_path], capture_output=True, text=True, timeout=5
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        return "El tiempo de ejecución ha expirado"
    except Exception as e:
        return f"Error en la ejecución: {str(e)}"

# Función para evaluar el código
def evaluate_code(output):
    expected_output = "Hello, World!"  # La salida esperada para este ejemplo
    if output.strip() == expected_output:
        return 10, "¡Éxito! El código generó la salida esperada."
    else:
        return 0, f"Error: se esperaba '{expected_output}', pero se obtuvo '{output.strip()}'"

if __name__ == '__main__':
    app.run(debug=True)
