"""
Genera las diapositivas de demostración de index.html a partir de
demo_expo.sql, para que el código mostrado y el guion nunca difieran.

Uso (desde la carpeta "expo final"):
    python tools/generar_demos.py

Reemplaza lo que haya entre <!-- DEMOS:INICIO --> y <!-- DEMOS:FIN -->
en index.html. El SQL se toma de demo_expo.sql (bloques [X.Y]); los
textos de la guía (objetivo, pasos, resultado esperado) viven en META.
"""
import html
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SQL = RAIZ / "demo_expo.sql"
INDEX = RAIZ / "index.html"

TEMAS = {
    "P": ("", "Preparación"),
    "1": ("Actividad 3", "Procedimientos y transacciones"),
    "2": ("Actividad 4", "Seguridad: roles y usuarios"),
    "3": ("Actividad 5", "Respaldos y restauración"),
    "C": ("Cierre", "Limpieza"),
}

SECCIONES = {
    "1": ("01", "Procedimientos almacenados y transacciones",
          "Lógica dentro del servidor y operaciones que se ejecutan completas o no se ejecutan."),
    "2": ("02", "Seguridad: roles y usuarios",
          "Cada cuenta accede sólo a lo que su función requiere. Se prueba entrando con cada usuario."),
    "3": ("03", "Respaldos y restauración",
          "Respaldar, perder la base a propósito, restaurarla y demostrar que sigue operando."),
}

# tipo de resultado esperado: ok | error | aviso
META = {
    "P.1": dict(
        titulo="Base de datos, tablas y datos de muestra",
        conexion="root",
        objetivo="Construir <code>optica_db</code> desde cero: 9 tablas en orden de dependencias, con sus llaves, restricciones e índices, y un juego de datos conocido.",
        pasos=[
            "<code>DROP</code> / <code>CREATE DATABASE</code> con <code>utf8mb4</code>.",
            "Tablas sin llaves foráneas primero (<code>optica</code>, <code>rol</code>), luego sus dependientes hasta <code>receta</code>.",
            "Datos de muestra con id derivados de <code>MD5('etiqueta')</code>.",
            "Verificar tablas, conteos y reglas de borrado.",
        ],
        esperado=[
            ("ok", "9 tablas creadas sin errores."),
            ("ok", "Filas: 2 ópticas · 3 roles · 4 sucursales · 5 usuarios · 9 asignaciones · 6 pacientes · 6 expedientes · 9 asientos · 8 recetas"),
            ("ok", "Llaves foráneas: <code>RESTRICT</code> en el historial clínico, <code>CASCADE</code> sólo en la tabla puente y en <code>receta</code>."),
            ("aviso", "Ejecutar con <kbd>Alt</kbd>+<kbd>X</kbd>: con <kbd>Ctrl</kbd>+<kbd>Enter</kbd> son más de 30 sentencias."),
        ],
    ),
    "P.2": dict(
        titulo="Variables de sesión y línea base",
        conexion="root",
        objetivo="Cargar los identificadores de los datos de muestra en variables <code>@</code> de la sesión.",
        pasos=[
            "Seleccionar los <code>SET</code> y ejecutarlos con <kbd>Alt</kbd>+<kbd>X</kbd>.",
            "Ejecutar el conteo con <kbd>Ctrl</kbd>+<kbd>Enter</kbd>.",
        ],
        esperado=[("ok", "6 pacientes · 6 expedientes · 9 asientos · 8 recetas · 1 sin receta")],
    ),
    "1.0": dict(
        titulo="Creación de los procedimientos",
        conexion="root",
        objetivo="Crear los cinco procedimientos. <code>DELIMITER $$</code> evita que los <code>;</code> del cuerpo corten el <code>CREATE PROCEDURE</code>.",
        pasos=[
            "<b>Copiar todo</b> y pegarlo en un editor nuevo.",
            "Ejecutar el bloque completo con <kbd>Alt</kbd>+<kbd>X</kbd>.",
            "Verificar en <code>information_schema.ROUTINES</code>.",
        ],
        esperado=[
            ("ok", "5 procedimientos · 2 con <code>START TRANSACTION</code>"),
            ("aviso", "<code>DELIMITER</code> lo interpreta el cliente (DBeaver o <code>mysql</code>); el servidor nunca lo recibe."),
        ],
    ),
    "1.1": dict(
        titulo="Procedimientos sin transacción",
        conexion="root",
        objetivo="Con una sola escritura, InnoDB ya garantiza la atomicidad: <code>START TRANSACTION</code> no aporta nada.",
        pasos=[
            "Búsqueda por prefijo con <code>sp_buscar_paciente</code>.",
            "Actualizar el contacto y comprobarlo con un <code>SELECT</code>.",
            "Alta de sucursal y lectura del parámetro <code>OUT</code>.",
        ],
        esperado=[
            ("ok", "Juan Pérez López y Juana Martínez Cruz, con edad y folio."),
            ("ok", "<code>@suc_nueva</code> devuelve el UUID generado."),
        ],
    ),
    "1.2": dict(
        titulo="Transacción: paciente + expediente",
        conexion="root",
        objetivo="Paciente y expediente se crean juntos o ninguno; el folio consecutivo se calcula con <code>FOR UPDATE</code>.",
        pasos=[
            "Ejecutar el <code>CALL</code>.",
            "Leer los parámetros <code>OUT</code>.",
            "Guardar <code>@exp_rosa</code>: lo usan las demos siguientes.",
        ],
        esperado=[("ok", "Folio <code>EXP-2026-0004</code>")],
    ),
    "1.3": dict(
        titulo="Atomicidad ante un dato inválido",
        conexion="root",
        objetivo="Falla un <code>CHECK</code>; el <code>EXIT HANDLER</code> hace <code>ROLLBACK</code> y <code>RESIGNAL</code>.",
        pasos=[
            "Conteo antes.",
            "<code>CALL</code> con un correo sin arroba.",
            "Conteo después.",
        ],
        esperado=[
            ("error", "Error 3819 · <code>chk_paciente_correo</code>"),
            ("ok", "7 / 7 antes y después: no queda rastro."),
        ],
    ),
    "1.4": dict(
        titulo="Consulta con receta y reglas de negocio",
        conexion="root",
        objetivo="Reglas que ninguna llave foránea puede expresar, validadas con <code>SIGNAL</code> dentro de la transacción.",
        pasos=[
            "Consulta válida: asiento y receta en una sola transacción.",
            "Sucursal que pertenece a otra óptica.",
            "Optometrista dado de baja.",
        ],
        esperado=[
            ("ok", "Se devuelven <code>asiento_id</code> y <code>receta_id</code>."),
            ("error", "Error 1644 (dos veces), con el mensaje de cada regla."),
        ],
    ),
    "2.0": dict(
        titulo="Creación de roles, permisos y cuentas",
        conexion="root",
        objetivo="Crear los 5 roles, darles sus permisos y otorgar cada uno a una cuenta. Va después de 1.0: los <code>GRANT EXECUTE</code> necesitan los procedimientos.",
        pasos=[
            "<b>Copiar todo</b> y ejecutarlo con <kbd>Alt</kbd>+<kbd>X</kbd>.",
            "<code>CREATE ROLE</code> y <code>GRANT</code> de permisos a cada rol.",
            "<code>CREATE USER</code> con su política de contraseña.",
            "<code>GRANT</code> rol → usuario y <code>SET DEFAULT ROLE</code>.",
        ],
        esperado=[
            ("ok", "<code>role_edges</code> = 5"),
            ("aviso", "Al inicio borra roles y cuentas: la demo se puede repetir."),
        ],
    ),
    "2.1": dict(
        titulo="Inventario de roles, permisos y políticas",
        conexion="root",
        objetivo="Cada usuario hereda sus permisos de un rol; las políticas de contraseña son por cuenta.",
        pasos=[
            "Rol otorgado vs. rol activo (<code>role_edges</code> / <code>default_roles</code>).",
            "<code>SHOW GRANTS … USING</code>: permisos efectivos.",
            "Políticas en <code>mysql.user</code>.",
        ],
        esperado=[
            ("ok", "5 usuarios, cada uno con su rol activo por defecto."),
            ("ok", "Expira a 90 días · historial 5 · bloqueo tras 5 intentos."),
        ],
    ),
    "2.2": dict(
        titulo="Recepción: lo permitido y lo negado",
        conexion="usr_recepcion1",
        cuentas=["usr_recepcion1"],
        objetivo="Menor privilegio: recepción gestiona pacientes, pero no ve información clínica ni contraseñas.",
        pasos=[
            "Cambiar la conexión del editor de root a <code>usr_recepcion1</code> (DBeaver: Ctrl+9).",
            "Confirmar usuario y rol activos.",
            "Lo permitido: el procedimiento y las columnas autorizadas.",
            "Lo negado: columna, tabla y operación.",
        ],
        esperado=[
            ("ok", "<code>CALL</code> y <code>SELECT id, nombre</code> funcionan."),
            ("error", "1143 <code>password_hash</code> · 1142 <code>asiento_clinico</code> · 1142 <code>DELETE</code>"),
        ],
    ),
    "2.3": dict(
        titulo="Optometrista y auditor",
        conexion="usr_optometrista1 · usr_auditor",
        cuentas=["usr_optometrista1", "usr_auditor"],
        objetivo="El historial clínico es inmutable y el auditor sólo lee.",
        pasos=[
            "Ctrl+9 → <code>usr_optometrista1</code>: confirmar usuario y rol; leer, intentar borrar recetas, intentar editar un paciente.",
            "Ctrl+9 → <code>usr_auditor</code>: confirmar usuario y rol; leer e intentar ejecutar un procedimiento de alta.",
        ],
        esperado=[
            ("ok", "Los <code>SELECT</code> funcionan."),
            ("error", "1142 en <code>DELETE</code> y <code>UPDATE</code> · 1370 en <code>CALL</code>"),
            ("aviso", "<code>usr_auditor</code> admite 2 conexiones: si aparece 1203, en DBeaver desactivar «conexión separada para metadatos»."),
        ],
    ),
    "2.4": dict(
        titulo="GRANT / REVOKE en vivo",
        conexion="root ↔ usr_auditor",
        cuentas=["root", "usr_auditor"],
        objetivo="Se administran roles, no personas: un <code>REVOKE</code> al rol afecta a todos sus usuarios.",
        pasos=[
            "Ctrl+9 → root: <code>REVOKE EXECUTE</code> al rol.",
            "Ctrl+9 → <code>usr_auditor</code>: el <code>CALL</code> ahora falla.",
            "Ctrl+9 → root: <code>GRANT</code> de vuelta.",
            "Ctrl+9 → <code>usr_auditor</code>: funciona otra vez.",
        ],
        esperado=[
            ("error", "1370 tras el <code>REVOKE</code>"),
            ("ok", "Resultado normal tras el <code>GRANT</code>"),
        ],
    ),
    "2.5": dict(
        titulo="Opcional · bloqueo por intentos fallidos",
        conexion="root + TERMINAL",
        objetivo="<code>FAILED_LOGIN_ATTEMPTS</code> bloquea la cuenta aunque después se use la contraseña correcta.",
        pasos=[
            "Crear una cuenta desechable (3 intentos).",
            "Tres accesos con contraseña incorrecta.",
            "Cuarto acceso con la correcta.",
            "Desbloquear y eliminar la cuenta.",
        ],
        esperado=[
            ("error", "Error 3955 · <em>Account is blocked … 3 consecutive failed logins</em>"),
            ("ok", "<code>ACCOUNT UNLOCK</code> la libera."),
        ],
    ),
    "3.1": dict(
        titulo="Estado previo al respaldo",
        conexion="root",
        objetivo="Registrar la línea base que la restauración tendrá que reproducir.",
        pasos=[
            "Conteo por tabla (anotarlo).",
            "Número de procedimientos.",
            "Permisos de la cuenta de respaldo.",
        ],
        esperado=[
            ("ok", "Conteos anotados · 5 procedimientos"),
            ("ok", "<code>usr_respaldo</code>: sólo lectura + <code>SHOW_ROUTINE</code>"),
        ],
    ),
    "3.2": dict(
        titulo="Respaldo lógico con mysqldump",
        conexion="TERMINAL (PowerShell)",
        cuentas=["usr_respaldo"],
        objetivo="Volcado consistente sin bloquear a los demás (<code>--single-transaction</code>), con rutinas incluidas.",
        pasos=[
            "Crear la carpeta <code>respaldos_optica</code> y entrar en ella.",
            "Agregar <code>mysql</code> y <code>mysqldump</code> al PATH y comprobar con <code>--version</code>.",
            "<code>mysqldump</code> con la cuenta <code>usr_respaldo</code>.",
            "Comprobar el contenido con <code>Select-String</code> y la última línea.",
            "Copiar el archivo fuera del equipo y comparar tamaños.",
        ],
        esperado=[
            ("ok", "9 <code>CREATE TABLE</code> · 5 <code>PROCEDURE</code>"),
            ("ok", "Última línea: <code>-- Dump completed on …</code>"),
            ("aviso", "No usar <code>&gt;</code> en PowerShell 5.1: escribe UTF-16."),
        ],
    ),
    "3.3": dict(
        titulo="Desastre y restauración",
        conexion="root + TERMINAL",
        objetivo="Perder la base a propósito y recuperarla desde el archivo.",
        pasos=[
            "<code>DROP DATABASE</code> y comprobar que ya no existe.",
            "Restaurar con <code>root</code> desde la carpeta del respaldo (misma terminal de 3.2).",
            "<kbd>F5</kbd> en DBeaver para refrescar.",
        ],
        esperado=[
            ("ok", "<code>SHOW DATABASES</code> vacío tras el <code>DROP</code>."),
            ("ok", "La base reaparece completa."),
            ("ok", "Usuarios, roles y permisos intactos: viven en el esquema <code>mysql</code>."),
        ],
    ),
    "3.4": dict(
        titulo="Verificación posterior",
        conexion="root",
        objetivo="Un respaldo no es válido hasta que se restaura y se verifica: estructura, datos y operación.",
        pasos=[
            "Conteos contra los de la demo 3.1.",
            "Los cinco procedimientos.",
            "Prueba funcional transaccional.",
        ],
        esperado=[
            ("ok", "Conteos idénticos a 3.1."),
            ("ok", "5 procedimientos <code>DEFINER</code> · nuevo folio asignado"),
        ],
    ),
    "3.5": dict(
        titulo="Respaldo físico (copia en frío)",
        conexion="sólo explicación",
        objetivo="Copiar los archivos: la restauración es rápida, pero queda atada a la versión y plataforma, y exige detener el servicio.",
        pasos=[
            "Mostrar qué archivos <code>.ibd</code> forman la base.",
            "Explicar los comandos de la copia en frío.",
            "Guardar el <code>.zip</code> con ruta absoluta en <code>respaldos_optica</code>.",
        ],
        esperado=[
            ("aviso", "Sólo se explica: detener el servidor en vivo es arriesgado."),
            ("aviso", "Como administrador, PowerShell abre en <code>C:\\Windows\\System32</code>: sin ruta absoluta el <code>.zip</code> queda ahí."),
        ],
    ),
    "C.1": dict(
        diapositiva=False,  # sólo para ensayos: el bloque sigue en demo_expo.sql
        titulo="Limpieza",
        conexion="root",
        objetivo="Dejar los datos de muestra como estaban (alternativa: repetir la preparación).",
        pasos=["Ejecutar el bloque completo con <kbd>Alt</kbd>+<kbd>X</kbd>."],
        esperado=[("ok", "Vuelve a 6 · 6 · 9 · 8 · 1")],
    ),
}

ICONOS = {"ok": "✔", "error": "✖", "aviso": "!"}

# Diapositiva previa a la demo 1.1: los procedimientos aún no existen.
# (grupo, descripción del grupo, [(nombre, firma, descripción, etiquetas, demos)])
PROCEDIMIENTOS = [
    ("Sin transacción", "Una sola escritura (o ninguna): InnoDB ya la hace atómica.", [
        ("sp_buscar_paciente", "(óptica, prefijo)",
         "Busca pacientes de una óptica por el inicio del nombre; devuelve edad y folio.",
         ["SELECT", "LIKE 'x%'"], "1.1"),
        ("sp_actualizar_contacto_paciente", "(paciente, tel, correo, dir)",
         "Valida que el paciente exista y actualiza su contacto en un solo <code>UPDATE</code>.",
         ["SIGNAL", "UPDATE"], "1.1"),
        ("sp_alta_sucursal", "(óptica, nombre, dir, OUT id)",
         "Inserta una sucursal; la FK y el <code>UNIQUE</code> cuidan la integridad.",
         ["INSERT", "OUT"], "1.1"),
    ]),
    ("Con transacción", "Varias escrituras que deben verse como una sola operación.", [
        ("sp_alta_paciente_con_expediente", "(…, OUT paciente, OUT folio)",
         "Crea paciente y expediente juntos; calcula el folio consecutivo <code>EXP-AAAA-NNNN</code>.",
         ["EXIT HANDLER", "FOR UPDATE"], "1.2 · 1.3"),
        ("sp_registrar_consulta", "(expediente, usuario, sucursal, …)",
         "Asiento clínico y receta en bloque; valida tres reglas de negocio antes de escribir.",
         ["SIGNAL", "ROLLBACK"], "1.4"),
    ]),
]

# Diapositiva previa a la demo 2.0: roles, su cuenta y sus permisos.
# Fuente: optica_db.sql (PARTE 4). Letras: S SELECT · I INSERT · U UPDATE · D DELETE
# (rol, usuario, demos, descripción, [(objeto, permisos)], [negado])
ROLES = [
    ("rol_admin_app", "usr_admin", "",
     "Administra la estructura de la óptica y las cuentas. No ve datos clínicos.",
     [("optica · sucursal · rol", "S I U"),
      ("usuario_sucursal", "S I D"),
      ("usuario", "S* I U"),
      ("EXECUTE", "sp_alta_sucursal")],
     ["pacientes y expedientes", "historial clínico"]),
    ("rol_optometrista", "usr_optometrista1", "2.3",
     "Atiende la consulta: registra asientos clínicos y emite recetas.",
     [("catálogos · usuario*", "S"),
      ("paciente · expediente", "S"),
      ("asiento_clinico · receta", "S I U"),
      ("EXECUTE", "sp_buscar_paciente · sp_registrar_consulta")],
     ["DELETE en el historial", "editar pacientes"]),
    ("rol_recepcion", "usr_recepcion1", "2.2",
     "Da de alta pacientes y expedientes y entrega recetas.",
     [("optica · sucursal · usuario*", "S"),
      ("paciente", "S I U"),
      ("expediente", "S I"),
      ("receta", "S"),
      ("EXECUTE", "sp_buscar_paciente · sp_alta_paciente_con_expediente · sp_actualizar_contacto_paciente")],
     ["asiento_clinico", "DELETE"]),
    ("rol_auditor", "usr_auditor", "2.3 · 2.4",
     "Revisión y cumplimiento: lee todo y no modifica nada.",
     [("las 8 tablas", "S"),
      ("usuario", "S*"),
      ("EXECUTE", "sp_buscar_paciente")],
     ["INSERT · UPDATE · DELETE", "procedimientos de alta"]),
    ("rol_respaldo", "usr_respaldo", "3.1 – 3.3",
     "Cuenta técnica: lo mínimo que necesita <code>mysqldump</code>.",
     [("optica_db.*", "SELECT · LOCK TABLES · SHOW VIEW · TRIGGER · EVENT"),
      ("*.* (global)", "PROCESS · SHOW_ROUTINE")],
     ["cualquier escritura"]),
]

# Detalle que se abre al hacer clic en la tarjeta de un rol.
# rol: (título, [(privilegio, ámbito, explicación)])
DETALLE_ROL = {
    "rol_respaldo": ("Privilegios de rol_respaldo", [
        ("LOCK TABLES", "optica_db.*",
         "Permite bloquear tablas (en las que ya tiene <code>SELECT</code>) mientras se leen. "
         "<code>mysqldump</code> lo usa para volcar un estado consistente cuando no se usa "
         "<code>--single-transaction</code> o hay tablas no transaccionales."),
        ("SHOW VIEW", "optica_db.*",
         "Permite leer la definición de las vistas (<code>SHOW CREATE VIEW</code>) para "
         "incluirlas en el respaldo."),
        ("TRIGGER", "optica_db.*",
         "Permite leer los disparadores (<code>SHOW CREATE TRIGGER</code>) y volcarlos con "
         "<code>--triggers</code>. Nota: también permitiría crearlos o borrarlos."),
        ("EVENT", "optica_db.*",
         "Permite leer los eventos programados del Event Scheduler y volcarlos con "
         "<code>--events</code>. Nota: también permitiría crearlos o modificarlos."),
        ("PROCESS", "*.* (global)",
         "Permite ver los procesos del servidor y leer la información de tablespaces. Desde "
         "MySQL 8.0.21 <code>mysqldump</code> lo exige; sin él hay que usar <code>--no-tablespaces</code>."),
        ("SHOW_ROUTINE", "*.* (global)",
         "Permite leer el cuerpo de procedimientos y funciones creados por otra cuenta. Sin él, "
         "<code>--routines</code> genera el volcado sin los procedimientos."),
    ]),
}

RE_ID = re.compile(r"^--\s+\[([A-Z0-9]\.\d)\]")
RE_REGLA = re.compile(r"^-- [=#]{10,}")
RE_GUIONES = re.compile(r"^-- -{10,}")
RE_CMD = re.compile(
    r"^(\$env:|\(Select-String\b"
    r"|(mysql|mysqldump|cd|New-Item|Get-Item|Get-Content|Get-PSDrive"
    r"|Copy-Item|Stop-Service|Start-Service|Compress-Archive)(?=\s|$))"
)


def leer_bloques():
    """Devuelve {id: [líneas del cuerpo]} en el orden del archivo."""
    lineas = SQL.read_text(encoding="utf-8").splitlines()
    bloques, i = {}, 0
    while i < len(lineas):
        m = RE_ID.match(lineas[i])
        if not m:
            i += 1
            continue
        clave = m.group(1)
        i += 1
        while i < len(lineas) and not RE_REGLA.match(lineas[i]):
            i += 1                      # resto del encabezado
        i += 1
        cuerpo = []
        while i < len(lineas) and not RE_REGLA.match(lineas[i]) and not RE_ID.match(lineas[i]):
            if not RE_GUIONES.match(lineas[i]):
                cuerpo.append(lineas[i])
            i += 1
        bloques[clave] = cuerpo
    return bloques


def clase_nota(texto):
    t = texto.upper()
    if "ERROR ESPERADO" in t:
        return "nota--error"
    if t.startswith("----") or t.startswith("SESIÓN"):
        return "nota--sesion"
    if t.startswith("OK"):
        return "nota--ok"
    if "ESPERADO" in t:
        return "nota--esperado"
    if t.startswith("TERMINAL"):
        return "nota--terminal"
    return ""


def nota(texto):
    texto = texto.strip()
    clase = clase_nota(texto)
    if clase == "nota--sesion":
        texto = texto.lstrip("- ").strip()
    return f'<p class="nota {clase}">{html.escape(texto)}</p>'


def trozos_comentario(lineas):
    """Comentarios puros: notas y comandos de terminal."""
    salida, cmd, parrafo = [], None, []

    def cerrar_parrafo():
        if parrafo:
            salida.append(("nota", " ".join(parrafo)))
            parrafo.clear()

    for ln in lineas:
        limpio = re.sub(r"^--", "", ln).strip()
        if cmd is not None and cmd[-1].endswith("`"):
            cmd.append("  " + limpio)          # continuación de PowerShell
            continue
        if cmd is not None:
            salida.append(("cmd", "\n".join(cmd)))
            cmd = None
        if RE_CMD.match(limpio):
            cerrar_parrafo()
            cmd = [limpio]
        elif not limpio:
            cerrar_parrafo()                   # "--" vacío separa párrafos
        else:
            # Viñetas, avisos y encabezados de sesión inician párrafo nuevo
            if limpio.startswith("·") or clase_nota(limpio):
                cerrar_parrafo()
            parrafo.append(limpio)
            if clase_nota(limpio) == "nota--sesion":
                cerrar_parrafo()               # el encabezado va solo
    cerrar_parrafo()
    if cmd is not None:
        salida.append(("cmd", "\n".join(cmd)))
    return salida


def render_cuerpo(cuerpo):
    # Trozos separados por líneas en blanco (igual que DBeaver)
    trozos, actual = [], []
    for ln in cuerpo:
        if ln.strip():
            actual.append(ln)
        elif actual:
            trozos.append(actual)
            actual = []
    if actual:
        trozos.append(actual)

    partes = []
    for t in trozos:
        primer_sql = next((k for k, ln in enumerate(t) if not ln.lstrip().startswith("--")), None)
        previos = t if primer_sql is None else t[:primer_sql]
        for tipo, texto in trozos_comentario(previos):
            if tipo == "nota":
                partes.append(nota(texto))
            else:
                partes.append(
                    '<div class="bloque bloque--cmd" tabindex="0" title="Clic para resaltar · botón Copiar para copiar">'
                    '<span class="bloque__ps">PS&gt;</span>'
                    f'<pre class="cmd">{html.escape(texto, quote=False)}</pre>'
                    '<button class="copiar" type="button">Copiar</button></div>'
                )
        if primer_sql is not None:
            sql = "\n".join(t[primer_sql:])
            partes.append(
                '<div class="bloque bloque--sql" tabindex="0" title="Clic para resaltar · botón Copiar para copiar">'
                f'<pre class="sql">{html.escape(sql, quote=False)}</pre>'
                '<button class="copiar" type="button">Copiar</button></div>'
            )
    return "\n          ".join(partes)


def slide_seccion(tema, ids):
    num, titulo, texto = SECCIONES[tema]
    actividad = TEMAS[tema][0]
    items = "\n".join(
        f'        <li><span>{k}</span>{META[k]["titulo"]}</li>' for k in ids
    )
    return f"""
  <section class="slide slide--seccion" data-titulo="{num} · {html.escape(titulo)}">
    <div class="seccion">
      <span class="seccion__num anim" style="--d:0">{num}</span>
      <div class="seccion__texto">
        <p class="sobretitulo anim" style="--d:1">{actividad}</p>
        <h2 class="seccion__titulo anim" style="--d:2">{titulo}</h2>
        <p class="seccion__desc anim" style="--d:3">{texto}</p>
        <ol class="seccion__lista anim" style="--d:4">
{items}
        </ol>
      </div>
    </div>
  </section>"""


def slide_procedimientos():
    total = sum(len(procs) for _, _, procs in PROCEDIMIENTOS)
    grupos, d = [], 3
    for n, (grupo, desc, procs) in enumerate(PROCEDIMIENTOS):
        items = []
        for nombre, firma, texto, etiquetas, demos in procs:
            chips = "".join(f"<span>{html.escape(e)}</span>" for e in etiquetas)
            items.append(f"""
          <li class="proc anim" style="--d:{d}">
            <div class="proc__cab">
              <code class="proc__nombre">{nombre}</code>
              <span class="proc__demo">{demos}</span>
            </div>
            <p class="proc__firma">{html.escape(firma)}</p>
            <p class="proc__texto">{texto}</p>
            <div class="chips">{chips}</div>
          </li>""")
            d += 1
        grupos.append(f"""
      <section class="procs__grupo procs__grupo--{n}">
        <header class="procs__cab anim" style="--d:2">
          <h3>{grupo}</h3>
          <p>{desc}</p>
        </header>
        <ol class="procs__lista">{"".join(items)}
        </ol>
      </section>""")
    return f"""
  <section class="slide slide--procs" data-titulo="Procedimientos a crear">
    <header class="encabezado encabezado--izq">
      <p class="sobretitulo anim" style="--d:0">{TEMAS["1"][0]} · {TEMAS["1"][1]}</p>
      <h2 class="encabezado__titulo anim" style="--d:1">{total} procedimientos por crear</h2>
      <p class="encabezado__texto anim" style="--d:1">
        Todavía no existen en <code>optica_db</code>. El criterio para usar transacción:
        <strong>¿cuántas escrituras deben verse como una sola operación?</strong>
      </p>
    </header>
    <div class="procs">{"".join(grupos)}
    </div>
  </section>"""


def slide_roles():
    tarjetas, dialogos = [], []
    for n, (rol, usuario, demos, desc, permisos, negado) in enumerate(ROLES):
        filas = "".join(
            f"""
            <li{' class="perm--exec"' if obj == "EXECUTE" else ""}><span class="perm__obj">{html.escape(obj)}</span><span class="perm__val">{"<br>".join(html.escape(v) for v in val.split(" · ")) if obj == "EXECUTE" else html.escape(val)}</span></li>"""
            for obj, val in permisos
        )
        negados = "".join(f"<span>{html.escape(x)}</span>" for x in negado)
        demo = f'<span class="proc__demo">{demos}</span>' if demos else ""
        detalle, atributos, pista = DETALLE_ROL.get(rol), "", ""
        if detalle:
            titulo_det, privs = detalle
            atributos = (f' role="button" tabindex="0" data-dialogo="dlg-{rol}"'
                         f' aria-haspopup="dialog" title="Clic para ver qué hace cada privilegio"')
            pista = '<p class="rol__pista">ⓘ clic para ver qué hace cada privilegio</p>'
            filas_det = "".join(f"""
          <li><div class="det__priv"><code>{html.escape(pr)}</code><span>{html.escape(amb)}</span></div><p>{txt}</p></li>"""
                for pr, amb, txt in privs)
            dialogos.append(f"""
    <dialog class="detalle rol--{n}" id="dlg-{rol}" aria-labelledby="dlg-{rol}-titulo">
      <div class="detalle__cab">
        <h3 id="dlg-{rol}-titulo">{titulo_det}</h3>
        <button class="detalle__cerrar" type="button" aria-label="Cerrar">&#10005;</button>
      </div>
      <ul class="detalle__lista">{filas_det}
      </ul>
    </dialog>""")
        tarjetas.append(f"""
      <li class="rol anim rol--{n}{' rol--clic' if detalle else ''}" style="--d:{n + 2}"{atributos}>
        <div class="proc__cab">
          <code class="proc__nombre">{rol}</code>
          {demo}
        </div>
        <p class="proc__firma">cuenta: {usuario}@localhost</p>
        <p class="proc__texto">{desc}</p>
        <ul class="perms">{filas}
        </ul>
        <div class="rol__negado"><b>✖</b>{negados}</div>{pista}
      </li>""")
    return f"""
  <section class="slide slide--procs" data-titulo="Roles y permisos">
    <header class="encabezado encabezado--izq">
      <p class="sobretitulo anim" style="--d:0">{TEMAS["2"][0]} · {TEMAS["2"][1]}</p>
      <h2 class="encabezado__titulo anim" style="--d:1">{len(ROLES)} roles por crear, una cuenta por rol</h2>
      <p class="encabezado__texto anim" style="--d:1">
        Los permisos se otorgan <strong>al rol</strong>; el usuario sólo lo hereda (<code>SET DEFAULT ROLE</code>).
        <span class="leyenda"><b>S</b> SELECT · <b>I</b> INSERT · <b>U</b> UPDATE · <b>D</b> DELETE · <b>*</b> sin <code>password_hash</code></span>
      </p>
    </header>
    <ol class="roles">{"".join(tarjetas)}
    </ol>{"".join(dialogos)}
  </section>"""


RE_CUENTA = re.compile(r"CREATE USER '(\w+)'@'localhost' IDENTIFIED BY '([^']+)'")


def leer_cuentas():
    """{usuario: contraseña} tomadas de los CREATE USER de demo_expo.sql."""
    return dict(RE_CUENTA.findall(SQL.read_text(encoding="utf-8")))


def campo_cred(etiqueta, valor, aviso):
    v = html.escape(valor)
    return (f'<div class="cred__campo"><span class="cred__etiqueta">{etiqueta}</span>'
            f'<code>{v}</code>'
            f'<button class="copiar cred__copiar" type="button" data-copiar="{v}" '
            f'data-aviso="{aviso}">Copiar</button></div>')


def bloque_credenciales(nombres, conexion=""):
    if not nombres:
        return ""
    cuentas = leer_cuentas()
    terminal = conexion.startswith("TERMINAL")
    donde = "Cuenta para la terminal" if terminal else "Conexión DBeaver"
    pegar = " · pégalo en la terminal" if terminal else " · pégalo en DBeaver"
    tarjetas = []
    for n in nombres:
        if n == "root":
            tarjetas.append(
                '<div class="cred"><p class="cred__conexion">Conexión DBeaver <b>localhost</b></p>'
                '<p class="cred__nota">root · la conexión de administración que ya existe</p></div>')
            continue
        if n not in cuentas:
            raise SystemExit(f"Sin CREATE USER para {n} en demo_expo.sql")
        tarjetas.append(
            f'<div class="cred"><p class="cred__conexion">{donde} <b>{html.escape(n)}</b></p>'
            f'{campo_cred("Usuario", n, "Usuario copiado" + pegar)}'
            f'{campo_cred("Contraseña", cuentas[n], "Contraseña copiada" + pegar)}</div>')
    return ('\n        <h3 class="demo__subtitulo">Credenciales</h3>\n        <div class="creds">'
            + "".join(tarjetas) + "</div>")


def slide_demo(clave, cuerpo):
    m = META[clave]
    actividad, tema = TEMAS[clave[0]]
    pasos = "\n".join(f"          <li>{p}</li>" for p in m["pasos"])
    esperados = "\n".join(
        f'          <li class="esperado esperado--{tipo}"><span class="esperado__icono">{ICONOS[tipo]}</span><span>{txt}</span></li>'
        for tipo, txt in m["esperado"]
    )
    return f"""
  <section class="slide slide--demo" data-titulo="{clave} · {html.escape(m['titulo'])}">
    <div class="demo">
      <header class="demo__cab anim" style="--d:0">
        <span class="demo__num">{clave}</span>
        <div class="demo__encabezado">
          <p class="sobretitulo">{f"{actividad} · " if actividad else ""}{tema}</p>
          <h2 class="demo__titulo">{html.escape(m['titulo'])}</h2>
        </div>
        <p class="demo__conexion"><span>Conexión</span><code>{html.escape(m['conexion'])}</code></p>
      </header>

      <aside class="demo__guia anim" style="--d:1">
        <p class="demo__objetivo">{m['objetivo']}</p>{bloque_credenciales(m.get('cuentas'), m['conexion'])}
        <h3 class="demo__subtitulo">Pasos</h3>
        <ol class="pasos">
{pasos}
        </ol>
        <h3 class="demo__subtitulo">Resultado esperado</h3>
        <ul class="esperados">
{esperados}
        </ul>
      </aside>

      <div class="codigo anim" style="--d:2">
        <div class="codigo__barra">
          <span class="codigo__puntos" aria-hidden="true"><i></i><i></i><i></i></span>
          <span class="codigo__archivo">demo_expo.sql · [{clave}]</span>
          <button class="copiar copiar--todo" type="button">Copiar todo</button>
        </div>
        <div class="codigo__cuerpo">
          {render_cuerpo(cuerpo)}
        </div>
      </div>
    </div>
  </section>"""


def main():
    bloques = leer_bloques()
    faltan = set(bloques) ^ set(META)
    if faltan:
        raise SystemExit(f"Bloques sin metadatos o metadatos sin bloque: {sorted(faltan)}")

    salida, tema_actual = [], None
    for clave, cuerpo in bloques.items():
        if not META[clave].get("diapositiva", True):
            continue
        tema = clave[0]
        if tema != tema_actual and tema in SECCIONES:
            salida.append(slide_seccion(tema, [k for k in bloques if k[0] == tema]))
            if tema == "1":
                salida.append(slide_procedimientos())
            elif tema == "2":
                salida.append(slide_roles())
        tema_actual = tema
        salida.append(slide_demo(clave, cuerpo))

    contenido = INDEX.read_text(encoding="utf-8")
    ini, fin = "<!-- DEMOS:INICIO -->", "<!-- DEMOS:FIN -->"
    a, b = contenido.index(ini) + len(ini), contenido.index(fin)
    aviso = "\n  <!-- Generado por tools/generar_demos.py a partir de demo_expo.sql. No editar a mano. -->"
    nuevo = contenido[:a] + aviso + "".join(salida) + "\n\n  " + contenido[b:]
    INDEX.write_text(nuevo, encoding="utf-8", newline="\n")
    generadas = sum(1 for k in bloques if META[k].get("diapositiva", True))
    print(f"{generadas} demos generadas en {INDEX.name}")


if __name__ == "__main__":
    main()
