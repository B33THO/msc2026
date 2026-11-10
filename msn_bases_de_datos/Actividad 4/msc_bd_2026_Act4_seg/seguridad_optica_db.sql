-- =====================================================================
--  optica_db · SEGURIDAD: usuarios, roles y permisos · MySQL 8.0
--  Ejecutar DESPUÉS de crear_optica_db.sql, con un usuario que tenga
--  CREATE USER, CREATE ROLE y GRANT OPTION (p. ej. root).
--
--  Principios aplicados:
--    1. Mínimo privilegio: cada rol recibe solo lo que necesita.
--    2. Permisos por ROL, no por usuario: los usuarios solo heredan.
--    3. Datos clínicos protegidos: recepción y administración no los ven.
--    4. Expediente clínico inmutable: ningún rol operativo hace DELETE
--       sobre asiento_clinico ni receta.
--    5. password_hash nunca se puede leer (solo escribir).
--    6. Cuentas con política de contraseñas, bloqueo e host restringido.
-- =====================================================================

USE optica_db;

-- ---------------------------------------------------------------------
-- 1. ROLES
--    (CREATE ROLE crea cuentas bloqueadas: nadie puede iniciar sesión
--     con un rol, solo sirven para agrupar permisos)
-- ---------------------------------------------------------------------
CREATE ROLE IF NOT EXISTS
  'rol_admin_app',       -- administra catálogos y usuarios de la óptica
  'rol_optometrista',    -- consulta clínica: asientos y recetas
  'rol_recepcion',       -- alta de pacientes y expedientes
  'rol_auditor',         -- solo lectura, sin credenciales
  'rol_respaldo';        -- exclusivo para mysqldump / backups

-- ---------------------------------------------------------------------
-- 2. PERMISOS POR ROL
-- ---------------------------------------------------------------------

-- ===== rol_admin_app ==================================================
-- Gestiona la estructura de la óptica y las cuentas, NO ve datos clínicos.
GRANT SELECT, INSERT, UPDATE ON optica_db.optica   TO 'rol_admin_app';
GRANT SELECT, INSERT, UPDATE ON optica_db.sucursal TO 'rol_admin_app';
GRANT SELECT, INSERT, UPDATE ON optica_db.rol      TO 'rol_admin_app';
GRANT SELECT, INSERT, DELETE ON optica_db.usuario_sucursal TO 'rol_admin_app';

-- usuario: puede crear y editar (incluido password_hash) pero NO leerlo
GRANT SELECT (id, optica_id, rol_id, nombre, correo, activo)
  ON optica_db.usuario TO 'rol_admin_app';
GRANT INSERT, UPDATE ON optica_db.usuario TO 'rol_admin_app';

-- ===== rol_optometrista ===============================================
-- Catálogos: solo lectura
GRANT SELECT ON optica_db.optica            TO 'rol_optometrista';
GRANT SELECT ON optica_db.sucursal          TO 'rol_optometrista';
GRANT SELECT ON optica_db.usuario_sucursal  TO 'rol_optometrista';
GRANT SELECT (id, nombre) ON optica_db.usuario TO 'rol_optometrista';

-- Pacientes y expedientes: lectura
GRANT SELECT ON optica_db.paciente   TO 'rol_optometrista';
GRANT SELECT ON optica_db.expediente TO 'rol_optometrista';

-- Clínico y receta: leer, crear y corregir; nunca borrar
GRANT SELECT, INSERT, UPDATE ON optica_db.asiento_clinico TO 'rol_optometrista';
GRANT SELECT, INSERT, UPDATE ON optica_db.receta          TO 'rol_optometrista';

-- ===== rol_recepcion ==================================================
GRANT SELECT ON optica_db.optica   TO 'rol_recepcion';
GRANT SELECT ON optica_db.sucursal TO 'rol_recepcion';
GRANT SELECT (id, nombre) ON optica_db.usuario TO 'rol_recepcion';

GRANT SELECT, INSERT, UPDATE ON optica_db.paciente   TO 'rol_recepcion';
GRANT SELECT, INSERT         ON optica_db.expediente TO 'rol_recepcion';

-- Solo la receta (para entregarla / cotizar lentes). SIN asiento_clinico.
GRANT SELECT ON optica_db.receta TO 'rol_recepcion';

-- ===== rol_auditor ====================================================
-- Lectura total, excepto password_hash
GRANT SELECT ON optica_db.optica           TO 'rol_auditor';
GRANT SELECT ON optica_db.sucursal         TO 'rol_auditor';
GRANT SELECT ON optica_db.rol              TO 'rol_auditor';
GRANT SELECT ON optica_db.usuario_sucursal TO 'rol_auditor';
GRANT SELECT ON optica_db.paciente         TO 'rol_auditor';
GRANT SELECT ON optica_db.expediente       TO 'rol_auditor';
GRANT SELECT ON optica_db.asiento_clinico  TO 'rol_auditor';
GRANT SELECT ON optica_db.receta           TO 'rol_auditor';
GRANT SELECT (id, optica_id, rol_id, nombre, correo, activo)
  ON optica_db.usuario TO 'rol_auditor';

-- ===== rol_respaldo ===================================================
-- Mínimo que necesita mysqldump --single-transaction --routines --triggers
GRANT SELECT, LOCK TABLES, SHOW VIEW, TRIGGER, EVENT
  ON optica_db.* TO 'rol_respaldo';
GRANT PROCESS ON *.* TO 'rol_respaldo';

-- ---------------------------------------------------------------------
-- 3. USUARIOS
--    · Contraseñas de ejemplo: CÁMBIALAS antes de usar en producción.
--    · Host 'localhost'; si la app está en otro servidor, usa su IP
--      (nunca '%') y añade REQUIRE SSL.
--    · Política: expira a 90 días, no repetir las últimas 5, se bloquea
--      1 día tras 5 intentos fallidos.
-- ---------------------------------------------------------------------

-- DBA: control total sobre optica_db (sin acceso a otras bases)
CREATE USER IF NOT EXISTS 'usr_dba'@'localhost'
  IDENTIFIED BY 'Cambiar#DBA_2026'
  PASSWORD EXPIRE INTERVAL 90 DAY
  PASSWORD HISTORY 5
  FAILED_LOGIN_ATTEMPTS 5 PASSWORD_LOCK_TIME 1;
GRANT ALL PRIVILEGES ON optica_db.* TO 'usr_dba'@'localhost';

-- Administrador de la aplicación
-- PASSWORD EXPIRE / PASSWORD HISTORY / FAILED_LOGIN_ATTEMPTS.
CREATE USER IF NOT EXISTS 'usr_admin'@'localhost'
  IDENTIFIED BY 'Cambiar#Admin_2026'
  WITH MAX_USER_CONNECTIONS 5
  PASSWORD EXPIRE INTERVAL 90 DAY
  PASSWORD HISTORY 5
  FAILED_LOGIN_ATTEMPTS 5 PASSWORD_LOCK_TIME 1;
GRANT 'rol_admin_app' TO 'usr_admin'@'localhost';
SET DEFAULT ROLE 'rol_admin_app' TO 'usr_admin'@'localhost';

-- Optometrista
CREATE USER IF NOT EXISTS 'usr_optometrista1'@'localhost'
  IDENTIFIED BY 'Cambiar#Opto_2026'
  WITH MAX_USER_CONNECTIONS 5
  PASSWORD EXPIRE INTERVAL 90 DAY
  PASSWORD HISTORY 5
  FAILED_LOGIN_ATTEMPTS 5 PASSWORD_LOCK_TIME 1;
GRANT 'rol_optometrista' TO 'usr_optometrista1'@'localhost';
SET DEFAULT ROLE 'rol_optometrista' TO 'usr_optometrista1'@'localhost';

-- Recepción
CREATE USER IF NOT EXISTS 'usr_recepcion1'@'localhost'
  IDENTIFIED BY 'Cambiar#Recep_2026'
  WITH MAX_USER_CONNECTIONS 5
  PASSWORD EXPIRE INTERVAL 90 DAY
  PASSWORD HISTORY 5
  FAILED_LOGIN_ATTEMPTS 5 PASSWORD_LOCK_TIME 1;
GRANT 'rol_recepcion' TO 'usr_recepcion1'@'localhost';
SET DEFAULT ROLE 'rol_recepcion' TO 'usr_recepcion1'@'localhost';

-- Auditor
CREATE USER IF NOT EXISTS 'usr_auditor'@'localhost'
  IDENTIFIED BY 'Cambiar#Audit_2026'
  WITH MAX_USER_CONNECTIONS 2
  PASSWORD EXPIRE INTERVAL 90 DAY
  PASSWORD HISTORY 5
  FAILED_LOGIN_ATTEMPTS 5 PASSWORD_LOCK_TIME 1;
GRANT 'rol_auditor' TO 'usr_auditor'@'localhost';
SET DEFAULT ROLE 'rol_auditor' TO 'usr_auditor'@'localhost';

-- Respaldos (cuenta técnica: la contraseña no expira para no romper el cron)
CREATE USER IF NOT EXISTS 'usr_respaldo'@'localhost'
  IDENTIFIED BY 'Cambiar#Backup_2026'
  WITH MAX_USER_CONNECTIONS 2
  PASSWORD EXPIRE NEVER
  FAILED_LOGIN_ATTEMPTS 5 PASSWORD_LOCK_TIME 1;
GRANT 'rol_respaldo' TO 'usr_respaldo'@'localhost';
SET DEFAULT ROLE 'rol_respaldo' TO 'usr_respaldo'@'localhost';

FLUSH PRIVILEGES;

-- ---------------------------------------------------------------------
-- 4. VERIFICACIÓN
-- ---------------------------------------------------------------------
-- Permisos efectivos de cada usuario (con los de su rol)
SHOW GRANTS FOR 'usr_admin'@'localhost'        USING 'rol_admin_app';
SHOW GRANTS FOR 'usr_optometrista1'@'localhost' USING 'rol_optometrista';
SHOW GRANTS FOR 'usr_recepcion1'@'localhost'   USING 'rol_recepcion';
SHOW GRANTS FOR 'usr_auditor'@'localhost'      USING 'rol_auditor';
SHOW GRANTS FOR 'usr_respaldo'@'localhost'     USING 'rol_respaldo';

-- Qué rol tiene OTORGADO cada usuario, y cuál queda ACTIVO por defecto
-- (son dos tablas distintas del catálogo: role_edges vs default_roles)
SELECT re.TO_USER AS usuario,
       re.FROM_USER AS rol_otorgado,
       dr.DEFAULT_ROLE_USER AS rol_activo_por_defecto
FROM mysql.role_edges re
LEFT JOIN mysql.default_roles dr
  ON dr.USER = re.TO_USER AND dr.HOST = re.TO_HOST
ORDER BY usuario;

-- Políticas de cada cuenta
SELECT user, host, password_lifetime, password_lock_time_days,
       account_locked, password_expired
FROM mysql.user
WHERE user LIKE 'usr\_%'
ORDER BY user;

