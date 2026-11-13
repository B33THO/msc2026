-- =====================================================================
--  optica_db · GUION DE DEMOSTRACIÓN EN VIVO (Exposición final)
--
--  Acompaña a expo final/index.html: cada bloque [X.Y] corresponde a la
--  diapositiva del mismo número.
--
--  Uso en DBeaver
--    · Ctrl+Enter  ejecuta la sentencia bajo el cursor (las sentencias
--                  se separan con una línea en blanco; no partir un
--                  CALL con líneas vacías).
--    · Alt+X       ejecuta el bloque seleccionado como script.
--    · Auto-commit ENCENDIDO (botón de la barra de herramientas).
--    · Los errores marcados "ERROR ESPERADO" son intencionales.
--
--  Requisitos
--    · La base, las tablas y los datos se crean en vivo en [P.1].
--    · Roles, permisos y cuentas usr_* se crean en vivo en [2.0].
--    · Conexiones en DBeaver (propiedad del driver
--      allowPublicKeyRetrieval=true):
--        root               creación de objetos y temas 1 y 3
--        usr_recepcion1     Cambiar#Recep_2026
--        usr_optometrista1  Cambiar#Opto_2026
--        usr_auditor        Cambiar#Audit_2026
--      OJO con Docker: las cuentas usr_* están definidas en 'localhost';
--      si DBeaver entra por el puerto publicado del contenedor responde
--      1045, y esas demos se hacen desde la terminal:
--        docker exec -it mysql-optica mysql -u usr_recepcion1 -p optica_db
--    · Bloques "TERMINAL": comandos de PowerShell, no SQL. Se asume el
--      contenedor Docker mysql-optica de la Actividad 5. Sin Docker,
--      quitar el prefijo "docker exec -it mysql-optica".
-- =====================================================================


-- =====================================================================
--  [P.1] CREACIÓN DE LA BASE: ESTRUCTURA Y DATOS DE MUESTRA   (root)
--  Ejecutar todo el bloque con Alt+X (o "Copiar todo" en la diapositiva
--  y pegarlo en un editor nuevo). Las tablas se crean en orden de
--  dependencias: primero las que no tienen llaves foráneas.
-- =====================================================================
-- ---- BASE DE DATOS
-- Se elimina si existe para partir de cero (roles y cuentas no se tocan:
-- viven en el esquema mysql).
DROP DATABASE IF EXISTS optica_db;

CREATE DATABASE optica_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE optica_db;

-- ---- 1. OPTICA
-- Entidad raíz del modelo. Todo cuelga directa o indirectamente de aquí.
CREATE TABLE optica (
    id      BINARY(16)   NOT NULL COMMENT 'UUID ordenado generado en la capa de aplicación',
    nombre  VARCHAR(150) NOT NULL COMMENT 'Nombre comercial o razón social',
    CONSTRAINT pk_optica PRIMARY KEY (id)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = 'Negocios registrados en el sistema';

-- ---- 2. ROL
-- Catálogo de perfiles de permisos.
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

-- ---- 3. SUCURSAL
-- Punto físico de atención perteneciente a una óptica.
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

-- ---- 4. USUARIO
-- Personal que accede al sistema.
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

-- ---- 5. USUARIO_SUCURSAL
-- Tabla puente. Resuelve el muchos a muchos entre usuario y sucursal.
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

-- ---- 6. PACIENTE
-- Datos de identificación y contacto de la persona atendida.
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

-- ---- 7. EXPEDIENTE
-- Contenedor del historial clínico. Uno solo por paciente.
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

-- ---- 8. ASIENTO_CLINICO
-- Registro de cada consulta. Tabla de mayor crecimiento del modelo.
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

-- ---- 9. RECETA
-- Graduación óptica derivada de una consulta.
-- OD = ojo derecho (oculus dexter) | OI = ojo izquierdo (oculus sinister)
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

-- ---- DATOS DE MUESTRA
-- Los id se derivan de una etiqueta legible: UNHEX(MD5('opt-01')) da
-- siempre los mismos 16 bytes, así las demos localizan registros
-- conocidos con BIN_TO_UUID(UNHEX(MD5('etiqueta'))).
-- password_hash contiene valores ficticios con formato bcrypt.

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

-- ---- VERIFICACIÓN
-- Esperado: 9 tablas
SHOW TABLES;

-- Esperado: 2 · 3 · 4 · 5 · 9 · 6 · 6 · 9 · 8
SELECT 'optica' AS tabla, COUNT(*) AS filas FROM optica UNION ALL
SELECT 'rol',              COUNT(*) FROM rol              UNION ALL
SELECT 'sucursal',         COUNT(*) FROM sucursal         UNION ALL
SELECT 'usuario',          COUNT(*) FROM usuario          UNION ALL
SELECT 'usuario_sucursal', COUNT(*) FROM usuario_sucursal UNION ALL
SELECT 'paciente',         COUNT(*) FROM paciente         UNION ALL
SELECT 'expediente',       COUNT(*) FROM expediente       UNION ALL
SELECT 'asiento_clinico',  COUNT(*) FROM asiento_clinico  UNION ALL
SELECT 'receta',           COUNT(*) FROM receta;

-- Llaves foráneas y su regla de borrado (RESTRICT protege el historial;
-- CASCADE sólo donde el hijo no tiene sentido sin el padre)
SELECT TABLE_NAME            AS tabla_hija,
       REFERENCED_TABLE_NAME AS tabla_padre,
       CONSTRAINT_NAME       AS restriccion,
       DELETE_RULE           AS al_borrar
FROM information_schema.REFERENTIAL_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA = 'optica_db'
ORDER BY TABLE_NAME, CONSTRAINT_NAME;


-- =====================================================================
--  [P.2] VARIABLES DE SESIÓN Y LÍNEA BASE   (conexión: root)
--  Ejecutar al abrir el editor del tema 1. Las variables @ viven sólo
--  en esta sesión.
-- =====================================================================
USE optica_db;

SET @opt01 = BIN_TO_UUID(UNHEX(MD5('opt-01')));
SET @suc01 = BIN_TO_UUID(UNHEX(MD5('suc-01')));
SET @suc04 = BIN_TO_UUID(UNHEX(MD5('suc-04')));
SET @usr02 = BIN_TO_UUID(UNHEX(MD5('usr-02')));
SET @usr04 = BIN_TO_UUID(UNHEX(MD5('usr-04')));
SET @pac01 = BIN_TO_UUID(UNHEX(MD5('pac-01')));

-- Esperado: 6 pacientes, 6 expedientes, 9 asientos, 8 recetas, 1 sin receta
SELECT (SELECT COUNT(*) FROM paciente)        AS pacientes,
       (SELECT COUNT(*) FROM expediente)      AS expedientes,
       (SELECT COUNT(*) FROM asiento_clinico) AS asientos,
       (SELECT COUNT(*) FROM receta)          AS recetas,
       (SELECT COUNT(*) FROM asiento_clinico a
          LEFT JOIN receta r ON r.asiento_id = a.id
         WHERE r.id IS NULL)                  AS asientos_sin_receta;


-- #####################################################################
--  TEMA 1 · PROCEDIMIENTOS ALMACENADOS Y TRANSACCIONES (Actividad 3)
-- #####################################################################

-- =====================================================================
--  [1.0] CREACIÓN DE LOS PROCEDIMIENTOS   (conexión: root)
--  Ejecutar TODO el bloque con Alt+X. DELIMITER $$ cambia el fin de
--  sentencia del cliente: así los ';' del cuerpo no cortan el
--  CREATE PROCEDURE. DELIMITER no llega al servidor; lo interpreta
--  DBeaver (o la terminal mysql). Al final se regresa a ';'.
-- =====================================================================
-- Por si se repite la demo: borrar las versiones anteriores (Alt+X)
DROP PROCEDURE IF EXISTS sp_buscar_paciente;
DROP PROCEDURE IF EXISTS sp_actualizar_contacto_paciente;
DROP PROCEDURE IF EXISTS sp_alta_sucursal;
DROP PROCEDURE IF EXISTS sp_alta_paciente_con_expediente;
DROP PROCEDURE IF EXISTS sp_registrar_consulta;

-- Desde aquí el fin de sentencia es $$
DELIMITER $$

-- 1/5 · sin TX · sólo lectura, búsqueda por prefijo
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

-- 2/5 · sin TX · validación previa + un solo UPDATE
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

-- 3/5 · sin TX · un solo INSERT, id en parámetro OUT
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

-- 4/5 · con TX · paciente + expediente, folio con FOR UPDATE
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

-- 5/5 · con TX · asiento + receta, tres reglas de negocio
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

-- De vuelta al ';' normal
DELIMITER ;

-- Esperado: 5 procedimientos, 2 con START TRANSACTION (con_tx = 1)
SELECT ROUTINE_NAME AS procedimiento,
       ROUTINE_DEFINITION LIKE '%START TRANSACTION%' AS con_tx,
       ROUTINE_COMMENT AS descripcion
FROM information_schema.ROUTINES
WHERE ROUTINE_SCHEMA = 'optica_db' AND ROUTINE_TYPE = 'PROCEDURE'
ORDER BY CREATED;


-- =====================================================================
--  [1.1] PROCEDIMIENTOS SIN TRANSACCIÓN   (conexión: root)
--  Una sola sentencia de escritura: InnoDB ya la hace atómica.
-- =====================================================================
-- Consulta por prefijo: devuelve Juan Pérez y Juana Martínez
CALL sp_buscar_paciente(@opt01, 'Juan');

-- Un solo UPDATE, con validación previa
CALL sp_actualizar_contacto_paciente(
  @pac01, '3511234567', 'juan.perez@correo.com',
  'Calle Morelos 15, Col. Centro, Zamora');

SELECT nombre, telefono, correo, direccion
FROM paciente WHERE id = UUID_TO_BIN(@pac01);

-- Un solo INSERT; el id generado regresa en el parámetro OUT
CALL sp_alta_sucursal(
  @opt01, 'Sucursal Poniente', 'Av. Juárez 500, Zamora', @suc_nueva);

SELECT @suc_nueva AS sucursal_id;


-- =====================================================================
--  [1.2] TRANSACCIÓN: PACIENTE + EXPEDIENTE   (conexión: root)
--  Dos tablas y un folio consecutivo en una sola unidad de trabajo.
-- =====================================================================
CALL sp_alta_paciente_con_expediente(
  @opt01, 'Rosa Medina Alcaraz', '1990-05-14', 'F',
  '3519876543', 'rosa.medina@correo.com', 'Calle Allende 22, Zamora',
  @pac_rosa, @folio_rosa);

-- Esperado: folio EXP-2026-0004 (siguiente del año en curso)
SELECT @pac_rosa AS paciente_id, @folio_rosa AS folio;

SET @exp_rosa = (SELECT BIN_TO_UUID(id) FROM expediente
                  WHERE paciente_id = UUID_TO_BIN(@pac_rosa));


-- =====================================================================
--  [1.3] ATOMICIDAD ANTE UN DATO INVÁLIDO   (conexión: root)
--  El correo viola chk_paciente_correo: ni paciente ni expediente.
-- =====================================================================
-- Antes: 7 pacientes, 7 expedientes
SELECT (SELECT COUNT(*) FROM paciente)   AS pacientes,
       (SELECT COUNT(*) FROM expediente) AS expedientes;

-- ERROR ESPERADO 3819: Check constraint 'chk_paciente_correo' is violated
CALL sp_alta_paciente_con_expediente(
  @opt01, 'Prueba Correo Invalido', '1990-01-01', 'M',
  '3510000000', 'correo-sin-arroba', NULL, @p_tmp, @f_tmp);

-- Después: los mismos 7 y 7
SELECT (SELECT COUNT(*) FROM paciente)   AS pacientes,
       (SELECT COUNT(*) FROM expediente) AS expedientes;


-- =====================================================================
--  [1.4] CONSULTA CON RECETA Y REGLAS DE NEGOCIO   (conexión: root)
--  SIGNAL SQLSTATE '45000' expresa reglas que ninguna FK puede.
-- =====================================================================
-- Caso válido: asiento + receta en una transacción
CALL sp_registrar_consulta(
  @exp_rosa, @usr02, @suc01,
  'Cansancio visual al leer', NULL, 'Madre con astigmatismo',
  'Astigmatismo leve', 'Primera consulta',
  'CR-39', 61.0, 20.5,
  -0.50, -0.75,  90, NULL,
  -0.75, -0.50,  85, NULL,
  @asiento_rosa, @receta_rosa);

SELECT @asiento_rosa AS asiento_id, @receta_rosa AS receta_id;

-- ERROR ESPERADO 1644: La sucursal no pertenece a la optica del paciente
-- (suc-04 es de opt-02; Rosa es de opt-01)
CALL sp_registrar_consulta(
  @exp_rosa, @usr02, @suc04,
  NULL, NULL, NULL, 'Prueba de optica cruzada', NULL,
  NULL, NULL, NULL,
  -1.00, NULL, NULL, NULL, -1.00, NULL, NULL, NULL,
  @a_tmp, @r_tmp);

-- ERROR ESPERADO 1644: El usuario no existe o esta dado de baja
-- (usr-04 tiene activo = FALSE)
CALL sp_registrar_consulta(
  @exp_rosa, @usr04, @suc01,
  NULL, NULL, NULL, 'Prueba de usuario inactivo', NULL,
  NULL, NULL, NULL,
  -1.00, NULL, NULL, NULL, -1.00, NULL, NULL, NULL,
  @a_tmp, @r_tmp);


-- #####################################################################
--  TEMA 2 · SEGURIDAD: ROLES Y USUARIOS (Actividad 4)
-- #####################################################################

-- =====================================================================
--  [2.0] CREACIÓN DE ROLES, PERMISOS Y CUENTAS   (conexión: root)
--  Ejecutar TODO el bloque con Alt+X. Va después de [1.0] porque los
--  GRANT EXECUTE necesitan que los procedimientos ya existan (y un
--  DROP PROCEDURE borra los EXECUTE que tenía).
--  Cada GRANT de rol a usuario crea una fila en mysql.role_edges; cada
--  SET DEFAULT ROLE, una en mysql.default_roles.
-- =====================================================================
-- Por si se repite la demo: partir de cero (las cuentas caen con sus GRANT)
DROP USER IF EXISTS 'usr_admin'@'localhost', 'usr_optometrista1'@'localhost',
  'usr_recepcion1'@'localhost', 'usr_auditor'@'localhost', 'usr_respaldo'@'localhost';
DROP ROLE IF EXISTS 'rol_admin_app', 'rol_optometrista', 'rol_recepcion',
  'rol_auditor', 'rol_respaldo';

-- ---- 1. ROLES · cuentas bloqueadas que sólo agrupan permisos
CREATE ROLE 'rol_admin_app', 'rol_optometrista', 'rol_recepcion',
  'rol_auditor', 'rol_respaldo';

-- ---- 2. PERMISOS POR ROL
-- rol_admin_app · estructura y cuentas; no ve datos clínicos ni password_hash
GRANT SELECT, INSERT, UPDATE ON optica_db.optica   TO 'rol_admin_app';
GRANT SELECT, INSERT, UPDATE ON optica_db.sucursal TO 'rol_admin_app';
GRANT SELECT, INSERT, UPDATE ON optica_db.rol      TO 'rol_admin_app';
GRANT SELECT, INSERT, DELETE ON optica_db.usuario_sucursal TO 'rol_admin_app';
GRANT SELECT (id, optica_id, rol_id, nombre, correo, activo)
  ON optica_db.usuario TO 'rol_admin_app';
GRANT INSERT, UPDATE ON optica_db.usuario TO 'rol_admin_app';
GRANT EXECUTE ON PROCEDURE optica_db.sp_alta_sucursal TO 'rol_admin_app';

-- rol_optometrista · lee catálogos y pacientes; historial sin DELETE
GRANT SELECT ON optica_db.optica           TO 'rol_optometrista';
GRANT SELECT ON optica_db.sucursal         TO 'rol_optometrista';
GRANT SELECT ON optica_db.usuario_sucursal TO 'rol_optometrista';
GRANT SELECT (id, nombre) ON optica_db.usuario TO 'rol_optometrista';
GRANT SELECT ON optica_db.paciente         TO 'rol_optometrista';
GRANT SELECT ON optica_db.expediente       TO 'rol_optometrista';
GRANT SELECT, INSERT, UPDATE ON optica_db.asiento_clinico TO 'rol_optometrista';
GRANT SELECT, INSERT, UPDATE ON optica_db.receta          TO 'rol_optometrista';
GRANT EXECUTE ON PROCEDURE optica_db.sp_buscar_paciente    TO 'rol_optometrista';
GRANT EXECUTE ON PROCEDURE optica_db.sp_registrar_consulta TO 'rol_optometrista';

-- rol_recepcion · pacientes y expedientes; receta sí, asiento_clinico no
GRANT SELECT ON optica_db.optica   TO 'rol_recepcion';
GRANT SELECT ON optica_db.sucursal TO 'rol_recepcion';
GRANT SELECT (id, nombre) ON optica_db.usuario TO 'rol_recepcion';
GRANT SELECT, INSERT, UPDATE ON optica_db.paciente   TO 'rol_recepcion';
GRANT SELECT, INSERT         ON optica_db.expediente TO 'rol_recepcion';
GRANT SELECT ON optica_db.receta TO 'rol_recepcion';
GRANT EXECUTE ON PROCEDURE optica_db.sp_buscar_paciente              TO 'rol_recepcion';
GRANT EXECUTE ON PROCEDURE optica_db.sp_alta_paciente_con_expediente TO 'rol_recepcion';
GRANT EXECUTE ON PROCEDURE optica_db.sp_actualizar_contacto_paciente TO 'rol_recepcion';

-- rol_auditor · lectura total, excepto password_hash
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
GRANT EXECUTE ON PROCEDURE optica_db.sp_buscar_paciente TO 'rol_auditor';

-- rol_respaldo · lo mínimo para mysqldump --single-transaction --routines
GRANT SELECT, LOCK TABLES, SHOW VIEW, TRIGGER, EVENT
  ON optica_db.* TO 'rol_respaldo';
GRANT PROCESS, SHOW_ROUTINE ON *.* TO 'rol_respaldo';

-- ---- 3. CUENTAS · expira a 90 días, no repetir las últimas 5,
-- bloqueo de 1 día tras 5 intentos fallidos
CREATE USER 'usr_admin'@'localhost' IDENTIFIED BY 'Cambiar#Admin_2026'
  WITH MAX_USER_CONNECTIONS 5
  PASSWORD EXPIRE INTERVAL 90 DAY PASSWORD HISTORY 5
  FAILED_LOGIN_ATTEMPTS 5 PASSWORD_LOCK_TIME 1;
CREATE USER 'usr_optometrista1'@'localhost' IDENTIFIED BY 'Cambiar#Opto_2026'
  WITH MAX_USER_CONNECTIONS 5
  PASSWORD EXPIRE INTERVAL 90 DAY PASSWORD HISTORY 5
  FAILED_LOGIN_ATTEMPTS 5 PASSWORD_LOCK_TIME 1;
CREATE USER 'usr_recepcion1'@'localhost' IDENTIFIED BY 'Cambiar#Recep_2026'
  WITH MAX_USER_CONNECTIONS 5
  PASSWORD EXPIRE INTERVAL 90 DAY PASSWORD HISTORY 5
  FAILED_LOGIN_ATTEMPTS 5 PASSWORD_LOCK_TIME 1;
CREATE USER 'usr_auditor'@'localhost' IDENTIFIED BY 'Cambiar#Audit_2026'
  WITH MAX_USER_CONNECTIONS 2
  PASSWORD EXPIRE INTERVAL 90 DAY PASSWORD HISTORY 5
  FAILED_LOGIN_ATTEMPTS 5 PASSWORD_LOCK_TIME 1;
-- Cuenta técnica: no expira para no romper el respaldo programado
CREATE USER 'usr_respaldo'@'localhost' IDENTIFIED BY 'Cambiar#Backup_2026'
  WITH MAX_USER_CONNECTIONS 2
  PASSWORD EXPIRE NEVER
  FAILED_LOGIN_ATTEMPTS 5 PASSWORD_LOCK_TIME 1;

-- ---- 4. ROL OTORGADO (role_edges) Y ROL ACTIVO (default_roles)
GRANT 'rol_admin_app'    TO 'usr_admin'@'localhost';
GRANT 'rol_optometrista' TO 'usr_optometrista1'@'localhost';
GRANT 'rol_recepcion'    TO 'usr_recepcion1'@'localhost';
GRANT 'rol_auditor'      TO 'usr_auditor'@'localhost';
GRANT 'rol_respaldo'     TO 'usr_respaldo'@'localhost';
SET DEFAULT ROLE 'rol_admin_app'    TO 'usr_admin'@'localhost';
SET DEFAULT ROLE 'rol_optometrista' TO 'usr_optometrista1'@'localhost';
SET DEFAULT ROLE 'rol_recepcion'    TO 'usr_recepcion1'@'localhost';
SET DEFAULT ROLE 'rol_auditor'      TO 'usr_auditor'@'localhost';
SET DEFAULT ROLE 'rol_respaldo'     TO 'usr_respaldo'@'localhost';

-- Esperado: 5 (un rol otorgado por cuenta)
SELECT COUNT(*) AS role_edges FROM mysql.role_edges WHERE TO_USER LIKE 'usr\_%';


-- =====================================================================
--  [2.1] INVENTARIO DE ROLES, PERMISOS Y POLÍTICAS   (conexión: root)
-- =====================================================================
-- Qué rol tiene cada usuario, y cuál queda activo por defecto
SELECT re.TO_USER   AS usuario,
       re.FROM_USER AS rol_otorgado,
       dr.DEFAULT_ROLE_USER AS rol_activo_por_defecto
FROM mysql.role_edges re
LEFT JOIN mysql.default_roles dr
  ON dr.USER = re.TO_USER AND dr.HOST = re.TO_HOST
WHERE re.TO_USER LIKE 'usr\_%'
ORDER BY usuario;

-- Permisos efectivos de un usuario a través de su rol
SHOW GRANTS FOR 'usr_recepcion1'@'localhost' USING 'rol_recepcion';

SHOW GRANTS FOR 'usr_optometrista1'@'localhost' USING 'rol_optometrista';

-- Políticas de contraseña y bloqueo de cada cuenta
SELECT user, host, password_lifetime, password_reuse_history,
       User_attributes->>'$.Password_locking.failed_login_attempts'   AS intentos_fallidos,
       User_attributes->>'$.Password_locking.password_lock_time_days' AS dias_bloqueo,
       account_locked
FROM mysql.user
WHERE user LIKE 'usr\_%'
ORDER BY user;


-- =====================================================================
--  [2.2] RECEPCIÓN: LO PERMITIDO Y LO NEGADO   (conexión: usr_recepcion1)
-- =====================================================================
SELECT CURRENT_USER(), CURRENT_ROLE();

-- OK: tiene EXECUTE sobre el procedimiento
CALL sp_buscar_paciente(BIN_TO_UUID(UNHEX(MD5('opt-01'))), 'Juan');

-- OK: columnas permitidas de usuario
SELECT BIN_TO_UUID(id) AS id, nombre FROM usuario;

-- ERROR ESPERADO 1143: column 'password_hash' denegada
SELECT nombre, password_hash FROM usuario;

-- ERROR ESPERADO 1142: recepción no ve información clínica
SELECT * FROM asiento_clinico;

-- ERROR ESPERADO 1142: no puede borrar pacientes
DELETE FROM paciente WHERE nombre = 'Juan Pérez López';


-- =====================================================================
--  [2.3] OPTOMETRISTA Y AUDITOR   (conexiones: usr_optometrista1, usr_auditor)
-- =====================================================================
-- ---- como usr_optometrista1
-- OK: lee y crea recetas
SELECT COUNT(*) AS recetas FROM receta;

-- ERROR ESPERADO 1142: el historial clínico no se borra
-- (WHERE acotado por si se ejecuta por error con root)
DELETE FROM receta WHERE asiento_id = UNHEX(MD5('asi-01'));

-- ERROR ESPERADO 1142: los datos de contacto son de recepción
UPDATE paciente SET telefono = '0000000000' WHERE id = UNHEX(MD5('pac-01'));

-- ---- como usr_auditor
-- OK: sólo lectura sobre todo el esquema
SELECT COUNT(*) AS asientos FROM asiento_clinico;

-- ERROR ESPERADO 1370: execute command denied (no tiene EXECUTE)
CALL sp_alta_sucursal(BIN_TO_UUID(UNHEX(MD5('opt-01'))), 'Prueba Auditor', 'X', @x);


-- =====================================================================
--  [2.4] GRANT / REVOKE EN VIVO   (root  ↔  usr_auditor)
--  Al cambiar el ROL cambian todos sus usuarios a la vez.
-- =====================================================================
-- root
REVOKE EXECUTE ON PROCEDURE optica_db.sp_buscar_paciente FROM 'rol_auditor';

-- usr_auditor · ERROR ESPERADO 1370 (si no cambia, reconectar)
CALL sp_buscar_paciente(BIN_TO_UUID(UNHEX(MD5('opt-01'))), 'Juan');

-- root · se restituye
GRANT EXECUTE ON PROCEDURE optica_db.sp_buscar_paciente TO 'rol_auditor';

-- usr_auditor · OK de nuevo
CALL sp_buscar_paciente(BIN_TO_UUID(UNHEX(MD5('opt-01'))), 'Juan');


-- =====================================================================
--  [2.5] OPCIONAL · BLOQUEO POR INTENTOS FALLIDOS
--  Cuenta desechable para no bloquear las cuentas reales.
-- =====================================================================
-- root
CREATE USER IF NOT EXISTS 'usr_demo_bloqueo'@'localhost'
  IDENTIFIED BY 'Demo#Bloqueo_2026'
  FAILED_LOGIN_ATTEMPTS 3 PASSWORD_LOCK_TIME 1;

-- TERMINAL · tres intentos con contraseña incorrecta (ERROR 1045)
--   docker exec -it mysql-optica mysql -u usr_demo_bloqueo -pIncorrecta
-- TERMINAL · cuarto intento, contraseña CORRECTA: ERROR ESPERADO 3955
--   "Account is blocked for 1 day(s) ... due to 3 consecutive failed logins"
--   docker exec -it mysql-optica mysql -u usr_demo_bloqueo -p

-- root · desbloqueo administrativo y retiro de la cuenta
ALTER USER 'usr_demo_bloqueo'@'localhost' ACCOUNT UNLOCK;

DROP USER 'usr_demo_bloqueo'@'localhost';


-- #####################################################################
--  TEMA 3 · RESPALDOS Y RESTAURACIÓN (Actividad 5)
-- #####################################################################

-- =====================================================================
--  [3.1] ESTADO PREVIO AL RESPALDO   (conexión: root)
--  Anotar estos números: son la referencia para validar la restauración.
-- =====================================================================
SELECT 'optica' AS tabla, COUNT(*) AS filas FROM optica UNION ALL
SELECT 'rol',              COUNT(*) FROM rol              UNION ALL
SELECT 'sucursal',         COUNT(*) FROM sucursal         UNION ALL
SELECT 'usuario',          COUNT(*) FROM usuario          UNION ALL
SELECT 'usuario_sucursal', COUNT(*) FROM usuario_sucursal UNION ALL
SELECT 'paciente',         COUNT(*) FROM paciente         UNION ALL
SELECT 'expediente',       COUNT(*) FROM expediente       UNION ALL
SELECT 'asiento_clinico',  COUNT(*) FROM asiento_clinico  UNION ALL
SELECT 'receta',           COUNT(*) FROM receta;

-- Esperado: 5
SELECT COUNT(*) AS procedimientos
FROM information_schema.ROUTINES
WHERE ROUTINE_SCHEMA = 'optica_db' AND ROUTINE_TYPE = 'PROCEDURE';

-- La cuenta de respaldo es de sólo lectura (+ SHOW_ROUTINE)
SHOW GRANTS FOR 'usr_respaldo'@'localhost' USING 'rol_respaldo';


-- =====================================================================
--  [3.2] RESPALDO LÓGICO CON mysqldump   (TERMINAL)
--  --result-file en lugar de ">": la redirección de PowerShell 5.1
--  escribe UTF-16 y el archivo ya no se puede restaurar.
-- =====================================================================
--   docker exec -it mysql-optica mysqldump -u usr_respaldo -p `
--     --single-transaction --routines --triggers --events `
--     --hex-blob --default-character-set=utf8mb4 `
--     --databases optica_db --result-file=/tmp/optica_db_respaldo.sql
--
--   Comprobación del contenido. Esperado: 9 y 5
--   docker exec mysql-optica grep -c "CREATE TABLE" /tmp/optica_db_respaldo.sql
--   docker exec mysql-optica grep -c "CREATE.*PROCEDURE" /tmp/optica_db_respaldo.sql
--
--   Copia fuera del servidor (un respaldo dentro del servidor no protege
--   contra la pérdida del servidor)
--   docker cp mysql-optica:/tmp/optica_db_respaldo.sql .


-- =====================================================================
--  [3.3] DESASTRE Y RESTAURACIÓN
-- =====================================================================
-- root · se simula la pérdida total de la base
DROP DATABASE optica_db;

-- Comprobación: ya no existe
SHOW DATABASES LIKE 'optica_db';

-- TERMINAL · restauración con una cuenta administrativa
--   (usr_respaldo es de sólo lectura: no puede crear objetos)
--   docker exec -it mysql-optica sh -c "mysql -uroot -p < /tmp/optica_db_respaldo.sql"
--
--   Cuentas, roles y GRANT no viajan en el volcado: viven en el esquema
--   mysql, que no se borró. Por eso los permisos siguen vigentes.
--   En DBeaver: F5 sobre la conexión para refrescar el navegador.


-- =====================================================================
--  [3.4] VERIFICACIÓN POSTERIOR   (conexión: root)
--  Un respaldo no es válido mientras no se restaure y se verifique.
-- =====================================================================
USE optica_db;

-- Debe coincidir, renglón por renglón, con [3.1]
SELECT 'optica' AS tabla, COUNT(*) AS filas FROM optica UNION ALL
SELECT 'rol',              COUNT(*) FROM rol              UNION ALL
SELECT 'sucursal',         COUNT(*) FROM sucursal         UNION ALL
SELECT 'usuario',          COUNT(*) FROM usuario          UNION ALL
SELECT 'usuario_sucursal', COUNT(*) FROM usuario_sucursal UNION ALL
SELECT 'paciente',         COUNT(*) FROM paciente         UNION ALL
SELECT 'expediente',       COUNT(*) FROM expediente       UNION ALL
SELECT 'asiento_clinico',  COUNT(*) FROM asiento_clinico  UNION ALL
SELECT 'receta',           COUNT(*) FROM receta;

-- Los cinco procedimientos regresaron (gracias a --routines)
SELECT ROUTINE_NAME, SECURITY_TYPE
FROM information_schema.ROUTINES
WHERE ROUTINE_SCHEMA = 'optica_db' AND ROUTINE_TYPE = 'PROCEDURE'
ORDER BY ROUTINE_NAME;

-- Prueba funcional: la base vuelve a escribir de forma transaccional
CALL sp_alta_paciente_con_expediente(
  BIN_TO_UUID(UNHEX(MD5('opt-01'))), 'Verificacion Restauracion',
  '1980-01-01', 'M', '3510000001', 'verificacion@correo.com', NULL,
  @pac_ver, @folio_ver);

SELECT @pac_ver AS paciente_id, @folio_ver AS folio_asignado;


-- =====================================================================
--  [3.5] RESPALDO FÍSICO · SÓLO SE EXPLICA (no ejecutar en vivo)
-- =====================================================================
-- root · qué archivos componen la base (esto sí se puede ejecutar)
SELECT s.NAME AS tablespace, d.PATH AS archivo,
       ROUND(s.FILE_SIZE / 1024 / 1024, 2) AS tamano_mb
FROM information_schema.INNODB_TABLESPACES s
LEFT JOIN information_schema.INNODB_DATAFILES d ON d.SPACE = s.SPACE
WHERE s.NAME LIKE 'optica_db/%'
ORDER BY s.NAME;

-- TERMINAL · copia en frío (detiene el servicio)
--   docker compose stop mysql
--   docker run --rm -v act5_mysql_optica_data:/var/lib/mysql:ro -v "${PWD}:/respaldo" `
--     alpine tar czf /respaldo/optica_db_fisico.tar.gz -C /var/lib/mysql .
--   docker compose start mysql


-- #####################################################################
--  [C.1] LIMPIEZA · deja los datos de muestra como estaban
--  (alternativa: volver a ejecutar [P.1])
-- #####################################################################
USE optica_db;

-- Asientos de los pacientes de prueba (sus recetas caen por CASCADE)
DELETE a FROM asiento_clinico a
  JOIN expediente e ON e.id = a.expediente_id
  JOIN paciente   p ON p.id = e.paciente_id
 WHERE p.nombre IN ('Rosa Medina Alcaraz', 'Verificacion Restauracion');

DELETE e FROM expediente e
  JOIN paciente p ON p.id = e.paciente_id
 WHERE p.nombre IN ('Rosa Medina Alcaraz', 'Verificacion Restauracion');

DELETE FROM paciente
 WHERE nombre IN ('Rosa Medina Alcaraz', 'Verificacion Restauracion');

DELETE FROM sucursal WHERE nombre IN ('Sucursal Poniente', 'Prueba Auditor');

-- Contacto de Juan Pérez como antes de [1.1]
UPDATE paciente
   SET telefono  = '3511234567',
       correo    = 'juan.perez@correo.com',
       direccion = 'Calle Morelos 15, Zamora'
 WHERE id = UNHEX(MD5('pac-01'));

DROP USER IF EXISTS 'usr_demo_bloqueo'@'localhost';

-- Esperado: 6 pacientes, 6 expedientes, 9 asientos, 8 recetas, 1 sin receta
SELECT (SELECT COUNT(*) FROM paciente)        AS pacientes,
       (SELECT COUNT(*) FROM expediente)      AS expedientes,
       (SELECT COUNT(*) FROM asiento_clinico) AS asientos,
       (SELECT COUNT(*) FROM receta)          AS recetas,
       (SELECT COUNT(*) FROM asiento_clinico a
          LEFT JOIN receta r ON r.asiento_id = a.id
         WHERE r.id IS NULL)                  AS asientos_sin_receta;
