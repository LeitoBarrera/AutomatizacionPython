from flask import Flask, request, send_file, render_template_string, jsonify
import os
import uuid
import zipfile
import re
from consulta.contraloria import consultar_contraloria
from consulta.personeria import consultar_personeria
from consulta.runt import consultar_runt
from consulta.simit import consultar_simit
from consulta.registraduria import consultar_registraduria

app = Flask(__name__)

def validar_fecha(fecha):
    patron = r'^\d{2}/\d{2}/(\d{2}|\d{4})$'
    return re.match(patron, fecha) is not None

@app.route('/', methods=['GET'])
def index():
    return render_template_string('''
        <h2>Consulta Masiva de Antecedentes</h2>
        <form method="POST" action="/consultar" id="consulta-form">
            <label>Documento:</label><br>
            <input type="text" name="cedula" id="cedula" required><br><br>

            <button type="button" onclick="autocompletarDatos()">Autocompletar desde Registraduría</button><br><br>

            <label>Primer Apellido:</label><br>
            <input type="text" name="primer_apellido" id="primer_apellido"><br><br>

            <label>Segundo Apellido:</label><br>
            <input type="text" name="segundo_apellido" id="segundo_apellido"><br><br>

            <label>Primer Nombre:</label><br>
            <input type="text" name="primer_nombre" id="primer_nombre"><br><br>

            <label>Segundo Nombre:</label><br>
            <input type="text" name="segundo_nombre" id="segundo_nombre"><br><br>

            <label>Sexo:</label><br>
            <input type="text" name="sexo" id="sexo"><br><br>

            <label>Fecha de expedición (dd/mm/aa):</label><br>
            <input type="text" name="fecha_expedicion" placeholder="dd/mm/aa" required><br><br>

            <label>Placa del vehículo (para RUNT y SIMIT):</label><br>
            <input type="text" name="placa" required><br><br>

            <button type="submit">Consultar y Descargar ZIP</button>
        </form>

        <script>
        function autocompletarDatos() {
            const cedula = document.getElementById("cedula").value;
            if (!cedula) return alert("Por favor ingrese primero el documento.");

            fetch(`/autocompletar?cedula=${cedula}`)
                .then(resp => resp.json())
                .then(data => {
                    if (data.error) return alert(data.error);
                    document.getElementById("cedula").value = data.cedula;
                    document.getElementById("primer_apellido").value = data.primer_apellido;
                    document.getElementById("segundo_apellido").value = data.segundo_apellido;
                    document.getElementById("primer_nombre").value = data.primer_nombre;
                    document.getElementById("segundo_nombre").value = data.segundo_nombre;
                    document.getElementById("sexo").value = data.sexo;
                })
                .catch(error => alert("Error en la solicitud."));
        }
        </script>
    ''')

@app.route('/consultar', methods=['POST'])
def consultar():
    cedula = request.form.get('cedula')
    fecha_expedicion = request.form.get('fecha_expedicion')
    placa = request.form.get('placa')

    if not fecha_expedicion or not validar_fecha(fecha_expedicion):
        return "Error: Debe ingresar una fecha de expedición válida."
    if not placa:
        return "Error: Debe ingresar una placa válida."

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
        archivos.append(consultar_runt(placa, cedula, "C", folder))
    except Exception as e:
        errores.append(f"RUNT: {str(e)}")

    try:
        archivos.append(consultar_simit(placa, folder))
    except Exception as e:
        errores.append(f"SIMIT: {str(e)}")

    if not archivos:
        return "Error: No se pudieron obtener resultados.<br>" + "<br>".join(errores)

    zip_path = os.path.join(folder, f"antecedentes_{cedula}.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for archivo in archivos:
            zipf.write(archivo, os.path.basename(archivo))

    if errores:
        return f"Advertencias:<br>{'<br>'.join(errores)}<br><br><a href='/{zip_path}'>Descargar ZIP</a>"
    else:
        return send_file(zip_path, as_attachment=True)

@app.route('/autocompletar')
def autocompletar():
    cedula = request.args.get("cedula")
    if not cedula:
        return jsonify({"error": "Falta el número de documento."})

    try:
        datos = consultar_registraduria(cedula)
        return jsonify(datos)
    except Exception as e:
        return jsonify({"error": f"Error al consultar Registraduría: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)