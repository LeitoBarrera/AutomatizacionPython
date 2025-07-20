from flask import Flask, request, send_file
import os
import uuid
from consulta import contraloria

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        cedula = request.form.get('cedula')
        uid = str(uuid.uuid4())
        folder = os.path.join('downloads', uid)
        os.makedirs(folder, exist_ok=True)

        try:
            pdf_path = contraloria.consultar_contraloria(cedula, folder)
        except Exception as e:
            return f"Error: {str(e)}"

        return send_file(pdf_path, as_attachment=True)

    return '''
        <form method="POST">
            <label>Documento:</label>
            <input type="text" name="cedula" required>
            <button type="submit">Consultar Contraloría</button>
        </form>
    '''

if __name__ == '__main__':
    app.run(debug=True)
