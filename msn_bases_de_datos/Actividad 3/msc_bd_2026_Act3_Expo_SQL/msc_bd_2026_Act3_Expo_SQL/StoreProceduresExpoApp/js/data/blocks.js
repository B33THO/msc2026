/* ============================================================
   blocks.js — catálogo de bloques arrastrables

   Cada bloque ocupa EXACTAMENTE una línea del script. Esa restricción
   mantiene la correspondencia 1:1 entre línea del editor y línea que
   reporta el motor, de modo que resaltar la línea en ejecución y
   señalar errores de sintaxis es exacto y no aproximado.

   Plantilla: texto plano con huecos escritos {nombre:clase[:refTabla]}
     clase ∈ tabla | columna | valor | nombre | variable | opcion
     refTabla = nombre de otro hueco de tipo tabla, para poblar el
                desplegable de columnas con las de ESA tabla.
   ============================================================ */

window.SQLSim = window.SQLSim || {};

(function () {
  'use strict';

  /* Palabras que se colorean, y con qué acento */
  var TX      = ['START', 'TRANSACTION', 'COMMIT', 'SAVEPOINT'];
  var PELIGRO = ['ROLLBACK'];
  var TIPOS   = ['INT', 'DECIMAL', 'VARCHAR'];
  var CLAVES  = [
    'DELIMITER', 'CREATE', 'PROCEDURE', 'CALL', 'BEGIN', 'END', 'DECLARE',
    'DEFAULT', 'SET', 'SELECT', 'INTO', 'FROM', 'WHERE', 'INSERT', 'VALUES',
    'UPDATE', 'DELETE', 'IF', 'THEN', 'ELSE', 'ELSEIF', 'TO', 'IN', 'OUT',
    'INOUT', 'AND', 'OR', 'NOT', 'AS', 'COUNT', 'SUM'
  ];

  function claseDePalabra(p) {
    var m = p.toUpperCase();
    if (TX.indexOf(m) !== -1)      return 'kw-tx';
    if (PELIGRO.indexOf(m) !== -1) return 'kw-peligro';
    if (TIPOS.indexOf(m) !== -1)   return 'tipo';
    if (CLAVES.indexOf(m) !== -1)  return 'kw';
    return null;
  }

  /* ── Compilación de la plantilla a partes ────────────────── */

  function compilar(plantilla) {
    var partes = [];
    var re = /\{([a-z0-9_]+):([a-z]+)(?::([a-z0-9_]+))?\}/gi;
    var ultimo = 0, m;
    while ((m = re.exec(plantilla)) !== null) {
      if (m.index > ultimo) partes.push({ t: 'texto', v: plantilla.slice(ultimo, m.index) });
      partes.push({ t: 'hueco', nombre: m[1], clase: m[2], refTabla: m[3] || null });
      ultimo = m.index + m[0].length;
    }
    if (ultimo < plantilla.length) partes.push({ t: 'texto', v: plantilla.slice(ultimo) });
    return partes;
  }

  var bloques = [];
  var porId = {};

  function def(id, categoria, plantilla, opciones) {
    var b = Object.assign({
      id: id,
      categoria: categoria,
      plantilla: plantilla,
      partes: compilar(plantilla),
      abre: false,
      cierra: false,
      opciones: null,
      valoresPorDefecto: null,
      etiquetaCorta: null   // texto alterno para el toolbox, si la plantilla es larga
    }, opciones || {});
    bloques.push(b);
    porId[id] = b;
    return b;
  }

  /* ── ESTRUCTURA: delimitador y procedimientos ────────────── */

  def('delim-abrir', 'estructura', 'DELIMITER //');
  def('delim-cerrar', 'estructura', 'DELIMITER ;');

  /* MySQL no tiene CREATE OR REPLACE PROCEDURE: el idioma real es soltar
     el procedimiento antes de recrearlo. */
  def('drop-proc', 'estructura', 'DROP PROCEDURE IF EXISTS {nombre:nombre};',
      { valoresPorDefecto: { nombre: 'MiProcedimiento' } });

  /* Ojo: los CREATE PROCEDURE NO llevan abre:true. Quien abre la sangria es
     BEGIN, para que el cuerpo quede indentado y el BEGIN alineado con el
     CREATE, que es como se formatea en MySQL. */

  def('proc-0', 'estructura',
      'CREATE PROCEDURE {nombre:nombre}()',
      { valoresPorDefecto: { nombre: 'MiProcedimiento' } });

  def('proc-1in', 'estructura',
      'CREATE PROCEDURE {nombre:nombre}(IN {p1:nombre} {t1:opcion})',
      { opciones: { t1: ['INT', 'DECIMAL', 'VARCHAR(40)'] },
        valoresPorDefecto: { nombre: 'RegistrarVenta', p1: 'p_producto', t1: 'INT' } });

  def('proc-2in', 'estructura',
      'CREATE PROCEDURE {nombre:nombre}(IN {p1:nombre} {t1:opcion}, IN {p2:nombre} {t2:opcion})',
      { opciones: { t1: ['INT', 'DECIMAL', 'VARCHAR(40)'], t2: ['INT', 'DECIMAL', 'VARCHAR(40)'] },
        valoresPorDefecto: { nombre: 'RegistrarVenta', p1: 'p_producto', t1: 'INT',
                             p2: 'p_cantidad', t2: 'INT' } });

  def('proc-in-out', 'estructura',
      'CREATE PROCEDURE {nombre:nombre}(IN {p1:nombre} {t1:opcion}, OUT {p2:nombre} {t2:opcion})',
      { opciones: { t1: ['INT', 'DECIMAL', 'VARCHAR(40)'], t2: ['INT', 'DECIMAL', 'VARCHAR(40)'] },
        valoresPorDefecto: { nombre: 'ConsultarStock', p1: 'p_producto', t1: 'INT',
                             p2: 'p_stock', t2: 'INT' } });

  def('proc-2in-out', 'estructura',
      'CREATE PROCEDURE {nombre:nombre}(IN {p1:nombre} {t1:opcion}, IN {p2:nombre} {t2:opcion}, OUT {p3:nombre} {t3:opcion})',
      { opciones: { t1: ['INT', 'DECIMAL', 'VARCHAR(40)'], t2: ['INT', 'DECIMAL', 'VARCHAR(40)'],
                    t3: ['INT', 'DECIMAL', 'VARCHAR(40)'] },
        valoresPorDefecto: { nombre: 'VentaFinal', p1: 'p_producto', t1: 'INT',
                             p2: 'p_cantidad', t2: 'INT', p3: 'p_estado', t3: 'VARCHAR(40)' } });

  def('begin', 'estructura', 'BEGIN', { abre: true });
  def('end', 'estructura', 'END', { cierra: true });
  def('end-delim', 'estructura', 'END //', { cierra: true });

  def('call-0', 'estructura', 'CALL {nombre:nombre}();',
      { valoresPorDefecto: { nombre: 'MiProcedimiento' } });
  def('call-1', 'estructura', 'CALL {nombre:nombre}({a1:valor});',
      { valoresPorDefecto: { nombre: 'RegistrarVenta', a1: '1' } });
  def('call-2', 'estructura', 'CALL {nombre:nombre}({a1:valor}, {a2:valor});',
      { valoresPorDefecto: { nombre: 'RegistrarVenta', a1: '1', a2: '2' } });
  def('call-out', 'estructura', 'CALL {nombre:nombre}({a1:valor}, {v:variable});',
      { valoresPorDefecto: { nombre: 'ConsultarStock', a1: '3', v: '@resultado' } });
  def('call-2out', 'estructura', 'CALL {nombre:nombre}({a1:valor}, {a2:valor}, {v:variable});',
      { valoresPorDefecto: { nombre: 'VentaFinal', a1: '1', a2: '2', v: '@estado1' } });

  /* ── TRANSACCIONES ───────────────────────────────────────── */

  def('start-tx', 'tx', 'START TRANSACTION;');
  def('commit', 'tx', 'COMMIT;');
  def('rollback', 'peligro', 'ROLLBACK;');
  def('savepoint', 'tx', 'SAVEPOINT {nombre:nombre};',
      { valoresPorDefecto: { nombre: 'punto1' } });
  def('rollback-sp', 'peligro', 'ROLLBACK TO SAVEPOINT {nombre:nombre};',
      { valoresPorDefecto: { nombre: 'punto1' } });

  /* ── DML ─────────────────────────────────────────────────── */

  def('select-todo', 'dml', 'SELECT * FROM {t:tabla};',
      { valoresPorDefecto: { t: 'Inventario' } });

  def('select-where', 'dml', 'SELECT * FROM {t:tabla} WHERE {c:columna:t} = {v:valor};',
      { valoresPorDefecto: { t: 'Inventario', c: 'producto_id', v: '1' } });

  def('select-into', 'dml',
      'SELECT {c:columna:t} INTO {v:valor} FROM {t:tabla} WHERE {c2:columna:t} = {v2:valor};',
      { valoresPorDefecto: { c: 'stock', v: 'v_stock', t: 'Inventario',
                             c2: 'producto_id', v2: 'p_producto' } });

  def('select-var', 'dml', 'SELECT {v:variable};',
      { valoresPorDefecto: { v: '@resultado' } });

  def('select-count', 'dml', 'SELECT COUNT(*) AS cuantos FROM {t:tabla};',
      { valoresPorDefecto: { t: 'Pedidos' } });

  def('update-menos', 'dml',
      'UPDATE {t:tabla} SET {c:columna:t} = {c2:columna:t} - {v:valor} WHERE {c3:columna:t} = {v2:valor};',
      { valoresPorDefecto: { t: 'Inventario', c: 'stock', c2: 'stock', v: 'p_cantidad',
                             c3: 'producto_id', v2: 'p_producto' } });

  def('update-igual', 'dml',
      'UPDATE {t:tabla} SET {c:columna:t} = {v:valor} WHERE {c2:columna:t} = {v2:valor};',
      { valoresPorDefecto: { t: 'Inventario', c: 'stock', v: '10',
                             c2: 'producto_id', v2: '1' } });

  def('insert-pedido', 'dml',
      "INSERT INTO Pedidos (producto_id, cantidad, total, estado) VALUES ({v1:valor}, {v2:valor}, {v3:valor}, {v4:valor});",
      { etiquetaCorta: 'INSERT INTO Pedidos …',
        valoresPorDefecto: { v1: 'p_producto', v2: 'p_cantidad', v3: 'v_total', v4: "'NUEVO'" } });

  def('delete-where', 'dml', 'DELETE FROM {t:tabla} WHERE {c:columna:t} = {v:valor};',
      { valoresPorDefecto: { t: 'Pedidos', c: 'pedido_id', v: '1' } });

  /* ── CONTROL ─────────────────────────────────────────────── */

  def('declare', 'control', 'DECLARE {nombre:nombre} {t:opcion} DEFAULT {v:valor};',
      { opciones: { t: ['INT', 'DECIMAL', 'VARCHAR(40)'] },
        valoresPorDefecto: { nombre: 'v_stock', t: 'INT', v: '0' } });

  def('set-local', 'control', 'SET {nombre:nombre} = {v:valor};',
      { valoresPorDefecto: { nombre: 'v_total', v: '0' } });

  def('set-sesion', 'control', 'SET {nombre:variable} = {v:valor};',
      { valoresPorDefecto: { nombre: '@resultado', v: '0' } });

  def('if-then', 'control', 'IF {izq:valor} {op:opcion} {der:valor} THEN',
      { abre: true,
        opciones: { op: ['<', '<=', '=', '<>', '>=', '>'] },
        valoresPorDefecto: { izq: 'v_stock', op: '<', der: '0' } });

  def('else', 'control', 'ELSE', { abre: true, cierra: true });
  def('end-if', 'control', 'END IF;', { cierra: true });

  /* ── Agrupación para el panel izquierdo ──────────────────── */

  var grupos = [
    { titulo: 'Procedimientos', ids: ['drop-proc', 'delim-abrir',
                                      'proc-0', 'proc-1in', 'proc-2in', 'proc-in-out', 'proc-2in-out',
                                      'begin', 'end-delim', 'end', 'delim-cerrar',
                                      'call-0', 'call-1', 'call-2', 'call-out', 'call-2out'] },
    { titulo: 'Transacciones',  ids: ['start-tx', 'commit', 'rollback', 'savepoint', 'rollback-sp'] },
    { titulo: 'Consultas y datos', ids: ['select-todo', 'select-where', 'select-into', 'select-var', 'select-count',
                                         'update-menos', 'update-igual', 'insert-pedido', 'delete-where'] },
    { titulo: 'Variables y control', ids: ['declare', 'set-local', 'set-sesion',
                                           'if-then', 'else', 'end-if'] }
  ];

  /* ── Resaltado de un fragmento de SQL completo ───────────── */

  function escapar(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  /**
   * Colorea SQL de varias lineas: comentarios "--", cadenas, numeros y
   * palabras reservadas. Se usa en las pantallas de teoria; el editor tiene
   * su propia version porque alli el texto viene troceado en partes.
   */
  function resaltarSQL(texto) {
    var re = /(--[^\n]*)|('(?:[^']|'')*')|(\b\d+(?:\.\d+)?\b)|([A-Za-z_][A-Za-z0-9_]*)/g;
    var salida = '', ultimo = 0, m;

    while ((m = re.exec(texto)) !== null) {
      salida += escapar(texto.slice(ultimo, m.index));

      if (m[1])      salida += '<span class="com">' + escapar(m[1]) + '</span>';
      else if (m[2]) salida += '<span class="txt">' + escapar(m[2]) + '</span>';
      else if (m[3]) salida += '<span class="num">' + m[3] + '</span>';
      else {
        var clase = claseDePalabra(m[4]);
        salida += clase ? '<span class="' + clase + '">' + m[4] + '</span>' : escapar(m[4]);
      }
      ultimo = m.index + m[0].length;
    }
    return salida + escapar(texto.slice(ultimo));
  }

  SQLSim.bloques = bloques;
  SQLSim.bloquePorId = function (id) { return porId[id]; };
  SQLSim.gruposBloques = grupos;
  SQLSim.claseDePalabra = claseDePalabra;
  SQLSim.resaltarSQL = resaltarSQL;

})();
