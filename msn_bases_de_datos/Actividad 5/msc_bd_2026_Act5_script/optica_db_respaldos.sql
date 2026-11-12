-- =====================================================================
--  optica_db · Respaldo y restauración
--  MySQL 8.4 / InnoDB · servidor en contenedor Docker
--
--  Requisito previo: haber ejecutado, en este orden,
--    1. optica_db_scripts.sql        (estructura, particionamiento, datos)
--    2. seguridad_optica_db.sql      (roles y cuentas de usuario)
--    3. optica_db_procedimientos.sql (procedimientos almacenados)
--
--  PARTE 1  Privilegios necesarios para respaldar
--  PARTE 2  Respaldo lógico con mysqldump
--  PARTE 3  Restauración del respaldo lógico
--  PARTE 4  Respaldo físico
--  PARTE 5  Restauración del respaldo físico
--  PARTE 6  Verificación posterior a cualquier restauración
--
--  NOTA SOBRE LA NOTACIÓN
--  Los bloques encabezados con "TERMINAL" contienen comandos del
--  sistema operativo y no deben ejecutarse en el cliente de MySQL.
--  El resto son sentencias SQL.
-- =====================================================================


-- =====================================================================
--  PARTE 1 · PRIVILEGIOS NECESARIOS PARA RESPALDAR
-- =====================================================================

-- ---------------------------------------------------------------------
--  Bloque 1 · Ajuste del rol de respaldo
--
--  En la actividad anterior rol_respaldo recibió SELECT, LOCK TABLES,
--  SHOW VIEW, TRIGGER, EVENT y PROCESS, suficientes para volcar tablas
--  y disparadores. Los procedimientos almacenados creados en esta
--  actividad exigen un permiso más, que entonces no tenía objeto
--  porque no había ninguna rutina que respaldar:
--
--    SHOW_ROUTINE   permite leer el cuerpo de las rutinas; sin él,
--                   mysqldump --routines produce un volcado sin los
--                   siete procedimientos.
-- ---------------------------------------------------------------------
USE optica_db;

GRANT SHOW_ROUTINE  ON *.* TO 'rol_respaldo';

FLUSH PRIVILEGES;

SHOW GRANTS FOR 'rol_respaldo';


-- =====================================================================
--  PARTE 2 · RESPALDO LÓGICO CON mysqldump
--
--  Un respaldo lógico no copia archivos: reconstruye la base como un
--  guion de sentencias CREATE e INSERT. Es portable entre versiones y
--  plataformas, y permite restaurar objetos por separado.
-- =====================================================================

-- ---------------------------------------------------------------------
--  Bloque 2 · Estado previo al respaldo
--
--  Se registran los conteos que deberán reproducirse tras restaurar.
-- ---------------------------------------------------------------------
SELECT 'optica' AS tabla, COUNT(*) AS filas FROM optica UNION ALL
SELECT 'rol',              COUNT(*) FROM rol              UNION ALL
SELECT 'sucursal',         COUNT(*) FROM sucursal         UNION ALL
SELECT 'usuario',          COUNT(*) FROM usuario          UNION ALL
SELECT 'usuario_sucursal', COUNT(*) FROM usuario_sucursal UNION ALL
SELECT 'paciente',         COUNT(*) FROM paciente         UNION ALL
SELECT 'expediente',       COUNT(*) FROM expediente       UNION ALL
SELECT 'asiento_clinico',  COUNT(*) FROM asiento_clinico  UNION ALL
SELECT 'receta',           COUNT(*) FROM receta;

SELECT COUNT(*) AS procedimientos
FROM information_schema.ROUTINES
WHERE ROUTINE_SCHEMA = 'optica_db' AND ROUTINE_TYPE = 'PROCEDURE';

SELECT COUNT(*) AS disparadores
FROM information_schema.TRIGGERS
WHERE TRIGGER_SCHEMA = 'optica_db';

-- ---------------------------------------------------------------------
--  Bloque 3 · TERMINAL · Generación del volcado
--
--  Significado de cada opción:
--
--   --single-transaction  Abre una transacción REPEATABLE READ con una
--                         vista consistente de los datos. El respaldo
--                         es, literalmente, una transacción de solo
--                         lectura: las demás sesiones siguen
--                         escribiendo sin bloquearse y el volcado
--                         refleja el estado del instante inicial.
--                         Solo es válido con tablas InnoDB, condición
--                         que optica_db cumple por completo.
--   --routines            Incluye procedimientos y funciones. NO está
--                         activo por omisión: sin esta opción los
--                         siete procedimientos no se respaldan.
--   --triggers            Incluye los disparadores. Está activo por
--                         omisión, pero se escribe de forma explícita
--                         porque en este esquema los disparadores
--                         sustituyen a una llave foránea.
--   --events              Incluye eventos programados.
--   --databases           Antepone CREATE DATABASE y USE, necesarios
--                         para restaurar en un servidor vacío.
--   --hex-blob            Vuelca los BINARY(16) en notación
--                         hexadecimal, evitando cualquier problema de
--                         codificación con los identificadores UUID.
--   --default-character-set=utf8mb4   Conserva los acentos.
--
--  Las credenciales no se escriben en la línea de comandos: cualquier
--  usuario del sistema podría leerlas con ps. Se colocan en un archivo
--  de opciones con permisos 600, propiedad de la cuenta que ejecuta el
--  respaldo programado:
--
--    # /etc/mysql/respaldo.cnf   (chmod 600)
--    [mysqldump]
--    user=usr_respaldo
--    password=Cambiar#Backup_2026
-- ---------------------------------------------------------------------
-- docker exec mysql-optica mysqldump \
--   --defaults-extra-file=/etc/mysql/respaldo.cnf \
--   --single-transaction \
--   --routines --triggers --events \
--   --hex-blob \
--   --default-character-set=utf8mb4 \
--   --databases optica_db > optica_db_logico_20260923.sql

-- ---------------------------------------------------------------------
--  Bloque 4 · TERMINAL · Comprobación del contenido del volcado
--
--  La tercera consulta es la más importante de este bloque: mysqldump
--  conserva la cláusula TABLESPACE dentro de cada CREATE TABLE, pero
--  NO genera las sentencias CREATE TABLESPACE. Restaurar el archivo en
--  un servidor limpio falla porque los cuatro tablespaces generales no
--  existen todavía. De ahí el bloque 5.
-- ---------------------------------------------------------------------
-- grep -c "CREATE TABLE"      optica_db_logico_20260923.sql   # 9
-- grep -c "CREATE PROCEDURE"  optica_db_logico_20260923.sql   # 7
-- grep -c "CREATE.*TRIGGER"   optica_db_logico_20260923.sql   # 3
-- grep -c "CREATE TABLESPACE" optica_db_logico_20260923.sql   # 0
-- grep -n  "TABLESPACE"       optica_db_logico_20260923.sql | head


-- =====================================================================
--  PARTE 3 · RESTAURACIÓN DEL RESPALDO LÓGICO
-- =====================================================================

-- ---------------------------------------------------------------------
--  Bloque 5 · Preparación del servidor destino
--
--  Se ejecuta ANTES del volcado, sobre el servidor limpio, para crear
--  los tablespaces generales que mysqldump no incluye. Son las mismas
--  sentencias de optica_db_scripts.sql.
-- ---------------------------------------------------------------------
CREATE TABLESPACE ts_catalogo  ADD DATAFILE 'ts_catalogo.ibd'  ENGINE = InnoDB;
CREATE TABLESPACE ts_pacientes ADD DATAFILE 'ts_pacientes.ibd' ENGINE = InnoDB;
CREATE TABLESPACE ts_clinico   ADD DATAFILE 'ts_clinico.ibd'   ENGINE = InnoDB;
CREATE TABLESPACE ts_receta    ADD DATAFILE 'ts_receta.ibd'    ENGINE = InnoDB;

-- ---------------------------------------------------------------------
--  Bloque 6 · TERMINAL · Restauración
--
--  La restauración se ejecuta con una cuenta administrativa: usr_dba.
--  usr_respaldo es de solo lectura y no puede crear objetos, lo cual
--  es deliberado y coherente con el principio del menor privilegio.
--
--  El volcado desactiva temporalmente la verificación de llaves
--  foráneas, de modo que el orden alfabético en que crea las tablas no
--  provoca errores de referencia.
-- ---------------------------------------------------------------------
-- # 1. Servidor limpio (ADVERTENCIA: -v elimina el volumen de datos)
-- docker compose down -v
-- docker compose up -d
--
-- # 2. Tablespaces generales (bloque 5)
-- docker exec -i mysql-optica mysql -uroot -poptica123 < 00_tablespaces.sql
--
-- # 3. Volcado completo
-- docker exec -i mysql-optica mysql -uroot -poptica123 < optica_db_logico_20260923.sql
--
-- # 4. Cuentas y roles (no viajan en el volcado: residen en el
-- #    esquema mysql, no en optica_db)
-- docker exec -i mysql-optica mysql -uroot -poptica123 < seguridad_optica_db.sql

-- ---------------------------------------------------------------------
--  Bloque 7 · Restauración selectiva de un solo objeto
--
--  Ventaja característica del respaldo lógico: permite recuperar un
--  objeto sin tocar el resto de la base. El volcado es texto, de modo
--  que basta extraer el fragmento correspondiente y ejecutarlo.
-- ---------------------------------------------------------------------
-- sed -n '/CREATE.*PROCEDURE.*sp_registrar_consulta/,/END ;;/p' \
--   optica_db_logico_20260923.sql > sp_registrar_consulta.sql
-- docker exec -i mysql-optica mysql -uroot -poptica123 optica_db < sp_registrar_consulta.sql


-- =====================================================================
--  PARTE 4 · RESPALDO FÍSICO
--
--  Un respaldo físico copia los archivos del directorio de datos: los
--  .ibd de cada tablespace, el registro de rehacer y el diccionario de
--  datos. Es mucho más rápido de restaurar en bases grandes, pero está
--  atado a la versión y a la plataforma del servidor de origen.
-- =====================================================================

-- ---------------------------------------------------------------------
--  Bloque 8 · Ubicación física de los objetos
--
--  Antes de copiar conviene saber qué archivos componen la base. Las
--  ocho tablas de tablespaces generales residen en cuatro archivos
--  compartidos; receta, al particionarse, quedó en archivos propios,
--  uno por partición.
-- ---------------------------------------------------------------------
SELECT s.NAME AS tablespace, d.PATH AS archivo,
       s.FILE_SIZE / 1024 / 1024 AS tamano_mb
FROM information_schema.INNODB_TABLESPACES s
LEFT JOIN information_schema.INNODB_DATAFILES d ON d.SPACE = s.SPACE
WHERE s.NAME IN ('ts_catalogo', 'ts_pacientes', 'ts_clinico', 'ts_receta')
   OR s.NAME LIKE 'optica_db/%'
ORDER BY s.NAME;

-- ---------------------------------------------------------------------
--  Bloque 9 · TERMINAL · Copia en frío
--
--  Es el respaldo físico más simple y el único que no requiere
--  herramientas adicionales: se detiene el servidor y se copia el
--  directorio de datos completo. Su costo es la indisponibilidad
--  durante la copia.
--
--  Detener el servidor de forma ordenada es indispensable: garantiza
--  que InnoDB vacíe el búfer y cierre el registro de rehacer, de modo
--  que los archivos queden en un estado consistente.
-- ---------------------------------------------------------------------
-- # 1. Detener el servidor
-- docker compose stop mysql
--
-- # 2. Comprimir el volumen de datos desde un contenedor auxiliar
-- docker run --rm \
--   -v act5_mysql_optica_data:/var/lib/mysql:ro \
--   -v "$PWD":/respaldo \
--   alpine tar czf /respaldo/optica_db_fisico_20260923.tar.gz -C /var/lib/mysql .
--
-- # 3. Reanudar el servicio
-- docker compose start mysql
--
-- # 4. Comprobar el archivo generado
-- ls -lh optica_db_fisico_20260923.tar.gz


-- =====================================================================
--  PARTE 5 · RESTAURACIÓN DEL RESPALDO FÍSICO
-- =====================================================================

-- ---------------------------------------------------------------------
--  Bloque 10 · TERMINAL · Restauración de la copia en frío
--
--  Se sustituye íntegramente el contenido del volumen de datos. El
--  servidor debe estar detenido: escribir sobre el directorio de datos
--  de un servidor en marcha corrompe la base.
-- ---------------------------------------------------------------------
-- # 1. Detener el servicio y eliminar el volumen dañado
-- docker compose down
-- docker volume rm act5_mysql_optica_data
-- docker volume create act5_mysql_optica_data
--
-- # 2. Extraer el respaldo dentro del volumen nuevo
-- docker run --rm \
--   -v act5_mysql_optica_data:/var/lib/mysql \
--   -v "$PWD":/respaldo \
--   alpine tar xzf /respaldo/optica_db_fisico_20260923.tar.gz -C /var/lib/mysql
--
-- # 3. Arrancar el servidor
-- docker compose up -d
-- docker compose logs -f mysql


-- =====================================================================
--  PARTE 6 · VERIFICACIÓN POSTERIOR A CUALQUIER RESTAURACIÓN
--
--  Las mismas consultas deben ejecutarse en el servidor restaurado y
--  sus resultados compararse con los del bloque 2. Un respaldo no se
--  considera válido mientras no se haya restaurado y verificado.
-- =====================================================================

-- ---------------------------------------------------------------------
--  Bloque 11 · Integridad de la estructura
-- ---------------------------------------------------------------------
USE optica_db;

-- Tablas y su tablespace
SELECT t.NAME AS tabla, s.NAME AS tablespace
FROM information_schema.INNODB_TABLES t
JOIN information_schema.INNODB_TABLESPACES s ON s.SPACE = t.SPACE
WHERE t.NAME LIKE 'optica_db/%'
ORDER BY s.NAME, t.NAME;

-- Particiones de receta y reparto de filas
SELECT PARTITION_NAME, PARTITION_METHOD, TABLE_ROWS
FROM information_schema.PARTITIONS
WHERE TABLE_SCHEMA = 'optica_db' AND TABLE_NAME = 'receta';

-- Restricciones de verificación
SELECT CONSTRAINT_NAME, CHECK_CLAUSE
FROM information_schema.CHECK_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA = 'optica_db'
ORDER BY CONSTRAINT_NAME;

-- Disparadores que sustituyen a la llave foránea de receta
SELECT TRIGGER_NAME, EVENT_MANIPULATION, EVENT_OBJECT_TABLE, ACTION_TIMING
FROM information_schema.TRIGGERS
WHERE TRIGGER_SCHEMA = 'optica_db'
ORDER BY TRIGGER_NAME;

-- Procedimientos almacenados
SELECT ROUTINE_NAME, SECURITY_TYPE
FROM information_schema.ROUTINES
WHERE ROUTINE_SCHEMA = 'optica_db' AND ROUTINE_TYPE = 'PROCEDURE'
ORDER BY ROUTINE_NAME;

-- ---------------------------------------------------------------------
--  Bloque 12 · Integridad de los datos
-- ---------------------------------------------------------------------
SELECT 'optica' AS tabla, COUNT(*) AS filas FROM optica UNION ALL
SELECT 'rol',              COUNT(*) FROM rol              UNION ALL
SELECT 'sucursal',         COUNT(*) FROM sucursal         UNION ALL
SELECT 'usuario',          COUNT(*) FROM usuario          UNION ALL
SELECT 'usuario_sucursal', COUNT(*) FROM usuario_sucursal UNION ALL
SELECT 'paciente',         COUNT(*) FROM paciente         UNION ALL
SELECT 'expediente',       COUNT(*) FROM expediente       UNION ALL
SELECT 'asiento_clinico',  COUNT(*) FROM asiento_clinico  UNION ALL
SELECT 'receta',           COUNT(*) FROM receta;

-- Asientos sin receta. El resultado no es cero: asi-09 es una revisión
-- de rutina que no generó corrección. Lo que se comprueba es que el
-- conteo coincida con el registrado antes del respaldo.
SELECT COUNT(*) AS asientos_sin_receta
FROM asiento_clinico a
LEFT JOIN receta r ON r.asiento_id = a.id
WHERE r.id IS NULL;

-- ---------------------------------------------------------------------
--  Bloque 13 · Prueba funcional sobre el servidor restaurado
--
--  La verificación definitiva no es contar filas, sino comprobar que
--  la base sigue siendo operable: se ejecuta un procedimiento
--  transaccional y se confirma que escribe correctamente.
-- ---------------------------------------------------------------------
CALL sp_buscar_paciente(BIN_TO_UUID(UNHEX(MD5('opt-01'))), 'Juan');

CALL sp_alta_paciente_con_expediente(
  BIN_TO_UUID(UNHEX(MD5('opt-01'))), 'Verificacion Restauracion',
  '1980-01-01', 'M', '3510000001', 'verificacion@correo.com', NULL,
  @pac_ver, @folio_ver);

SELECT @pac_ver AS paciente_id, @folio_ver AS folio_asignado;
