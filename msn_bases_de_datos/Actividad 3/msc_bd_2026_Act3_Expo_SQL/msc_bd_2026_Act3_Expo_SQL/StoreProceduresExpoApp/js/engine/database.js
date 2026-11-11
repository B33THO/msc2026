/* ============================================================
   database.js — tablas en memoria, undo log, savepoints, autocommit

   Decisión central: las transacciones se implementan con un UNDO LOG,
   no con copias del estado. Cada mutación apila su operación inversa;
   ROLLBACK desapila y las aplica en orden inverso. Eso da gratis dos
   cosas: SAVEPOINT (una simple marca de posición en el log) y el
   rebobinado animado fila por fila.
   ============================================================ */

window.SQLSim = window.SQLSim || {};

(function () {
  'use strict';

  function clonarFila(fila) {
    return Object.assign({}, fila);
  }

  function ErrorSQL(mensaje, linea) {
    var e = new Error(mensaje);
    e.esErrorSQL = true;
    e.linea = linea || null;
    return e;
  }

  /* ---------------------------------------------------------- */

  function BaseDeDatos(esquema) {
    this.esquema = esquema;
    this.reiniciar();
  }

  BaseDeDatos.prototype.reiniciar = function () {
    var self = this;
    this.tablas = {};
    Object.keys(this.esquema).forEach(function (nombre) {
      self.tablas[nombre] = self.esquema[nombre].semilla.map(clonarFila);
    });
    this.undoLog = [];        // operaciones inversas pendientes
    this.savepoints = {};     // nombre -> índice dentro de undoLog
    this.enTransaccion = false;
    this.procedimientos = {}; // nombre -> nodo AST del CREATE PROCEDURE
    this.variablesSesion = {};// @variables
  };

  /* ── Utilidades de esquema ───────────────────────────────── */

  BaseDeDatos.prototype.existeTabla = function (nombre) {
    return Object.prototype.hasOwnProperty.call(this.tablas, nombre);
  };

  /* Resuelve el nombre de tabla sin distinguir mayúsculas, como MySQL
     en Windows. Devuelve el nombre canónico o null. */
  BaseDeDatos.prototype.resolverTabla = function (nombre) {
    var claves = Object.keys(this.tablas);
    for (var i = 0; i < claves.length; i++) {
      if (claves[i].toLowerCase() === String(nombre).toLowerCase()) return claves[i];
    }
    return null;
  };

  BaseDeDatos.prototype.columnasDe = function (nombre) {
    return this.esquema[nombre].columnas.map(function (c) { return c.nombre; });
  };

  BaseDeDatos.prototype.existeColumna = function (tabla, columna) {
    return this.columnasDe(tabla).some(function (c) {
      return c.toLowerCase() === String(columna).toLowerCase();
    });
  };

  BaseDeDatos.prototype.resolverColumna = function (tabla, columna) {
    var cols = this.columnasDe(tabla);
    for (var i = 0; i < cols.length; i++) {
      if (cols[i].toLowerCase() === String(columna).toLowerCase()) return cols[i];
    }
    return null;
  };

  BaseDeDatos.prototype.filas = function (tabla) {
    return this.tablas[tabla];
  };

  /* ── Undo log ────────────────────────────────────────────── */

  /* Sólo registramos operaciones inversas si hay una transacción
     abierta. Fuera de ella rige autocommit: lo hecho, hecho está.
     Ese contraste es el punto didáctico del nivel 5. */
  BaseDeDatos.prototype._registrar = function (inversa) {
    if (this.enTransaccion) this.undoLog.push(inversa);
  };

  /* ── Mutaciones ──────────────────────────────────────────── */

  BaseDeDatos.prototype.insertar = function (tabla, fila) {
    var filas = this.tablas[tabla];
    var copia = clonarFila(fila);
    filas.push(copia);
    this._registrar({ tipo: 'quitar', tabla: tabla, fila: copia });
    return copia;
  };

  BaseDeDatos.prototype.actualizarFila = function (tabla, fila, cambios) {
    var anterior = {};
    Object.keys(cambios).forEach(function (col) {
      anterior[col] = fila[col];
      fila[col] = cambios[col];
    });
    this._registrar({ tipo: 'restaurar', tabla: tabla, fila: fila, valores: anterior });
    return anterior;
  };

  BaseDeDatos.prototype.borrarFila = function (tabla, fila) {
    var filas = this.tablas[tabla];
    var pos = filas.indexOf(fila);
    if (pos === -1) return null;
    filas.splice(pos, 1);
    this._registrar({ tipo: 'reinsertar', tabla: tabla, fila: fila, pos: pos });
    return fila;
  };

  /* Siguiente valor para una clave autoincremental */
  BaseDeDatos.prototype.siguienteId = function (tabla) {
    var clave = this.esquema[tabla].clave;
    var max = 0;
    this.tablas[tabla].forEach(function (f) {
      var v = Number(f[clave]);
      if (!isNaN(v) && v > max) max = v;
    });
    return max + 1;
  };

  /* ── Control transaccional ───────────────────────────────── */

  BaseDeDatos.prototype.iniciarTransaccion = function () {
    this.enTransaccion = true;
    this.undoLog = [];
    this.savepoints = {};
  };

  BaseDeDatos.prototype.confirmar = function () {
    this.enTransaccion = false;
    this.undoLog = [];
    this.savepoints = {};
  };

  BaseDeDatos.prototype.crearSavepoint = function (nombre) {
    this.savepoints[nombre.toLowerCase()] = this.undoLog.length;
  };

  BaseDeDatos.prototype.tieneSavepoint = function (nombre) {
    return Object.prototype.hasOwnProperty.call(this.savepoints, nombre.toLowerCase());
  };

  /* Deshace hasta `hasta` (índice en el undo log; 0 = todo).
     Devuelve la lista de eventos de deshacer, en el orden en que
     ocurrieron, para que la UI los anime como un rebobinado. */
  BaseDeDatos.prototype.deshacerHasta = function (hasta) {
    var eventos = [];
    while (this.undoLog.length > hasta) {
      var op = this.undoLog.pop();

      if (op.tipo === 'quitar') {
        // deshacer un INSERT
        var filas = this.tablas[op.tabla];
        var pos = filas.indexOf(op.fila);
        if (pos !== -1) filas.splice(pos, 1);
        eventos.push({ tipo: 'row-delete', tabla: op.tabla, fila: op.fila, deshaciendo: true });

      } else if (op.tipo === 'restaurar') {
        // deshacer un UPDATE
        var previos = {};
        Object.keys(op.valores).forEach(function (col) {
          previos[col] = op.fila[col];
          op.fila[col] = op.valores[col];
        });
        eventos.push({
          tipo: 'row-update', tabla: op.tabla, fila: op.fila,
          antes: previos, despues: op.valores, deshaciendo: true
        });

      } else if (op.tipo === 'reinsertar') {
        // deshacer un DELETE
        this.tablas[op.tabla].splice(op.pos, 0, op.fila);
        eventos.push({ tipo: 'row-insert', tabla: op.tabla, fila: op.fila, deshaciendo: true });
      }
    }
    return eventos;
  };

  BaseDeDatos.prototype.revertir = function () {
    var eventos = this.deshacerHasta(0);
    this.enTransaccion = false;
    this.savepoints = {};
    return eventos;
  };

  BaseDeDatos.prototype.revertirASavepoint = function (nombre) {
    var marca = this.savepoints[nombre.toLowerCase()];
    var eventos = this.deshacerHasta(marca);
    // Los savepoints creados después de este dejan de existir
    var self = this;
    Object.keys(this.savepoints).forEach(function (n) {
      if (self.savepoints[n] > marca) delete self.savepoints[n];
    });
    return eventos;
  };

  /* ── Instantánea para validar objetivos de nivel ─────────── */

  BaseDeDatos.prototype.instantanea = function () {
    var self = this;
    var out = {};
    Object.keys(this.tablas).forEach(function (t) {
      out[t] = self.tablas[t].map(clonarFila);
    });
    return out;
  };

  SQLSim.BaseDeDatos = BaseDeDatos;
  SQLSim.ErrorSQL = ErrorSQL;
  SQLSim.clonarFila = clonarFila;

})();
