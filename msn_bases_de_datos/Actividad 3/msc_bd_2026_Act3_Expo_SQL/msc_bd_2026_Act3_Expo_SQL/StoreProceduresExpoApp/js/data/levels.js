/* ============================================================
   levels.js — los 7 niveles guiados y el sandbox

   Cada nivel valida su objetivo mirando DOS cosas:
     · el estado final de la base
     · los eventos que ocurrieron durante la ejecución
   Lo segundo evita aprobar por accidente: en el nivel 6, dejar el
   inventario intacto no basta, tiene que haber ocurrido un ROLLBACK.
   ============================================================ */

window.SQLSim = window.SQLSim || {};

(function () {
  'use strict';

  /* ── Ayudas para escribir objetivos ──────────────────────── */

  function stock(db, id) {
    var f = db.tablas.Inventario.filter(function (r) { return r.producto_id === id; })[0];
    return f ? f.stock : null;
  }
  function pedidos(db) { return db.tablas.Pedidos; }
  function hubo(eventos, tipo) {
    return eventos.some(function (e) { return e.tipo === tipo; });
  }
  function bien(mensaje) { return { ok: true, mensaje: mensaje }; }
  function mal(mensaje)  { return { ok: false, mensaje: mensaje }; }

  /* ── Niveles ─────────────────────────────────────────────── */

  var niveles = [

    /* ───────────────────────────────── 1 ── */
    {
      id: 'terreno',
      titulo: '1. Reconocer el terreno',
      reto: 'La tienda recibio 8 <strong>Webcam HD</strong> (producto 5), que estaba en 2 piezas. ' +
            'Deja su <code>stock</code> en <strong>10</strong> y comprueba el resultado.',
      explicacion: 'Antes de complicarnos: una consulta y una modificacion sueltas. ' +
                   'Fijate en la animacion de la celda al cambiar de valor.',
      bloques: ['select-todo', 'select-where', 'update-igual'],
      guionInicial: [],
      pistas: [
        'Arrastra un UPDATE y elige la tabla Inventario.',
        'La condicion debe ser producto_id = 5, y el nuevo stock es 10.',
        'Solucion: UPDATE Inventario SET stock = 10 WHERE producto_id = 5;'
      ],
      objetivo: function (ctx) {
        if (!hubo(ctx.eventos, 'row-update')) return mal('Todavia no modificaste ninguna fila.');
        var s = stock(ctx.db, 5);
        if (s !== 10) return mal('El stock del producto 5 quedo en ' + s + ', y deberia ser 10.');
        return bien('Correcto. Modificaste una fila y viste el cambio animado en la tabla.');
      }
    },

    /* ───────────────────────────────── 2 ── */
    {
      id: 'primer-procedimiento',
      titulo: '2. Tu primer procedimiento',
      reto: 'Crea un procedimiento llamado <code>VerInventario</code> que consulte toda la tabla ' +
            '<code>Inventario</code>, y despues llamalo con <code>CALL</code>.',
      explicacion: 'El cuerpo de un procedimiento lleva varios ";" dentro. Si no cambiaramos el ' +
                   'delimitador, el cliente cortaria la sentencia en el primer ";" y el CREATE ' +
                   'quedaria incompleto. Por eso se abre con DELIMITER // y se restaura al final. ' +
                   'Si ejecutas dos veces veras el otro detalle: MySQL no deja recrear un ' +
                   'procedimiento existente, hay que soltarlo antes con DROP PROCEDURE IF EXISTS.',
      bloques: ['drop-proc', 'delim-abrir', 'proc-0', 'begin', 'select-todo',
                'end-delim', 'delim-cerrar', 'call-0'],
      guionInicial: [],
      pistas: [
        'El orden es: DELIMITER //, CREATE PROCEDURE, BEGIN, tu consulta, END //, DELIMITER ; y por ultimo el CALL.',
        'Usa el mismo nombre en el CREATE PROCEDURE y en el CALL.',
        'Si olvidas DELIMITER //, el motor te lo va a reclamar: pruebalo, vale la pena verlo.',
        'Si al ejecutar de nuevo falla con "ya existe", pon DROP PROCEDURE IF EXISTS al principio: ' +
        'MySQL no tiene CREATE OR REPLACE para procedimientos.'
      ],
      objetivo: function (ctx) {
        var creado = ctx.eventos.some(function (e) {
          return e.tipo === 'log' && /creado correctamente/.test(e.texto);
        });
        var llamado = ctx.eventos.some(function (e) {
          return e.tipo === 'log' && /ejecutado/.test(e.texto);
        });
        if (!creado)  return mal('Todavia no se creo ningun procedimiento.');
        if (!llamado) return mal('El procedimiento existe, pero falta llamarlo con CALL.');
        if (!hubo(ctx.eventos, 'resultado')) return mal('El procedimiento no devolvio ninguna consulta.');
        return bien('Procedimiento creado y ejecutado. Ese es el ciclo completo: DELIMITER, CREATE, CALL.');
      }
    },

    /* ───────────────────────────────── 3 ── */
    {
      id: 'parametros-in',
      titulo: '3. Parametros de entrada',
      reto: 'Construye <code>RegistrarVenta(IN p_producto INT, IN p_cantidad INT)</code>: debe ' +
            '<strong>calcular el total</strong>, <strong>descontar el stock</strong> y ' +
            '<strong>registrar el pedido</strong>. Luego vende 2 unidades del producto 1.',
      explicacion: 'Los parametros IN entran como variables locales. Fijate que una sola llamada ' +
                   'toca DOS tablas: ahi empieza el problema que resolveremos con transacciones.',
      bloques: ['drop-proc', 'delim-abrir', 'proc-2in', 'begin', 'declare', 'select-into',
                'set-local', 'update-menos', 'insert-pedido', 'end-delim', 'delim-cerrar',
                'call-2', 'select-todo'],
      guionInicial: [],
      pistas: [
        'Empieza por el envoltorio, igual que en el nivel 2: DROP PROCEDURE IF EXISTS RegistrarVenta; ' +
        'DELIMITER //, CREATE PROCEDURE con los dos parametros IN, BEGIN ... END //, DELIMITER ; y el CALL.',
        'Dentro del BEGIN, el DECLARE va siempre primero: DECLARE v_total DECIMAL DEFAULT 0;',
        'Para el precio: SELECT precio INTO v_total FROM Productos WHERE producto_id = p_producto; ' +
        'y despues SET v_total = v_total * p_cantidad;',
        'Para descontar: UPDATE Inventario SET stock = stock - p_cantidad WHERE producto_id = p_producto;',
        'Para registrar: INSERT INTO Pedidos ... VALUES (p_producto, p_cantidad, v_total, \'NUEVO\');',
        'La llamada final es CALL RegistrarVenta(1, 2);'
      ],
      objetivo: function (ctx) {
        if (stock(ctx.db, 1) !== 8) {
          return mal('El stock del producto 1 quedo en ' + stock(ctx.db, 1) + '; deberia bajar de 10 a 8.');
        }
        var nuevos = pedidos(ctx.db).filter(function (p) { return p.producto_id === 1; });
        if (!nuevos.length) return mal('Se descontó el stock pero no se registro el pedido.');
        var p = nuevos[nuevos.length - 1];
        if (p.cantidad !== 2) return mal('El pedido quedo con cantidad ' + p.cantidad + ' en vez de 2.');
        if (Math.abs(p.total - 2500) > 0.01) {
          return mal('El total del pedido es ' + p.total + '; con precio 1250 y 2 piezas deberia ser 2500.');
        }
        return bien('Una llamada, dos tablas modificadas. Recuerda esto para el nivel 5.');
      }
    },

    /* ───────────────────────────────── 4 ── */
    {
      id: 'parametro-out',
      titulo: '4. Parametros de salida',
      reto: 'Construye <code>ConsultarStock(IN p_producto INT, OUT p_stock INT)</code> para que ' +
            'devuelva el stock en su parametro <code>OUT</code>; llamalo con el producto 3 guardando ' +
            'el resultado en <code>@resultado</code>, y despues <strong>consulta esa variable</strong> ' +
            'para ver su valor.',
      explicacion: 'Un parametro OUT no devuelve un resultado en pantalla: escribe en una variable ' +
                   'de sesion del cliente, que sigue disponible despues de que el procedimiento termina. ' +
                   'Por eso el ultimo paso es un SELECT normal sobre esa variable.',
      bloques: ['drop-proc', 'delim-abrir', 'proc-in-out', 'begin', 'select-into', 'set-local',
                'end-delim', 'delim-cerrar', 'call-out', 'select-var'],
      guionInicial: [],
      pistas: [
        'El envoltorio es el de siempre, pero ahora con el bloque CREATE PROCEDURE que lleva IN y OUT.',
        'Dentro del BEGIN...END basta una sola linea.',
        'Un SELECT ... INTO puede escribir directamente sobre el parametro p_stock.',
        'Cuerpo: SELECT stock INTO p_stock FROM Inventario WHERE producto_id = p_producto;',
        'La llamada: CALL ConsultarStock(3, @resultado); — el segundo argumento tiene que ser una variable.',
        'Para ver lo que quedo guardado, agrega al final: SELECT @resultado;'
      ],
      objetivo: function (ctx) {
        var v = ctx.db.variablesSesion['@resultado'];
        if (v === undefined || v === null) {
          return mal('@resultado sigue vacia: el parametro OUT no recibio ningun valor.');
        }
        if (Number(v) !== 4) {
          return mal('@resultado vale ' + v + '; el stock del producto 3 es 4.');
        }
        if (!hubo(ctx.eventos, 'resultado')) {
          return mal('El valor ya esta en @resultado, pero todavia no lo consultas: agrega SELECT @resultado;');
        }
        return bien('El valor sobrevivio al final del procedimiento dentro de @resultado, y lo confirmaste con un SELECT.');
      }
    },

    /* ───────────────────────────────── 5 ── */
    {
      id: 'desastre',
      titulo: '5. El desastre: una venta a medias',
      reto: 'Construye <code>VentaRiesgosa</code>, que <strong>descuenta primero y valida despues</strong>, ' +
            'e intenta vender <strong>50 Webcam HD</strong> (producto 5), que solo tiene 2 en stock. ' +
            'Ejecuta y observa como queda la base de datos.',
      explicacion: 'El procedimiento descuenta primero y valida despues. Cuando la validacion falla, ' +
                   'el descuento YA ocurrio y nadie lo deshace: hay stock negativo y ningun pedido que ' +
                   'lo justifique. Fuera de una transaccion rige autocommit y cada sentencia es definitiva.',
      bloques: ['drop-proc', 'delim-abrir', 'proc-2in', 'begin', 'declare', 'update-menos',
                'select-into', 'if-then', 'insert-pedido', 'end-if', 'end-delim', 'delim-cerrar',
                'call-2'],
      guionInicial: [],
      pistas: [
        'Mismo envoltorio del nivel 3, pero llamalo VentaRiesgosa y dentro declara DECLARE v_stock INT DEFAULT 0;',
        'El orden es a proposito el equivocado: primero UPDATE Inventario SET stock = stock - p_cantidad ' +
        'WHERE producto_id = p_producto; y despues SELECT stock INTO v_stock ... para revisar como quedo.',
        'La validacion va al final: IF v_stock >= 0 THEN, dentro el INSERT INTO Pedidos, y END IF;',
        'Llama con CALL VentaRiesgosa(5, 50); y compara el stock del producto 5 con la tabla Pedidos.',
        'El stock queda en -48 y no hay pedido: eso es un estado inconsistente.'
      ],
      inconsistencia: function (db) {
        var malo = db.tablas.Inventario.some(function (r) { return r.stock < 0; });
        return malo ? ['Inventario', 'Pedidos'] : [];
      },
      objetivo: function (ctx) {
        var s = stock(ctx.db, 5);
        if (s === null || s >= 0) {
          return mal('Todavia no se produce el desastre: ejecuta la venta de 50 unidades del producto 5.');
        }
        var hayPedido = pedidos(ctx.db).some(function (p) { return p.producto_id === 5; });
        if (hayPedido) return mal('Se registro un pedido; para este nivel la validacion debe impedirlo.');
        return bien('Ahi esta el problema: stock en ' + s + ' y ningun pedido que lo explique. ' +
                    'La base quedo en un estado que no deberia poder existir.');
      }
    },

    /* ───────────────────────────────── 6 ── */
    {
      id: 'transaccion',
      titulo: '6. La solucion: la transaccion',
      reto: 'Construye <code>VentaSegura</code>: la misma venta imposible, pero envuelta en una ' +
            'transaccion. Si el stock queda negativo, <code>ROLLBACK</code>; si no, <code>COMMIT</code>.',
      explicacion: 'Con START TRANSACTION los cambios quedan pendientes. ROLLBACK los deshace uno por ' +
                   'uno en orden inverso, que es exactamente lo que veras animado. La operacion pasa a ' +
                   'ser atomica: ocurre completa o no ocurre.',
      bloques: ['drop-proc', 'delim-abrir', 'proc-2in', 'begin', 'declare', 'start-tx',
                'update-menos', 'insert-pedido', 'select-into', 'if-then', 'rollback', 'else',
                'commit', 'end-if', 'end-delim', 'delim-cerrar', 'call-2'],
      guionInicial: [],
      pistas: [
        'Parte del mismo esqueleto del nivel 5, pero con el nombre VentaSegura.',
        'Necesitas START TRANSACTION justo despues del DECLARE, antes de tocar las tablas.',
        'Dentro de la transaccion van el UPDATE que descuenta, el INSERT del pedido y el SELECT INTO ' +
        'que lee como quedo el stock.',
        'Al final, un IF v_stock < 0 THEN ... ELSE ... END IF con ROLLBACK y COMMIT en cada rama.',
        'Orden completo del cuerpo: DECLARE, START TRANSACTION, UPDATE, INSERT, SELECT INTO, ' +
        'IF v_stock < 0 THEN ROLLBACK; ELSE COMMIT; END IF;',
        'Y la llamada: CALL VentaSegura(5, 50);'
      ],
      objetivo: function (ctx) {
        if (!hubo(ctx.eventos, 'tx-begin')) {
          return mal('No se abrio ninguna transaccion: falta START TRANSACTION.');
        }
        if (!hubo(ctx.eventos, 'tx-rollback')) {
          return mal('La venta era imposible y aun asi no hubo ROLLBACK. Revisa la condicion del IF.');
        }
        if (stock(ctx.db, 5) !== 2) {
          return mal('El stock del producto 5 quedo en ' + stock(ctx.db, 5) +
                     '; tras el ROLLBACK deberia volver a 2.');
        }
        if (pedidos(ctx.db).some(function (p) { return p.producto_id === 5; })) {
          return mal('Quedo un pedido del producto 5: el ROLLBACK no deshizo el INSERT.');
        }
        return bien('Atomico: el UPDATE y el INSERT se deshicieron juntos y la base quedo intacta. ' +
                    'Compara con lo que paso en el nivel 5.');
      }
    },

    /* ───────────────────────────────── 7 ── */
    {
      id: 'savepoint',
      titulo: '7. SAVEPOINT: deshacer solo una parte',
      reto: 'Un pedido de dos lineas: la primera (producto 1) es valida, la segunda (producto 5) ' +
            'no alcanza. Conserva la primera y descarta solo la segunda.',
      explicacion: 'ROLLBACK sin mas deshace TODA la transaccion. ROLLBACK TO SAVEPOINT deshace ' +
                   'solamente lo ocurrido despues de la marca, y lo anterior sigue vivo esperando el COMMIT.',
      bloques: ['start-tx', 'update-menos', 'insert-pedido', 'savepoint', 'rollback-sp',
                'commit', 'rollback', 'select-todo'],
      guionInicial: [],
      pistas: [
        'Aqui no hace falta procedimiento: son sentencias sueltas dentro de una transaccion.',
        'Cada linea del pedido son dos bloques: el UPDATE que descuenta y el INSERT que registra. ' +
        'La primera es UPDATE ... - 2 WHERE producto_id = 1 e INSERT (1, 2, 2500, \'NUEVO\').',
        'Coloca un SAVEPOINT entre la primera linea del pedido y la segunda.',
        'La segunda linea es UPDATE ... - 50 WHERE producto_id = 5 e INSERT (5, 50, 55000, \'NUEVO\').',
        'Al final, ROLLBACK TO SAVEPOINT con el mismo nombre, y luego COMMIT.',
        'Orden: START TRANSACTION, UPDATE p1, INSERT p1, SAVEPOINT linea1, UPDATE p5, INSERT p5, ROLLBACK TO SAVEPOINT linea1, COMMIT;'
      ],
      objetivo: function (ctx) {
        var conSp = ctx.eventos.some(function (e) { return e.tipo === 'tx-rollback' && e.savepoint; });
        if (!conSp) return mal('Falta un ROLLBACK TO SAVEPOINT. Un ROLLBACK a secas borraria todo.');
        if (stock(ctx.db, 1) !== 8) {
          return mal('El producto 1 quedo en ' + stock(ctx.db, 1) +
                     '; su linea era valida y deberia conservarse en 8.');
        }
        if (stock(ctx.db, 5) !== 2) {
          return mal('El producto 5 quedo en ' + stock(ctx.db, 5) + '; su linea debia descartarse (2).');
        }
        var p1 = pedidos(ctx.db).some(function (p) { return p.producto_id === 1; });
        var p5 = pedidos(ctx.db).some(function (p) { return p.producto_id === 5; });
        if (!p1) return mal('Se perdio tambien el pedido valido del producto 1.');
        if (p5)  return mal('Quedo el pedido del producto 5, que debia descartarse.');
        if (ctx.db.enTransaccion) {
          return mal('Todo bien, pero la transaccion sigue abierta: falta el COMMIT final.');
        }
        return bien('Rollback parcial: se descarto solo lo posterior al savepoint y lo valido sobrevivio al COMMIT.');
      }
    },

    /* ───────────────────────────────── 8 ── */
    {
      id: 'integrador',
      titulo: '8. Integrador: una venta con reporte de estado',
      reto: 'Cierra el recorrido con <code>VentaFinal(IN p_producto INT, IN p_cantidad INT, ' +
            'OUT p_estado VARCHAR(40))</code>: calcula el total desde <code>Productos</code>, ' +
            'revisa el stock <strong>antes</strong> de tocarlo y, solo si alcanza, descuenta el ' +
            'stock, registra el pedido y confirma; si no alcanza, no modifiques nada y revierte. ' +
            'En cualquier caso deja el resultado en <code>p_estado</code> (<code>\'COMPLETADO\'</code> ' +
            'o <code>\'RECHAZADO\'</code>). Pruebalo dos veces: vende 2 <strong>Teclado mecanico</strong> ' +
            '(producto 1) y despues intenta vender 50 <strong>Webcam HD</strong> (producto 5).',
      explicacion: 'Aqui se juntan las piezas de todo el recorrido: parametros IN y OUT (niveles 3 y 4), ' +
                   'una transaccion completa con COMMIT y ROLLBACK (nivel 6), y la leccion del nivel 5 ' +
                   'aplicada correctamente: esta vez la validacion va antes de modificar nada.',
      bloques: ['drop-proc', 'delim-abrir', 'proc-2in-out', 'begin', 'declare', 'start-tx',
                'select-into', 'set-local', 'if-then', 'update-menos', 'insert-pedido', 'else',
                'rollback', 'commit', 'end-if', 'end-delim', 'delim-cerrar', 'call-2out', 'select-var'],
      guionInicial: [],
      pistas: [
        'El envoltorio de siempre: DROP PROCEDURE IF EXISTS, DELIMITER //, CREATE PROCEDURE con ' +
        'dos IN y un OUT, BEGIN ... END //, DELIMITER ;.',
        'Declara dos variables: DECLARE v_total DECIMAL DEFAULT 0; y DECLARE v_stock INT DEFAULT 0;',
        'Abre la transaccion antes de tocar ninguna tabla: START TRANSACTION;',
        'Calcula el total: SELECT precio INTO v_total FROM Productos WHERE producto_id = p_producto; ' +
        'y despues SET v_total = v_total * p_cantidad;',
        'Revisa el stock ANTES de modificarlo: SELECT stock INTO v_stock FROM Inventario ' +
        'WHERE producto_id = p_producto;',
        'La condicion es IF v_stock >= p_cantidad THEN.',
        'Si alcanza: UPDATE Inventario SET stock = stock - p_cantidad WHERE producto_id = p_producto; ' +
        'luego INSERT INTO Pedidos (producto_id, cantidad, total, estado) VALUES (p_producto, p_cantidad, ' +
        'v_total, \'NUEVO\'); luego SET p_estado = \'COMPLETADO\'; y COMMIT;',
        'Si no alcanza, en el ELSE: SET p_estado = \'RECHAZADO\'; y ROLLBACK;',
        'Llama dos veces: CALL VentaFinal(1, 2, @estado1); y CALL VentaFinal(5, 50, @estado2);',
        'Para ver el resultado de cada una: SELECT @estado1; y SELECT @estado2;'
      ],
      objetivo: function (ctx) {
        if (stock(ctx.db, 1) !== 8) {
          return mal('El stock del producto 1 quedo en ' + stock(ctx.db, 1) +
                     '; la venta que si alcanza deberia descontar 2 unidades (de 10 a 8).');
        }
        if (stock(ctx.db, 5) !== 2) {
          return mal('El stock del producto 5 quedo en ' + stock(ctx.db, 5) +
                     '; la venta imposible no deberia tocarlo.');
        }
        var p1 = pedidos(ctx.db).some(function (p) { return p.producto_id === 1 && p.cantidad === 2; });
        if (!p1) return mal('Falta el pedido del producto 1, o quedo con otra cantidad.');
        var p5 = pedidos(ctx.db).some(function (p) { return p.producto_id === 5; });
        if (p5) return mal('Se registro un pedido del producto 5; la venta imposible no debia dejar rastro en Pedidos.');
        var e1 = ctx.db.variablesSesion['@estado1'];
        if (e1 !== 'COMPLETADO') return mal('@estado1 vale ' + e1 + '; deberia ser COMPLETADO.');
        var e2 = ctx.db.variablesSesion['@estado2'];
        if (e2 !== 'RECHAZADO') return mal('@estado2 vale ' + e2 + '; deberia ser RECHAZADO.');
        if (!hubo(ctx.eventos, 'tx-commit')) {
          return mal('Falta un COMMIT: la venta que si alcanza debe confirmarse.');
        }
        if (!hubo(ctx.eventos, 'tx-rollback')) {
          return mal('Falta un ROLLBACK: la venta imposible debe revertirse.');
        }
        if (ctx.db.enTransaccion) return mal('Quedo una transaccion abierta.');
        return bien('Las dos ventas se resolvieron: una se confirmo con su pedido registrado, la otra ' +
                    'se revirtio sin dejar rastro, y el resultado de cada una quedo disponible en su ' +
                    'propia variable de sesion.');
      }
    },

    /* ───────────────────────────────── sandbox ── */
    {
      id: 'sandbox',
      titulo: 'Sandbox libre',
      reto: 'Todos los bloques estan disponibles. Construye lo que quieras y experimenta.',
      explicacion: 'Sin objetivos ni validacion. Buen momento para probar que pasa si olvidas el ' +
                   'COMMIT, si haces ROLLBACK sin transaccion, o si anidas savepoints.',
      bloques: null,          // sin restriccion
      guionInicial: [],
      pistas: ['Prueba a ejecutar en modo paso a paso para narrar cada sentencia.'],
      objetivo: null
    }

  ];

  SQLSim.niveles = niveles;

})();
