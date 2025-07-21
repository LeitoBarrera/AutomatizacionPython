from flask import Flask, request, send_file, render_template_string
import os
import uuid
import zipfile
import re
from consulta.contraloria import consultar_contraloria
from consulta.personeria import consultar_personeria
from consulta.policia_nacional import consultar_policia_nacional  # IMPORTA la función aquí

app = Flask(__name__)

def validar_fecha(fecha):
    # Valida dd/mm/aa o dd/mm/yyyy, admite años 2 o 4 dígitos
    patron = r'^\d{2}/\d{2}/(\d{2}|\d{4})$'
    return re.match(patron, fecha) is not None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        cedula = request.form.get('cedula')
        fecha_expedicion = request.form.get('fecha_expedicion')

        if not fecha_expedicion or not validar_fecha(fecha_expedicion):
            return "Error: Debe ingresar una fecha de expedición válida en formato dd/mm/aa o dd/mm/yyyy."

        uid = str(uuid.uuid4())
        folder = os.path.join('downloads', uid)
        os.makedirs(folder, exist_ok=True)

        archivos_pdf = []
        errores = []

        try:
            pdf_contraloria = consultar_contraloria(cedula, folder)
            archivos_pdf.append(pdf_contraloria)
        except Exception as e:
            errores.append(f"Contraloría: {str(e)}")

        try:
            pdf_personeria = consultar_personeria(cedula, fecha_expedicion, folder)
            archivos_pdf.append(pdf_personeria)
        except Exception as e:
            errores.append(f"Personería: {str(e)}")

        try:
            # Aquí se llama a la función de Policía Nacional
            pdf_policia = consultar_policia_nacional(cedula, folder)
            archivos_pdf.append(pdf_policia)
        except Exception as e:
            errores.append(f"Policía Nacional: {str(e)}")

        if not archivos_pdf:
            return "Error: No se pudieron obtener resultados de ninguna consulta.<br>" + "<br>".join(errores)

        zip_path = os.path.join(folder, f'antecedentes_{cedula}.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for pdf in archivos_pdf:
                zipf.write(pdf, os.path.basename(pdf))

        # Si hubo errores, incluir mensaje junto con la descarga
        if errores:
            return f"Advertencias:<br>{'<br>'.join(errores)}<br><br><a href='/{zip_path}'>Descargar ZIP</a>"
        else:
            return send_file(zip_path, as_attachment=True)

    return render_template_string('''
        <h2>Consulta Masiva de Antecedentes</h2>
        <form method="POST">
            <label>Documento:</label><br>
            <input type="text" name="cedula" required><br><br>

            <label>Fecha de expedición (dd/mm/aa):</label><br>
            <input type="text" name="fecha_expedicion" placeholder="dd/mm/aa" required><br><br>

            <button type="submit">Consultar y Descargar ZIP</button>
        </form>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
