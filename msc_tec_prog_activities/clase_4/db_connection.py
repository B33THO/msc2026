# import psycopg2
#
# try:
#     config_conexion = {
#         "host": "localhost",
#         "database": "tdpdb",
#         "user": "postgres",
#         "password": "31416nche",
#         "port": 5432
#     }
#
#     try:
#         # 2. Conexión y cursor dentro del contexto 'with'
#         with psycopg2.connect(**config_conexion) as conn:
#             with conn.cursor() as cursor:
#                 # Consulta 1: Versión de PostgreSQL
#                 cursor.execute("SELECT version();")
#                 version = cursor.fetchone()
#                 print(f"Conexión exitosa. Versión: {version[0]}\n")
#
#                 # Consulta 2: Obtener los datos ingresados
#                 cursor.execute("SELECT clave, nombre, carrera, municipio, edad FROM datos;")
#                 registros = cursor.fetchall()
#
#                 for fila in registros:
#                     print(
#                         f"Clave: {fila[0]} | Nombre: {fila[1]} | Carrera: {fila[2]} | Municipio: {fila[3]} | Edad: {fila[4]}")
#
#     except Exception as e:
#         print(f"Error al conectar o consultar PostgreSQL: {e}")
#
#
# except Exception as e:
#     print(f"Error al conectar a PostgreSQL: {e}")