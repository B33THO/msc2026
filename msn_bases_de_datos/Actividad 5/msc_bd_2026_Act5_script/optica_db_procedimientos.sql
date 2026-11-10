-- =====================================================================
--  optica_db · Procedimientos almacenados y transacciones
--  MySQL 8.4 / InnoDB
--
--  Requisito previo: haber ejecutado, en este orden,
--    1. optica_db_scripts.sql     (estructura, particionamiento y datos)
--    2. seguridad_optica_db.sql   (roles y cuentas de usuario)
--
--  PARTE 1  Preparación del entorno
--  PARTE 2  Procedimientos SIN control transaccional
--  PARTE 3  Procedimientos CON control transaccional
--  PARTE 4  Procedimiento de contraste (solo para la demostración)
--  PARTE 5  Pruebas de ejecución
--  PARTE 6  Verificación y otorgamiento de permisos
-- =====================================================================


-- =====================================================================
--  PARTE 1 · PREPARACIÓN DEL ENTORNO
--  El borrado previo permite volver a ejecutar el script completo
--  cuantas veces sea necesario sin errores de objeto duplicado.
-- =====================================================================

USE optica_db;

DROP PROCEDURE IF EXISTS sp_buscar_paciente;
DROP PROCEDURE IF EXISTS sp_actualizar_contacto_paciente;
DROP PROCEDURE IF EXISTS sp_alta_sucursal;
DROP PROCEDURE IF EXISTS sp_alta_paciente_con_expediente;
DROP PROCEDURE IF EXISTS sp_registrar_consulta;
DROP PROCEDURE IF EXISTS sp_reasignar_sucursales_usuario;
DROP PROCEDURE IF EXISTS sp_registrar_consulta_sin_tx;


-- =====================================================================
--  PARTE 2 · PROCEDIMIENTOS SIN CONTROL TRANSACCIONAL
--
--  Criterio: el procedimiento ejecuta una sola sentencia que modifica
--  datos, o ninguna. InnoDB ya garantiza que una sentencia individual
--  es atómica, de modo que START TRANSACTION / COMMIT no aportaría
--  ninguna garantía adicional. Cuando hay validaciones, éstas se
--  colocan ANTES de la escritura: si fallan, no hay nada que revertir.
-- =====================================================================

DELIMITER $$

-- ---------------------------------------------------------------------
--  1. sp_buscar_paciente
--     Localiza pacientes de una óptica por prefijo de nombre.
--     Solo lectura. Aprovecha el índice ix_paciente_optica_nombre, por
--     eso el comodín se coloca únicamente al final del patrón.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_buscar_paciente(
  IN p_optica_id CHAR(36),
  IN p_nombre    VARCHAR(150)
)
COMMENT 'Consulta: pacientes de una optica cuyo nombre inicia con el texto dado'
BEGIN
  SELECT BIN_TO_UUID(p.id) AS paciente_id,
         p.nombre,
         p.fecha_nacimiento,
         p.sexo,
         p.telefono,
         p.correo,
         e.folio
  FROM paciente p
  LEFT JOIN expediente e ON e.paciente_id = p.id
  WHERE p.optica_id = UUID_TO_BIN(p_optica_id)
    AND p.nombre LIKE CONCAT(p_nombre, '%')
  ORDER BY p.nombre;
END$$


-- ---------------------------------------------------------------------
--  2. sp_actualizar_contacto_paciente
--     Actualiza teléfono, correo y dirección. La restricción
--     ck_paciente_correo valida el formato del correo; si no se cumple,
--     la sentencia completa se rechaza sin dejar efectos parciales.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_actualizar_contacto_paciente(
  IN p_paciente_id CHAR(36),
  IN p_telefono    VARCHAR(20),
  IN p_correo      VARCHAR(150),
  IN p_direccion   VARCHAR(200)
)
COMMENT 'Actualiza datos de contacto del paciente (una sola sentencia UPDATE)'
BEGIN
  DECLARE v_paciente BINARY(16);

  SET v_paciente = UUID_TO_BIN(p_paciente_id);

  -- La validación precede a la única escritura del procedimiento.
  IF NOT EXISTS (SELECT 1 FROM paciente WHERE id = v_paciente) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El paciente indicado no existe';
  END IF;

  UPDATE paciente
     SET telefono  = p_telefono,
         correo    = p_correo,
         direccion = p_direccion
   WHERE id = v_paciente;
END$$


-- ---------------------------------------------------------------------
--  3. sp_alta_sucursal
--     Un solo INSERT. La integridad la aporta el esquema:
--       fk_sucursal_optica        -> la óptica debe existir
--       uq_sucursal_optica_nombre -> el nombre no se repite en la óptica
--     El identificador generado se devuelve en un parámetro OUT.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_alta_sucursal(
  IN  p_optica_id   CHAR(36),
  IN  p_nombre      VARCHAR(150),
  IN  p_direccion   VARCHAR(200),
  OUT p_sucursal_id CHAR(36)
)
COMMENT 'Alta de sucursal; la integridad la garantizan la FK y el UNIQUE'
BEGIN
  DECLARE v_sucursal BINARY(16);

  SET v_sucursal = UUID_TO_BIN(UUID());

  INSERT INTO sucursal (id, optica_id, nombre, direccion)
  VALUES (v_sucursal, UUID_TO_BIN(p_optica_id), p_nombre, p_direccion);

  SET p_sucursal_id = BIN_TO_UUID(v_sucursal);
END$$


-- =====================================================================
--  PARTE 3 · PROCEDIMIENTOS CON CONTROL TRANSACCIONAL
--
--  Criterio: el procedimiento escribe en más de una tabla, o ejecuta
--  varias sentencias que deben observarse como una sola operación.
--
--  Patrón común de manejo de errores:
--      DECLARE EXIT HANDLER FOR SQLEXCEPTION
--      BEGIN
--        ROLLBACK;    -- deshace lo realizado hasta el momento
--        RESIGNAL;    -- devuelve el error original a la aplicación
--      END;
--
--  Sin RESIGNAL el procedimiento terminaría en silencio y la
--  aplicación supondría que la operación tuvo éxito.
-- =====================================================================

-- ---------------------------------------------------------------------
--  4. sp_alta_paciente_con_expediente
--     Da de alta al paciente y abre su expediente con folio
--     consecutivo. Son dos tablas y un consecutivo calculado: si el
--     INSERT del expediente falla, el paciente no debe quedar
--     registrado sin expediente.
--
--     La lectura con FOR UPDATE bloquea el rango de folios del año en
--     el índice uq_expediente_folio, de modo que dos altas simultáneas
--     no obtengan el mismo consecutivo.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_alta_paciente_con_expediente(
  IN  p_optica_id        CHAR(36),
  IN  p_nombre           VARCHAR(150),
  IN  p_fecha_nacimiento DATE,
  IN  p_sexo             CHAR(1),
  IN  p_telefono         VARCHAR(20),
  IN  p_correo           VARCHAR(150),
  IN  p_direccion        VARCHAR(200),
  OUT p_paciente_id      CHAR(36),
  OUT p_folio            VARCHAR(20)
)
COMMENT 'Alta de paciente y apertura de expediente en una sola transaccion'
BEGIN
  DECLARE v_paciente   BINARY(16);
  DECLARE v_expediente BINARY(16);
  DECLARE v_anio       CHAR(4);
  DECLARE v_consec     INT;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  SET v_paciente   = UUID_TO_BIN(UUID());
  SET v_expediente = UUID_TO_BIN(UUID());
  SET v_anio       = DATE_FORMAT(CURRENT_DATE, '%Y');

  START TRANSACTION;

    -- Consecutivo del año en curso. En 'EXP-2026-0007' la numeración
    -- empieza en la posición 10.
    SELECT COALESCE(MAX(CAST(SUBSTRING(folio, 10) AS UNSIGNED)), 0) + 1
      INTO v_consec
      FROM expediente
     WHERE folio LIKE CONCAT('EXP-', v_anio, '-%')
     FOR UPDATE;

    SET p_folio = CONCAT('EXP-', v_anio, '-', LPAD(v_consec, 4, '0'));

    INSERT INTO paciente
      (id, optica_id, nombre, fecha_nacimiento, sexo, telefono, correo, direccion)
    VALUES
      (v_paciente, UUID_TO_BIN(p_optica_id), p_nombre, p_fecha_nacimiento,
       p_sexo, p_telefono, p_correo, p_direccion);

    INSERT INTO expediente (id, paciente_id, fecha_creacion, folio)
    VALUES (v_expediente, v_paciente, CURRENT_DATE, p_folio);

  COMMIT;

  SET p_paciente_id = BIN_TO_UUID(v_paciente);
END$$


-- ---------------------------------------------------------------------
--  5. sp_registrar_consulta
--     Registra el asiento clínico y, cuando procede, la receta.
--
--     Éste es el caso crítico del esquema: al particionar RECETA se
--     eliminó fk_receta_asiento, y la referencia ahora la vigilan los
--     disparadores trg_receta_bi y trg_receta_bu. Si el INSERT de la
--     receta se rechaza, sin transacción el asiento clínico quedaría
--     almacenado y huérfano sin que ninguna restricción lo impida.
--
--     El procedimiento verifica además tres reglas de negocio que el
--     esquema no puede expresar por sí mismo.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_registrar_consulta(
  IN  p_expediente_id    CHAR(36),
  IN  p_usuario_id       CHAR(36),
  IN  p_sucursal_id      CHAR(36),
  IN  p_sintomas         TEXT,
  IN  p_enfermedades     TEXT,
  IN  p_heredofamiliares TEXT,
  IN  p_analisis         TEXT,
  IN  p_observaciones    TEXT,
  IN  p_material_mica    VARCHAR(100),
  IN  p_dip              NUMERIC(4,1),
  IN  p_altura           NUMERIC(4,1),
  IN  p_od_esfera        NUMERIC(4,2),
  IN  p_od_cilindro      NUMERIC(4,2),
  IN  p_od_eje           SMALLINT,
  IN  p_od_adicion       NUMERIC(3,2),
  IN  p_oi_esfera        NUMERIC(4,2),
  IN  p_oi_cilindro      NUMERIC(4,2),
  IN  p_oi_eje           SMALLINT,
  IN  p_oi_adicion       NUMERIC(3,2),
  OUT p_asiento_id       CHAR(36),
  OUT p_receta_id        CHAR(36)
)
COMMENT 'Registra consulta y receta de forma atomica'
BEGIN
  DECLARE v_expediente BINARY(16);
  DECLARE v_usuario    BINARY(16);
  DECLARE v_sucursal   BINARY(16);
  DECLARE v_asiento    BINARY(16);
  DECLARE v_receta     BINARY(16);
  DECLARE v_optica_pac BINARY(16);
  DECLARE v_optica_suc BINARY(16);
  DECLARE v_activo     BOOLEAN;
  DECLARE v_con_receta BOOLEAN;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  SET v_expediente = UUID_TO_BIN(p_expediente_id);
  SET v_usuario    = UUID_TO_BIN(p_usuario_id);
  SET v_sucursal   = UUID_TO_BIN(p_sucursal_id);
  SET v_asiento    = UUID_TO_BIN(UUID());

  -- Hay receta cuando se capturó graduación de al menos un ojo.
  SET v_con_receta = (p_od_esfera IS NOT NULL OR p_oi_esfera IS NOT NULL);

  START TRANSACTION;

    -- Regla 1: el expediente debe existir.
    SELECT p.optica_id
      INTO v_optica_pac
      FROM expediente e
      JOIN paciente   p ON p.id = e.paciente_id
     WHERE e.id = v_expediente;

    IF v_optica_pac IS NULL THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'El expediente indicado no existe';
    END IF;

    -- Regla 2: quien atiende debe ser una cuenta activa.
    SELECT activo INTO v_activo FROM usuario WHERE id = v_usuario;

    IF v_activo IS NULL OR v_activo = FALSE THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'El usuario no existe o esta dado de baja';
    END IF;

    -- Regla 3: la sucursal debe pertenecer a la óptica del paciente.
    -- Ninguna llave foránea puede expresar esta condición, porque
    -- relaciona dos ramas distintas del modelo.
    SELECT optica_id INTO v_optica_suc FROM sucursal WHERE id = v_sucursal;

    IF v_optica_suc IS NULL OR v_optica_suc <> v_optica_pac THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'La sucursal no pertenece a la optica del paciente';
    END IF;

    INSERT INTO asiento_clinico
      (id, expediente_id, usuario_id, sucursal_id, fecha,
       sintomas, enfermedades, heredofamiliares,
       analisis_preliminar, observaciones)
    VALUES
      (v_asiento, v_expediente, v_usuario, v_sucursal, CURRENT_DATE,
       p_sintomas, p_enfermedades, p_heredofamiliares,
       p_analisis, p_observaciones);

    IF v_con_receta THEN
      SET v_receta = UUID_TO_BIN(UUID());

      INSERT INTO receta
        (id, asiento_id, fecha, material_mica, dip, altura,
         od_esfera, od_cilindro, od_eje, od_adicion,
         oi_esfera, oi_cilindro, oi_eje, oi_adicion)
      VALUES
        (v_receta, v_asiento, CURRENT_DATE, p_material_mica, p_dip, p_altura,
         p_od_esfera, p_od_cilindro, p_od_eje, p_od_adicion,
         p_oi_esfera, p_oi_cilindro, p_oi_eje, p_oi_adicion);

      SET p_receta_id = BIN_TO_UUID(v_receta);
    ELSE
      SET p_receta_id = NULL;
    END IF;

  COMMIT;

  SET p_asiento_id = BIN_TO_UUID(v_asiento);
END$$


-- ---------------------------------------------------------------------
--  6. sp_reasignar_sucursales_usuario
--     Sustituye por completo las sucursales asignadas a un usuario.
--
--     Entre el DELETE y los INSERT el usuario queda sin ninguna
--     sucursal; la transacción impide que otra sesión observe ese
--     estado intermedio.
--
--     La lista puede provenir de un sistema externo y contener
--     sucursales dadas de baja. En lugar de abortar toda la operación,
--     cada renglón se protege con un SAVEPOINT: si falla se deshace
--     únicamente ese renglón y el proceso continúa. Solo si ninguna
--     sucursal resultó válida se revierte la transacción completa.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_reasignar_sucursales_usuario(
  IN  p_usuario_id CHAR(36),
  IN  p_sucursales JSON,
  OUT p_asignadas  INT,
  OUT p_omitidas   INT
)
COMMENT 'Reasigna sucursales usando SAVEPOINT para tolerar renglones invalidos'
BEGIN
  DECLARE v_usuario  BINARY(16);
  DECLARE v_sucursal BINARY(16);
  DECLARE v_total    INT;
  DECLARE v_i        INT DEFAULT 0;
  DECLARE v_error    INT DEFAULT 0;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  SET v_usuario   = UUID_TO_BIN(p_usuario_id);
  SET v_total     = COALESCE(JSON_LENGTH(p_sucursales), 0);
  SET p_asignadas = 0;
  SET p_omitidas  = 0;

  START TRANSACTION;

    IF NOT EXISTS (SELECT 1 FROM usuario WHERE id = v_usuario) THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'El usuario indicado no existe';
    END IF;

    DELETE FROM usuario_sucursal WHERE usuario_id = v_usuario;

    WHILE v_i < v_total DO

      SET v_error = 0;
      SAVEPOINT sp_renglon;

      -- Bloque anidado con su propio manejador: atrapa el error de
      -- este renglón sin abortar el procedimiento completo.
      BEGIN
        DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET v_error = 1;

        SET v_sucursal = UUID_TO_BIN(
              JSON_UNQUOTE(JSON_EXTRACT(p_sucursales, CONCAT('$[', v_i, ']'))));

        INSERT INTO usuario_sucursal (usuario_id, sucursal_id)
        VALUES (v_usuario, v_sucursal);
      END;

      IF v_error = 1 THEN
        ROLLBACK TO SAVEPOINT sp_renglon;
        SET p_omitidas = p_omitidas + 1;
      ELSE
        SET p_asignadas = p_asignadas + 1;
      END IF;

      SET v_i = v_i + 1;
    END WHILE;

    IF p_asignadas = 0 THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Ninguna sucursal de la lista resulto valida';
    END IF;

  COMMIT;
END$$


-- =====================================================================
--  PARTE 4 · PROCEDIMIENTO DE CONTRASTE
--
--  Reproduce la operación de sp_registrar_consulta SIN control
--  transaccional. Existe únicamente para demostrar el efecto de la
--  ausencia de transacciones y no forma parte de la aplicación.
--
--  Con autocommit activo (valor por omisión), cada INSERT se confirma
--  por separado: si el segundo es rechazado, el primero permanece.
-- =====================================================================

CREATE PROCEDURE sp_registrar_consulta_sin_tx(
  IN p_expediente_id CHAR(36),
  IN p_usuario_id    CHAR(36),
  IN p_sucursal_id   CHAR(36),
  IN p_analisis      TEXT,
  IN p_od_esfera     NUMERIC(4,2),
  IN p_od_eje        SMALLINT
)
COMMENT 'DEMOSTRATIVO: misma operacion sin transaccion. No usar en produccion'
BEGIN
  DECLARE v_asiento BINARY(16);
  DECLARE v_receta  BINARY(16);

  SET v_asiento = UUID_TO_BIN(UUID());
  SET v_receta  = UUID_TO_BIN(UUID());

  INSERT INTO asiento_clinico
    (id, expediente_id, usuario_id, sucursal_id, fecha, analisis_preliminar)
  VALUES
    (v_asiento, UUID_TO_BIN(p_expediente_id), UUID_TO_BIN(p_usuario_id),
     UUID_TO_BIN(p_sucursal_id), CURRENT_DATE, p_analisis);

  INSERT INTO receta (id, asiento_id, fecha, od_esfera, od_eje)
  VALUES (v_receta, v_asiento, CURRENT_DATE, p_od_esfera, p_od_eje);
END$$

DELIMITER ;


-- =====================================================================
--  PARTE 5 · PRUEBAS DE EJECUCIÓN
--
--  Los identificadores de los datos de muestra se recuperan con
--  BIN_TO_UUID(UNHEX(MD5('etiqueta'))), la misma expresión con que
--  fueron generados en optica_db_scripts.sql.
--
--  ATENCIÓN: las pruebas 3, 5 y 6 provocan errores de forma
--  deliberada, porque ése es justamente el comportamiento que se
--  quiere demostrar. El cliente de línea de comandos se detiene en el
--  primer error, de modo que la PARTE 6 no llegaría a ejecutarse. Para
--  recorrer el archivo completo:
--
--      mysql --force -u root -p < optica_db_procedimientos.sql
--
--  o bien ejecutar cada prueba por separado desde el cliente.
--
--  El apartado de limpieza, al final de esta parte, devuelve la base
--  al estado previo para que el archivo pueda repetirse.
-- =====================================================================

USE optica_db;

SET @opt01 = BIN_TO_UUID(UNHEX(MD5('opt-01')));
SET @suc01 = BIN_TO_UUID(UNHEX(MD5('suc-01')));
SET @suc02 = BIN_TO_UUID(UNHEX(MD5('suc-02')));
SET @suc04 = BIN_TO_UUID(UNHEX(MD5('suc-04')));
SET @usr02 = BIN_TO_UUID(UNHEX(MD5('usr-02')));
SET @usr03 = BIN_TO_UUID(UNHEX(MD5('usr-03')));
SET @usr04 = BIN_TO_UUID(UNHEX(MD5('usr-04')));
SET @pac01 = BIN_TO_UUID(UNHEX(MD5('pac-01')));

-- ---------------------------------------------------------------------
--  Prueba 1 · Procedimientos sin control transaccional
--  Ninguno de los tres necesita transacción: el primero solo lee y los
--  otros dos ejecutan una única sentencia de modificación.
-- ---------------------------------------------------------------------

-- 1.1 Consulta por prefijo de nombre
CALL sp_buscar_paciente(@opt01, 'Juan');

-- 1.2 Actualización de contacto: un solo UPDATE
CALL sp_actualizar_contacto_paciente(
  @pac01, '3511234567', 'juan.perez@correo.com',
  'Calle Morelos 15, Col. Centro, Zamora');

SELECT nombre, telefono, correo, direccion
FROM paciente
WHERE id = UUID_TO_BIN(@pac01);

-- 1.3 Alta de sucursal: un solo INSERT; el identificador generado
--     regresa en el parámetro de salida
CALL sp_alta_sucursal(
  @opt01, 'Sucursal Poniente', 'Av. Juárez 500, Zamora', @suc_nueva);

SELECT @suc_nueva AS sucursal_id;

-- ---------------------------------------------------------------------
--  Prueba 2 · Alta de paciente con expediente (transacción)
--  Resultado esperado: un folio consecutivo EXP-AAAA-NNNN.
-- ---------------------------------------------------------------------
CALL sp_alta_paciente_con_expediente(
  @opt01, 'Rosa Medina Alcaraz', '1990-05-14', 'F',
  '3519876543', 'rosa.medina@correo.com', 'Calle Allende 22, Zamora',
  @pac_rosa, @folio_rosa);

SELECT @pac_rosa AS paciente_id, @folio_rosa AS folio;

SET @exp_rosa = (SELECT BIN_TO_UUID(id) FROM expediente
                  WHERE paciente_id = UUID_TO_BIN(@pac_rosa));

-- ---------------------------------------------------------------------
--  Prueba 3 · Atomicidad ante un dato inválido
--  El correo no cumple ck_paciente_correo: debe fallar el INSERT del
--  paciente y no crearse ningún expediente. Los conteos no cambian.
-- ---------------------------------------------------------------------
SELECT COUNT(*) AS pacientes, (SELECT COUNT(*) FROM expediente) AS expedientes
FROM paciente;

-- Error esperado 3819: Check constraint 'ck_paciente_correo' is violated
CALL sp_alta_paciente_con_expediente(
  @opt01, 'Prueba Correo Invalido', '1990-01-01', 'M',
  NULL, 'correo-sin-arroba', NULL, @p_tmp, @f_tmp);

SELECT COUNT(*) AS pacientes, (SELECT COUNT(*) FROM expediente) AS expedientes
FROM paciente;

-- ---------------------------------------------------------------------
--  Prueba 4 · Registro de consulta con receta (transacción)
-- ---------------------------------------------------------------------
CALL sp_registrar_consulta(
  @exp_rosa, @usr02, @suc01,
  'Cansancio visual al leer', NULL, 'Madre con astigmatismo',
  'Astigmatismo leve', 'Primera consulta',
  'CR-39', 61.0, 20.5,
  -0.50, -0.75,  90, NULL,
  -0.75, -0.50,  85, NULL,
  @asiento_rosa, @receta_rosa);

SELECT @asiento_rosa AS asiento_id, @receta_rosa AS receta_id;

-- ---------------------------------------------------------------------
--  Prueba 5 · Reglas de negocio verificadas por el procedimiento
-- ---------------------------------------------------------------------

-- 5.1 Sucursal de otra óptica (suc-04 pertenece a opt-02)
-- Error esperado 1644: La sucursal no pertenece a la optica del paciente
CALL sp_registrar_consulta(
  @exp_rosa, @usr02, @suc04,
  NULL, NULL, NULL, 'Prueba de optica cruzada', NULL,
  NULL, NULL, NULL,
  -1.00, NULL, NULL, NULL, -1.00, NULL, NULL, NULL,
  @a_tmp, @r_tmp);

-- 5.2 Usuario dado de baja (usr-04 tiene activo = FALSE)
-- Error esperado 1644: El usuario no existe o esta dado de baja
CALL sp_registrar_consulta(
  @exp_rosa, @usr04, @suc01,
  NULL, NULL, NULL, 'Prueba de usuario inactivo', NULL,
  NULL, NULL, NULL,
  -1.00, NULL, NULL, NULL, -1.00, NULL, NULL, NULL,
  @a_tmp, @r_tmp);

-- ---------------------------------------------------------------------
--  Prueba 6 · CON transacción frente a SIN transacción
--
--  Se fuerza el mismo error en ambas versiones: un eje de 200 grados
--  viola ck_receta_od_eje (rango permitido 0-180). Lo que cambia es el
--  estado en que queda la base de datos.
--
--  El conteo asientos_sin_receta no parte de cero: asi-09 es una
--  revisión de rutina que no generó corrección. Lo que interesa es la
--  variación del conteo, no su valor absoluto.
-- ---------------------------------------------------------------------

-- Estado inicial
SELECT COUNT(*) AS asientos,
       (SELECT COUNT(*) FROM receta) AS recetas,
       (SELECT COUNT(*) FROM asiento_clinico a
          LEFT JOIN receta r ON r.asiento_id = a.id
         WHERE r.id IS NULL) AS asientos_sin_receta
FROM asiento_clinico;

-- 6.1 Versión SIN transacción
-- Error esperado 3819: Check constraint 'ck_receta_od_eje' is violated
CALL sp_registrar_consulta_sin_tx(
  @exp_rosa, @usr02, @suc01, 'Prueba sin transaccion', -1.00, 200);

-- El asiento quedó almacenado aunque la receta se rechazó:
-- asientos_sin_receta aumenta en uno
SELECT COUNT(*) AS asientos,
       (SELECT COUNT(*) FROM receta) AS recetas,
       (SELECT COUNT(*) FROM asiento_clinico a
          LEFT JOIN receta r ON r.asiento_id = a.id
         WHERE r.id IS NULL) AS asientos_sin_receta
FROM asiento_clinico;

-- Identificación del renglón huérfano
SELECT BIN_TO_UUID(a.id) AS asiento_huerfano, a.fecha, a.analisis_preliminar
FROM asiento_clinico a
LEFT JOIN receta r ON r.asiento_id = a.id
WHERE r.id IS NULL
  AND a.analisis_preliminar = 'Prueba sin transaccion';

-- 6.2 Versión CON transacción, mismo error
-- Error esperado 3819: Check constraint 'ck_receta_od_eje' is violated
CALL sp_registrar_consulta(
  @exp_rosa, @usr02, @suc01,
  NULL, NULL, NULL, 'Prueba con transaccion', NULL,
  'CR-39', 61.0, 20.5,
  -1.00, NULL, 200, NULL,
  -1.00, NULL,  90, NULL,
  @a_tmp, @r_tmp);

-- Los conteos son idénticos a los de 6.1: la transacción no dejó rastro
SELECT COUNT(*) AS asientos,
       (SELECT COUNT(*) FROM receta) AS recetas,
       (SELECT COUNT(*) FROM asiento_clinico a
          LEFT JOIN receta r ON r.asiento_id = a.id
         WHERE r.id IS NULL) AS asientos_sin_receta
FROM asiento_clinico;

-- 6.3 El renglón huérfano hay que localizarlo y eliminarlo a mano: no
--     existe restricción que lo señale. El orden del borrado lo impone
--     trg_asiento_bd, que reproduce el ON DELETE RESTRICT perdido al
--     particionar RECETA: primero la receta, después el asiento.
SET @huerfano = (SELECT BIN_TO_UUID(a.id)
                   FROM asiento_clinico a
                   LEFT JOIN receta r ON r.asiento_id = a.id
                  WHERE r.id IS NULL
                    AND a.analisis_preliminar = 'Prueba sin transaccion'
                  LIMIT 1);

DELETE FROM receta          WHERE asiento_id = UUID_TO_BIN(@huerfano);
DELETE FROM asiento_clinico WHERE id         = UUID_TO_BIN(@huerfano);

-- ---------------------------------------------------------------------
--  Prueba 7 · SAVEPOINT: reasignación tolerante a renglones inválidos
--  La lista incluye dos sucursales válidas y un identificador
--  inexistente. Resultado esperado: 2 asignadas, 1 omitida.
-- ---------------------------------------------------------------------
CALL sp_reasignar_sucursales_usuario(
  @usr03,
  JSON_ARRAY(@suc01, @suc02, '00000000-0000-0000-0000-000000000000'),
  @asignadas, @omitidas);

SELECT @asignadas AS asignadas, @omitidas AS omitidas;

SELECT s.nombre AS sucursal_asignada
FROM usuario_sucursal us
JOIN sucursal s ON s.id = us.sucursal_id
WHERE us.usuario_id = UUID_TO_BIN(@usr03);

-- ---------------------------------------------------------------------
--  Prueba 8 · Concurrencia del folio (ejecutar en dos sesiones)
-- ---------------------------------------------------------------------
--  Sesion A                          Sesion B
--  --------------------------------  --------------------------------
--  START TRANSACTION;
--  SELECT COALESCE(MAX(CAST(
--    SUBSTRING(folio,10) AS UNSIGNED
--  )),0)+1 INTO @n
--    FROM expediente
--   WHERE folio LIKE 'EXP-2026-%'
--   FOR UPDATE;
--                                    START TRANSACTION;
--                                    -- la misma lectura queda en
--                                    -- espera del bloqueo de A
--  INSERT INTO expediente ...
--  COMMIT;
--                                    -- se desbloquea y obtiene el
--                                    -- consecutivo siguiente
--
--  Sin FOR UPDATE ambas sesiones leerian el mismo maximo y la segunda
--  fallaria con el error 1062 (Duplicate entry, uq_expediente_folio).
-- ---------------------------------------------------------------------

-- ---------------------------------------------------------------------
--  Limpieza · devuelve la base al estado previo a las pruebas
--
--  Sin esta sección el archivo no podría repetirse: la prueba 2 daría
--  de alta otra Rosa Medina en cada pasada y la 1.3 fallaría con el
--  error 1062 por uq_sucursal_optica_nombre.
--
--  El orden respeta trg_asiento_bd: la receta antes que el asiento.
-- ---------------------------------------------------------------------
DELETE FROM receta
 WHERE asiento_id IN (
       SELECT a.id
         FROM asiento_clinico a
         JOIN expediente e ON e.id = a.expediente_id
        WHERE e.paciente_id = UUID_TO_BIN(@pac_rosa));

DELETE FROM asiento_clinico
 WHERE expediente_id IN (
       SELECT id FROM expediente
        WHERE paciente_id = UUID_TO_BIN(@pac_rosa));

DELETE FROM expediente WHERE paciente_id = UUID_TO_BIN(@pac_rosa);
DELETE FROM paciente   WHERE id          = UUID_TO_BIN(@pac_rosa);

-- Sucursal creada en la prueba 1.3
DELETE FROM sucursal WHERE id = UUID_TO_BIN(@suc_nueva);

-- Sucursales de Sofía Ramírez tal como estaban antes de la prueba 7
DELETE FROM usuario_sucursal WHERE usuario_id = UUID_TO_BIN(@usr03);
INSERT INTO usuario_sucursal (usuario_id, sucursal_id)
VALUES (UUID_TO_BIN(@usr03), UUID_TO_BIN(@suc01));

-- Contacto de Juan Pérez tal como estaba antes de la prueba 1.2
UPDATE paciente
   SET telefono  = '3511234567',
       correo    = 'juan.perez@correo.com',
       direccion = 'Calle Morelos 15, Zamora'
 WHERE id = UUID_TO_BIN(@pac01);


-- =====================================================================
--  PARTE 6 · VERIFICACIÓN Y PERMISOS
-- =====================================================================

-- ---------------------------------------------------------------------
--  Procedimientos registrados en el catálogo
--  Resultado esperado: siete renglones, todos con SECURITY_TYPE DEFINER
-- ---------------------------------------------------------------------
SELECT ROUTINE_NAME    AS procedimiento,
       SECURITY_TYPE   AS seguridad,
       ROUTINE_COMMENT AS descripcion
FROM information_schema.ROUTINES
WHERE ROUTINE_SCHEMA = 'optica_db'
  AND ROUTINE_TYPE   = 'PROCEDURE'
ORDER BY ROUTINE_NAME;

-- ---------------------------------------------------------------------
--  Permisos de ejecución por rol (continuación de la actividad 4)
--
--  Los procedimientos se crean con SQL SECURITY DEFINER, el valor por
--  omisión en MySQL: se ejecutan con los privilegios de quien los creó.
--  Esto permite conceder EXECUTE sobre una operación completa sin
--  otorgar permisos directos sobre las tablas, lo que refuerza el
--  principio del menor privilegio.
--
--  sp_registrar_consulta_sin_tx no se concede a ningún rol: existe
--  únicamente para la demostración de la PARTE 5.
-- ---------------------------------------------------------------------
GRANT EXECUTE ON PROCEDURE optica_db.sp_buscar_paciente              TO 'rol_recepcion';
GRANT EXECUTE ON PROCEDURE optica_db.sp_alta_paciente_con_expediente TO 'rol_recepcion';
GRANT EXECUTE ON PROCEDURE optica_db.sp_actualizar_contacto_paciente TO 'rol_recepcion';

GRANT EXECUTE ON PROCEDURE optica_db.sp_buscar_paciente              TO 'rol_optometrista';
GRANT EXECUTE ON PROCEDURE optica_db.sp_registrar_consulta           TO 'rol_optometrista';

GRANT EXECUTE ON PROCEDURE optica_db.sp_alta_sucursal                TO 'rol_admin_app';
GRANT EXECUTE ON PROCEDURE optica_db.sp_reasignar_sucursales_usuario TO 'rol_admin_app';

GRANT EXECUTE ON PROCEDURE optica_db.sp_buscar_paciente              TO 'rol_auditor';

FLUSH PRIVILEGES;

-- ---------------------------------------------------------------------
--  Permisos de ejecución concedidos a cada rol
-- ---------------------------------------------------------------------
SHOW GRANTS FOR 'rol_optometrista';
SHOW GRANTS FOR 'rol_recepcion';
SHOW GRANTS FOR 'rol_admin_app';
SHOW GRANTS FOR 'rol_auditor';
