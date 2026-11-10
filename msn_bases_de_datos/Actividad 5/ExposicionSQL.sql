-- ============================================================
-- SISTEMA POS - SCRIPT DE CONFIGURACIÓN COMPLETA
-- ============================================================
-- Orden de ejecución:
-- 1. Creación de base de datos y tablas
-- 2. Creación de usuarios MySQL base
-- 3. Procedimientos de gestión de usuarios
-- 4. Procedimientos de negocio
-- 5. Ejemplos y pruebas
-- ============================================================

-- ============================================================
-- PASO 1: CREAR BASE DE DATOS Y TABLAS
-- ============================================================
CREATE DATABASE IF NOT EXISTS pos_system;
USE pos_system;

-- Tabla principal de cuentas
CREATE TABLE IF NOT EXISTS cuentas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100),
    saldo DECIMAL(10,2) DEFAULT 0.00
);

-- Insertar datos iniciales
INSERT INTO cuentas (nombre, saldo)
VALUES 
('Caja Principal', 5000.00),
('Caja Secundaria', 2000.00)
ON DUPLICATE KEY UPDATE saldo = VALUES(saldo);

-- ============================================================
-- PASO 2: CREAR USUARIOS MYSQL BASE Y ASIGNAR PRIVILEGIOS
-- ============================================================
CREATE USER IF NOT EXISTS 'admin_pos'@'localhost' IDENTIFIED BY 'Admin123!';
CREATE USER IF NOT EXISTS 'cajero_pos'@'localhost' IDENTIFIED BY 'Cajero123!';
CREATE USER IF NOT EXISTS 'supervisor_pos'@'localhost' IDENTIFIED BY 'Super123!';

-- Asignar privilegios según roles
GRANT ALL PRIVILEGES ON pos_system.* TO 'admin_pos'@'localhost';
GRANT SELECT, INSERT ON pos_system.* TO 'cajero_pos'@'localhost';
GRANT SELECT, UPDATE ON pos_system.* TO 'supervisor_pos'@'localhost';

-- Privilegio adicional para cajeros (UPDATE necesario para algunas operaciones)
GRANT UPDATE ON pos_system.* TO 'cajero_pos'@'localhost';

-- Aplicar cambios inmediatamente
FLUSH PRIVILEGES;

-- ============================================================
-- PASO 3: PROCEDIMIENTOS DE GESTIÓN DE USUARIOS MYSQL
-- ============================================================
USE pos_system;

DELIMITER $$

-- Procedimiento para registrar nuevos usuarios en el sistema
DROP PROCEDURE IF EXISTS RegistrarUsuarioSistema$$
CREATE PROCEDURE RegistrarUsuarioSistema(
    IN p_username VARCHAR(50),
    IN p_password VARCHAR(50),
    IN p_host VARCHAR(50),
    IN p_role ENUM('admin','cajero','supervisor')
)
BEGIN
    -- Validar si el usuario MySQL ya existe
    IF EXISTS (SELECT 1 FROM mysql.user WHERE user = p_username AND host = p_host) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'El usuario ya existe en el sistema MySQL';
    END IF;

    START TRANSACTION;

    -- Crear usuario MySQL
    SET @create_sql = CONCAT(
        "CREATE USER '", p_username, "'@'", p_host,
        "' IDENTIFIED BY '", p_password, "';"
    );
    PREPARE stmt FROM @create_sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    -- Asignar permisos según el rol
    IF p_role = 'admin' THEN
        SET @grant_sql = CONCAT("GRANT ALL PRIVILEGES ON pos_system.* TO '", p_username, "'@'", p_host, "';");
    ELSEIF p_role = 'supervisor' THEN
        SET @grant_sql = CONCAT("GRANT SELECT, UPDATE ON pos_system.* TO '", p_username, "'@'", p_host, "';");
    ELSEIF p_role = 'cajero' THEN
        SET @grant_sql = CONCAT("GRANT SELECT, INSERT ON pos_system.* TO '", p_username, "'@'", p_host, "';");
    ELSE
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Rol no válido. Use admin, supervisor o cajero';
    END IF;

    PREPARE stmt2 FROM @grant_sql;
    EXECUTE stmt2;
    DEALLOCATE PREPARE stmt2;

    COMMIT;

    SELECT CONCAT('Usuario "', p_username, '" creado exitosamente con rol "', p_role, '"') AS mensaje;
END$$

-- Procedimiento para eliminar usuarios del sistema
DROP PROCEDURE IF EXISTS EliminarUsuarioSistema$$
CREATE PROCEDURE EliminarUsuarioSistema(
    IN p_username VARCHAR(50),
    IN p_host VARCHAR(50)
)
BEGIN
    -- Validar que el usuario MySQL exista
    IF NOT EXISTS (SELECT 1 FROM mysql.user WHERE user = p_username AND host = p_host) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'El usuario MySQL no existe';
    END IF;

    START TRANSACTION;

    -- Eliminar usuario MySQL usando PREPARE
    SET @drop_sql = CONCAT("DROP USER '", p_username, "'@'", p_host, "';");
    PREPARE stmt FROM @drop_sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    COMMIT;

    SELECT CONCAT('Usuario "', p_username, '" eliminado correctamente') AS mensaje;
END$$

-- Procedimiento para actualizar permisos de usuarios existentes
DROP PROCEDURE IF EXISTS ActualizarPermisosUsuario$$
CREATE PROCEDURE ActualizarPermisosUsuario(
    IN p_username VARCHAR(50),
    IN p_host VARCHAR(50),
    IN p_nuevo_rol ENUM('admin','cajero','supervisor')
)
BEGIN
    -- Validar que el usuario MySQL exista
    IF NOT EXISTS (SELECT 1 FROM mysql.user WHERE user = p_username AND host = p_host) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'El usuario MySQL no existe';
    END IF;

    START TRANSACTION;

    -- Revocar todos los permisos actuales del usuario
    SET @revoke_sql = CONCAT("REVOKE ALL PRIVILEGES ON pos_system.* FROM '", p_username, "'@'", p_host, "';");
    PREPARE stmt_revoke FROM @revoke_sql;
    EXECUTE stmt_revoke;
    DEALLOCATE PREPARE stmt_revoke;

    -- Asignar nuevos permisos según el rol
    IF p_nuevo_rol = 'admin' THEN
        SET @grant_sql = CONCAT("GRANT ALL PRIVILEGES ON pos_system.* TO '", p_username, "'@'", p_host, "';");
    ELSEIF p_nuevo_rol = 'supervisor' THEN
        SET @grant_sql = CONCAT("GRANT SELECT, UPDATE ON pos_system.* TO '", p_username, "'@'", p_host, "';");
    ELSEIF p_nuevo_rol = 'cajero' THEN
        SET @grant_sql = CONCAT("GRANT SELECT, INSERT ON pos_system.* TO '", p_username, "'@'", p_host, "';");
    ELSE
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Rol no válido. Use admin, supervisor o cajero';
    END IF;

    PREPARE stmt_grant FROM @grant_sql;
    EXECUTE stmt_grant;
    DEALLOCATE PREPARE stmt_grant;

    -- Aplicar cambios inmediatamente
    FLUSH PRIVILEGES;

    COMMIT;

    SELECT CONCAT('Permisos actualizados para usuario "', p_username, '" con rol "', p_nuevo_rol, '"') AS mensaje;
END$$

-- ============================================================
-- PASO 4: PROCEDIMIENTOS DE NEGOCIO
-- ============================================================

-- Procedimiento para transferir fondos entre cuentas
DROP PROCEDURE IF EXISTS TransferirFondos$$
CREATE PROCEDURE TransferirFondos(
    IN cuentaOrigen INT,
    IN cuentaDestino INT,
    IN monto DECIMAL(10,2)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SELECT 'Ocurrió un error: Transacción revertida' AS mensaje;
    END;

    START TRANSACTION;

    IF (SELECT COALESCE(saldo,0) FROM cuentas WHERE id = cuentaOrigen) < monto THEN -- COALESCE devuelve el primer valor no null
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Saldo insuficiente en la cuenta origen';
    END IF;

    UPDATE cuentas SET saldo = saldo - monto WHERE id = cuentaOrigen;
    UPDATE cuentas SET saldo = saldo + monto WHERE id = cuentaDestino;

    COMMIT;
    SELECT 'Transferencia realizada correctamente' AS mensaje;
END$$

-- Procedimiento para depositar fondos en una cuenta
DROP PROCEDURE IF EXISTS DepositarFondos$$
CREATE PROCEDURE DepositarFondos(
    IN p_cuenta INT,
    IN p_monto DECIMAL(10,2)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SELECT 'Error al realizar el depósito, se revirtió la operación' AS mensaje;
    END;

    START TRANSACTION;

    IF p_monto <= 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'El monto debe ser mayor a cero';
    END IF;

    UPDATE cuentas
    SET saldo = saldo + p_monto
    WHERE id = p_cuenta;

    COMMIT;
    SELECT CONCAT('Depósito de ', p_monto, ' realizado en la cuenta ', p_cuenta) AS mensaje;
END$$

-- Procedimiento para registrar ventas
DROP PROCEDURE IF EXISTS RegistrarVenta$$
CREATE PROCEDURE RegistrarVenta(
    IN p_cuenta INT,
    IN p_monto DECIMAL(10,2),
    IN p_cajero VARCHAR(50)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SELECT 'Error en la transacción de venta. Se revirtió la operación.' AS mensaje;
    END;

    START TRANSACTION;

    IF p_monto <= 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'El monto de la venta debe ser mayor que cero';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM cuentas WHERE id = p_cuenta) THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'La cuenta especificada no existe';
    END IF;

    IF (SELECT COALESCE(saldo,0) FROM cuentas WHERE id = p_cuenta) < p_monto THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Saldo insuficiente para registrar la venta';
    END IF;

    UPDATE cuentas SET saldo = saldo - p_monto WHERE id = p_cuenta;

    CREATE TABLE IF NOT EXISTS ventas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        cuenta_id INT,
        cajero VARCHAR(50),
        monto DECIMAL(10,2),
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    INSERT INTO ventas (cuenta_id, cajero, monto)
    VALUES (p_cuenta, p_cajero, p_monto);

    COMMIT;
    SELECT 'Venta registrada correctamente' AS mensaje;
END$$

DELIMITER ;

-- ============================================================
-- PASO 5: EJEMPLOS Y PRUEBAS
-- ============================================================

-- Prueba 1: Transferencia exitosa
CALL TransferirFondos(1, 2, 500.00);
SELECT * FROM cuentas;

-- Prueba 2: Transferencia con saldo insuficiente
CALL TransferirFondos(2, 1, 999999.00);
SELECT * FROM cuentas;

-- Prueba 3: Depositar fondos correcto
CALL DepositarFondos(1, 1500.00);
SELECT * FROM cuentas;

-- Prueba 4: Depositar fondos inválido
CALL DepositarFondos(1, -50.00);

-- Prueba 5: Registrar venta exitosa
CALL RegistrarVenta(2, 250.00, 'cajero1');
SELECT * FROM cuentas;
SELECT * FROM ventas;

-- Prueba 6: Registrar venta con monto inválido
CALL RegistrarVenta(2, -100.00, 'cajero1');
CALL RegistrarVenta(2, 999999.00, 'cajero1');

-- Prueba 7: Gestión de usuarios del sistema MySQL
-- Crear un nuevo usuario cajero
CALL RegistrarUsuarioSistema('cajero_nuevo', 'NuevoCajero123!', 'localhost', 'cajero');

-- Crear un supervisor
CALL RegistrarUsuarioSistema('supervisor_nuevo', 'NuevoSuper123!', 'localhost', 'supervisor');

-- Actualizar permisos de un usuario existente (cambiar de cajero a supervisor)
CALL ActualizarPermisosUsuario('cajero_pos', 'localhost', 'supervisor');

-- Verificar permisos después del cambio
SHOW GRANTS FOR 'cajero_pos'@'localhost';

-- Volver a cambiar permisos (de supervisor a cajero)
CALL ActualizarPermisosUsuario('cajero_pos', 'localhost', 'cajero');

-- Eliminar un usuario del sistema
CALL EliminarUsuarioSistema('cajero_nuevo', 'localhost');

-- Ejemplo de como funciona la seguridad por permisos MySQL:
-- Solo usuarios con privilegios admin pueden ejecutar estos procedimientos
-- Si un usuario cajero o supervisor intenta ejecutarlos, MySQL denegará la operación

-- ============================================================
-- DEMOSTRACIÓN DE EJECUCIÓN POR TIPO DE USUARIO
-- ============================================================

/*
======================
1. Usuario admin_pos (Administrador)
======================
Consola:
mysql -u admin_pos -p

SELECT User, Host FROM mysql.user;

-- Transferencia (funciona - tiene todos los permisos)
CALL TransferirFondos(1, 2, 100.00);

-- Depositar fondos
CALL DepositarFondos(1, 200.00);

-- Registrar venta
CALL RegistrarVenta(1, 50.00, 'admin1');

-- Actualizar permisos de usuarios (solo admin puede hacer esto)
CALL ActualizarPermisosUsuario('cajero_pos', 'localhost', 'supervisor');
*/

/*
======================
2. Usuario cajero_pos (Cajero)
======================
Consola:
mysql -u cajero_pos -p

-- INSERT permitido
INSERT INTO cuentas (nombre, saldo) VALUES ('Caja Extra', 500.00);

-- SELECT permitido
SELECT * FROM cuentas;

-- UPDATE NO permitido → error 1142
UPDATE cuentas SET saldo = 0 WHERE id = 1;

-- DELETE NO permitido → error 1142
DELETE FROM cuentas WHERE id = 1;

-- TransferirFondos (UPDATE interno) → error de permisos
CALL TransferirFondos(1, 2, 50.00);

-- DepositarFondos (UPDATE) → error de permisos
CALL DepositarFondos(1, 100.00);

-- RegistrarVenta (INSERT en ventas) → permitido
CALL RegistrarVenta(2, 50.00, 'cajero1');
*/

/*
======================
3. Usuario supervisor_pos (Supervisor)
======================
Consola:
mysql -u supervisor_pos -p

-- SELECT permitido
SELECT * FROM cuentas;

-- UPDATE permitido
UPDATE cuentas SET saldo = saldo + 10 WHERE id = 1;

-- INSERT NO permitido → error 1142
INSERT INTO cuentas (nombre, saldo) VALUES ('Caja Prueba', 100.00);

-- DELETE NO permitido → error 1142
DELETE FROM cuentas WHERE id = 1;

-- DepositarFondos (UPDATE) → permitido
CALL DepositarFondos(1, 100.00);

-- TransferirFondos (UPDATE) → permitido
CALL TransferirFondos(1, 2, 50.00);

-- RegistrarVenta (INSERT en ventas) → ERROR
CALL RegistrarVenta(2, 50.00, 'super1');

-- ActualizarPermisosUsuario → ERROR (sin permisos para gestionar usuarios MySQL)
-- CALL ActualizarPermisosUsuario('otro_usuario', 'localhost', 'cajero');
*/

-- ============================================================
-- VERIFICAR USUARIOS MYSQL Y PRIVILEGIOS
-- ============================================================
SELECT User, Host FROM mysql.user WHERE User LIKE '%_pos';
SHOW GRANTS FOR 'cajero_pos'@'localhost';
SHOW GRANTS FOR 'supervisor_pos'@'localhost';
SHOW GRANTS FOR 'admin_pos'@'localhost';