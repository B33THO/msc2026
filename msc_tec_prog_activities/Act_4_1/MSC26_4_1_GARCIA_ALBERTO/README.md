# Programa Cuentas

Aplicación de escritorio para administrar cuentas de ahorro y de crédito.
Hecha con **Python + PyQt6 (Qt Designer) + MySQL**, siguiendo la arquitectura **MVR (Modelo - Vista - Repositorio)**.

## Requisitos

- Python 3.12 o superior (desarrollado con 3.15)
- MySQL Server 8 o superior
- Qt Designer (opcional, solo para editar las ventanas `.ui`)

## Instalación

### 1. Crear y activar el entorno virtual

Desde la carpeta `MSC26_4_1_GARCIA_ALBERTO/`:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

En macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar las dependencias

```powershell
pip install -r requirements.txt
```

O una por una:

```powershell
pip install mysql-connector-python   # conexión a MySQL
pip install python-dotenv            # leer credenciales del archivo .env
pip install PyQt6                    # interfaz gráfica
pip install openpyxl                 # leer/guardar archivos .xlsx
```

> Qt Designer no viene con PyQt6. Se puede instalar con `pip install pyqt6-tools`
> o descargar por separado desde Qt.

### 3. Crear la base de datos

Ejecutar el script en MySQL (Workbench o consola):

```powershell
mysql -u root -p < db/script.sql
```

Esto crea la base de datos `BankAccounts` con las tablas `Client`, `Account` y `CreditAccount`.

> ⚠️ El script empieza con `DROP DATABASE IF EXISTS BankAccounts`: si se vuelve a ejecutar, **borra todos los datos**.

### 4. Configurar el archivo `.env`

Crear un archivo `.env` en `MSC26_4_1_GARCIA_ALBERTO/` con las credenciales de MySQL:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=tu_contraseña
DB_DATABASE=BankAccounts
```

El archivo `.env` está en `.gitignore` y **no se sube al repositorio**.

## Ejecución

```powershell
python main.py
```

El programa debe llamar a `load_dotenv()` (de `python-dotenv`) al iniciar, antes de crear `Connection`,
para que `os.getenv()` encuentre las variables del `.env`.

Al arrancar, `main.py` también carga la hoja de estilos `ui/styles.qss` y registra la carpeta `icons/`
con el prefijo `icons:` (`QDir.addSearchPath`), por lo que el programa se puede ejecutar desde cualquier carpeta.

## Exportar e importar (CSV / XLSX)

Los botones **Exportar** e **Importar** (también en el menú) guardan y cargan las cuentas en archivos `.csv` o `.xlsx`.
Se exporta lo que se ve en la tabla, es decir, respeta el filtro o la búsqueda activa.

Columnas del archivo (en este orden, la primera fila es el encabezado):

| Columna | Ejemplo | Notas |
| :--- | :--- | :--- |
| No. Cuenta | `1005` | Opcional. Si ya existe en la BD la fila **se omite**; si viene vacío se genera un número nuevo |
| Apellido paterno | `BRONCA` | Requerido |
| Apellido materno | `SEGURA` | Requerido |
| Nombre | `ARMANDO` | Requerido |
| Tipo | `AHORRO` / `CREDITO` | También acepta `CRÉDITO` |
| Saldo | `5000.00` | Sin signo de moneda ni separador de miles |
| Límite de crédito | `20000.00` | Solo cuentas de crédito |
| Adeudo | `0.00` | Solo cuentas de crédito; vacío se toma como 0 |
| Fecha de apertura | `2024-09-12` | `AAAA-MM-DD` o `DD/MM/AAAA`; vacío se toma la fecha de hoy |

- Como el archivo lleva el número de cuenta, volver a importar un archivo exportado **no duplica cuentas**:
  las que ya existen se omiten y el resumen indica cuántas.
- Cada fila se guarda en su propia transacción (cliente + cuenta). Una fila con error no detiene la importación;
  al final se muestra la lista de filas con error.
- `data/cuentas.csv` es un ejemplo con las cuentas 1000 - 1009 de `script.sql`.

## Reglas de negocio

- Cada cliente tiene una sola cuenta (de ahorro o de crédito); al eliminar la cuenta se elimina también el cliente.
- Las cantidades no pueden ser negativas ni mayores a **99,999,999.99** (máximo de `DECIMAL(10,2)`);
  un depósito tampoco puede dejar el saldo por encima de ese máximo.
- En cuentas de crédito los depósitos primero pagan el adeudo y los retiros se toman primero del saldo
  y luego del crédito disponible.
- El monto de crédito no puede quedar por debajo del adeudo.
- Al editar una cuenta, el nombre del cliente y el monto de crédito se guardan juntos en una transacción:
  si el monto es inválido no se cambia nada.
- La fecha de apertura no puede ser posterior a hoy ni anterior al 01/01/1900.

## Estructura del proyecto (MVR)

| Carpeta | Capa | Propósito |
| :--- | :--- | :--- |
| `domain/` | **Modelo** | Clases Cliente, Cuenta (ahorro) y CuentaCredito |
| `repositories/` | **Repositorio** | Único lugar con SQL (CRUD y consultas). Usa `db/Connection` y devuelve objetos de `domain/` |
| `ui/` | **Vista** | Ventanas, formularios y tabla. Llama a `services/`, nunca a `db/` |
| `services/` | Negocio | Depósitos, retiros y validaciones de saldo/crédito. Llama a `repositories/` |
| `db/` | Infraestructura | `Connection.py` (conexión a MySQL) y `script.sql` |
| `utilities/` | Apoyo | Validación de campos, lectura/escritura de CSV/XLSX |
| `data/` | — | Archivos `.csv` / `.xlsx` que se cargan o guardan |
| `icons/` | — | Iconos de la interfaz (se usan en los `.ui` y en `ui/styles.qss`) |

Flujo de las llamadas:

```
ui  →  services  →  repositories  →  db (MySQL)
          ↑ objetos de domain/ viajan entre capas ↑
```
