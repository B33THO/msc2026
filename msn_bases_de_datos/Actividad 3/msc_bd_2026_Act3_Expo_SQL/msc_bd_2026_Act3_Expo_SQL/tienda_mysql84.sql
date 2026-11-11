-- ============================================================
-- tienda_mysql84.sql
--
-- Replica en MySQL 8.4 real la base de datos y los procedimientos
-- del simulador (SQL Sandbox: Procedimientos Almacenados y
-- Transacciones). Pensado para ejecutarse tal cual desde el
-- cliente `mysql`, MySQL Workbench o similar.
--
-- Escenario: una tienda con tres tablas. Vender un producto toca
-- DOS de ellas (descuenta Inventario.stock e inserta en Pedidos),
-- que es justo lo que hace interesante a las transacciones.
--
-- Orden del archivo: esquema y datos semilla, y despues un
-- procedimiento por cada nivel del recorrido (2 a 8), en el mismo
-- orden en que se ensenan.
-- ============================================================

CREATE DATABASE IF NOT EXISTS tienda_sp
    CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE tienda_sp;

-- ── Limpieza (permite re-ejecutar el script completo) ───────

DROP PROCEDURE IF EXISTS VerInventario;
DROP PROCEDURE IF EXISTS RegistrarVenta;
DROP PROCEDURE IF EXISTS ConsultarStock;
DROP PROCEDURE IF EXISTS VentaRiesgosa;
DROP PROCEDURE IF EXISTS VentaSegura;
DROP PROCEDURE IF EXISTS VentaFinal;

DROP TABLE IF EXISTS Pedidos;
DROP TABLE IF EXISTS Inventario;
DROP TABLE IF EXISTS Productos;

-- ============================================================
-- ESQUEMA
-- ============================================================

CREATE TABLE Productos (
    producto_id INT PRIMARY KEY,
    nombre      VARCHAR(60)    NOT NULL,
    precio      DECIMAL(10,2)  NOT NULL
) ENGINE = InnoDB;

CREATE TABLE Inventario (
    producto_id INT PRIMARY KEY,
    stock       INT NOT NULL,
    CONSTRAINT fk_inventario_producto
        FOREIGN KEY (producto_id) REFERENCES Productos(producto_id)
) ENGINE = InnoDB;

CREATE TABLE Pedidos (
    pedido_id   INT AUTO_INCREMENT PRIMARY KEY,
    producto_id INT            NOT NULL,
    cantidad    INT            NOT NULL,
    total       DECIMAL(10,2)  NOT NULL,
    estado      VARCHAR(20)    NOT NULL,
    CONSTRAINT fk_pedidos_producto
        FOREIGN KEY (producto_id) REFERENCES Productos(producto_id)
) ENGINE = InnoDB;

-- ── Datos semilla ────────────────────────────────────────────

INSERT INTO Productos (producto_id, nombre, precio) VALUES
    (1, 'Teclado mecanico',  1250.00),
    (2, 'Mouse inalambrico',  480.00),
    (3, 'Monitor 24"',       3200.00),
    (4, 'Audifonos',          890.00),
    (5, 'Webcam HD',         1100.00);

INSERT INTO Inventario (producto_id, stock) VALUES
    (1, 10),
    (2, 25),
    (3, 4),
    (4, 15),
    (5, 2);

-- pedido_id se asigna solo por el AUTO_INCREMENT (arranca en 1)
INSERT INTO Pedidos (producto_id, cantidad, total, estado) VALUES
    (2, 3, 1440.00, 'COMPLETADO'),
    (4, 1,  890.00, 'COMPLETADO');

-- ============================================================
-- NIVEL 2 — Tu primer procedimiento
-- Un procedimiento sin parametros: solo agrupa una consulta.
-- ============================================================

DELIMITER $$

CREATE PROCEDURE VerInventario()
BEGIN
    SELECT * FROM Inventario;
END$$

DELIMITER ;

CALL VerInventario();

-- ============================================================
-- NIVEL 3 — Parametros de entrada
-- IN entra como variable local. Una sola llamada toca DOS tablas:
-- descuenta Inventario y registra en Pedidos.
-- ============================================================

DELIMITER $$

CREATE PROCEDURE RegistrarVenta(IN p_producto INT, IN p_cantidad INT)
BEGIN
    DECLARE v_total DECIMAL(10,2) DEFAULT 0;

    SELECT precio INTO v_total FROM Productos WHERE producto_id = p_producto;
    SET v_total = v_total * p_cantidad;

    UPDATE Inventario SET stock = stock - p_cantidad
        WHERE producto_id = p_producto;

    INSERT INTO Pedidos (producto_id, cantidad, total, estado)
        VALUES (p_producto, p_cantidad, v_total, 'NUEVO');
END$$

DELIMITER ;

CALL RegistrarVenta(1, 2);

-- ============================================================
-- NIVEL 4 — Parametros de salida
-- OUT escribe en una variable de sesion (@algo), que sigue
-- disponible despues de que el procedimiento termina.
-- ============================================================

DELIMITER $$

CREATE PROCEDURE ConsultarStock(IN p_producto INT, OUT p_stock INT)
BEGIN
    SELECT stock INTO p_stock FROM Inventario WHERE producto_id = p_producto;
END$$

DELIMITER ;

CALL ConsultarStock(3, @resultado);
SELECT @resultado;

-- ============================================================
-- NIVEL 5 — El problema: una venta a medias
-- Descuenta primero y valida despues. Fuera de una transaccion,
-- MySQL confirma cada sentencia sola (autocommit): cuando el IF
-- descubre el problema, el UPDATE ya es definitivo.
--
-- ADVERTENCIA: este procedimiento es deliberadamente incorrecto,
-- solo para demostrar el fallo. No usar este patron en produccion.
-- Ejecutar el CALL comentado abajo deja el stock del producto 5
-- en -48 y ningun pedido que lo explique.
-- ============================================================

DELIMITER $$

CREATE PROCEDURE VentaRiesgosa(IN p_producto INT, IN p_cantidad INT)
BEGIN
    DECLARE v_stock INT DEFAULT 0;

    -- Esto se confirma SOLO, en este mismo instante. Ya no hay marcha atras.
    UPDATE Inventario SET stock = stock - p_cantidad
        WHERE producto_id = p_producto;

    SELECT stock INTO v_stock FROM Inventario WHERE producto_id = p_producto;

    -- Llegamos tarde: la validacion descubre el problema, pero no puede repararlo
    IF v_stock >= 0 THEN
        INSERT INTO Pedidos (producto_id, cantidad, total, estado)
            VALUES (p_producto, p_cantidad, 0, 'NUEVO');
    END IF;
END$$

DELIMITER ;

-- CALL VentaRiesgosa(5, 50);   -- descomentar solo para observar el desastre

-- ============================================================
-- NIVEL 6 — La solucion: la transaccion
-- Mismo procedimiento del nivel 5, envuelto en una transaccion.
-- Si el stock queda negativo: ROLLBACK. Si no: COMMIT.
-- ============================================================

DELIMITER $$

CREATE PROCEDURE VentaSegura(IN p_producto INT, IN p_cantidad INT)
BEGIN
    DECLARE v_stock INT DEFAULT 0;

    START TRANSACTION;

    UPDATE Inventario SET stock = stock - p_cantidad
        WHERE producto_id = p_producto;
    INSERT INTO Pedidos (producto_id, cantidad, total, estado)
        VALUES (p_producto, p_cantidad, 0, 'NUEVO');

    SELECT stock INTO v_stock FROM Inventario WHERE producto_id = p_producto;

    IF v_stock < 0 THEN
        ROLLBACK;
    ELSE
        COMMIT;
    END IF;
END$$

DELIMITER ;

CALL VentaSegura(5, 50);

-- ============================================================
-- NIVEL 7 — SAVEPOINT: deshacer solo una parte
-- Sentencias sueltas (no hace falta procedimiento). Un pedido de
-- dos lineas: la primera (producto 1) es valida, la segunda
-- (producto 5) no alcanza. Se conserva la primera y se descarta
-- solo la segunda.
-- ============================================================

START TRANSACTION;

-- Primera linea del pedido: valida
UPDATE Inventario SET stock = stock - 2 WHERE producto_id = 1;
INSERT INTO Pedidos (producto_id, cantidad, total, estado)
    VALUES (1, 2, 2500, 'NUEVO');

SAVEPOINT linea1;           -- marca: hasta aqui todo bien

-- Segunda linea: no hay stock suficiente
UPDATE Inventario SET stock = stock - 50 WHERE producto_id = 5;
INSERT INTO Pedidos (producto_id, cantidad, total, estado)
    VALUES (5, 50, 55000, 'NUEVO');

ROLLBACK TO SAVEPOINT linea1;   -- descarta SOLO la segunda linea
COMMIT;                          -- y confirma la primera

-- ============================================================
-- NIVEL 8 — Integrador: una venta con reporte de estado
-- Junta parametros IN/OUT, calculo de total, y una transaccion
-- donde la validacion va ANTES de modificar nada (a diferencia
-- del nivel 5). El resultado ('COMPLETADO' / 'RECHAZADO') se
-- reporta en un parametro OUT.
-- ============================================================

DELIMITER $$

CREATE PROCEDURE VentaFinal(
    IN  p_producto INT,
    IN  p_cantidad INT,
    OUT p_estado   VARCHAR(40)
)
BEGIN
    DECLARE v_total DECIMAL(10,2) DEFAULT 0;
    DECLARE v_stock INT DEFAULT 0;

    START TRANSACTION;

    SELECT precio INTO v_total FROM Productos WHERE producto_id = p_producto;
    SET v_total = v_total * p_cantidad;

    -- Esta vez la validacion va ANTES de modificar nada
    SELECT stock INTO v_stock FROM Inventario WHERE producto_id = p_producto;

    IF v_stock >= p_cantidad THEN
        UPDATE Inventario SET stock = stock - p_cantidad
            WHERE producto_id = p_producto;
        INSERT INTO Pedidos (producto_id, cantidad, total, estado)
            VALUES (p_producto, p_cantidad, v_total, 'NUEVO');
        SET p_estado = 'COMPLETADO';
        COMMIT;
    ELSE
        SET p_estado = 'RECHAZADO';
        ROLLBACK;
    END IF;
END$$

DELIMITER ;

-- Una venta que si alcanza y otra que no, para ver ambas ramas
CALL VentaFinal(1, 2, @estado1);
CALL VentaFinal(5, 50, @estado2);
SELECT @estado1 AS resultado_venta_1, @estado2 AS resultado_venta_2;

-- ============================================================
-- Verificacion final: como quedaron las tablas
-- ============================================================

SELECT * FROM Productos;
SELECT * FROM Inventario;
SELECT * FROM Pedidos;
