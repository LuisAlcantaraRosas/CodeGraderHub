from flask import Flask, render_template, request, redirect, url_for, flash
import os
import subprocess

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.secret_key = 'your_secret_key'

# Asegurarse de que exista la carpeta de uploads
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_code', methods=['POST'])
def submit_code():
    if 'code_file' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for('index'))
    
    file = request.files['code_file']
    
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for('index'))

    if file:
        # Guardar el archivo
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        # Ejecutar el código de manera segura
        result = execute_code(file_path)
        
        # Evaluar el código
        score, feedback = evaluate_code(result)
        
        flash(f"Score: {score}, Feedback: {feedback}", "success")
        return redirect(url_for('index'))

def execute_code(file_path):
    try:
        result = subprocess.run(
            ['python', file_path], capture_output=True, text=True, timeout=5
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        return "Execution timed out"
    except Exception as e:
        return str(e)

def evaluate_code(output):
    expected_output = "Hello, World!"
    if output.strip() == expected_output:
        return 10, "Success"
    else:
        return 0, f"Expected '{expected_output}', but got '{output.strip()}'"

if __name__ == '__main__':
    app.run(debug=True)
