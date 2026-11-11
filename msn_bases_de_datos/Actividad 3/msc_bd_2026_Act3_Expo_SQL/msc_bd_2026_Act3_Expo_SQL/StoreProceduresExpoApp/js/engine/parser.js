/* ============================================================
   parser.js — descenso recursivo, de tokens a AST

   Los mensajes de error van en español y siempre llevan número de
   línea: son parte del material didáctico, no un detalle técnico.
   ============================================================ */

window.SQLSim = window.SQLSim || {};

(function () {
  'use strict';

  var ErrorSQL = SQLSim.ErrorSQL;

  function Parser(tokens) {
    this.tokens = tokens;
    this.pos = 0;
  }

  /* ── Navegación ──────────────────────────────────────────── */

  Parser.prototype.actual = function () { return this.tokens[this.pos]; };
  Parser.prototype.linea  = function () { return this.actual().linea; };

  Parser.prototype.es = function (tipo, valor) {
    var t = this.actual();
    if (t.tipo !== tipo) return false;
    if (valor === undefined) return true;
    return String(t.valor).toUpperCase() === String(valor).toUpperCase();
  };

  Parser.prototype.esPalabra = function () {
    for (var i = 0; i < arguments.length; i++) {
      if (this.es('palabra', arguments[i])) return true;
    }
    return false;
  };

  Parser.prototype.avanzar = function () { return this.tokens[this.pos++]; };

  Parser.prototype.aceptar = function (tipo, valor) {
    if (this.es(tipo, valor)) return this.avanzar();
    return null;
  };

  Parser.prototype.exigir = function (tipo, valor, mensaje) {
    if (this.es(tipo, valor)) return this.avanzar();
    var t = this.actual();
    var visto = t.tipo === 'fin' ? 'el final del script' : '"' + t.valor + '"';
    throw ErrorSQL(mensaje || ('Se esperaba ' + (valor || tipo) + ' pero se encontro ' + visto), t.linea);
  };

  Parser.prototype.exigirPuntoYComa = function (queSentencia) {
    if (this.es('op', ';')) { this.avanzar(); return; }
    var t = this.actual();
    throw ErrorSQL(
      'Falta ";" al final de ' + queSentencia + (t.tipo === 'fin' ? '' : ' (antes de "' + t.valor + '")'),
      this.tokens[this.pos - 1] ? this.tokens[this.pos - 1].linea : t.linea
    );
  };

  Parser.prototype.exigirIdent = function (que) {
    // Aceptamos también palabras reservadas como nombre cuando el contexto
    // lo permite (p. ej. una columna llamada "estado" no lo es, pero
    // conviene no ser más estrictos de lo necesario en clase).
    if (this.es('ident')) return this.avanzar().valor;
    var t = this.actual();
    throw ErrorSQL('Se esperaba ' + que + ' pero se encontro "' +
      (t.tipo === 'fin' ? 'el final del script' : t.valor) + '"', t.linea);
  };

  /* ── Punto de entrada ────────────────────────────────────── */

  Parser.prototype.parsearPrograma = function () {
    var sentencias = [];
    while (!this.es('fin')) {
      if (this.aceptar('delim')) continue;   // DELIMITER ya lo manejó el lexer
      if (this.aceptar('op', ';')) continue; // punto y coma suelto
      sentencias.push(this.parsearSentencia());
    }
    return { tipo: 'programa', cuerpo: sentencias };
  };

  /* ── Sentencias ──────────────────────────────────────────── */

  Parser.prototype.parsearSentencia = function () {
    var t = this.actual();
    var l = t.linea;

    if (t.tipo !== 'palabra') {
      throw ErrorSQL('No se reconoce el inicio de la sentencia: "' + t.valor + '"', l);
    }

    switch (t.valor) {
      case 'CREATE':      return this.parsearCreateProcedure();
      case 'DROP':        return this.parsearDropProcedure();
      case 'CALL':        return this.parsearCall();
      case 'DECLARE':     return this.parsearDeclare();
      case 'SET':         return this.parsearSet();
      case 'SELECT':      return this.parsearSelect();
      case 'INSERT':      return this.parsearInsert();
      case 'UPDATE':      return this.parsearUpdate();
      case 'DELETE':      return this.parsearDelete();
      case 'IF':          return this.parsearIf();
      case 'BEGIN':       return this.parsearBloque();
      case 'START':       return this.parsearStartTransaction();
      case 'COMMIT':      this.avanzar(); this.exigirPuntoYComa('COMMIT');
                          return { tipo: 'commit', linea: l };
      case 'ROLLBACK':    return this.parsearRollback();
      case 'SAVEPOINT':   return this.parsearSavepoint();
      default:
        throw ErrorSQL('Sentencia no soportada por el simulador: "' + t.valor + '"', l);
    }
  };

  /* CREATE PROCEDURE nombre(IN p INT, OUT q DECIMAL) BEGIN ... END */
  Parser.prototype.parsearCreateProcedure = function () {
    var l = this.linea();
    this.avanzar(); // CREATE
    this.exigir('palabra', 'PROCEDURE', 'Despues de CREATE se esperaba PROCEDURE');
    var nombre = this.exigirIdent('el nombre del procedimiento');

    var parametros = [];
    this.exigir('op', '(', 'Falta "(" para la lista de parametros de ' + nombre);
    if (!this.es('op', ')')) {
      do {
        var modo = 'IN';
        if (this.esPalabra('IN', 'OUT', 'INOUT')) modo = this.avanzar().valor;
        var pnombre = this.exigirIdent('el nombre de un parametro');
        var ptipo = 'INT';
        if (this.esPalabra('INT', 'DECIMAL', 'VARCHAR')) {
          ptipo = this.avanzar().valor;
          // longitud opcional: VARCHAR(40), DECIMAL(10,2)
          if (this.aceptar('op', '(')) {
            while (!this.es('op', ')') && !this.es('fin')) this.avanzar();
            this.exigir('op', ')', 'Falta ")" en el tipo del parametro ' + pnombre);
          }
        }
        parametros.push({ modo: modo, nombre: pnombre, tipo: ptipo });
      } while (this.aceptar('op', ','));
    }
    this.exigir('op', ')', 'Falta ")" al cerrar los parametros de ' + nombre);

    if (!this.esPalabra('BEGIN')) {
      throw ErrorSQL('El cuerpo del procedimiento ' + nombre + ' debe empezar con BEGIN', this.linea());
    }
    var cuerpo = this.parsearBloque();
    this.aceptar('op', ';'); // el delimitador // se tokenizó como ";"

    return { tipo: 'create_procedure', nombre: nombre, parametros: parametros, cuerpo: cuerpo, linea: l };
  };

  /* DROP PROCEDURE [IF EXISTS] nombre; */
  Parser.prototype.parsearDropProcedure = function () {
    var l = this.linea();
    this.avanzar(); // DROP
    this.exigir('palabra', 'PROCEDURE',
      'El simulador solo soporta DROP PROCEDURE (no se pueden borrar tablas)');

    var siExiste = false;
    if (this.aceptar('palabra', 'IF')) {
      this.exigir('palabra', 'EXISTS', 'Despues de IF se esperaba EXISTS');
      siExiste = true;
    }

    var nombre = this.exigirIdent('el nombre del procedimiento a eliminar');
    this.exigirPuntoYComa('DROP PROCEDURE');
    return { tipo: 'drop_procedure', nombre: nombre, siExiste: siExiste, linea: l };
  };

  /* BEGIN ... END */
  Parser.prototype.parsearBloque = function () {
    var l = this.linea();
    this.exigir('palabra', 'BEGIN');
    var sentencias = [];
    while (!this.esPalabra('END')) {
      if (this.es('fin')) {
        throw ErrorSQL('Falta END: el BEGIN de la linea ' + l + ' nunca se cierra', l);
      }
      if (this.aceptar('op', ';')) continue;
      sentencias.push(this.parsearSentencia());
    }
    this.avanzar(); // END
    return { tipo: 'bloque', cuerpo: sentencias, linea: l };
  };

  /* CALL nombre(args) */
  Parser.prototype.parsearCall = function () {
    var l = this.linea();
    this.avanzar();
    var nombre = this.exigirIdent('el nombre del procedimiento a llamar');
    var args = [];
    if (this.aceptar('op', '(')) {
      if (!this.es('op', ')')) {
        do { args.push(this.parsearExpresion()); } while (this.aceptar('op', ','));
      }
      this.exigir('op', ')', 'Falta ")" al cerrar los argumentos de CALL ' + nombre);
    }
    this.exigirPuntoYComa('CALL ' + nombre);
    return { tipo: 'call', nombre: nombre, args: args, linea: l };
  };

  /* DECLARE v INT DEFAULT 0; */
  Parser.prototype.parsearDeclare = function () {
    var l = this.linea();
    this.avanzar();
    var nombres = [];
    do { nombres.push(this.exigirIdent('el nombre de la variable')); } while (this.aceptar('op', ','));

    var tipo = 'INT';
    if (this.esPalabra('INT', 'DECIMAL', 'VARCHAR')) {
      tipo = this.avanzar().valor;
      if (this.aceptar('op', '(')) {
        while (!this.es('op', ')') && !this.es('fin')) this.avanzar();
        this.exigir('op', ')');
      }
    }
    var porDefecto = null;
    if (this.aceptar('palabra', 'DEFAULT')) porDefecto = this.parsearExpresion();

    this.exigirPuntoYComa('DECLARE');
    return { tipo: 'declare', nombres: nombres, tipoDato: tipo, porDefecto: porDefecto, linea: l };
  };

  /* SET v = expr;  |  SET @v = expr; */
  Parser.prototype.parsearSet = function () {
    var l = this.linea();
    this.avanzar();
    var asignaciones = [];
    do {
      var destino;
      if (this.es('variable')) destino = { clase: 'sesion', nombre: this.avanzar().valor };
      else destino = { clase: 'local', nombre: this.exigirIdent('el nombre de la variable a asignar') };
      this.exigir('op', '=', 'Falta "=" en la asignacion de ' + destino.nombre);
      asignaciones.push({ destino: destino, valor: this.parsearExpresion() });
    } while (this.aceptar('op', ','));
    this.exigirPuntoYComa('SET');
    return { tipo: 'set', asignaciones: asignaciones, linea: l };
  };

  /* SELECT lista [INTO vars] [FROM tabla [WHERE cond]] */
  Parser.prototype.parsearSelect = function () {
    var l = this.linea();
    this.avanzar();

    var columnas = [];
    do {
      if (this.es('op', '*')) { this.avanzar(); columnas.push({ clase: 'todas' }); }
      else {
        var e = this.parsearExpresion();
        var alias = null;
        if (this.aceptar('palabra', 'AS')) alias = this.exigirIdent('el alias de la columna');
        columnas.push({ clase: 'expr', expr: e, alias: alias });
      }
    } while (this.aceptar('op', ','));

    var destinos = null;
    if (this.aceptar('palabra', 'INTO')) {
      destinos = [];
      do {
        if (this.es('variable')) destinos.push({ clase: 'sesion', nombre: this.avanzar().valor });
        else destinos.push({ clase: 'local', nombre: this.exigirIdent('la variable destino del INTO') });
      } while (this.aceptar('op', ','));
    }

    var tabla = null, donde = null;
    if (this.aceptar('palabra', 'FROM')) {
      tabla = this.exigirIdent('el nombre de la tabla');
      if (this.aceptar('palabra', 'WHERE')) donde = this.parsearExpresion();
    }

    this.exigirPuntoYComa('SELECT');
    return { tipo: 'select', columnas: columnas, destinos: destinos, tabla: tabla, donde: donde, linea: l };
  };

  /* INSERT INTO tabla (cols) VALUES (exprs), (exprs) */
  Parser.prototype.parsearInsert = function () {
    var l = this.linea();
    this.avanzar();
    this.exigir('palabra', 'INTO', 'Despues de INSERT se esperaba INTO');
    var tabla = this.exigirIdent('el nombre de la tabla');

    var columnas = null;
    if (this.aceptar('op', '(')) {
      columnas = [];
      do { columnas.push(this.exigirIdent('el nombre de una columna')); } while (this.aceptar('op', ','));
      this.exigir('op', ')', 'Falta ")" al cerrar la lista de columnas de ' + tabla);
    }

    this.exigir('palabra', 'VALUES', 'Falta VALUES en el INSERT sobre ' + tabla);
    var filas = [];
    do {
      this.exigir('op', '(', 'Los valores del INSERT van entre parentesis');
      var vals = [];
      if (!this.es('op', ')')) {
        do { vals.push(this.parsearExpresion()); } while (this.aceptar('op', ','));
      }
      this.exigir('op', ')', 'Falta ")" al cerrar los VALUES');
      filas.push(vals);
    } while (this.aceptar('op', ','));

    this.exigirPuntoYComa('INSERT');
    return { tipo: 'insert', tabla: tabla, columnas: columnas, filas: filas, linea: l };
  };

  /* UPDATE tabla SET col = expr [, ...] [WHERE cond] */
  Parser.prototype.parsearUpdate = function () {
    var l = this.linea();
    this.avanzar();
    var tabla = this.exigirIdent('el nombre de la tabla');
    this.exigir('palabra', 'SET', 'Falta SET en el UPDATE sobre ' + tabla);

    var cambios = [];
    do {
      var col = this.exigirIdent('el nombre de la columna a modificar');
      this.exigir('op', '=', 'Falta "=" al asignar la columna ' + col);
      cambios.push({ columna: col, valor: this.parsearExpresion() });
    } while (this.aceptar('op', ','));

    var donde = null;
    if (this.aceptar('palabra', 'WHERE')) donde = this.parsearExpresion();

    this.exigirPuntoYComa('UPDATE');
    return { tipo: 'update', tabla: tabla, cambios: cambios, donde: donde, linea: l };
  };

  /* DELETE FROM tabla [WHERE cond] */
  Parser.prototype.parsearDelete = function () {
    var l = this.linea();
    this.avanzar();
    this.exigir('palabra', 'FROM', 'Despues de DELETE se esperaba FROM');
    var tabla = this.exigirIdent('el nombre de la tabla');
    var donde = null;
    if (this.aceptar('palabra', 'WHERE')) donde = this.parsearExpresion();
    this.exigirPuntoYComa('DELETE');
    return { tipo: 'delete', tabla: tabla, donde: donde, linea: l };
  };

  /* IF cond THEN ... ELSEIF ... ELSE ... END IF; */
  Parser.prototype.parsearIf = function () {
    var l = this.linea();
    this.avanzar();
    var cond = this.parsearExpresion();
    this.exigir('palabra', 'THEN', 'Falta THEN despues de la condicion del IF');

    var ramas = [{ cond: cond, cuerpo: [] }];
    var sino = null;
    var actual = ramas[0].cuerpo;

    while (true) {
      if (this.es('fin')) {
        throw ErrorSQL('Falta END IF: el IF de la linea ' + l + ' nunca se cierra', l);
      }
      if (this.esPalabra('ELSEIF')) {
        this.avanzar();
        var c2 = this.parsearExpresion();
        this.exigir('palabra', 'THEN', 'Falta THEN despues de la condicion del ELSEIF');
        ramas.push({ cond: c2, cuerpo: [] });
        actual = ramas[ramas.length - 1].cuerpo;
        continue;
      }
      if (this.esPalabra('ELSE')) {
        this.avanzar();
        sino = [];
        actual = sino;
        continue;
      }
      if (this.esPalabra('END')) {
        this.avanzar();
        // Un END suelto suele ser el END del BEGIN: el IF se quedó sin cerrar.
        this.exigir('palabra', 'IF',
          'Falta END IF: el IF de la linea ' + l + ' se quedo sin cerrar ' +
          '(se encontro el END del bloque antes de cerrarlo)');
        this.exigirPuntoYComa('END IF');
        break;
      }
      if (this.aceptar('op', ';')) continue;
      actual.push(this.parsearSentencia());
    }

    return { tipo: 'if', ramas: ramas, sino: sino, linea: l };
  };

  /* START TRANSACTION; */
  Parser.prototype.parsearStartTransaction = function () {
    var l = this.linea();
    this.avanzar();
    this.exigir('palabra', 'TRANSACTION', 'Despues de START se esperaba TRANSACTION');
    this.exigirPuntoYComa('START TRANSACTION');
    return { tipo: 'start_transaction', linea: l };
  };

  /* ROLLBACK;  |  ROLLBACK TO SAVEPOINT n; */
  Parser.prototype.parsearRollback = function () {
    var l = this.linea();
    this.avanzar();
    var savepoint = null;
    if (this.aceptar('palabra', 'TO')) {
      this.aceptar('palabra', 'SAVEPOINT'); // la palabra SAVEPOINT es opcional en MySQL
      savepoint = this.exigirIdent('el nombre del savepoint');
    }
    this.exigirPuntoYComa('ROLLBACK');
    return { tipo: 'rollback', savepoint: savepoint, linea: l };
  };

  /* SAVEPOINT n; */
  Parser.prototype.parsearSavepoint = function () {
    var l = this.linea();
    this.avanzar();
    var nombre = this.exigirIdent('el nombre del savepoint');
    this.exigirPuntoYComa('SAVEPOINT');
    return { tipo: 'savepoint', nombre: nombre, linea: l };
  };

  /* ── Expresiones (precedencia de menor a mayor) ──────────── */

  Parser.prototype.parsearExpresion = function () { return this.parsearOr(); };

  Parser.prototype.parsearOr = function () {
    var izq = this.parsearAnd();
    while (this.esPalabra('OR')) {
      var l = this.avanzar().linea;
      izq = { tipo: 'logico', op: 'OR', izq: izq, der: this.parsearAnd(), linea: l };
    }
    return izq;
  };

  Parser.prototype.parsearAnd = function () {
    var izq = this.parsearNot();
    while (this.esPalabra('AND')) {
      var l = this.avanzar().linea;
      izq = { tipo: 'logico', op: 'AND', izq: izq, der: this.parsearNot(), linea: l };
    }
    return izq;
  };

  Parser.prototype.parsearNot = function () {
    if (this.esPalabra('NOT')) {
      var l = this.avanzar().linea;
      return { tipo: 'no', expr: this.parsearNot(), linea: l };
    }
    return this.parsearComparacion();
  };

  Parser.prototype.parsearComparacion = function () {
    var izq = this.parsearSuma();

    // IS NULL / IS NOT NULL
    if (this.esPalabra('IS')) {
      var lIs = this.avanzar().linea;
      var negado = !!this.aceptar('palabra', 'NOT');
      this.exigir('palabra', 'NULL', 'Despues de IS se esperaba NULL');
      return { tipo: 'es_nulo', expr: izq, negado: negado, linea: lIs };
    }

    var ops = ['=', '<>', '!=', '<', '>', '<=', '>='];
    for (var i = 0; i < ops.length; i++) {
      if (this.es('op', ops[i])) {
        var t = this.avanzar();
        return { tipo: 'comparacion', op: t.valor, izq: izq, der: this.parsearSuma(), linea: t.linea };
      }
    }
    return izq;
  };

  Parser.prototype.parsearSuma = function () {
    var izq = this.parsearProducto();
    while (this.es('op', '+') || this.es('op', '-')) {
      var t = this.avanzar();
      izq = { tipo: 'aritmetica', op: t.valor, izq: izq, der: this.parsearProducto(), linea: t.linea };
    }
    return izq;
  };

  Parser.prototype.parsearProducto = function () {
    var izq = this.parsearUnario();
    while (this.es('op', '*') || this.es('op', '/')) {
      var t = this.avanzar();
      izq = { tipo: 'aritmetica', op: t.valor, izq: izq, der: this.parsearUnario(), linea: t.linea };
    }
    return izq;
  };

  Parser.prototype.parsearUnario = function () {
    if (this.es('op', '-')) {
      var t = this.avanzar();
      return { tipo: 'negativo', expr: this.parsearUnario(), linea: t.linea };
    }
    return this.parsearPrimario();
  };

  Parser.prototype.parsearPrimario = function () {
    var t = this.actual();

    if (t.tipo === 'numero')   { this.avanzar(); return { tipo: 'literal', valor: t.valor, linea: t.linea }; }
    if (t.tipo === 'cadena')   { this.avanzar(); return { tipo: 'literal', valor: t.valor, linea: t.linea }; }
    if (t.tipo === 'variable') { this.avanzar(); return { tipo: 'var_sesion', nombre: t.valor, linea: t.linea }; }

    if (this.es('palabra', 'NULL')) { this.avanzar(); return { tipo: 'literal', valor: null, linea: t.linea }; }

    // Agregados: COUNT(*) y SUM(expr)
    if (this.esPalabra('COUNT', 'SUM')) {
      var fn = this.avanzar().valor;
      this.exigir('op', '(', 'Falta "(" despues de ' + fn);
      var arg;
      if (this.es('op', '*')) { this.avanzar(); arg = { tipo: 'todas' }; }
      else arg = this.parsearExpresion();
      this.exigir('op', ')', 'Falta ")" al cerrar ' + fn);
      return { tipo: 'agregado', fn: fn, arg: arg, linea: t.linea };
    }

    if (this.aceptar('op', '(')) {
      var dentro = this.parsearExpresion();
      this.exigir('op', ')', 'Falta ")" al cerrar la expresion');
      return dentro;
    }

    if (t.tipo === 'ident') {
      this.avanzar();
      // tabla.columna
      if (this.es('op', '.')) {
        this.avanzar();
        var col = this.exigirIdent('el nombre de la columna');
        return { tipo: 'referencia', tabla: t.valor, nombre: col, linea: t.linea };
      }
      return { tipo: 'referencia', tabla: null, nombre: t.valor, linea: t.linea };
    }

    throw ErrorSQL(
      'Se esperaba un valor o una columna pero se encontro ' +
      (t.tipo === 'fin' ? 'el final del script' : '"' + t.valor + '"'),
      t.linea
    );
  };

  /* ── API ─────────────────────────────────────────────────── */

  function parsear(texto) {
    var tokens = SQLSim.tokenizar(texto);
    return new Parser(tokens).parsearPrograma();
  }

  SQLSim.parsear = parsear;
  SQLSim.Parser = Parser;

})();
