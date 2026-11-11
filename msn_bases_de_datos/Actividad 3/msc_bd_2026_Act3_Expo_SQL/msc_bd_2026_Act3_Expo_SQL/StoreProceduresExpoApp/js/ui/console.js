/* ============================================================
   console.js — salida de consola con estilo por severidad
   ============================================================ */

window.SQLSim = window.SQLSim || {};

(function () {
  'use strict';

  function Consola(elemento, led) {
    this.el = elemento;
    this.led = led;
  }

  Consola.prototype.limpiar = function () {
    this.el.innerHTML = '';
    this.estado('ok');
  };

  /** nivel ∈ ok | info | aviso | error | tx
      tabular: mantiene la alineacion (no envuelve) para filas de resultado */
  Consola.prototype.escribir = function (texto, nivel, tabular) {
    var linea = document.createElement('div');
    linea.className = 'consola__linea consola__linea--' + (nivel || 'info') +
                      (tabular ? ' consola__linea--tabla' : '');
    linea.textContent = texto;
    this.el.appendChild(linea);
    this.el.scrollTop = this.el.scrollHeight;
    if (nivel === 'error') this.estado('error');
  };

  Consola.prototype.separador = function (titulo) {
    var linea = document.createElement('div');
    linea.className = 'consola__linea consola__linea--info consola__linea--tabla';
    linea.style.opacity = '0.55';
    linea.style.marginTop = '6px';
    linea.textContent = '── ' + titulo + ' ' + '─'.repeat(Math.max(0, 18 - titulo.length));
    this.el.appendChild(linea);
    this.el.scrollTop = this.el.scrollHeight;
  };

  /** Pinta el resultado de un SELECT como tabla de texto alineada */
  Consola.prototype.resultado = function (columnas, filas) {
    if (!filas.length) {
      this.escribir('(0 filas)', 'info');
      return;
    }
    var fmt = SQLSim.formatearValor;
    var anchos = columnas.map(function (c) { return c.length; });
    filas.forEach(function (f) {
      columnas.forEach(function (c, i) {
        anchos[i] = Math.max(anchos[i], fmt(f[c]).length);
      });
    });

    var rellenar = function (s, n) { return s + ' '.repeat(Math.max(0, n - s.length)); };

    this.escribir(columnas.map(function (c, i) { return rellenar(c, anchos[i]); }).join('  '), 'info', true);
    this.escribir(anchos.map(function (a) { return '─'.repeat(a); }).join('  '), 'info', true);
    var self = this;
    filas.forEach(function (f) {
      self.escribir(columnas.map(function (c, i) { return rellenar(fmt(f[c]), anchos[i]); }).join('  '), 'ok', true);
    });
    this.escribir('(' + filas.length + ' fila' + (filas.length === 1 ? '' : 's') + ')', 'info');
  };

  /** estado ∈ ok | error | trabajando */
  Consola.prototype.estado = function (estado) {
    if (!this.led) return;
    this.led.className = 'led' + (estado === 'ok' ? '' : ' led--' + estado);
  };

  SQLSim.Consola = Consola;

})();
