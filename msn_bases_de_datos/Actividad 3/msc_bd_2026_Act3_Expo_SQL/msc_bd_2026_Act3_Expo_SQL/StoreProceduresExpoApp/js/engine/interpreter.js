/* ============================================================
   interpreter.js — recorre el AST y EMITE EVENTOS

   Regla de oro: este archivo nunca toca el DOM. Es un generador que
   produce eventos ('row-insert', 'tx-rollback', 'log'…) y la capa de
   interfaz decide cómo animarlos y a qué velocidad. Gracias a eso
   salen gratis el modo paso a paso y el control de velocidad.

   Eventos emitidos:
     { tipo:'line-enter',  linea }
     { tipo:'log',         nivel, texto }
     { tipo:'row-insert',  tabla, fila, deshaciendo? }
     { tipo:'row-update',  tabla, fila, antes, despues, deshaciendo? }
     { tipo:'row-delete',  tabla, fila, deshaciendo? }
     { tipo:'tx-begin' | 'tx-commit' | 'tx-rollback', savepoint? }
     { tipo:'savepoint',   nombre }
     { tipo:'resultado',   columnas, filas }
   ============================================================ */

window.SQLSim = window.SQLSim || {};

(function () {
  'use strict';

  var ErrorSQL = SQLSim.ErrorSQL;

  /* ── Ámbitos de variables ────────────────────────────────── */

  function Contexto(db) {
    this.db = db;
    this.ambitos = [];  // pila de ámbitos locales (uno por CALL)
    this.filaActual = null;
    this.tablaActual = null;
  }

  Contexto.prototype.abrirAmbito = function (vars) {
    this.ambitos.push(vars || {});
  };

  Contexto.prototype.cerrarAmbito = function () {
    return this.ambitos.pop();
  };

  Contexto.prototype.ambitoActual = function () {
    return this.ambitos[this.ambitos.length - 1] || null;
  };

  Contexto.prototype.declararLocal = function (nombre, valor) {
    var a = this.ambitoActual();
    if (!a) throw ErrorSQL('DECLARE solo puede usarse dentro de un procedimiento');
    a[nombre.toLowerCase()] = valor;
  };

  Contexto.prototype.buscarLocal = function (nombre) {
    var a = this.ambitoActual();
    if (a && Object.prototype.hasOwnProperty.call(a, nombre.toLowerCase())) {
      return { existe: true, valor: a[nombre.toLowerCase()] };
    }
    return { existe: false };
  };

  Contexto.prototype.asignarLocal = function (nombre, valor) {
    var a = this.ambitoActual();
    if (a && Object.prototype.hasOwnProperty.call(a, nombre.toLowerCase())) {
      a[nombre.toLowerCase()] = valor;
      return true;
    }
    return false;
  };

  /* ── Evaluación de expresiones ───────────────────────────── */

  function esNulo(v) { return v === null || v === undefined; }

  function aNumero(v) {
    if (esNulo(v)) return null;
    var n = Number(v);
    return isNaN(n) ? null : n;
  }

  /* MySQL trata 0 como falso y cualquier otro número como verdadero */
  function esVerdad(v) {
    if (esNulo(v)) return false;
    if (typeof v === 'boolean') return v;
    if (typeof v === 'number') return v !== 0;
    return String(v).length > 0 && String(v) !== '0';
  }

  function comparar(a, b) {
    if (typeof a === 'number' || typeof b === 'number') {
      var na = aNumero(a), nb = aNumero(b);
      if (na === null || nb === null) return null;
      return na < nb ? -1 : (na > nb ? 1 : 0);
    }
    var sa = String(a), sb = String(b);
    return sa < sb ? -1 : (sa > sb ? 1 : 0);
  }

  function evaluar(nodo, ctx) {
    switch (nodo.tipo) {

      case 'literal':
        return nodo.valor;

      case 'negativo': {
        var v = aNumero(evaluar(nodo.expr, ctx));
        return v === null ? null : -v;
      }

      case 'var_sesion': {
        var nom = nodo.nombre;
        return Object.prototype.hasOwnProperty.call(ctx.db.variablesSesion, nom)
          ? ctx.db.variablesSesion[nom]
          : null;   // en MySQL una @variable sin asignar vale NULL
      }

      case 'referencia': {
        // 1) columna de la fila que se está evaluando
        if (ctx.filaActual) {
          var canon = ctx.tablaActual
            ? ctx.db.resolverColumna(ctx.tablaActual, nodo.nombre)
            : null;
          if (canon !== null && Object.prototype.hasOwnProperty.call(ctx.filaActual, canon)) {
            return ctx.filaActual[canon];
          }
        }
        // 2) variable local del procedimiento
        var local = ctx.buscarLocal(nodo.nombre);
        if (local.existe) return local.valor;

        throw ErrorSQL(
          'No existe la columna ni la variable "' + nodo.nombre + '"' +
          (ctx.tablaActual ? ' en la tabla ' + ctx.tablaActual : ''),
          nodo.linea
        );
      }

      case 'aritmetica': {
        var a = aNumero(evaluar(nodo.izq, ctx));
        var b = aNumero(evaluar(nodo.der, ctx));
        if (a === null || b === null) return null;
        switch (nodo.op) {
          case '+': return a + b;
          case '-': return a - b;
          case '*': return a * b;
          case '/': return b === 0 ? null : a / b;   // MySQL devuelve NULL, no error
        }
        return null;
      }

      case 'comparacion': {
        var x = evaluar(nodo.izq, ctx);
        var y = evaluar(nodo.der, ctx);
        if (esNulo(x) || esNulo(y)) return null;     // NULL contagia
        var c = comparar(x, y);
        if (c === null) return null;
        switch (nodo.op) {
          case '=':  return c === 0;
          case '<>':
          case '!=': return c !== 0;
          case '<':  return c < 0;
          case '>':  return c > 0;
          case '<=': return c <= 0;
          case '>=': return c >= 0;
        }
        return null;
      }

      case 'logico': {
        var izq = esVerdad(evaluar(nodo.izq, ctx));
        if (nodo.op === 'AND' && !izq) return false;  // corto circuito
        if (nodo.op === 'OR'  &&  izq) return true;
        return esVerdad(evaluar(nodo.der, ctx));
      }

      case 'no':
        return !esVerdad(evaluar(nodo.expr, ctx));

      case 'es_nulo': {
        var nulo = esNulo(evaluar(nodo.expr, ctx));
        return nodo.negado ? !nulo : nulo;
      }

      case 'agregado':
        throw ErrorSQL('Los agregados como ' + nodo.fn + '() solo pueden usarse en un SELECT con FROM', nodo.linea);

      default:
        throw ErrorSQL('Expresion no soportada: ' + nodo.tipo, nodo.linea);
    }
  }

  /* ── Ayudas de tabla ─────────────────────────────────────── */

  function tablaOError(db, nombre, linea) {
    var canon = db.resolverTabla(nombre);
    if (!canon) {
      throw ErrorSQL('No existe la tabla "' + nombre + '". Las tablas disponibles son: ' +
        Object.keys(db.tablas).join(', '), linea);
    }
    return canon;
  }

  function filtrar(db, tabla, donde, ctx) {
    var filas = db.filas(tabla);
    if (!donde) return filas.slice();
    var previaFila = ctx.filaActual, previaTabla = ctx.tablaActual;
    var out = [];
    for (var i = 0; i < filas.length; i++) {
      ctx.filaActual = filas[i];
      ctx.tablaActual = tabla;
      if (esVerdad(evaluar(donde, ctx))) out.push(filas[i]);
    }
    ctx.filaActual = previaFila;
    ctx.tablaActual = previaTabla;
    return out;
  }

  /* Evalúa una expresión "fuera de fila" (valores de INSERT, SET…) */
  function evaluarLibre(nodo, ctx) {
    var pf = ctx.filaActual, pt = ctx.tablaActual;
    ctx.filaActual = null; ctx.tablaActual = null;
    try { return evaluar(nodo, ctx); }
    finally { ctx.filaActual = pf; ctx.tablaActual = pt; }
  }

  function asignarDestino(destino, valor, ctx) {
    if (destino.clase === 'sesion') {
      ctx.db.variablesSesion[destino.nombre] = valor;
      return;
    }
    if (!ctx.asignarLocal(destino.nombre, valor)) {
      throw ErrorSQL('La variable "' + destino.nombre + '" no fue declarada con DECLARE');
    }
  }

  function formatear(v) {
    if (esNulo(v)) return 'NULL';
    if (typeof v === 'number') return String(Math.round(v * 100) / 100);
    return String(v);
  }

  /* ── Ejecución: generadores ──────────────────────────────── */

  function* ejecutarLista(lista, ctx) {
    for (var i = 0; i < lista.length; i++) {
      yield* ejecutarSentencia(lista[i], ctx);
    }
  }

  function* ejecutarSentencia(nodo, ctx) {
    var db = ctx.db;

    if (nodo.linea) yield { tipo: 'line-enter', linea: nodo.linea };

    switch (nodo.tipo) {

      /* ── Estructura ───────────────────────────────────── */

      case 'bloque':
        yield* ejecutarLista(nodo.cuerpo, ctx);
        return;

      case 'create_procedure': {
        // MySQL no tiene CREATE OR REPLACE PROCEDURE (eso es de MariaDB):
        // recrear un procedimiento existente es el error 1304. Se respeta,
        // porque el idioma correcto (DROP ... IF EXISTS antes) es parte de
        // lo que hay que ensenar.
        if (db.procedimientos[nodo.nombre.toLowerCase()]) {
          throw ErrorSQL(
            'El procedimiento ' + nodo.nombre + ' ya existe (en MySQL: ERROR 1304). ' +
            'MySQL no permite recrearlo encima; agrega DROP PROCEDURE IF EXISTS ' +
            nodo.nombre + '; antes del CREATE.', nodo.linea);
        }
        db.procedimientos[nodo.nombre.toLowerCase()] = nodo;
        yield { tipo: 'log', nivel: 'ok',
                texto: 'Procedimiento ' + nodo.nombre + ' creado correctamente.' };
        return;
      }

      case 'drop_procedure': {
        var clave = nodo.nombre.toLowerCase();
        if (db.procedimientos[clave]) {
          delete db.procedimientos[clave];
          yield { tipo: 'log', nivel: 'ok',
                  texto: 'Procedimiento ' + nodo.nombre + ' eliminado.' };
          return;
        }
        if (nodo.siExiste) {
          yield { tipo: 'log', nivel: 'info',
                  texto: 'El procedimiento ' + nodo.nombre + ' no existia; IF EXISTS evita el error.' };
          return;
        }
        throw ErrorSQL('No existe el procedimiento "' + nodo.nombre +
          '" (en MySQL: ERROR 1305). Usa DROP PROCEDURE IF EXISTS para no fallar cuando aun no existe.',
          nodo.linea);
      }

      case 'call': {
        var proc = db.procedimientos[nodo.nombre.toLowerCase()];
        if (!proc) {
          throw ErrorSQL('No existe el procedimiento "' + nodo.nombre +
            '". Recuerda crearlo con CREATE PROCEDURE antes de llamarlo.', nodo.linea);
        }
        if (nodo.args.length !== proc.parametros.length) {
          throw ErrorSQL('El procedimiento ' + proc.nombre + ' espera ' + proc.parametros.length +
            ' parametro(s) y se le pasaron ' + nodo.args.length + '.', nodo.linea);
        }

        // Enlazar parámetros
        var locales = {};
        var salidas = [];   // parámetros OUT/INOUT que hay que devolver
        for (var i = 0; i < proc.parametros.length; i++) {
          var p = proc.parametros[i];
          var arg = nodo.args[i];

          if (p.modo === 'OUT' || p.modo === 'INOUT') {
            if (arg.tipo !== 'var_sesion') {
              throw ErrorSQL('El parametro ' + p.modo + ' "' + p.nombre +
                '" necesita recibir una variable de sesion (por ejemplo @resultado).', nodo.linea);
            }
            salidas.push({ param: p.nombre.toLowerCase(), variable: arg.nombre });
          }

          locales[p.nombre.toLowerCase()] =
            (p.modo === 'OUT') ? null : evaluarLibre(arg, ctx);
        }

        yield { tipo: 'log', nivel: 'info', texto: 'CALL ' + proc.nombre + ' ...' };

        ctx.abrirAmbito(locales);
        try {
          yield* ejecutarSentencia(proc.cuerpo, ctx);
        } finally {
          var finales = ctx.cerrarAmbito();
          // Copiar de vuelta los parámetros de salida
          for (var s = 0; s < salidas.length; s++) {
            db.variablesSesion[salidas[s].variable] = finales[salidas[s].param];
          }
        }

        for (var s2 = 0; s2 < salidas.length; s2++) {
          yield { tipo: 'log', nivel: 'ok',
                  texto: salidas[s2].variable + ' = ' + formatear(db.variablesSesion[salidas[s2].variable]) };
        }
        yield { tipo: 'log', nivel: 'ok', texto: 'Procedimiento ' + proc.nombre + ' ejecutado.' };
        return;
      }

      /* ── Variables ────────────────────────────────────── */

      case 'declare': {
        var inicial = nodo.porDefecto ? evaluarLibre(nodo.porDefecto, ctx) : null;
        for (var d = 0; d < nodo.nombres.length; d++) {
          ctx.declararLocal(nodo.nombres[d], inicial);
        }
        return;
      }

      case 'set': {
        for (var a = 0; a < nodo.asignaciones.length; a++) {
          var asig = nodo.asignaciones[a];
          asignarDestino(asig.destino, evaluarLibre(asig.valor, ctx), ctx);
        }
        return;
      }

      /* ── Consulta ─────────────────────────────────────── */

      case 'select': {
        yield* ejecutarSelect(nodo, ctx);
        return;
      }

      /* ── Mutaciones ───────────────────────────────────── */

      case 'insert': {
        var tIns = tablaOError(db, nodo.tabla, nodo.linea);
        var colsTabla = db.columnasDe(tIns);
        var cols = nodo.columnas;

        if (cols) {
          cols = cols.map(function (c) {
            var canon = db.resolverColumna(tIns, c);
            if (!canon) throw ErrorSQL('La tabla ' + tIns + ' no tiene la columna "' + c + '"', nodo.linea);
            return canon;
          });
        } else {
          cols = colsTabla;
        }

        for (var f = 0; f < nodo.filas.length; f++) {
          var vals = nodo.filas[f];
          if (vals.length !== cols.length) {
            throw ErrorSQL('Se indicaron ' + cols.length + ' columna(s) pero ' + vals.length +
              ' valor(es) en el INSERT sobre ' + tIns, nodo.linea);
          }
          var nueva = {};
          colsTabla.forEach(function (c) { nueva[c] = null; });
          for (var v = 0; v < cols.length; v++) {
            nueva[cols[v]] = evaluarLibre(vals[v], ctx);
          }
          // Clave autoincremental si no se especificó
          var clave = db.esquema[tIns].clave;
          if (db.esquema[tIns].autoincremento && esNulo(nueva[clave])) {
            nueva[clave] = db.siguienteId(tIns);
          }
          var creada = db.insertar(tIns, nueva);
          yield { tipo: 'row-insert', tabla: tIns, fila: creada };
        }

        yield { tipo: 'log', nivel: 'ok',
                texto: nodo.filas.length + ' fila(s) insertada(s) en ' + tIns + '.' };
        return;
      }

      case 'update': {
        var tUpd = tablaOError(db, nodo.tabla, nodo.linea);
        var objetivo = filtrar(db, tUpd, nodo.donde, ctx);

        var cambiosCanon = nodo.cambios.map(function (c) {
          var canon = db.resolverColumna(tUpd, c.columna);
          if (!canon) throw ErrorSQL('La tabla ' + tUpd + ' no tiene la columna "' + c.columna + '"', nodo.linea);
          return { columna: canon, valor: c.valor };
        });

        for (var u = 0; u < objetivo.length; u++) {
          var fila = objetivo[u];
          var nuevos = {};

          // Se evalúa con la fila como contexto: permite balance = balance - 100
          ctx.filaActual = fila; ctx.tablaActual = tUpd;
          for (var cc = 0; cc < cambiosCanon.length; cc++) {
            nuevos[cambiosCanon[cc].columna] = evaluar(cambiosCanon[cc].valor, ctx);
          }
          ctx.filaActual = null; ctx.tablaActual = null;

          var antes = db.actualizarFila(tUpd, fila, nuevos);
          yield { tipo: 'row-update', tabla: tUpd, fila: fila, antes: antes, despues: nuevos };
        }

        yield { tipo: 'log', nivel: objetivo.length ? 'ok' : 'aviso',
                texto: objetivo.length + ' fila(s) modificada(s) en ' + tUpd + '.' };
        return;
      }

      case 'delete': {
        var tDel = tablaOError(db, nodo.tabla, nodo.linea);
        var aBorrar = filtrar(db, tDel, nodo.donde, ctx);
        for (var b = 0; b < aBorrar.length; b++) {
          db.borrarFila(tDel, aBorrar[b]);
          yield { tipo: 'row-delete', tabla: tDel, fila: aBorrar[b] };
        }
        yield { tipo: 'log', nivel: aBorrar.length ? 'ok' : 'aviso',
                texto: aBorrar.length + ' fila(s) eliminada(s) de ' + tDel + '.' };
        return;
      }

      /* ── Control de flujo ─────────────────────────────── */

      case 'if': {
        for (var r = 0; r < nodo.ramas.length; r++) {
          if (esVerdad(evaluarLibre(nodo.ramas[r].cond, ctx))) {
            yield* ejecutarLista(nodo.ramas[r].cuerpo, ctx);
            return;
          }
        }
        if (nodo.sino) yield* ejecutarLista(nodo.sino, ctx);
        return;
      }

      /* ── Transacciones ────────────────────────────────── */

      case 'start_transaction': {
        if (db.enTransaccion) {
          yield { tipo: 'log', nivel: 'aviso',
                  texto: 'Ya habia una transaccion abierta; MySQL confirma la anterior antes de abrir la nueva.' };
        }
        db.iniciarTransaccion();
        yield { tipo: 'tx-begin' };
        yield { tipo: 'log', nivel: 'tx',
                texto: 'START TRANSACTION — los cambios quedan pendientes hasta COMMIT.' };
        return;
      }

      case 'commit': {
        if (!db.enTransaccion) {
          yield { tipo: 'log', nivel: 'aviso',
                  texto: 'COMMIT sin transaccion abierta: no habia nada pendiente que confirmar.' };
          return;
        }
        var pendientes = db.undoLog.length;
        db.confirmar();
        yield { tipo: 'tx-commit' };
        yield { tipo: 'log', nivel: 'tx',
                texto: 'COMMIT — ' + pendientes + ' cambio(s) quedaron permanentes.' };
        return;
      }

      case 'rollback': {
        if (!db.enTransaccion) {
          yield { tipo: 'log', nivel: 'aviso',
                  texto: 'ROLLBACK sin transaccion abierta: no hay nada que revertir. ' +
                         'Fuera de una transaccion rige autocommit y los cambios ya son definitivos.' };
          return;
        }

        var deshacer;
        if (nodo.savepoint) {
          if (!db.tieneSavepoint(nodo.savepoint)) {
            throw ErrorSQL('No existe el savepoint "' + nodo.savepoint + '"', nodo.linea);
          }
          deshacer = db.revertirASavepoint(nodo.savepoint);
          yield { tipo: 'tx-rollback', savepoint: nodo.savepoint };
        } else {
          deshacer = db.revertir();
          yield { tipo: 'tx-rollback', savepoint: null };
        }

        // El rebobinado: se reemiten los cambios al revés, uno por uno
        for (var e = 0; e < deshacer.length; e++) yield deshacer[e];

        yield { tipo: 'log', nivel: 'tx',
                texto: nodo.savepoint
                  ? 'ROLLBACK TO SAVEPOINT ' + nodo.savepoint + ' — ' + deshacer.length + ' cambio(s) deshecho(s).'
                  : 'ROLLBACK — ' + deshacer.length + ' cambio(s) deshecho(s). La base volvio a su estado anterior.' };
        return;
      }

      case 'savepoint': {
        if (!db.enTransaccion) {
          yield { tipo: 'log', nivel: 'aviso',
                  texto: 'SAVEPOINT fuera de una transaccion no sirve de nada: no hay cambios que marcar.' };
          return;
        }
        db.crearSavepoint(nodo.nombre);
        yield { tipo: 'savepoint', nombre: nodo.nombre };
        yield { tipo: 'log', nivel: 'tx', texto: 'SAVEPOINT ' + nodo.nombre + ' establecido.' };
        return;
      }

      case 'programa':
        yield* ejecutarLista(nodo.cuerpo, ctx);
        return;

      default:
        throw ErrorSQL('Sentencia no soportada por el simulador: ' + nodo.tipo, nodo.linea);
    }
  }

  /* ── SELECT ──────────────────────────────────────────────── */

  function* ejecutarSelect(nodo, ctx) {
    var db = ctx.db;

    // SELECT sin FROM: sólo expresiones
    if (!nodo.tabla) {
      var fila = {}, encabezados = [];
      nodo.columnas.forEach(function (c, idx) {
        if (c.clase === 'todas') throw ErrorSQL('SELECT * necesita un FROM', nodo.linea);
        var nombre = c.alias || ('col' + (idx + 1));
        encabezados.push(nombre);
        fila[nombre] = evaluarLibre(c.expr, ctx);
      });
      if (nodo.destinos) {
        for (var i = 0; i < nodo.destinos.length; i++) {
          asignarDestino(nodo.destinos[i], fila[encabezados[i]], ctx);
        }
        return;
      }
      yield { tipo: 'resultado', columnas: encabezados, filas: [fila] };
      return;
    }

    var tabla = tablaOError(db, nodo.tabla, nodo.linea);
    var filas = filtrar(db, tabla, nodo.donde, ctx);

    // ¿Hay agregados? Entonces el resultado es una sola fila.
    var hayAgregado = nodo.columnas.some(function (c) {
      return c.clase === 'expr' && c.expr.tipo === 'agregado';
    });

    var cols = [], salida = [];

    if (hayAgregado) {
      var unica = {};
      nodo.columnas.forEach(function (c, idx) {
        if (c.clase === 'todas') throw ErrorSQL('No se puede combinar * con funciones de agregado', nodo.linea);
        var nombre = c.alias || (c.expr.tipo === 'agregado'
          ? c.expr.fn + '(...)'
          : (c.expr.nombre || ('col' + (idx + 1))));
        cols.push(nombre);
        unica[nombre] = calcularAgregado(c.expr, filas, tabla, ctx);
      });
      salida.push(unica);

    } else {
      // Encabezados
      nodo.columnas.forEach(function (c, idx) {
        if (c.clase === 'todas') {
          db.columnasDe(tabla).forEach(function (n) { cols.push(n); });
        } else {
          cols.push(c.alias || c.expr.nombre || ('col' + (idx + 1)));
        }
      });

      for (var f = 0; f < filas.length; f++) {
        ctx.filaActual = filas[f]; ctx.tablaActual = tabla;
        var out = {}, k = 0;
        for (var c2 = 0; c2 < nodo.columnas.length; c2++) {
          var col = nodo.columnas[c2];
          if (col.clase === 'todas') {
            db.columnasDe(tabla).forEach(function (n) { out[n] = filas[f][n]; k++; });
          } else {
            out[cols[k]] = evaluar(col.expr, ctx);
            k++;
          }
        }
        salida.push(out);
      }
      ctx.filaActual = null; ctx.tablaActual = null;
    }

    // SELECT ... INTO variables: toma la primera fila
    if (nodo.destinos) {
      if (salida.length === 0) {
        // MySQL deja las variables intactas y avisa; aquí lo hacemos explícito
        yield { tipo: 'log', nivel: 'aviso',
                texto: 'El SELECT ... INTO no encontro ninguna fila; las variables no cambiaron.' };
        return;
      }
      if (nodo.destinos.length !== cols.length) {
        throw ErrorSQL('El SELECT devuelve ' + cols.length + ' columna(s) pero el INTO tiene ' +
          nodo.destinos.length + ' variable(s)', nodo.linea);
      }
      for (var d = 0; d < nodo.destinos.length; d++) {
        asignarDestino(nodo.destinos[d], salida[0][cols[d]], ctx);
      }
      yield { tipo: 'log', nivel: 'info',
              texto: 'SELECT INTO: ' + nodo.destinos.map(function (dd, ii) {
                return dd.nombre + ' = ' + formatear(salida[0][cols[ii]]);
              }).join(', ') };
      return;
    }

    yield { tipo: 'resultado', columnas: cols, filas: salida };
  }

  function calcularAgregado(nodo, filas, tabla, ctx) {
    if (nodo.tipo !== 'agregado') {
      // Columna suelta junto a un agregado: MySQL toma la primera fila
      if (!filas.length) return null;
      ctx.filaActual = filas[0]; ctx.tablaActual = tabla;
      var v = evaluar(nodo, ctx);
      ctx.filaActual = null; ctx.tablaActual = null;
      return v;
    }

    if (nodo.fn === 'COUNT') {
      if (nodo.arg.tipo === 'todas') return filas.length;
      var n = 0;
      for (var i = 0; i < filas.length; i++) {
        ctx.filaActual = filas[i]; ctx.tablaActual = tabla;
        if (!esNulo(evaluar(nodo.arg, ctx))) n++;
      }
      ctx.filaActual = null; ctx.tablaActual = null;
      return n;
    }

    // SUM
    var suma = 0, hubo = false;
    for (var j = 0; j < filas.length; j++) {
      ctx.filaActual = filas[j]; ctx.tablaActual = tabla;
      var val = aNumero(evaluar(nodo.arg, ctx));
      if (val !== null) { suma += val; hubo = true; }
    }
    ctx.filaActual = null; ctx.tablaActual = null;
    return hubo ? suma : null;
  }

  /* ── API pública ─────────────────────────────────────────── */

  /**
   * Devuelve un generador de eventos. No ejecuta nada hasta que se
   * consume; así la UI controla el ritmo.
   */
  function ejecutar(db, ast) {
    var ctx = new Contexto(db);
    return ejecutarSentencia(ast, ctx);
  }

  SQLSim.ejecutar = ejecutar;
  SQLSim.Contexto = Contexto;
  SQLSim.formatearValor = formatear;
  SQLSim.esVerdad = esVerdad;

})();
