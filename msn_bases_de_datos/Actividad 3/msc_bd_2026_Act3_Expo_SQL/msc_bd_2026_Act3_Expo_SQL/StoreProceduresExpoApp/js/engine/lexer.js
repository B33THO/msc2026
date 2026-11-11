/* ============================================================
   lexer.js — tokenizador del subconjunto de MySQL soportado

   Particularidad: DELIMITER no es una sentencia de SQL sino una
   directiva del cliente (mysql CLI). Aquí se trata igual: se procesa
   antes de tokenizar el resto y cambia qué secuencia termina una
   sentencia. Ese es justamente el punto que confunde a todo el mundo
   la primera vez que escribe un procedimiento, y por eso el nivel 2
   lo trabaja de forma explícita.
   ============================================================ */

window.SQLSim = window.SQLSim || {};

(function () {
  'use strict';

  var PALABRAS = [
    'DELIMITER', 'CREATE', 'DROP', 'EXISTS', 'PROCEDURE', 'CALL', 'BEGIN', 'END',
    'DECLARE', 'DEFAULT', 'SET', 'SELECT', 'INTO', 'FROM', 'WHERE',
    'INSERT', 'VALUES', 'UPDATE', 'DELETE',
    'IF', 'THEN', 'ELSE', 'ELSEIF',
    'START', 'TRANSACTION', 'COMMIT', 'ROLLBACK', 'SAVEPOINT', 'TO',
    'IN', 'OUT', 'INOUT',
    'AND', 'OR', 'NOT', 'NULL', 'IS',
    'INT', 'DECIMAL', 'VARCHAR', 'AS', 'COUNT', 'SUM'
  ];

  var ES_PALABRA = {};
  PALABRAS.forEach(function (p) { ES_PALABRA[p] = true; });

  var OPERADORES = ['<=', '>=', '<>', '!=', '=', '<', '>', '+', '-', '*', '/', '(', ')', ',', ';', '.'];

  function esLetra(c)  { return /[A-Za-z_]/.test(c); }
  function esDigito(c) { return /[0-9]/.test(c); }
  function esAlnum(c)  { return /[A-Za-z0-9_]/.test(c); }

  /**
   * Convierte el texto en una lista de tokens.
   * Cada token: { tipo, valor, linea, col }
   * tipo ∈ palabra | ident | numero | cadena | variable | op | delim | fin
   */
  function tokenizar(texto) {
    var tokens = [];
    var i = 0;
    var linea = 1;
    var inicioLinea = 0;
    var delimitador = ';';

    function col() { return i - inicioLinea + 1; }

    function empujar(tipo, valor, l, c) {
      tokens.push({ tipo: tipo, valor: valor, linea: l, col: c });
    }

    while (i < texto.length) {
      var c = texto[i];

      // Saltos de línea
      if (c === '\n') { linea++; i++; inicioLinea = i; continue; }
      // Espacios
      if (/\s/.test(c)) { i++; continue; }

      // Comentarios -- ... y # ...
      if ((c === '-' && texto[i + 1] === '-') || c === '#') {
        while (i < texto.length && texto[i] !== '\n') i++;
        continue;
      }
      // Comentario /* ... */
      if (c === '/' && texto[i + 1] === '*') {
        i += 2;
        while (i < texto.length && !(texto[i] === '*' && texto[i + 1] === '/')) {
          if (texto[i] === '\n') { linea++; i++; inicioLinea = i; } else i++;
        }
        i += 2;
        continue;
      }

      // Directiva DELIMITER: se consume la línea completa
      if (/^delimiter\b/i.test(texto.slice(i))) {
        var lDelim = linea, cDelim = col();
        i += 'delimiter'.length;
        while (i < texto.length && /[ \t]/.test(texto[i])) i++;
        var nuevo = '';
        while (i < texto.length && !/[\s]/.test(texto[i])) { nuevo += texto[i]; i++; }
        if (!nuevo) {
          throw SQLSim.ErrorSQL('DELIMITER necesita un simbolo despues, por ejemplo: DELIMITER //', lDelim);
        }
        delimitador = nuevo;
        empujar('delim', nuevo, lDelim, cDelim);
        continue;
      }

      // El delimitador vigente cierra la sentencia
      if (delimitador !== ';' && texto.startsWith(delimitador, i)) {
        empujar('op', ';', linea, col());
        i += delimitador.length;
        continue;
      }
      if (delimitador === ';' && c === ';') {
        empujar('op', ';', linea, col());
        i++;
        continue;
      }

      // Cadenas 'texto' (con '' como escape)
      if (c === "'" || c === '"') {
        var comilla = c, lC = linea, cC = col();
        i++;
        var s = '';
        while (i < texto.length) {
          if (texto[i] === comilla && texto[i + 1] === comilla) { s += comilla; i += 2; continue; }
          if (texto[i] === comilla) break;
          if (texto[i] === '\n') { linea++; inicioLinea = i + 1; }
          s += texto[i]; i++;
        }
        if (i >= texto.length) {
          throw SQLSim.ErrorSQL('Falta cerrar la comilla de la cadena', lC);
        }
        i++; // comilla de cierre
        empujar('cadena', s, lC, cC);
        continue;
      }

      // Variables de sesión @nombre
      if (c === '@') {
        var lV = linea, cV = col();
        i++;
        var v = '';
        while (i < texto.length && esAlnum(texto[i])) { v += texto[i]; i++; }
        if (!v) throw SQLSim.ErrorSQL('Se esperaba un nombre despues de @', lV);
        empujar('variable', '@' + v, lV, cV);
        continue;
      }

      // Números
      if (esDigito(c)) {
        var lN = linea, cN = col();
        var n = '';
        while (i < texto.length && (esDigito(texto[i]) || texto[i] === '.')) { n += texto[i]; i++; }
        empujar('numero', parseFloat(n), lN, cN);
        continue;
      }

      // Identificadores y palabras reservadas
      if (esLetra(c)) {
        var lI = linea, cI = col();
        var p = '';
        while (i < texto.length && esAlnum(texto[i])) { p += texto[i]; i++; }
        var mayus = p.toUpperCase();
        empujar(ES_PALABRA[mayus] ? 'palabra' : 'ident', ES_PALABRA[mayus] ? mayus : p, lI, cI);
        continue;
      }

      // Identificadores entre acentos graves: `mi tabla`
      if (c === '`') {
        var lB = linea, cB = col();
        i++;
        var b = '';
        while (i < texto.length && texto[i] !== '`') { b += texto[i]; i++; }
        i++;
        empujar('ident', b, lB, cB);
        continue;
      }

      // Operadores
      var encontrado = null;
      for (var k = 0; k < OPERADORES.length; k++) {
        if (texto.startsWith(OPERADORES[k], i)) { encontrado = OPERADORES[k]; break; }
      }
      if (encontrado) {
        empujar('op', encontrado, linea, col());
        i += encontrado.length;
        continue;
      }

      throw SQLSim.ErrorSQL('Caracter no reconocido: "' + c + '"', linea);
    }

    empujar('fin', null, linea, col());
    return tokens;
  }

  SQLSim.tokenizar = tokenizar;
  SQLSim.PALABRAS_RESERVADAS = PALABRAS;

})();
