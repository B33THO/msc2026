-- =====================================================================
-- Sistema de Gestión Óptica -- Script principal (v3)
-- Motor: MySQL 8.0.20 o superior (InnoDB)
--   8.0.13+  DEFAULT con expresión
--   8.0.16+  restricciones CHECK aplicadas
--   8.0.19+  FAILED_LOGIN_ATTEMPTS / PASSWORD_LOCK_TIME
--   8.0.20+  privilegio SHOW_ROUTINE (respaldos)
--
-- Contenido:
--   PARTE 1  Estructura (modelo físico)
--   PARTE 2  Datos de muestra
--   PARTE 3  Procedimientos almacenados y transacciones
--   PARTE 4  Seguridad: roles, usuarios y permisos
--   PARTE 5  Verificación
--   PARTE 6  Pruebas de ejecución (provocan errores A PROPÓSITO)
--
-- Ejecución completa (todo el archivo, incluidas las pruebas):
--   mysql --force -u root -p < optica_db.sql
--   Sin --force el cliente se detiene en el primer error deliberado de
--   la PARTE 6; las partes 1 a 5 ya habrán quedado creadas.
--   En Workbench: Query > "Continue on SQL Script Error".
--
-- Debe ejecutarse con una cuenta que tenga CREATE USER, CREATE ROLE y
-- GRANT OPTION (p. ej. root). El archivo se puede repetir: elimina y
-- recrea tablas y procedimientos; roles y cuentas usan IF NOT EXISTS.
--
-- Cambios respecto a la v2:
--   1. expediente.folio (EXP-AAAA-NNNN, único): identificador legible del
--      expediente; lo genera sp_alta_paciente_con_expediente.
--   2. Se integran datos de muestra, procedimientos (Act. 5) y seguridad
--      (Act. 4) en un solo archivo.
--
-- Cambios de la v2 respecto a la v1:
--   1. asiento_clinico.sucursal_id: identifica la sucursal donde se
--      atendió la consulta. usuario_id no basta, porque un usuario puede
--      operar en varias sucursales (relación N:M).
--   2. paciente.telefono y paciente.correo pasan a NOT NULL: el escenario
--      declara únicamente Dirección como dato opcional.
--   3. receta -> asiento_clinico se confirma ON DELETE CASCADE.
--   4. CHECK del eje corregido a BETWEEN 1 AND 180 (convención
--      optométrica: el eje 0 no se usa, el meridiano horizontal es 180).
--   5. CHECK cruzado: si se captura cilindro, el eje es obligatorio.
--   6. Índice ix_asiento_sucursal para dar soporte a la nueva llave
--      foránea.
--
-- Nota sobre las llaves primarias:
--   Todas son BINARY(16). Deben generarse ORDENADAS en el tiempo
--   (UUID_TO_BIN(UUID(), 1) o UUID v7). Un UUID v4 aleatorio como llave
--   primaria agrupada provoca división de páginas y fragmentación del
--   índice agrupado de InnoDB.
--
--   Convención del script: las llaves nuevas se generan con
--   UUID_TO_BIN(UUID(), 1) (binario ordenado). Toda conversión entre
--   texto y binario (parámetros, resultados) se hace SIN el indicador
--   de intercambio: BIN_TO_UUID(id) / UUID_TO_BIN(texto). Así el texto
--   es solo la representación hexadecimal del binario y la conversión
--   de ida y vuelta siempre coincide.
-- =====================================================================


-- =====================================================================
--  PARTE 1 · ESTRUCTURA
-- =====================================================================

CREATE DATABASE IF NOT EXISTS optica_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE optica_db;

-- ---------------------------------------------------------------------
-- Limpieza previa. Orden inverso al de creación para no violar las FK.
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS receta;
DROP TABLE IF EXISTS asiento_clinico;
DROP TABLE IF EXISTS expediente;
DROP TABLE IF EXISTS paciente;
DROP TABLE IF EXISTS usuario_sucursal;
DROP TABLE IF EXISTS usuario;
DROP TABLE IF EXISTS sucursal;
DROP TABLE IF EXISTS rol;
DROP TABLE IF EXISTS optica;

-- =====================================================================
-- 1. OPTICA
-- Entidad raíz del modelo. Todo cuelga directa o indirectamente de aquí.
-- =====================================================================
CREATE TABLE optica (
    id      BINARY(16)   NOT NULL COMMENT 'UUID ordenado generado en la capa de aplicación',
    nombre  VARCHAR(150) NOT NULL COMMENT 'Nombre comercial o razón social',

    CONSTRAINT pk_optica PRIMARY KEY (id)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = 'Negocios registrados en el sistema';

-- =====================================================================
-- 2. ROL
-- Catálogo de perfiles de permisos.
-- =====================================================================
CREATE TABLE rol (
    id           BINARY(16)   NOT NULL,
    nombre       VARCHAR(150) NOT NULL COMMENT 'Administrador, Optometrista, Recepción, etc.',
    descripcion  VARCHAR(200) NULL     COMMENT 'Atribuciones del perfil',

    CONSTRAINT pk_rol PRIMARY KEY (id),
    CONSTRAINT uq_rol_nombre UNIQUE (nombre)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = 'Perfiles de permisos del sistema';

-- =====================================================================
-- 3. SUCURSAL
-- Punto físico de atención perteneciente a una óptica.
-- =====================================================================
CREATE TABLE sucursal (
    id         BINARY(16)   NOT NULL,
    optica_id  BINARY(16)   NOT NULL,
    nombre     VARCHAR(150) NOT NULL,
    direccion  VARCHAR(200) NULL COMMENT 'Calle, número, colonia y ciudad',

    CONSTRAINT pk_sucursal PRIMARY KEY (id),

    -- Unicidad compuesta: dos ópticas distintas sí pueden repetir el nombre.
    -- Este índice también resuelve la búsqueda por optica_id (prefijo izquierdo).
    CONSTRAINT uq_sucursal_optica_nombre UNIQUE (optica_id, nombre),

    CONSTRAINT fk_sucursal_optica
        FOREIGN KEY (optica_id) REFERENCES optica (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = 'Sucursales o consultorios de cada óptica';

-- =====================================================================
-- 4. USUARIO
-- Personal que accede al sistema.
-- =====================================================================
CREATE TABLE usuario (
    id             BINARY(16)   NOT NULL,
    optica_id      BINARY(16)   NOT NULL,
    rol_id         BINARY(16)   NOT NULL,
    nombre         VARCHAR(150) NOT NULL,
    correo         VARCHAR(150) NOT NULL COMMENT 'Credencial de acceso',
    password_hash  VARCHAR(255) NOT NULL COMMENT 'Hash bcrypt. Nunca la contraseña en claro',
    activo         BOOLEAN      NOT NULL DEFAULT TRUE
                                COMMENT 'Baja lógica: conserva el historial del usuario',

    CONSTRAINT pk_usuario PRIMARY KEY (id),

    -- Un correo puede repetirse entre ópticas distintas, no dentro de la misma.
    CONSTRAINT uq_usuario_optica_correo UNIQUE (optica_id, correo),

    CONSTRAINT fk_usuario_optica
        FOREIGN KEY (optica_id) REFERENCES optica (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_usuario_rol
        FOREIGN KEY (rol_id) REFERENCES rol (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = 'Personal con acceso al sistema';

-- La llave foránea rol_id no queda cubierta por ningún índice existente.
CREATE INDEX ix_usuario_rol ON usuario (rol_id);

-- =====================================================================
-- 5. USUARIO_SUCURSAL
-- Tabla puente. Resuelve el muchos a muchos entre usuario y sucursal.
-- =====================================================================
CREATE TABLE usuario_sucursal (
    usuario_id   BINARY(16) NOT NULL,
    sucursal_id  BINARY(16) NOT NULL,

    -- La llave primaria compuesta es la tabla misma: no hay columnas propias.
    CONSTRAINT pk_usuario_sucursal PRIMARY KEY (usuario_id, sucursal_id),

    -- CASCADE es correcto aquí: la asignación no tiene existencia propia.
    CONSTRAINT fk_usuario_sucursal_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuario (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_usuario_sucursal_sucursal
        FOREIGN KEY (sucursal_id) REFERENCES sucursal (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = 'Sucursales en las que puede operar cada usuario';

-- La PK cubre usuario_id; la navegación inversa necesita su propio índice.
CREATE INDEX ix_usuario_sucursal_sucursal ON usuario_sucursal (sucursal_id);

-- =====================================================================
-- 6. PACIENTE
-- Datos de identificación y contacto de la persona atendida.
-- =====================================================================
CREATE TABLE paciente (
    id                BINARY(16)   NOT NULL,
    optica_id         BINARY(16)   NOT NULL,
    nombre            VARCHAR(150) NOT NULL,
    fecha_nacimiento  DATE         NOT NULL COMMENT 'Permite derivar la edad en cada consulta',
    sexo              CHAR(1)      COLLATE utf8mb4_0900_as_cs NOT NULL
                                   COMMENT 'Intercalación sensible a mayúsculas: solo acepta M o F',
    telefono          VARCHAR(20)  NOT NULL COMMENT 'Dato requerido por el escenario',
    correo            VARCHAR(150) NOT NULL COMMENT 'Dato requerido por el escenario',
    direccion         VARCHAR(200) NULL     COMMENT 'Único dato declarado como opcional',

    CONSTRAINT pk_paciente PRIMARY KEY (id),

    -- Con la intercalación por defecto (ai_ci) este CHECK aceptaría 'm' y 'f'
    -- minúsculas. Por eso la columna declara utf8mb4_0900_as_cs.
    CONSTRAINT chk_paciente_sexo
        CHECK (sexo IN ('M', 'F')),

    -- correo es NOT NULL, por lo que el CHECK se evalúa siempre.
    CONSTRAINT chk_paciente_correo
        CHECK (correo REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'),

    CONSTRAINT fk_paciente_optica
        FOREIGN KEY (optica_id) REFERENCES optica (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = 'Personas atendidas por la óptica';

-- Búsqueda más frecuente del sistema: paciente por nombre dentro de la óptica.
-- Su prefijo izquierdo también da soporte a la llave foránea optica_id.
CREATE INDEX ix_paciente_optica_nombre ON paciente (optica_id, nombre);

-- =====================================================================
-- 7. EXPEDIENTE
-- Contenedor del historial clínico. Uno solo por paciente.
-- =====================================================================
CREATE TABLE expediente (
    id              BINARY(16)  NOT NULL,
    paciente_id     BINARY(16)  NOT NULL,
    fecha_creacion  DATE        NOT NULL DEFAULT (CURRENT_DATE),
    folio           VARCHAR(20) NOT NULL COMMENT 'EXP-AAAA-NNNN, consecutivo anual',

    CONSTRAINT pk_expediente PRIMARY KEY (id),

    -- La unicidad es lo que impone la relación uno a uno con paciente.
    CONSTRAINT uq_expediente_paciente UNIQUE (paciente_id),

    -- El folio es único en todo el sistema. Este índice también permite
    -- bloquear el rango de folios de un año (SELECT ... FOR UPDATE) al
    -- calcular el siguiente consecutivo.
    CONSTRAINT uq_expediente_folio UNIQUE (folio),

    CONSTRAINT chk_expediente_folio
        CHECK (folio REGEXP '^EXP-[0-9]{4}-[0-9]{4}$'),

    -- RESTRICT: el historial clínico sobrevive a la ficha de contacto.
    CONSTRAINT fk_expediente_paciente
        FOREIGN KEY (paciente_id) REFERENCES paciente (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = 'Historial clínico del paciente';

-- =====================================================================
-- 8. ASIENTO_CLINICO
-- Registro de cada consulta. Tabla de mayor crecimiento del modelo.
-- =====================================================================
CREATE TABLE asiento_clinico (
    id                   BINARY(16) NOT NULL,
    expediente_id        BINARY(16) NOT NULL,
    usuario_id           BINARY(16) NOT NULL COMMENT 'Quién atendió la consulta',
    sucursal_id          BINARY(16) NOT NULL COMMENT 'Dónde se atendió. usuario_id no lo determina: un usuario opera en varias sucursales',
    fecha                DATE       NOT NULL DEFAULT (CURRENT_DATE),
    sintomas             TEXT       NULL,
    enfermedades         TEXT       NULL,
    heredofamiliares     TEXT       NULL,
    analisis_preliminar  TEXT       NULL,
    observaciones        TEXT       NULL,

    CONSTRAINT pk_asiento_clinico PRIMARY KEY (id),

    -- RESTRICT protege el historial clínico.
    CONSTRAINT fk_asiento_expediente
        FOREIGN KEY (expediente_id) REFERENCES expediente (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    -- RESTRICT preserva la trazabilidad de quién atendió; para dar de baja
    -- a un usuario se usa activo = FALSE.
    CONSTRAINT fk_asiento_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuario (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    -- RESTRICT: una sucursal con historial no se elimina.
    CONSTRAINT fk_asiento_sucursal
        FOREIGN KEY (sucursal_id) REFERENCES sucursal (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = 'Consultas registradas en un expediente';

-- Recupera el historial de un paciente en orden cronológico sin ordenar aparte.
CREATE INDEX ix_asiento_expediente_fecha ON asiento_clinico (expediente_id, fecha);
CREATE INDEX ix_asiento_usuario          ON asiento_clinico (usuario_id);

-- Da soporte a la FK y resuelve el reporte por sucursal y periodo,
-- que es el equivalente al archivo de Excel de cada sucursal.
CREATE INDEX ix_asiento_sucursal_fecha   ON asiento_clinico (sucursal_id, fecha);

-- =====================================================================
-- 9. RECETA
-- Graduación óptica derivada de una consulta.
-- OD = ojo derecho (oculus dexter) | OI = ojo izquierdo (oculus sinister)
-- =====================================================================
CREATE TABLE receta (
    id             BINARY(16)   NOT NULL,
    asiento_id     BINARY(16)   NOT NULL,
    fecha          DATE         NOT NULL COMMENT 'Fecha de emisión: puede ser posterior a la de la consulta',
    material_mica  VARCHAR(100) NULL COMMENT 'Policarbonato, CR-39, alto índice, etc. Será catálogo al integrar inventarios',
    dip            DECIMAL(4,1) NULL COMMENT 'Distancia interpupilar en milímetros',
    altura         DECIMAL(4,1) NULL COMMENT 'Altura del centro óptico en milímetros',
    od_esfera      DECIMAL(4,2) NULL COMMENT 'Potencia esférica en dioptrías',
    od_cilindro    DECIMAL(4,2) NULL COMMENT 'Potencia cilíndrica (astigmatismo)',
    od_eje         SMALLINT     NULL COMMENT 'Orientación del cilindro en grados',
    od_adicion     DECIMAL(3,1) NULL COMMENT 'Adición para visión cercana',
    oi_esfera      DECIMAL(4,2) NULL,
    oi_cilindro    DECIMAL(4,2) NULL,
    oi_eje         SMALLINT     NULL,
    oi_adicion     DECIMAL(3,1) NULL,

    CONSTRAINT pk_receta PRIMARY KEY (id),

    -- Una consulta genera cuando mucho una receta.
    CONSTRAINT uq_receta_asiento UNIQUE (asiento_id),

    -- El eje se expresa de 1 a 180 grados. El 0 no se usa: el meridiano
    -- horizontal se anota como 180.
    CONSTRAINT chk_receta_od_eje CHECK (od_eje BETWEEN 1 AND 180),
    CONSTRAINT chk_receta_oi_eje CHECK (oi_eje BETWEEN 1 AND 180),

    -- Un cilindro sin eje no define una corrección: si hay uno, debe haber el otro.
    CONSTRAINT chk_receta_od_cilindro_eje
        CHECK (od_cilindro IS NULL OR od_eje IS NOT NULL),
    CONSTRAINT chk_receta_oi_cilindro_eje
        CHECK (oi_cilindro IS NULL OR oi_eje IS NOT NULL),

    -- CASCADE: la receta carece de sentido sin la consulta que la originó.
    CONSTRAINT fk_receta_asiento
        FOREIGN KEY (asiento_id) REFERENCES asiento_clinico (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = 'Graduación óptica emitida en una consulta';


-- =====================================================================
--  PARTE 2 · DATOS DE MUESTRA
--
--  Los identificadores se derivan de una etiqueta legible:
--      UNHEX(MD5('opt-01'))  ->  16 bytes, siempre los mismos
--  Así cualquier script o prueba recupera un registro conocido con
--  BIN_TO_UUID(UNHEX(MD5('etiqueta'))) sin consultar la base.
--  (Estos ids no están ordenados en el tiempo; es aceptable para un
--  puñado de datos de muestra. Los procedimientos generan ids ordenados.)
--
--  password_hash contiene valores ficticios con formato bcrypt.
-- =====================================================================

INSERT INTO optica (id, nombre) VALUES
  (UNHEX(MD5('opt-01')), 'Óptica Visión Clara'),
  (UNHEX(MD5('opt-02')), 'Óptica Mirada Jacona');

INSERT INTO rol (id, nombre, descripcion) VALUES
  (UNHEX(MD5('rol-01')), 'Administrador', 'Gestiona sucursales, usuarios y catálogos'),
  (UNHEX(MD5('rol-02')), 'Optometrista',  'Registra consultas y emite recetas'),
  (UNHEX(MD5('rol-03')), 'Recepción',     'Alta de pacientes y entrega de recetas');

INSERT INTO sucursal (id, optica_id, nombre, direccion) VALUES
  (UNHEX(MD5('suc-01')), UNHEX(MD5('opt-01')), 'Matriz Centro',       'Av. Madero 120, Col. Centro, Zamora'),
  (UNHEX(MD5('suc-02')), UNHEX(MD5('opt-01')), 'Sucursal Jardinadas', 'Calle Amado Nervo 45, Col. Jardinadas, Zamora'),
  (UNHEX(MD5('suc-03')), UNHEX(MD5('opt-01')), 'Sucursal Norte',      'Blvd. Lázaro Cárdenas 980, Zamora'),
  (UNHEX(MD5('suc-04')), UNHEX(MD5('opt-02')), 'Matriz Jacona',       'Av. Independencia 33, Jacona');

INSERT INTO usuario (id, optica_id, rol_id, nombre, correo, password_hash, activo) VALUES
  (UNHEX(MD5('usr-01')), UNHEX(MD5('opt-01')), UNHEX(MD5('rol-01')),
   'Laura Gómez Torres',     'laura.gomez@visionclara.mx',
   '$2b$12$EjemploHashNoRealAdminLauraGomezTorres000000000000000', TRUE),
  (UNHEX(MD5('usr-02')), UNHEX(MD5('opt-01')), UNHEX(MD5('rol-02')),
   'Carlos Herrera Ruiz',    'carlos.herrera@visionclara.mx',
   '$2b$12$EjemploHashNoRealOptoCarlosHerreraRuiz00000000000000', TRUE),
  (UNHEX(MD5('usr-03')), UNHEX(MD5('opt-01')), UNHEX(MD5('rol-03')),
   'Sofía Ramírez Díaz',     'sofia.ramirez@visionclara.mx',
   '$2b$12$EjemploHashNoRealRecepSofiaRamirezDiaz00000000000000', TRUE),
  -- Baja lógica: conserva su historial de consultas, pero no puede atender.
  (UNHEX(MD5('usr-04')), UNHEX(MD5('opt-01')), UNHEX(MD5('rol-02')),
   'Miguel Ángel Soto Vega', 'miguel.soto@visionclara.mx',
   '$2b$12$EjemploHashNoRealOptoMiguelSotoVega0000000000000000', FALSE),
  (UNHEX(MD5('usr-05')), UNHEX(MD5('opt-02')), UNHEX(MD5('rol-02')),
   'Patricia Luna Méndez',   'patricia.luna@miradajacona.mx',
   '$2b$12$EjemploHashNoRealOptoPatriciaLunaMendez000000000000', TRUE);

INSERT INTO usuario_sucursal (usuario_id, sucursal_id) VALUES
  (UNHEX(MD5('usr-01')), UNHEX(MD5('suc-01'))),
  (UNHEX(MD5('usr-01')), UNHEX(MD5('suc-02'))),
  (UNHEX(MD5('usr-01')), UNHEX(MD5('suc-03'))),
  (UNHEX(MD5('usr-02')), UNHEX(MD5('suc-01'))),
  (UNHEX(MD5('usr-02')), UNHEX(MD5('suc-02'))),
  (UNHEX(MD5('usr-02')), UNHEX(MD5('suc-03'))),
  (UNHEX(MD5('usr-03')), UNHEX(MD5('suc-01'))),
  (UNHEX(MD5('usr-04')), UNHEX(MD5('suc-02'))),
  (UNHEX(MD5('usr-05')), UNHEX(MD5('suc-04')));

INSERT INTO paciente
  (id, optica_id, nombre, fecha_nacimiento, sexo, telefono, correo, direccion)
VALUES
  (UNHEX(MD5('pac-01')), UNHEX(MD5('opt-01')), 'Juan Pérez López',      '1985-03-12', 'M',
   '3511234567', 'juan.perez@correo.com',      'Calle Morelos 15, Zamora'),
  (UNHEX(MD5('pac-02')), UNHEX(MD5('opt-01')), 'María Fernanda Ochoa',  '1992-07-25', 'F',
   '3512345678', 'mafer.ochoa@correo.com',     NULL),
  (UNHEX(MD5('pac-03')), UNHEX(MD5('opt-01')), 'Roberto Sánchez Mora',  '1958-11-02', 'M',
   '3513456789', 'roberto.sanchez@correo.com', 'Av. Juárez 210, Zamora'),
  (UNHEX(MD5('pac-04')), UNHEX(MD5('opt-01')), 'Ana Lucía Torres Gil',  '2010-01-30', 'F',
   '3514567890', 'ana.torres@correo.com',      'Calle Hidalgo 8, Zamora'),
  -- 'Juana' también empieza con 'Juan': útil para ver la búsqueda por prefijo.
  (UNHEX(MD5('pac-05')), UNHEX(MD5('opt-01')), 'Juana Martínez Cruz',   '1970-09-18', 'F',
   '3515678901', 'juana.martinez@correo.com',  NULL),
  (UNHEX(MD5('pac-06')), UNHEX(MD5('opt-02')), 'Luis Alberto Rivas',    '1979-04-07', 'M',
   '3516789012', 'luis.rivas@correo.com',      'Calle Allende 9, Jacona');

-- El consecutivo del folio es global, no por óptica (uq_expediente_folio).
INSERT INTO expediente (id, paciente_id, fecha_creacion, folio) VALUES
  (UNHEX(MD5('exp-01')), UNHEX(MD5('pac-01')), '2025-02-10', 'EXP-2025-0001'),
  (UNHEX(MD5('exp-02')), UNHEX(MD5('pac-02')), '2025-06-03', 'EXP-2025-0002'),
  (UNHEX(MD5('exp-03')), UNHEX(MD5('pac-03')), '2025-09-20', 'EXP-2025-0003'),
  (UNHEX(MD5('exp-04')), UNHEX(MD5('pac-04')), '2026-03-05', 'EXP-2026-0001'),
  (UNHEX(MD5('exp-05')), UNHEX(MD5('pac-05')), '2026-04-22', 'EXP-2026-0002'),
  (UNHEX(MD5('exp-06')), UNHEX(MD5('pac-06')), '2026-05-10', 'EXP-2026-0003');

INSERT INTO asiento_clinico
  (id, expediente_id, usuario_id, sucursal_id, fecha,
   sintomas, enfermedades, heredofamiliares, analisis_preliminar, observaciones)
VALUES
  (UNHEX(MD5('asi-01')), UNHEX(MD5('exp-01')), UNHEX(MD5('usr-02')), UNHEX(MD5('suc-01')), '2025-02-10',
   'Visión borrosa de lejos', NULL, 'Padre con miopía', 'Miopía leve', 'Primera consulta'),
  (UNHEX(MD5('asi-02')), UNHEX(MD5('exp-01')), UNHEX(MD5('usr-02')), UNHEX(MD5('suc-02')), '2026-02-15',
   'Revisión anual', NULL, NULL, 'Miopía estable con astigmatismo leve', 'Cambio de graduación'),
  (UNHEX(MD5('asi-03')), UNHEX(MD5('exp-02')), UNHEX(MD5('usr-02')), UNHEX(MD5('suc-01')), '2025-06-03',
   'Dolor de cabeza al usar computadora', NULL, NULL, 'Astigmatismo', 'Uso de filtro de luz azul'),
  (UNHEX(MD5('asi-04')), UNHEX(MD5('exp-03')), UNHEX(MD5('usr-02')), UNHEX(MD5('suc-02')), '2025-09-20',
   'Dificultad para leer de cerca', 'Diabetes tipo 2', 'Madre con glaucoma', 'Presbicia', 'Se sugiere revisión de fondo de ojo'),
  -- Atendido por usr-04 antes de su baja: el historial conserva la referencia.
  (UNHEX(MD5('asi-05')), UNHEX(MD5('exp-03')), UNHEX(MD5('usr-04')), UNHEX(MD5('suc-02')), '2026-01-12',
   'Seguimiento', 'Diabetes tipo 2', NULL, 'Presbicia progresiva', 'Aumenta adición'),
  (UNHEX(MD5('asi-06')), UNHEX(MD5('exp-04')), UNHEX(MD5('usr-02')), UNHEX(MD5('suc-01')), '2026-03-05',
   'No ve el pizarrón', NULL, 'Ambos padres con miopía', 'Miopía', 'Paciente menor de edad, acude con su madre'),
  (UNHEX(MD5('asi-07')), UNHEX(MD5('exp-05')), UNHEX(MD5('usr-02')), UNHEX(MD5('suc-03')), '2026-04-22',
   'Fatiga visual', 'Hipertensión', NULL, 'Hipermetropía y presbicia', NULL),
  (UNHEX(MD5('asi-08')), UNHEX(MD5('exp-06')), UNHEX(MD5('usr-05')), UNHEX(MD5('suc-04')), '2026-05-10',
   'Visión borrosa', NULL, NULL, 'Astigmatismo miópico', NULL),
  -- Revisión de rutina sin corrección: asiento SIN receta (caso legítimo).
  (UNHEX(MD5('asi-09')), UNHEX(MD5('exp-02')), UNHEX(MD5('usr-02')), UNHEX(MD5('suc-01')), '2026-06-18',
   'Revisión de rutina', NULL, NULL, 'Graduación sin cambios', 'No se emite receta nueva');

INSERT INTO receta
  (id, asiento_id, fecha, material_mica, dip, altura,
   od_esfera, od_cilindro, od_eje, od_adicion,
   oi_esfera, oi_cilindro, oi_eje, oi_adicion)
VALUES
  (UNHEX(MD5('rec-01')), UNHEX(MD5('asi-01')), '2025-02-10', 'CR-39',          63.0, 21.0,
   -1.25, NULL,  NULL, NULL,   -1.00, NULL,  NULL, NULL),
  (UNHEX(MD5('rec-02')), UNHEX(MD5('asi-02')), '2026-02-15', 'Policarbonato',  63.0, 21.0,
   -1.50, -0.50, 180,  NULL,   -1.25, -0.25, 170,  NULL),
  (UNHEX(MD5('rec-03')), UNHEX(MD5('asi-03')), '2025-06-03', 'CR-39',          60.5, 19.5,
   -0.25, -1.00,  90,  NULL,   -0.50, -0.75,  85,  NULL),
  (UNHEX(MD5('rec-04')), UNHEX(MD5('asi-04')), '2025-09-20', 'Alto índice',    66.0, 22.0,
    0.75, NULL,  NULL, 1.5,     0.50, NULL,  NULL, 1.5),
  (UNHEX(MD5('rec-05')), UNHEX(MD5('asi-05')), '2026-01-14', 'Alto índice',    66.0, 22.0,
    0.75, NULL,  NULL, 2.0,     0.75, NULL,  NULL, 2.0),
  (UNHEX(MD5('rec-06')), UNHEX(MD5('asi-06')), '2026-03-05', 'Policarbonato',  56.0, 18.0,
   -2.00, NULL,  NULL, NULL,   -2.25, NULL,  NULL, NULL),
  (UNHEX(MD5('rec-07')), UNHEX(MD5('asi-07')), '2026-04-22', 'CR-39',          62.0, 20.0,
    1.25, NULL,  NULL, 1.0,     1.50, NULL,  NULL, 1.0),
  (UNHEX(MD5('rec-08')), UNHEX(MD5('asi-08')), '2026-05-10', 'Policarbonato',  64.0, 21.5,
   -0.75, -1.25,  10,  NULL,   -1.00, -1.50, 175,  NULL);


-- =====================================================================
--  PARTE 3 · PROCEDIMIENTOS ALMACENADOS Y TRANSACCIONES
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_buscar_paciente;
DROP PROCEDURE IF EXISTS sp_actualizar_contacto_paciente;
DROP PROCEDURE IF EXISTS sp_alta_sucursal;
DROP PROCEDURE IF EXISTS sp_alta_paciente_con_expediente;
DROP PROCEDURE IF EXISTS sp_registrar_consulta;
DROP PROCEDURE IF EXISTS sp_reasignar_sucursales_usuario;
DROP PROCEDURE IF EXISTS sp_registrar_consulta_sin_tx;

-- ---------------------------------------------------------------------
--  3.A · Procedimientos SIN control transaccional
--
--  Criterio: el procedimiento ejecuta una sola sentencia que modifica
--  datos, o ninguna. InnoDB ya garantiza que una sentencia individual
--  es atómica, de modo que START TRANSACTION / COMMIT no aportaría
--  ninguna garantía adicional. Cuando hay validaciones, éstas se
--  colocan ANTES de la escritura: si fallan, no hay nada que revertir.
-- ---------------------------------------------------------------------

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
         TIMESTAMPDIFF(YEAR, p.fecha_nacimiento, CURRENT_DATE) AS edad,
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
--     Actualiza teléfono, correo y dirección. chk_paciente_correo valida
--     el formato del correo y telefono es NOT NULL; si algo no se
--     cumple, la sentencia completa se rechaza sin efectos parciales.
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

  SET v_sucursal = UUID_TO_BIN(UUID(), 1);

  INSERT INTO sucursal (id, optica_id, nombre, direccion)
  VALUES (v_sucursal, UUID_TO_BIN(p_optica_id), p_nombre, p_direccion);

  SET p_sucursal_id = BIN_TO_UUID(v_sucursal);
END$$


-- ---------------------------------------------------------------------
--  3.B · Procedimientos CON control transaccional
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
-- ---------------------------------------------------------------------

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

  SET v_paciente   = UUID_TO_BIN(UUID(), 1);
  SET v_expediente = UUID_TO_BIN(UUID(), 1);
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
--     Éste es el caso crítico del esquema: un asiento SIN receta es un
--     estado válido (una revisión de rutina, como asi-09), así que
--     ninguna restricción detecta una consulta a medias. Si el INSERT
--     de la receta se rechaza, sin transacción el asiento quedaría
--     almacenado como si nunca se hubiera graduado al paciente.
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
  IN  p_dip              DECIMAL(4,1),
  IN  p_altura           DECIMAL(4,1),
  IN  p_od_esfera        DECIMAL(4,2),
  IN  p_od_cilindro      DECIMAL(4,2),
  IN  p_od_eje           SMALLINT,
  IN  p_od_adicion       DECIMAL(3,1),
  IN  p_oi_esfera        DECIMAL(4,2),
  IN  p_oi_cilindro      DECIMAL(4,2),
  IN  p_oi_eje           SMALLINT,
  IN  p_oi_adicion       DECIMAL(3,1),
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
  SET v_asiento    = UUID_TO_BIN(UUID(), 1);

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
      SET v_receta = UUID_TO_BIN(UUID(), 1);

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
--     sucursales inexistentes. En lugar de abortar toda la operación,
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


-- ---------------------------------------------------------------------
--  3.C · Procedimiento de contraste
--
--  Reproduce la operación de sp_registrar_consulta SIN control
--  transaccional. Existe únicamente para demostrar el efecto de la
--  ausencia de transacciones y no forma parte de la aplicación.
--
--  Con autocommit activo (valor por omisión), cada INSERT se confirma
--  por separado: si el segundo es rechazado, el primero permanece.
-- ---------------------------------------------------------------------
CREATE PROCEDURE sp_registrar_consulta_sin_tx(
  IN p_expediente_id CHAR(36),
  IN p_usuario_id    CHAR(36),
  IN p_sucursal_id   CHAR(36),
  IN p_analisis      TEXT,
  IN p_od_esfera     DECIMAL(4,2),
  IN p_od_eje        SMALLINT
)
COMMENT 'DEMOSTRATIVO: misma operacion sin transaccion. No usar en produccion'
BEGIN
  DECLARE v_asiento BINARY(16);
  DECLARE v_receta  BINARY(16);

  SET v_asiento = UUID_TO_BIN(UUID(), 1);
  SET v_receta  = UUID_TO_BIN(UUID(), 1);

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
--  PARTE 4 · SEGURIDAD: ROLES, USUARIOS Y PERMISOS
--
--  Principios aplicados:
--    1. Mínimo privilegio: cada rol recibe solo lo que necesita.
--    2. Permisos por ROL, no por usuario: los usuarios solo heredan.
--    3. Datos clínicos protegidos: recepción y administración no los ven.
--    4. Expediente clínico inmutable: ningún rol operativo hace DELETE
--       sobre asiento_clinico ni receta.
--    5. password_hash nunca se puede leer (solo escribir).
--    6. Cuentas con política de contraseñas, bloqueo y host restringido.
--
--  Nota: GRANT y CREATE USER actualizan las tablas de privilegios en
--  memoria por sí mismos; FLUSH PRIVILEGES no es necesario.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 4.1 ROLES
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
-- 4.2 PERMISOS SOBRE TABLAS
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
-- Mínimo que necesita:
--   mysqldump --single-transaction --routines --triggers --events
-- SHOW_ROUTINE permite leer el cuerpo de los procedimientos; sin él el
-- volcado sale sin rutinas.
GRANT SELECT, LOCK TABLES, SHOW VIEW, TRIGGER, EVENT
  ON optica_db.* TO 'rol_respaldo';
GRANT PROCESS, SHOW_ROUTINE ON *.* TO 'rol_respaldo';

-- ---------------------------------------------------------------------
-- 4.3 PERMISOS DE EJECUCIÓN SOBRE PROCEDIMIENTOS
--
--  Los procedimientos se crean con SQL SECURITY DEFINER, el valor por
--  omisión en MySQL: se ejecutan con los privilegios de quien los creó.
--  Esto permite conceder EXECUTE sobre una operación completa sin
--  otorgar permisos directos sobre las tablas que toca.
--
--  sp_registrar_consulta_sin_tx no se concede a ningún rol: existe
--  únicamente para la demostración de la PARTE 6.
-- ---------------------------------------------------------------------
GRANT EXECUTE ON PROCEDURE optica_db.sp_buscar_paciente              TO 'rol_recepcion';
GRANT EXECUTE ON PROCEDURE optica_db.sp_alta_paciente_con_expediente TO 'rol_recepcion';
GRANT EXECUTE ON PROCEDURE optica_db.sp_actualizar_contacto_paciente TO 'rol_recepcion';

GRANT EXECUTE ON PROCEDURE optica_db.sp_buscar_paciente              TO 'rol_optometrista';
GRANT EXECUTE ON PROCEDURE optica_db.sp_registrar_consulta           TO 'rol_optometrista';

GRANT EXECUTE ON PROCEDURE optica_db.sp_alta_sucursal                TO 'rol_admin_app';
GRANT EXECUTE ON PROCEDURE optica_db.sp_reasignar_sucursales_usuario TO 'rol_admin_app';

GRANT EXECUTE ON PROCEDURE optica_db.sp_buscar_paciente              TO 'rol_auditor';

-- ---------------------------------------------------------------------
-- 4.4 USUARIOS
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

-- Respaldos (cuenta técnica: la contraseña no expira para no romper el
-- respaldo programado)
CREATE USER IF NOT EXISTS 'usr_respaldo'@'localhost'
  IDENTIFIED BY 'Cambiar#Backup_2026'
  WITH MAX_USER_CONNECTIONS 2
  PASSWORD EXPIRE NEVER
  FAILED_LOGIN_ATTEMPTS 5 PASSWORD_LOCK_TIME 1;
GRANT 'rol_respaldo' TO 'usr_respaldo'@'localhost';
SET DEFAULT ROLE 'rol_respaldo' TO 'usr_respaldo'@'localhost';


-- =====================================================================
--  PARTE 5 · VERIFICACIÓN
-- =====================================================================

SHOW TABLES;

-- TABLE_ROWS es una estimación del optimizador en InnoDB, no un conteo
-- exacto. Sirve para confirmar que las tablas existen y con qué motor e
-- intercalación quedaron.
SELECT
    TABLE_NAME       AS tabla,
    TABLE_ROWS       AS filas_estimadas,
    ENGINE           AS motor,
    TABLE_COLLATION  AS intercalacion
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'optica_db'
ORDER BY TABLE_NAME;

-- Conteo exacto de los datos de muestra
SELECT 'optica' AS tabla, COUNT(*) AS filas FROM optica UNION ALL
SELECT 'rol',              COUNT(*) FROM rol              UNION ALL
SELECT 'sucursal',         COUNT(*) FROM sucursal         UNION ALL
SELECT 'usuario',          COUNT(*) FROM usuario          UNION ALL
SELECT 'usuario_sucursal', COUNT(*) FROM usuario_sucursal UNION ALL
SELECT 'paciente',         COUNT(*) FROM paciente         UNION ALL
SELECT 'expediente',       COUNT(*) FROM expediente       UNION ALL
SELECT 'asiento_clinico',  COUNT(*) FROM asiento_clinico  UNION ALL
SELECT 'receta',           COUNT(*) FROM receta;

SELECT
    TABLE_NAME             AS tabla_hija,
    CONSTRAINT_NAME        AS restriccion,
    COLUMN_NAME            AS columna,
    REFERENCED_TABLE_NAME  AS tabla_padre
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'optica_db'
  AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY TABLE_NAME, CONSTRAINT_NAME;

-- Reglas de borrado declaradas, para contrastar contra la tabla de
-- Integridad Referencial del documento.
SELECT
    CONSTRAINT_NAME  AS restriccion,
    TABLE_NAME       AS tabla_hija,
    REFERENCED_TABLE_NAME AS tabla_padre,
    DELETE_RULE      AS regla_de_borrado,
    UPDATE_RULE      AS regla_de_actualizacion
FROM information_schema.REFERENTIAL_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA = 'optica_db'
ORDER BY TABLE_NAME, CONSTRAINT_NAME;

-- Procedimientos registrados: siete renglones, todos SECURITY_TYPE DEFINER
SELECT ROUTINE_NAME    AS procedimiento,
       SECURITY_TYPE   AS seguridad,
       ROUTINE_COMMENT AS descripcion
FROM information_schema.ROUTINES
WHERE ROUTINE_SCHEMA = 'optica_db'
  AND ROUTINE_TYPE   = 'PROCEDURE'
ORDER BY ROUTINE_NAME;

-- Permisos efectivos de cada usuario (con los de su rol)
SHOW GRANTS FOR 'usr_admin'@'localhost'         USING 'rol_admin_app';
SHOW GRANTS FOR 'usr_optometrista1'@'localhost' USING 'rol_optometrista';
SHOW GRANTS FOR 'usr_recepcion1'@'localhost'    USING 'rol_recepcion';
SHOW GRANTS FOR 'usr_auditor'@'localhost'       USING 'rol_auditor';
SHOW GRANTS FOR 'usr_respaldo'@'localhost'      USING 'rol_respaldo';

-- Qué rol tiene OTORGADO cada usuario, y cuál queda ACTIVO por defecto
-- (son dos tablas distintas del catálogo: role_edges vs default_roles)
SELECT re.TO_USER AS usuario,
       re.FROM_USER AS rol_otorgado,
       dr.DEFAULT_ROLE_USER AS rol_activo_por_defecto
FROM mysql.role_edges re
LEFT JOIN mysql.default_roles dr
  ON dr.USER = re.TO_USER AND dr.HOST = re.TO_HOST
WHERE re.TO_USER LIKE 'usr\_%'
ORDER BY usuario;

-- Políticas de cada cuenta. El bloqueo por intentos fallidos no tiene
-- columna propia: se guarda en el JSON User_attributes.
SELECT user, host, password_lifetime, password_reuse_history,
       User_attributes->>'$.Password_locking.failed_login_attempts'   AS intentos_fallidos,
       User_attributes->>'$.Password_locking.password_lock_time_days' AS dias_bloqueo,
       account_locked, password_expired
FROM mysql.user
WHERE user LIKE 'usr\_%'
ORDER BY user;


-- =====================================================================
--  PARTE 6 · PRUEBAS DE EJECUCIÓN
--
--  ATENCIÓN: las pruebas 3, 5 y 6 provocan errores de forma
--  deliberada, porque ése es justamente el comportamiento que se
--  quiere demostrar. Ejecutar el archivo con --force, o cada prueba
--  por separado.
--
--  El apartado de limpieza, al final, devuelve los datos de muestra a
--  su estado original para que el archivo pueda repetirse.
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
-- ---------------------------------------------------------------------

-- 1.1 Consulta por prefijo de nombre: devuelve Juan y Juana
CALL sp_buscar_paciente(@opt01, 'Juan');

-- 1.2 Actualización de contacto: un solo UPDATE
CALL sp_actualizar_contacto_paciente(
  @pac01, '3511234567', 'juan.perez@correo.com',
  'Calle Morelos 15, Col. Centro, Zamora');

SELECT nombre, telefono, correo, direccion
FROM paciente
WHERE id = UUID_TO_BIN(@pac01);

-- 1.3 Alta de sucursal: el identificador generado regresa en el OUT
CALL sp_alta_sucursal(
  @opt01, 'Sucursal Poniente', 'Av. Juárez 500, Zamora', @suc_nueva);

SELECT @suc_nueva AS sucursal_id;

-- ---------------------------------------------------------------------
--  Prueba 2 · Alta de paciente con expediente (transacción)
--  Resultado esperado: el siguiente folio del año en curso.
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
--  El correo no cumple chk_paciente_correo: falla el INSERT del
--  paciente y no se crea ningún expediente. Los conteos no cambian.
-- ---------------------------------------------------------------------
SELECT COUNT(*) AS pacientes, (SELECT COUNT(*) FROM expediente) AS expedientes
FROM paciente;

-- Error esperado 3819: Check constraint 'chk_paciente_correo' is violated
CALL sp_alta_paciente_con_expediente(
  @opt01, 'Prueba Correo Invalido', '1990-01-01', 'M',
  '3510000000', 'correo-sin-arroba', NULL, @p_tmp, @f_tmp);

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
--  viola chk_receta_od_eje (rango permitido 1-180). Lo que cambia es el
--  estado en que queda la base de datos.
--
--  asientos_sin_receta no parte de cero: asi-09 es una revisión de
--  rutina que no generó receta. Lo que interesa es la variación.
-- ---------------------------------------------------------------------

-- Estado inicial
SELECT COUNT(*) AS asientos,
       (SELECT COUNT(*) FROM receta) AS recetas,
       (SELECT COUNT(*) FROM asiento_clinico a
          LEFT JOIN receta r ON r.asiento_id = a.id
         WHERE r.id IS NULL) AS asientos_sin_receta
FROM asiento_clinico;

-- 6.1 Versión SIN transacción
-- Error esperado 3819: Check constraint 'chk_receta_od_eje' is violated
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

-- Identificación del renglón incompleto
SELECT BIN_TO_UUID(a.id) AS asiento_incompleto, a.fecha, a.analisis_preliminar
FROM asiento_clinico a
LEFT JOIN receta r ON r.asiento_id = a.id
WHERE r.id IS NULL
  AND a.analisis_preliminar = 'Prueba sin transaccion';

-- 6.2 Versión CON transacción, mismo error
-- Error esperado 3819: Check constraint 'chk_receta_od_eje' is violated
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

-- 6.3 El renglón incompleto hay que localizarlo y eliminarlo a mano:
--     ninguna restricción lo señala, porque un asiento sin receta es
--     un estado válido del modelo.
DELETE FROM asiento_clinico
 WHERE analisis_preliminar = 'Prueba sin transaccion'
   AND NOT EXISTS (SELECT 1 FROM receta r WHERE r.asiento_id = asiento_clinico.id);

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
--  Prueba 9 · Permisos por rol (ejecutar en otra sesión)
-- ---------------------------------------------------------------------
--  mysql -u usr_recepcion1 -p optica_db
--    CALL sp_buscar_paciente(BIN_TO_UUID(UNHEX(MD5('opt-01'))), 'Juan');  -- OK
--    SELECT * FROM asiento_clinico;          -- ERROR 1142: sin acceso clínico
--    SELECT password_hash FROM usuario;      -- ERROR 1143: columna no permitida
--
--  mysql -u usr_optometrista1 -p optica_db
--    DELETE FROM receta;                     -- ERROR 1142: expediente inmutable
-- ---------------------------------------------------------------------

-- ---------------------------------------------------------------------
--  Limpieza · devuelve los datos de muestra a su estado original
--
--  Orden: asientos (sus recetas se borran por CASCADE), expediente y
--  paciente, que están protegidos con RESTRICT.
-- ---------------------------------------------------------------------
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

-- Conteo final: debe coincidir con el de la PARTE 5
SELECT 'optica' AS tabla, COUNT(*) AS filas FROM optica UNION ALL
SELECT 'rol',              COUNT(*) FROM rol              UNION ALL
SELECT 'sucursal',         COUNT(*) FROM sucursal         UNION ALL
SELECT 'usuario',          COUNT(*) FROM usuario          UNION ALL
SELECT 'usuario_sucursal', COUNT(*) FROM usuario_sucursal UNION ALL
SELECT 'paciente',         COUNT(*) FROM paciente         UNION ALL
SELECT 'expediente',       COUNT(*) FROM expediente       UNION ALL
SELECT 'asiento_clinico',  COUNT(*) FROM asiento_clinico  UNION ALL
SELECT 'receta',           COUNT(*) FROM receta;
