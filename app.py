from flask import Flask, request, send_file, render_template_string, jsonify
import os
import uuid
import zipfile
import re
import threading, time
from consulta.contraloria import consultar_contraloria
from consulta.personeria import consultar_personeria
from consulta.runt import consultar_runt
from consulta.simit import consultar_simit
from consulta.registraduria import consultar_registraduria
from consulta.inhabilidades import consultar_inhabilidades
from consulta.rama_judicial import consultar_rama_judicial
from consulta.dea import consultar_dea
from consulta.offshore import consultar_offshore
from consulta.offshore_paradise import consultar_offshore_paradise 
from consulta.offshore_panama import consultar_offshore_panama  
from consulta.offshore_bahamas import consultar_offshore_bahamas
from consulta.offshore_offshoreleaks import consultar_offshore_offshoreleaks
from consulta.samm import consultar_samm 
from consulta.samm_policy_memo import consultar_samm_policy_memo
from consulta.fbi_news import consultar_fbi_news
from consulta.state_terrorist_orgs import consultar_state_terrorist_orgs
from consulta.eo_13224_findit import consultar_eo_13224_findit
from consulta.eu_taric import consultar_eu_taric
from consulta.eu_travelban_pdf import consultar_eu_travelban_pdf
from consulta.pdf_search_highlight import buscar_en_pdf_y_resaltar
from consulta.eu_fin_sanctions import consultar_eu_fin_sanctions
from consulta.eu_sanctions_tracker import consultar_eu_sanctions_tracker
from consulta.un_consolidated_list import consultar_un_consolidated_list
from consulta.interpol_red_notices import consultar_interpol_red_notices
from consulta.ofsi_sanctions_pdf import consultar_ofsi_pdf


app = Flask(__name__)

def _shutdown_server(fn):
    if fn is None:
        print("[APP] No se pudo obtener werkzeug.server.shutdown (¿no es dev server?)")
        return False
    try:
        fn()
        return True
    except Exception as e:
        print(f"[APP] Error apagando: {e}")
        return False

def _shutdown_later(fn, delay=1.0):
    def _later():
        time.sleep(delay)
        print("[APP] Apagando servidor Flask…")
        ok = _shutdown_server(fn)
        if not ok:
            # Fallback si no existe shutdown de werkzeug (p.ej. servidor distinto)
            try:
                os._exit(0)
            except Exception as e:
                print(f"[APP] Fallback os._exit(0) falló: {e}")
    threading.Thread(target=_later, daemon=True).start()


def consultar_travelbans_con_busqueda(nombre_completo, folder):
    print("[TRAVELBANS] Descargando PDF...")
    pdf_path = consultar_eu_travelban_pdf(nombre_completo, folder)
    print(f"[TRAVELBANS] PDF guardado en: {pdf_path}")
    print("[TRAVELBANS] Buscando en PDF con PyMuPDF...")

    imgs = buscar_en_pdf_y_resaltar(
        pdf_path,
        nombre_completo,
        folder,
        export_first_if_none=False,  # sin preview si no hay hallazgos
        stop_on_first=True,          # corta al primer match
        page_limit=300,              # limita páginas (ajústalo o quítalo)
        dpi=150
    )

    if not imgs:
        print("[TRAVELBANS] No hay hallazgos en el PDF.")
        marker = os.path.join(folder, "travelbans_sin_hallazgos.txt")
        with open(marker, "w", encoding="utf-8") as f:
            f.write("Sin hallazgos para: " + (nombre_completo or "").strip())
        return [pdf_path, marker]

    print(f"[TRAVELBANS] Imágenes generadas: {imgs}")
    return [pdf_path] + imgs



def validar_fecha(fecha):
    """Valida formato dd/mm/aa o dd/mm/aaaa"""
    patron = r'^\d{2}/\d{2}/(\d{2}|\d{4})$'
    return re.match(patron, fecha) is not None

@app.route('/', methods=['GET'])
def index():
    return render_template_string('''
        <h2>Consulta Masiva de Antecedentes</h2>
        <form method="POST" action="/consultar" id="consulta-form">

            <label>Tipo de Documento:</label><br>
            <select name="tipo_doc" id="tipo_doc" required>
                <option value="CC">Cédula de Ciudadanía</option>
                <option value="TI">Tarjeta de Identidad</option>
                <option value="CE">Cédula de Extranjería</option>
                <option value="PP">Pasaporte</option>
                <option value="PTP">Permiso Temporal de Permanencia</option>
                <option value="PPT">Permiso por Protección Temporal</option>
            </select><br><br>

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

            <h3>Datos para Inhabilidades</h3>
            <label>Tipo de Persona:</label><br>
            <select name="tipo_persona" required>
                <option value="Natural">Natural</option>
                <option value="Jurídica">Jurídica</option>
            </select><br><br>

            <label>Razón Social / Empresa:</label><br>
            <input type="text" name="razon_social" required><br><br>

            <label>NIT de la Empresa:</label><br>
            <input type="text" name="nit_empresa" required><br><br>

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
                    document.getElementById("primer_apellido").value = data.primer_apellido || '';
                    document.getElementById("segundo_apellido").value = data.segundo_apellido || '';
                    document.getElementById("primer_nombre").value = data.primer_nombre || '';
                    document.getElementById("segundo_nombre").value = data.segundo_nombre || '';
                    document.getElementById("sexo").value = data.sexo || '';
                })
                .catch(() => alert("Error en la solicitud."));
        }
        </script>
    ''')

@app.route('/consultar', methods=['POST'])
def consultar():
    tipo_doc = request.form.get('tipo_doc')
    cedula = request.form.get('cedula')
    fecha_expedicion = request.form.get('fecha_expedicion')
    placa = request.form.get('placa')
    razon_social = request.form.get('razon_social')
    nit_empresa = request.form.get('nit_empresa')
    tipo_persona = request.form.get('tipo_persona')

    # Generar nombre completo para Offshore
    nombre_completo = " ".join([
        request.form.get('primer_nombre') or '',
        request.form.get('segundo_nombre') or '',
        request.form.get('primer_apellido') or '',
        request.form.get('segundo_apellido') or ''
    ]).strip()

    # Validaciones
    if not fecha_expedicion or not validar_fecha(fecha_expedicion):
        return "Error: Debe ingresar una fecha de expedición válida."
    if not placa:
        return "Error: Debe ingresar una placa válida."
    if not razon_social or not nit_empresa:
        return "Error: Debe ingresar razón social y NIT para la consulta de inhabilidades."

    uid = str(uuid.uuid4())
    folder = os.path.join('downloads', uid)
    os.makedirs(folder, exist_ok=True)

    archivos = []
    errores = []

    consultas = [
        # ("Contraloría", consultar_contraloria, (cedula, folder, tipo_doc)),
        # ("Personería", consultar_personeria, (cedula, fecha_expedicion, folder)),
        # ("Inhabilidades", consultar_inhabilidades, (tipo_doc, cedula, fecha_expedicion, razon_social, nit_empresa, folder)),
        # ("RUNT", consultar_runt, (placa, cedula, tipo_doc, folder)),
        # ("SIMIT", consultar_simit, (placa, folder)),
        # ("Rama Judicial", consultar_rama_judicial, (razon_social, tipo_persona, folder)),
        #  ("DEA", consultar_dea, (cedula, folder)),
        #  ("SAMM DSCA", consultar_samm, (nombre_completo, folder)),
        #  ("SAMM DSCA Policy Memo", consultar_samm_policy_memo, (nombre_completo, folder)),
        #  ("FBI News", consultar_fbi_news, (nombre_completo, folder)),
        # ("State Terrorist Orgs", consultar_state_terrorist_orgs, (nombre_completo, folder)),  
        # ("EO 13224 (FindIt)", consultar_eo_13224_findit, (nombre_completo, folder)),
        # ("EU TARIC Consultation", consultar_eu_taric, (nombre_completo, folder)),
        # ("EU Travel Bans (PDF + búsqueda)", consultar_travelbans_con_busqueda, (nombre_completo, folder))
        # ("EU Financial Sanctions (data.europa.eu)", consultar_eu_fin_sanctions, (nombre_completo, folder)),
        # ("EU Sanctions Tracker", consultar_eu_sanctions_tracker, (nombre_completo, folder)),
        # ("UN Consolidated List (CSNU)", consultar_un_consolidated_list, (nombre_completo, folder)),
        # ("INTERPOL Red Notices", consultar_interpol_red_notices, (nombre_completo, folder)),
        ("OFSI (UK Treasury) – PDF", consultar_ofsi_pdf, (nombre_completo, folder)),
    ]

    # Solo agregamos Offshore si hay nombre completo
    if nombre_completo:
        # consultas.append(("Offshore Leaks", consultar_offshore, (nombre_completo, folder)))
        # consultas.append(("Paradise Papers", consultar_offshore_paradise, (nombre_completo, folder)))
        # consultas.append(("Panama Papers", consultar_offshore_panama, (nombre_completo, folder)))
        # consultas.append(("Bahamas Leaks", consultar_offshore_bahamas, (nombre_completo, folder)))
        consultas.append(("Offshore Leaks investigación", consultar_offshore_offshoreleaks, (nombre_completo, folder)))
        
    # Ejecutar todas las consultas
    for nombre, funcion, args in consultas:
        try:
            resultado = funcion(*args)
            if resultado:
                if isinstance(resultado, list):
                    archivos.extend(resultado)
                else:
                    archivos.append(resultado)
        except Exception as e:
            errores.append(f"{nombre}: {str(e)}")

    if not archivos:
        return "Error: No se pudieron obtener resultados.<br>" + "<br>".join(errores)

    zip_path = os.path.join(folder, f"antecedentes_{cedula}.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for archivo in archivos:
            if archivo and os.path.exists(archivo):
                zipf.write(archivo, os.path.basename(archivo))

    # 🔹 Apagar Flask después de generar el ZIP y enviarlo
    resp = send_file(zip_path, as_attachment=True)
    # capturar la función de apagado dentro del request context
    shutdown_fn = request.environ.get("werkzeug.server.shutdown")
    _shutdown_later(shutdown_fn, 1.5)

    return resp


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
    app.run(debug=True, use_reloader=False)
