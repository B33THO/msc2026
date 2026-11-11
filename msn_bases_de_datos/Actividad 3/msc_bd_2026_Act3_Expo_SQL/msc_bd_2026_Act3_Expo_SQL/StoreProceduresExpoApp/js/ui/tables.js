/* ============================================================
   tables.js — pinta las tablas y anima los eventos del intérprete

   Reconciliación por identidad de fila: cada objeto-fila del motor se
   asocia a su <tr> mediante un WeakMap. Al sincronizar sólo se mueven
   los <tr> que realmente cambiaron de posición, de modo que las
   animaciones en curso no se reinician.
   ============================================================ */

window.SQLSim = window.SQLSim || {};

(function () {
  'use strict';

  function Tablas(contenedor, db) {
    this.el = contenedor;
    this.db = db;
    this.mapa = new WeakMap();   // fila (objeto) -> <tr>
    this.cuerpos = {};           // nombre de tabla -> <tbody>
    this.conteos = {};           // nombre de tabla -> <span> del conteo
    this.bloques = {};           // nombre de tabla -> contenedor del bloque
    this.ritmo = 400;
  }

  Tablas.prototype.fijarRitmo = function (ms) { this.ritmo = ms; };

  /* ── Construcción inicial ────────────────────────────────── */

  Tablas.prototype.construir = function () {
    var self = this;
    this.el.innerHTML = '';
    this.mapa = new WeakMap();
    this.cuerpos = {};
    this.conteos = {};
    this.bloques = {};

    SQLSim.ordenTablas.forEach(function (nombre) {
      var bloque = document.createElement('div');
      bloque.className = 'tabla-bloque';

      var titulo = document.createElement('div');
      titulo.className = 'tabla-bloque__nombre';
      titulo.innerHTML = 'Tabla: ' + nombre + ' <span class="tabla-bloque__conteo"></span>';
      bloque.appendChild(titulo);

      var tabla = document.createElement('table');
      tabla.className = 'datos';

      var thead = document.createElement('thead');
      var trh = document.createElement('tr');
      self.db.columnasDe(nombre).forEach(function (c) {
        var th = document.createElement('th');
        th.textContent = c;
        trh.appendChild(th);
      });
      thead.appendChild(trh);
      tabla.appendChild(thead);

      var tbody = document.createElement('tbody');
      tabla.appendChild(tbody);

      // La tabla se desplaza dentro de su propio contenedor: el panel nunca
      // desborda horizontalmente aunque la columna sea angosta.
      var scroll = document.createElement('div');
      scroll.className = 'tabla-bloque__scroll';
      scroll.appendChild(tabla);
      bloque.appendChild(scroll);
      self.el.appendChild(bloque);

      self.cuerpos[nombre] = tbody;
      self.conteos[nombre] = titulo.querySelector('.tabla-bloque__conteo');
      self.bloques[nombre] = bloque;
    });

    this.sincronizarTodo();
  };

  /* ── Reconciliación ──────────────────────────────────────── */

  Tablas.prototype.crearFila = function (nombre, fila) {
    var tr = document.createElement('tr');
    this.db.columnasDe(nombre).forEach(function (c) {
      var td = document.createElement('td');
      td.dataset.col = c;
      td.textContent = SQLSim.formatearValor(fila[c]);
      tr.appendChild(td);
    });
    this.mapa.set(fila, tr);
    return tr;
  };

  Tablas.prototype.sincronizar = function (nombre) {
    var tbody = this.cuerpos[nombre];
    if (!tbody) return;
    var deseadas = this.db.filas(nombre);
    var self = this;

    // Las filas que se están desvaneciendo no participan del orden
    var salientes = Array.prototype.filter.call(tbody.children, function (tr) {
      return tr.dataset.saliendo === '1';
    });

    var actuales = Array.prototype.filter.call(tbody.children, function (tr) {
      return tr.dataset.saliendo !== '1' && !tr.classList.contains('sin-datos');
    });

    // Quitar los <tr> cuyas filas ya no existen
    actuales.forEach(function (tr) {
      if (deseadas.indexOf(tr._fila) === -1) tr.remove();
    });

    // Colocar cada fila en su posición, moviendo sólo lo necesario
    deseadas.forEach(function (fila, i) {
      var tr = self.mapa.get(fila);
      if (!tr || !tr.isConnected) {
        tr = self.crearFila(nombre, fila);
        tr._fila = fila;
      }
      var enPosicion = tbody.children[i];
      if (enPosicion !== tr) tbody.insertBefore(tr, enPosicion || null);
      tr._fila = fila;
    });

    // Reanexar al final las filas que aún se están yendo
    salientes.forEach(function (tr) { tbody.appendChild(tr); });

    // Mensaje de tabla vacía
    var vacio = tbody.querySelector('.sin-datos');
    if (deseadas.length === 0 && !salientes.length) {
      if (!vacio) {
        var trv = document.createElement('tr');
        trv.className = 'sin-datos';
        var td = document.createElement('td');
        td.className = 'vacio';
        td.colSpan = this.db.columnasDe(nombre).length;
        td.textContent = 'sin registros';
        trv.appendChild(td);
        tbody.appendChild(trv);
      }
    } else if (vacio) {
      vacio.remove();
    }

    this.conteos[nombre].textContent = '(' + deseadas.length + ')';
  };

  Tablas.prototype.sincronizarTodo = function () {
    var self = this;
    SQLSim.ordenTablas.forEach(function (n) { self.sincronizar(n); });
  };

  /* Refresca el texto de todas las celdas de una fila, sin animar */
  Tablas.prototype.refrescarFila = function (nombre, fila) {
    var tr = this.mapa.get(fila);
    if (!tr) return;
    this.db.columnasDe(nombre).forEach(function (c) {
      var td = tr.querySelector('td[data-col="' + c + '"]');
      if (td && !td.dataset.animando) td.textContent = SQLSim.formatearValor(fila[c]);
    });
  };

  /* ── Animación de eventos ────────────────────────────────── */

  Tablas.prototype.aplicarEvento = function (ev) {
    switch (ev.tipo) {

      case 'row-insert': {
        this.sincronizar(ev.tabla);
        var tr = this.mapa.get(ev.fila);
        if (tr) {
          tr.classList.remove('fila--insertada', 'fila--rebobinada');
          void tr.offsetWidth;   // reinicia la animación
          tr.classList.add(ev.deshaciendo ? 'fila--rebobinada' : 'fila--insertada');
        }
        this.destacar(ev.tabla);
        break;
      }

      case 'row-update': {
        var trU = this.mapa.get(ev.fila);
        if (!trU) { this.sincronizar(ev.tabla); trU = this.mapa.get(ev.fila); }
        if (trU) this.animarCambio(trU, ev);
        this.destacar(ev.tabla);
        break;
      }

      case 'row-delete': {
        var trD = this.mapa.get(ev.fila);
        if (trD) {
          trD.dataset.saliendo = '1';
          trD.classList.add('fila--borrada');
          var self = this, tabla = ev.tabla;
          setTimeout(function () {
            trD.remove();
            self.sincronizar(tabla);
          }, Math.max(120, this.ritmo * 1.6));
        }
        this.conteos[ev.tabla].textContent = '(' + this.db.filas(ev.tabla).length + ')';
        this.destacar(ev.tabla);
        break;
      }
    }
  };

  /* Muestra el valor anterior tachado desvaneciéndose junto al nuevo */
  Tablas.prototype.animarCambio = function (tr, ev) {
    var self = this;
    Object.keys(ev.despues).forEach(function (col) {
      var td = tr.querySelector('td[data-col="' + col + '"]');
      if (!td) return;

      var viejo = SQLSim.formatearValor(ev.antes[col]);
      var nuevo = SQLSim.formatearValor(ev.despues[col]);

      if (viejo === nuevo) return;   // nada que mostrar

      td.dataset.animando = '1';
      td.innerHTML = '';
      var spanViejo = document.createElement('span');
      spanViejo.className = 'valor-viejo';
      spanViejo.textContent = viejo;
      var spanNuevo = document.createElement('span');
      spanNuevo.className = 'valor-nuevo';
      spanNuevo.textContent = nuevo;
      td.appendChild(spanViejo);
      td.appendChild(spanNuevo);

      td.classList.remove('celda--cambiada');
      void td.offsetWidth;
      td.classList.add('celda--cambiada');

      setTimeout(function () {
        delete td.dataset.animando;
        td.textContent = SQLSim.formatearValor(ev.fila[col]);
        td.classList.remove('celda--cambiada');
      }, Math.max(160, self.ritmo * 2));
    });

    if (ev.deshaciendo) {
      tr.classList.remove('fila--rebobinada');
      void tr.offsetWidth;
      tr.classList.add('fila--rebobinada');
    }
  };

  /* Deja el panel de la tabla tocada visible si estaba fuera de vista */
  Tablas.prototype.destacar = function (nombre) {
    var bloque = this.bloques[nombre];
    if (!bloque) return;
    var cont = this.el;
    var arriba = bloque.offsetTop;
    var abajo = arriba + bloque.offsetHeight;
    if (arriba < cont.scrollTop || abajo > cont.scrollTop + cont.clientHeight) {
      cont.scrollTo({ top: Math.max(0, arriba - 12), behavior: 'smooth' });
    }
  };

  /* ── Carteles de COMMIT / ROLLBACK ───────────────────────── */

  Tablas.prototype.cartel = function (texto, clase) {
    var panel = this.el.closest('.panel');
    if (!panel) return;
    var c = document.createElement('div');
    c.className = 'cartel cartel--' + clase;
    c.textContent = texto;
    panel.appendChild(c);
    setTimeout(function () { c.remove(); }, Math.max(700, this.ritmo * 3.5));
  };

  /* ── Marca de estado inconsistente (nivel del desastre) ──── */

  Tablas.prototype.marcarInconsistencia = function (nombres) {
    var self = this;
    SQLSim.ordenTablas.forEach(function (n) {
      self.bloques[n].classList.toggle('tabla-bloque--inconsistente', nombres.indexOf(n) !== -1);
    });
  };

  Tablas.prototype.limpiarInconsistencia = function () {
    this.marcarInconsistencia([]);
  };

  SQLSim.Tablas = Tablas;

})();
