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
| `icons/` | — | Iconos de la interfaz |

Flujo de las llamadas:

```
ui  →  services  →  repositories  →  db (MySQL)
          ↑ objetos de domain/ viajan entre capas ↑
```
