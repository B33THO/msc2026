/* ============================================================
   theory.js — contenido de las pantallas de teoría

   Una entrada por nivel, con la misma id que el nivel. Se abre
   automáticamente la primera vez que se entra a cada nivel, y con el
   botón "Teoría" o la tecla T las veces que haga falta.

   Secciones de cada pantalla:
     parrafos  — la explicación en prosa
     diagrama  — figura hecha con CSS (ver tipos abajo)
     codigo    — ejemplo comentado, resaltado con SQLSim.resaltarSQL
     avisos    — errores comunes y trampas

   Tipos de diagrama:
     { tipo:'flujo', conector?:'→'|'·', nodos:[{texto, sub?, clase?}] }
     { tipo:'linea', pasos:[{texto, estado}], ramas?:[{texto, estado, nota}] }
   Estados: neutro | ok | pendiente | error | deshecho | marca
   ============================================================ */

window.SQLSim = window.SQLSim || {};

(function () {
  'use strict';

  SQLSim.teoria = {

    /* ─────────────────────────────────────────── Nivel 1 ── */
    /* Hace de portada: presenta el recorrido completo. */
    terreno: {
      esPortada: true,
      numero: 'Inicio',
      titulo: 'Procedimientos almacenados y transacciones',
      subtitulo: 'MySQL · Bases de Datos',

      parrafos: [
        'Vamos a ver dos ideas que resuelven problemas distintos pero que en la práctica ' +
        'casi siempre aparecen juntas.',

        'Un <strong>procedimiento almacenado</strong> es código SQL con nombre, guardado dentro ' +
        'del servidor. En vez de mandar cinco sentencias desde la aplicación, mandas una sola ' +
        'llamada: <code>CALL RegistrarVenta(1, 2)</code>. El servidor ya sabe qué hacer.',

        'Una <strong>transacción</strong> es una garantía distinta: que un grupo de sentencias ' +
        'ocurra <em>completo o no ocurra</em>. Sin ella, un fallo a la mitad de una operación ' +
        'deja la base de datos en un estado que no debería poder existir.',

        'El recorrido son ocho ejercicios. El más importante es el quinto, donde vamos a ' +
        '<strong>romper la base de datos a propósito</strong> para que se vea el problema antes ' +
        'de conocer la solución. El octavo junta todas las piezas en un caso realista.'
      ],

      diagrama: {
        tipo: 'flujo',
        nodos: [
          { texto: '1 · 2', sub: 'Consultar y crear procedimientos' },
          { texto: '3 · 4', sub: 'Parámetros de entrada y salida' },
          { texto: '5', sub: 'El desastre', clase: 'error' },
          { texto: '6 · 7', sub: 'Transacciones y savepoints', clase: 'ok' },
          { texto: '8', sub: 'Integrador: todo junto', clase: 'marca' }
        ]
      },

      codigo:
        '-- La tienda tiene tres tablas. Vender toca DOS de ellas:\n' +
        'SELECT * FROM Inventario;\n' +
        '\n' +
        '-- Modificar una fila es tan simple como esto.\n' +
        '-- Fíjate en la animación de la celda al cambiar de valor.\n' +
        'UPDATE Inventario SET stock = 10 WHERE producto_id = 5;',

      avisosTitulo: 'Antes de empezar',
      avisos: [
        { titulo: 'Un UPDATE sin WHERE modifica TODAS las filas',
          texto: 'Es el error más caro que existe en SQL. En este simulador puedes reiniciar ' +
                 'la base con la tecla R; en producción no hay tecla R.' },
        { titulo: 'Cada sentencia suelta es definitiva',
          texto: 'Fuera de una transacción, MySQL confirma cada sentencia sola. Recuérdalo, ' +
                 'porque en el nivel 5 esto se vuelve el problema central.' }
      ],

      comoUsar: [
        'Arrastra bloques desde la izquierda al editor, o haz clic en ellos.',
        'Los huecos de color ámbar se rellenan con un clic.',
        'Tecla <kbd>T</kbd> para volver a esta pantalla, <kbd>Espacio</kbd> para ejecutar.'
      ]
    },

    /* ─────────────────────────────────────────── Nivel 2 ── */
    'primer-procedimiento': {
      numero: '2',
      titulo: 'Procedimientos almacenados',

      parrafos: [
        'Un procedimiento almacenado se crea una vez y se queda viviendo en el servidor. ' +
        'A partir de ahí cualquiera puede invocarlo con <code>CALL</code> sin conocer su interior.',

        'Su cuerpo va entre <code>BEGIN</code> y <code>END</code>, y ahí está el problema: ' +
        'ese cuerpo contiene puntos y coma. El cliente de MySQL corta las sentencias en cada ' +
        '<code>;</code>, así que partiría el <code>CREATE PROCEDURE</code> por la mitad.',

        'Por eso se cambia el delimitador antes de empezar. <code>DELIMITER //</code> le dice al ' +
        'cliente: «de aquí en adelante, una sentencia termina cuando veas <code>//</code>, no ' +
        'cuando veas <code>;</code>». Al terminar se restaura con <code>DELIMITER ;</code>.',

        '<code>DELIMITER</code> no es SQL. Es una instrucción para el programa cliente, y el ' +
        'servidor nunca la ve.'
      ],

      diagrama: {
        tipo: 'flujo',
        conector: '·',
        nodos: [
          { texto: 'DELIMITER //', sub: 'cambia el separador', clase: 'marca' },
          { texto: 'CREATE PROCEDURE', sub: 'BEGIN … END' },
          { texto: '//', sub: 'aquí sí termina', clase: 'marca' },
          { texto: 'DELIMITER ;', sub: 'se restaura', clase: 'marca' }
        ]
      },

      codigo:
        '-- 1. Soltarlo si ya existía (MySQL no permite recrearlo encima)\n' +
        'DROP PROCEDURE IF EXISTS VerInventario;\n' +
        '\n' +
        '-- 2. Cambiar el delimitador ANTES del CREATE\n' +
        'DELIMITER //\n' +
        '\n' +
        '-- 3. Los parentesis son obligatorios aunque no haya parametros\n' +
        'CREATE PROCEDURE VerInventario()\n' +
        'BEGIN\n' +
        '    SELECT * FROM Inventario;   -- este ";" es el que causaba el problema\n' +
        'END //\n' +
        '\n' +
        '-- 4. Restaurar el delimitador normal\n' +
        'DELIMITER ;\n' +
        '\n' +
        'CALL VerInventario();',

      avisos: [
        { titulo: 'Olvidar DELIMITER',
          texto: 'Es el error clásico. El <code>CREATE</code> se corta en el primer <code>;</code> ' +
                 'del cuerpo y el servidor recibe un procedimiento incompleto. Pruébalo a ' +
                 'propósito: quita el bloque <code>DELIMITER //</code> y ejecuta.' },
        { titulo: 'Recrear un procedimiento existente falla',
          texto: 'MySQL responde <code>ERROR 1304: PROCEDURE ya existe</code>. No existe ' +
                 '<code>CREATE OR REPLACE PROCEDURE</code> (eso es de MariaDB). Hay que soltarlo ' +
                 'antes con <code>DROP PROCEDURE IF EXISTS</code>.' },
        { titulo: 'Los paréntesis vacíos son obligatorios',
          texto: '<code>CREATE PROCEDURE VerInventario</code> sin <code>()</code> es un error de ' +
                 'sintaxis, aunque no reciba ningún parámetro.' }
      ]
    },

    /* ─────────────────────────────────────────── Nivel 3 ── */
    'parametros-in': {
      numero: '3',
      titulo: 'Parámetros de entrada',

      parrafos: [
        'Un parámetro <code>IN</code> es un valor que entra al procedimiento y se comporta ' +
        'dentro como una variable normal. Es lo que convierte un procedimiento rígido en uno ' +
        'reutilizable: el mismo código sirve para cualquier producto y cualquier cantidad.',

        'Dentro del cuerpo también puedes declarar tus propias variables con ' +
        '<code>DECLARE</code>, y llenarlas leyendo de una tabla con ' +
        '<code>SELECT … INTO</code>.',

        'Fíjate en lo que hace este procedimiento: <strong>modifica dos tablas</strong>. ' +
        'Descuenta el stock en <code>Inventario</code> y registra la venta en ' +
        '<code>Pedidos</code>. Guarda ese detalle, porque es exactamente donde va a estallar ' +
        'todo en el nivel 5.'
      ],

      diagrama: {
        tipo: 'flujo',
        nodos: [
          { texto: 'CALL RegistrarVenta(1, 2)', sub: 'la llamada' },
          { texto: 'p_producto = 1\np_cantidad = 2', sub: 'parámetros IN' },
          { texto: 'Inventario\nPedidos', sub: 'dos tablas modificadas', clase: 'marca' }
        ]
      },

      codigo:
        'CREATE PROCEDURE RegistrarVenta(IN p_producto INT, IN p_cantidad INT)\n' +
        'BEGIN\n' +
        '    -- Los DECLARE van SIEMPRE al principio del bloque\n' +
        '    DECLARE v_total DECIMAL DEFAULT 0;\n' +
        '\n' +
        '    -- SELECT ... INTO guarda el resultado en una variable\n' +
        '    SELECT precio INTO v_total FROM Productos WHERE producto_id = p_producto;\n' +
        '    SET v_total = v_total * p_cantidad;\n' +
        '\n' +
        '    UPDATE Inventario SET stock = stock - p_cantidad   -- tabla 1\n' +
        '        WHERE producto_id = p_producto;\n' +
        '\n' +
        '    INSERT INTO Pedidos (producto_id, cantidad, total, estado)   -- tabla 2\n' +
        '        VALUES (p_producto, p_cantidad, v_total, \'NUEVO\');\n' +
        'END',

      avisos: [
        { titulo: 'Los DECLARE van al principio',
          texto: 'MySQL exige que todos los <code>DECLARE</code> aparezcan al inicio del ' +
                 '<code>BEGIN … END</code>, antes de cualquier otra sentencia. Declarar a media ' +
                 'altura es error de sintaxis.' },
        { titulo: 'No le pongas a un parámetro el nombre de una columna',
          texto: 'Si el parámetro se llamara <code>producto_id</code>, en ' +
                 '<code>WHERE producto_id = producto_id</code> MySQL entendería columna contra ' +
                 'columna: siempre cierto, y actualizarías la tabla entera. Por eso el prefijo ' +
                 '<code>p_</code>.' }
      ]
    },

    /* ─────────────────────────────────────────── Nivel 4 ── */
    'parametro-out': {
      numero: '4',
      titulo: 'Parámetros de salida',

      parrafos: [
        'Un parámetro <code>OUT</code> viaja en sentido contrario: el procedimiento escribe en ' +
        'él y quien lo llamó puede leerlo después.',

        'Para recibirlo hace falta una <strong>variable de sesión</strong>, esas que llevan ' +
        '<code>@</code> delante. No pertenecen al procedimiento sino a tu conexión, así que ' +
        'siguen existiendo cuando el procedimiento ya terminó. Ahí está la diferencia con un ' +
        '<code>SELECT</code> normal: el <code>SELECT</code> muestra algo en pantalla y se acabó; ' +
        'un <code>OUT</code> te deja un valor con el que puedes seguir trabajando.',

        'También existe <code>INOUT</code>, que entra con un valor y sale con otro.'
      ],

      diagrama: {
        tipo: 'flujo',
        nodos: [
          { texto: 'CALL ConsultarStock(3, @resultado)', sub: 'se pasa la variable' },
          { texto: 'SELECT stock INTO p_stock', sub: 'el procedimiento escribe' },
          { texto: '@resultado = 4', sub: 'sobrevive a la llamada', clase: 'ok' }
        ]
      },

      codigo:
        'CREATE PROCEDURE ConsultarStock(IN p_producto INT, OUT p_stock INT)\n' +
        'BEGIN\n' +
        '    -- Escribir en el parametro OUT es como escribir en una variable\n' +
        '    SELECT stock INTO p_stock FROM Inventario WHERE producto_id = p_producto;\n' +
        'END\n' +
        '\n' +
        '-- Al llamarlo hay que darle una variable de sesion, no un valor\n' +
        'CALL ConsultarStock(3, @resultado);\n' +
        '\n' +
        '-- Y el valor sigue disponible aqui\n' +
        'SELECT @resultado;',

      avisos: [
        { titulo: 'Un OUT no acepta un valor literal',
          texto: '<code>CALL ConsultarStock(3, 5)</code> falla: el procedimiento necesita algo ' +
                 'donde escribir. Tiene que ser <code>@algo</code>.' },
        { titulo: 'Un OUT entra siempre como NULL',
          texto: 'Aunque la variable ya tuviera un valor, dentro del procedimiento el parámetro ' +
                 '<code>OUT</code> empieza en <code>NULL</code>. Si necesitas leer y escribir, ' +
                 'usa <code>INOUT</code>.' }
      ]
    },

    /* ─────────────────────────────────────────── Nivel 5 ── */
    desastre: {
      numero: '5',
      titulo: 'El problema: una venta a medias',
      destacado: true,

      parrafos: [
        'Este es el nivel importante. Vamos a intentar vender <strong>50 webcams cuando solo ' +
        'hay 2</strong>, con un procedimiento que descuenta primero y valida después.',

        'Cuando la validación falla, el descuento <em>ya ocurrió</em>. Y nadie lo deshace. ' +
        'La base queda con stock en <code>-48</code> y ningún pedido que lo justifique: un ' +
        'estado que las reglas del negocio dicen que no puede existir, y sin embargo ahí está.',

        'La causa es el <strong>autocommit</strong>. Fuera de una transacción, MySQL confirma ' +
        'cada sentencia por separado en cuanto la ejecuta. Para cuando el <code>IF</code> se da ' +
        'cuenta del problema, el <code>UPDATE</code> ya es historia. No hay nada pendiente que ' +
        'cancelar.',

        'Ejecuta y observa el panel de la derecha antes de seguir al nivel 6.'
      ],

      diagrama: {
        tipo: 'linea',
        pasos: [
          { texto: 'UPDATE stock', estado: 'ok', nota: 'confirmado al instante' },
          { texto: 'stock = -48', estado: 'error', nota: 'nadie lo revisó antes' },
          { texto: 'IF stock >= 0', estado: 'error', nota: 'falla' },
          { texto: 'INSERT pedido', estado: 'deshecho', nota: 'nunca ocurre' }
        ],
        pie: 'Resultado: stock descontado + ningún pedido = base inconsistente'
      },

      codigo:
        'CREATE PROCEDURE VentaRiesgosa(IN p_producto INT, IN p_cantidad INT)\n' +
        'BEGIN\n' +
        '    DECLARE v_stock INT DEFAULT 0;\n' +
        '\n' +
        '    -- Esto se confirma SOLO, en este mismo instante. Ya no hay marcha atras.\n' +
        '    UPDATE Inventario SET stock = stock - p_cantidad\n' +
        '        WHERE producto_id = p_producto;\n' +
        '\n' +
        '    SELECT stock INTO v_stock FROM Inventario WHERE producto_id = p_producto;\n' +
        '\n' +
        '    -- Llegamos tarde: la validacion descubre el problema, pero no puede repararlo\n' +
        '    IF v_stock >= 0 THEN\n' +
        '        INSERT INTO Pedidos (producto_id, cantidad, total, estado)\n' +
        '            VALUES (p_producto, p_cantidad, 0, \'NUEVO\');\n' +
        '    END IF;\n' +
        'END',

      avisos: [
        { titulo: 'Un IF no protege nada',
          texto: 'Validar antes de modificar ayuda, pero no basta: entre la validación y la ' +
                 'modificación puede fallar la conexión, el disco, o la propia sentencia. Lo que ' +
                 'hace falta es poder <em>deshacer</em>.' },
        { titulo: 'Aquí un ROLLBACK no sirve de nada',
          texto: 'Pruébalo: agrega <code>ROLLBACK;</code> al final. El simulador te dirá que no ' +
                 'hay nada que revertir, porque sin <code>START TRANSACTION</code> no había nada ' +
                 'pendiente.' }
      ]
    },

    /* ─────────────────────────────────────────── Nivel 6 ── */
    transaccion: {
      numero: '6',
      titulo: 'La solución: transacciones',

      parrafos: [
        'Una transacción agrupa varias sentencias en una sola unidad que ocurre completa o no ' +
        'ocurre. Eso es la <strong>atomicidad</strong>.',

        '<code>START TRANSACTION</code> apaga el autocommit: a partir de ahí los cambios quedan ' +
        '<em>pendientes</em>. Tú los ves, pero todavía no son definitivos. Al final decides: ' +
        '<code>COMMIT</code> los vuelve permanentes, <code>ROLLBACK</code> los borra como si ' +
        'nunca hubieran pasado.',

        'Es exactamente el mismo procedimiento del nivel 5, con tres líneas más. La diferencia ' +
        'es que ahora el <code>IF</code> llega a tiempo, porque nada se confirmó todavía.',

        'Cuando ejecutes, baja la velocidad a 1x: el <code>ROLLBACK</code> se anima deshaciendo ' +
        'los cambios uno por uno, en orden inverso. Así es como funciona de verdad por dentro.'
      ],

      diagrama: {
        tipo: 'linea',
        pasos: [
          { texto: 'START TRANSACTION', estado: 'marca', nota: 'autocommit apagado' },
          { texto: 'UPDATE stock', estado: 'pendiente', nota: 'pendiente' },
          { texto: 'INSERT pedido', estado: 'pendiente', nota: 'pendiente' },
          { texto: 'IF v_stock < 0', estado: 'neutro', nota: 'ahora sí llega a tiempo' }
        ],
        ramas: [
          { texto: 'ROLLBACK', estado: 'error', nota: 'todo se deshace, la base queda intacta' },
          { texto: 'COMMIT', estado: 'ok', nota: 'todo se confirma junto' }
        ],
        pie: 'O las dos tablas cambian, o no cambia ninguna. Nunca a medias.'
      },

      codigo:
        'CREATE PROCEDURE VentaSegura(IN p_producto INT, IN p_cantidad INT)\n' +
        'BEGIN\n' +
        '    DECLARE v_stock INT DEFAULT 0;\n' +
        '\n' +
        '    START TRANSACTION;          -- a partir de aqui, nada es definitivo\n' +
        '\n' +
        '    UPDATE Inventario SET stock = stock - p_cantidad\n' +
        '        WHERE producto_id = p_producto;\n' +
        '    INSERT INTO Pedidos (producto_id, cantidad, total, estado)\n' +
        '        VALUES (p_producto, p_cantidad, 0, \'NUEVO\');\n' +
        '\n' +
        '    SELECT stock INTO v_stock FROM Inventario WHERE producto_id = p_producto;\n' +
        '\n' +
        '    IF v_stock < 0 THEN\n' +
        '        ROLLBACK;               -- deshace el UPDATE Y el INSERT, juntos\n' +
        '    ELSE\n' +
        '        COMMIT;                 -- confirma los dos, juntos\n' +
        '    END IF;\n' +
        'END',

      avisos: [
        { titulo: 'Si olvidas el COMMIT, no guardaste nada',
          texto: 'Los cambios se quedan pendientes y desaparecen al cerrar la conexión. El ' +
                 'simulador te avisa cuando un script termina con una transacción abierta.' },
        { titulo: 'ROLLBACK fuera de una transacción no hace nada',
          texto: 'No da error: simplemente no hay nada que revertir. Es lo que viste en el nivel 5.' },
        { titulo: 'Las sentencias DDL confirman sin avisar',
          texto: 'En MySQL, un <code>CREATE</code>, <code>DROP</code> o <code>ALTER</code> dentro ' +
                 'de una transacción provoca un <em>commit implícito</em> de todo lo pendiente. ' +
                 'No los mezcles con transacciones.' }
      ]
    },

    /* ─────────────────────────────────────────── Nivel 7 ── */
    savepoint: {
      numero: '7',
      titulo: 'SAVEPOINT: deshacer solo una parte',

      parrafos: [
        'A veces tirar toda la transacción es demasiado. Un pedido de cinco líneas donde falla ' +
        'la tercera no debería obligarte a repetir las otras cuatro.',

        'Un <code>SAVEPOINT</code> es una marca dentro de la transacción. ' +
        '<code>ROLLBACK TO SAVEPOINT</code> deshace <strong>únicamente lo ocurrido después de ' +
        'la marca</strong>, y lo anterior sigue vivo, todavía pendiente.',

        'Ojo con esto: <code>ROLLBACK TO SAVEPOINT</code> <em>no cierra la transacción</em>. ' +
        'Te deja dentro, y al final sigues necesitando un <code>COMMIT</code> para que lo que ' +
        'sobrevivió se guarde de verdad.'
      ],

      diagrama: {
        tipo: 'linea',
        pasos: [
          { texto: 'línea válida', estado: 'pendiente', nota: 'producto 1' },
          { texto: 'SAVEPOINT linea1', estado: 'marca', nota: 'la marca' },
          { texto: 'línea imposible', estado: 'error', nota: 'producto 5' },
          { texto: 'ROLLBACK TO linea1', estado: 'deshecho', nota: 'borra solo lo de la derecha' },
          { texto: 'COMMIT', estado: 'ok', nota: 'guarda lo que sobrevivió' }
        ],
        pie: 'Un ROLLBACK a secas habría borrado también la línea válida.'
      },

      codigo:
        'START TRANSACTION;\n' +
        '\n' +
        '-- Primera linea del pedido: valida\n' +
        'UPDATE Inventario SET stock = stock - 2 WHERE producto_id = 1;\n' +
        'INSERT INTO Pedidos (producto_id, cantidad, total, estado)\n' +
        '    VALUES (1, 2, 2500, \'NUEVO\');\n' +
        '\n' +
        'SAVEPOINT linea1;           -- marca: hasta aqui todo bien\n' +
        '\n' +
        '-- Segunda linea: no hay stock suficiente\n' +
        'UPDATE Inventario SET stock = stock - 50 WHERE producto_id = 5;\n' +
        'INSERT INTO Pedidos (producto_id, cantidad, total, estado)\n' +
        '    VALUES (5, 50, 55000, \'NUEVO\');\n' +
        '\n' +
        'ROLLBACK TO SAVEPOINT linea1;   -- descarta SOLO la segunda linea\n' +
        'COMMIT;                          -- y confirma la primera',

      avisos: [
        { titulo: 'El COMMIT final sigue haciendo falta',
          texto: 'Volver a un savepoint no termina la transacción. Sin <code>COMMIT</code>, ' +
                 'también se pierde lo que habías salvado.' },
        { titulo: 'Un COMMIT borra todos los savepoints',
          texto: 'Al confirmar o revertir la transacción completa, las marcas desaparecen. Solo ' +
                 'existen mientras la transacción está abierta.' }
      ]
    },

    /* ─────────────────────────────────────────── Nivel 8 ── */
    integrador: {
      numero: '8',
      titulo: 'Integrador: una venta completa',
      destacado: true,

      parrafos: [
        'Este último nivel no enseña nada nuevo: junta todo lo que ya sabes en un solo ' +
        'procedimiento, que es más parecido a como se ve el código en la vida real.',

        '<code>VentaFinal</code> recibe el pedido por parámetros <code>IN</code>, calcula el total ' +
        'consultando <code>Productos</code>, y usa un parámetro <code>OUT</code> para avisar si la ' +
        'venta se pudo completar o no.',

        'La diferencia con el nivel 5 es el orden: aquí el stock se revisa <strong>antes</strong> ' +
        'de tocar la tabla, y todo pasa dentro de una transacción. Si alcanza, se descuenta el ' +
        'stock, se registra el pedido y se hace <code>COMMIT</code>. Si no alcanza, no se modifica ' +
        'nada y se hace <code>ROLLBACK</code>.',

        'Ejecuta el procedimiento dos veces seguidas —una venta que sí alcanza y otra que no— y ' +
        'compara <code>@estado1</code> con <code>@estado2</code> al final.'
      ],

      diagrama: {
        tipo: 'flujo',
        nodos: [
          { texto: 'IN: producto, cantidad', sub: 'parametros de entrada' },
          { texto: 'START TRANSACTION', sub: 'nada es definitivo todavia', clase: 'marca' },
          { texto: 'stock >= cantidad ?', sub: 'se revisa ANTES de modificar' },
          { texto: 'COMMIT / ROLLBACK', sub: 'segun la validacion', clase: 'ok' },
          { texto: 'OUT: p_estado', sub: "'COMPLETADO' o 'RECHAZADO'" }
        ]
      },

      codigo:
        'CREATE PROCEDURE VentaFinal(IN p_producto INT, IN p_cantidad INT, OUT p_estado VARCHAR(40))\n' +
        'BEGIN\n' +
        '    DECLARE v_total DECIMAL DEFAULT 0;\n' +
        '    DECLARE v_stock INT DEFAULT 0;\n' +
        '\n' +
        '    START TRANSACTION;\n' +
        '\n' +
        '    SELECT precio INTO v_total FROM Productos WHERE producto_id = p_producto;\n' +
        '    SET v_total = v_total * p_cantidad;\n' +
        '\n' +
        '    -- Esta vez la validacion va ANTES de modificar nada\n' +
        '    SELECT stock INTO v_stock FROM Inventario WHERE producto_id = p_producto;\n' +
        '\n' +
        '    IF v_stock >= p_cantidad THEN\n' +
        '        UPDATE Inventario SET stock = stock - p_cantidad WHERE producto_id = p_producto;\n' +
        '        INSERT INTO Pedidos (producto_id, cantidad, total, estado)\n' +
        '            VALUES (p_producto, p_cantidad, v_total, \'NUEVO\');\n' +
        '        SET p_estado = \'COMPLETADO\';\n' +
        '        COMMIT;\n' +
        '    ELSE\n' +
        '        SET p_estado = \'RECHAZADO\';\n' +
        '        ROLLBACK;\n' +
        '    END IF;\n' +
        'END\n' +
        '\n' +
        'CALL VentaFinal(1, 2, @estado1);\n' +
        'CALL VentaFinal(5, 50, @estado2);\n' +
        '\n' +
        'SELECT @estado1;\n' +
        'SELECT @estado2;',

      avisos: [
        { titulo: 'Validar antes no es un detalle, es el punto',
          texto: 'Compáralo con el nivel 5: ahí se descontaba primero y se revisaba después. Aquí ' +
                 'la transacción permite revisar primero sin ningún riesgo, porque nada se confirma ' +
                 'hasta el <code>COMMIT</code>.' },
        { titulo: 'El OUT no reemplaza al COMMIT/ROLLBACK',
          texto: '<code>p_estado</code> es solo un mensaje para quien llamó al procedimiento. Sin el ' +
                 '<code>COMMIT</code> o el <code>ROLLBACK</code> correspondiente, la transacción se ' +
                 'quedaría abierta sin importar lo que diga la variable.' }
      ]
    },

    /* ─────────────────────────────────────── Sandbox ── */
    sandbox: {
      numero: '∞',
      titulo: 'Sandbox libre',

      parrafos: [
        'Todos los bloques disponibles, sin objetivos ni validación. Es el sitio para probar ' +
        'las preguntas que salgan durante la exposición.',

        'Recuerda que la tecla <kbd>R</kbd> reinicia la base de datos en cualquier momento.'
      ],

      avisosTitulo: 'Cosas que vale la pena probar',
      avisos: [
        { titulo: '¿Qué pasa si olvidas el COMMIT?',
          texto: 'Abre una transacción, modifica algo y termina el script sin confirmar. Mira el ' +
                 'aviso de la consola y la insignia de transacción abierta.' },
        { titulo: '¿Y si haces ROLLBACK sin transacción?',
          texto: 'No da error, no hace nada. Es la lección del nivel 5 en una sola línea.' },
        { titulo: '¿Savepoints anidados?',
          texto: 'Pon dos marcas y vuelve a la primera. Verás que la segunda deja de existir.' },
        { titulo: '¿Recrear un procedimiento sin soltarlo?',
          texto: 'Ejecuta dos veces un CREATE PROCEDURE sin el DROP delante y aparecerá el ' +
                 'error 1304 de MySQL.' }
      ]
    }

  };

})();
