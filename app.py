from flask import Flask, request, send_file, render_template_string
import os
import uuid
import zipfile
import re
from consulta.contraloria import consultar_contraloria
from consulta.personeria import consultar_personeria
from consulta.runt import consultar_runt
from consulta.simit import consultar_simit  # ← Agregado

app = Flask(__name__)

def validar_fecha(fecha):
    patron = r'^\d{2}/\d{2}/(\d{2}|\d{4})$'
    return re.match(patron, fecha) is not None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        cedula = request.form.get('cedula')
        fecha_expedicion = request.form.get('fecha_expedicion')
        placa = request.form.get('placa')

        if not fecha_expedicion or not validar_fecha(fecha_expedicion):
            return "Error: Debe ingresar una fecha de expedición válida en formato dd/mm/aa o dd/mm/yyyy."
        if not placa:
            return "Error: Debe ingresar una placa válida para la consulta en el RUNT y SIMIT."

        uid = str(uuid.uuid4()) 
        folder = os.path.join('downloads', uid)
        os.makedirs(folder, exist_ok=True)

        archivos = []
        errores = []

        try:
            archivos.append(consultar_contraloria(cedula, folder))
        except Exception as e:
            errores.append(f"Contraloría: {str(e)}")

        try:
            archivos.append(consultar_personeria(cedula, fecha_expedicion, folder))
        except Exception as e:
            errores.append(f"Personería: {str(e)}")

        try:
            resultado_runt = consultar_runt(placa, cedula, "C", folder)
            archivos.append(resultado_runt)
        except Exception as e:
            errores.append(f"RUNT: {str(e)}")

        try:
            archivos.append(consultar_simit(placa, folder))
        except Exception as e:
            errores.append(f"SIMIT: {str(e)}")

        if not archivos:
            return "Error: No se pudieron obtener resultados de ninguna consulta.<br>" + "<br>".join(errores)

        zip_path = os.path.join(folder, f'antecedentes_{cedula}.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for archivo in archivos:
                zipf.write(archivo, os.path.basename(archivo))

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

            <label>Placa del vehículo (para RUNT y SIMIT):</label><br>
            <input type="text" name="placa" required><br><br>

            <button type="submit">Consultar y Descargar ZIP</button>
        </form>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
