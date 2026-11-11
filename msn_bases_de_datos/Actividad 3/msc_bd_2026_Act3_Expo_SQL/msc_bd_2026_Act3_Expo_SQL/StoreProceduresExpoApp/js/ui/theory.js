/* ============================================================
   theory.js (ui) — pantalla de teoría a pantalla completa

   Se abre automáticamente la PRIMERA vez que se entra a cada nivel, y
   a demanda con el botón "Teoría" o la tecla T. Se cierra y quedas en
   el ejercicio.
   ============================================================ */

window.SQLSim = window.SQLSim || {};

(function () {
  'use strict';

  function Teoria(elOverlay, elCaja) {
    this.el = elOverlay;
    this.caja = elCaja;
    this.vistos = {};        // niveles cuya teoría ya se mostró sola
    this.idActual = null;
    this.alCerrar = function () {};

    var self = this;
    this.el.addEventListener('click', function (e) {
      if (e.target === self.el) self.cerrar();
    });
  }

  Teoria.prototype.visible = function () {
    return !this.el.classList.contains('oculto');
  };

  Teoria.prototype.hayPara = function (id) {
    return !!SQLSim.teoria[id];
  };

  /* Se abre sola solo la primera visita: al volver a un nivel para
     corregir algo, no debe estorbar. */
  Teoria.prototype.mostrarSiEsNueva = function (id) {
    if (!this.hayPara(id) || this.vistos[id]) return false;
    this.mostrar(id);
    return true;
  };

  Teoria.prototype.mostrar = function (id) {
    var datos = SQLSim.teoria[id];
    if (!datos) return;
    this.idActual = id;
    this.vistos[id] = true;
    this.caja.innerHTML = '';
    this.caja.appendChild(construir(datos));
    this.el.classList.remove('oculto');

    // Se enfoca el cuerpo, no el boton: así las flechas y AvPag desplazan
    // el texto en vez de no hacer nada.
    var cuerpo = this.caja.querySelector('.teoria__cuerpo');
    if (cuerpo) {
      cuerpo.scrollTop = 0;
      cuerpo.focus();
    }
    this.vigilarDesplazamiento();
  };

  /* Muestra el aviso de "hay mas contenido" mientras quede algo por ver */
  Teoria.prototype.vigilarDesplazamiento = function () {
    var cuerpo = this.caja.querySelector('.teoria__cuerpo');
    var aviso = this.caja.querySelector('.teoria__mas');
    if (!cuerpo || !aviso) return;

    function actualizar() {
      var restante = cuerpo.scrollHeight - cuerpo.scrollTop - cuerpo.clientHeight;
      aviso.classList.toggle('oculto', restante <= 8);
    }

    cuerpo.addEventListener('scroll', actualizar);
    // En este instante el navegador aún no ha calculado la altura real
    requestAnimationFrame(actualizar);
  };

  /**
   * Avanza una pantalla de texto. Devuelve true si de verdad quedaba algo
   * por ver; false si ya estaba al final (y entonces toca cerrar).
   * Con esto la barra espaciadora se comporta como un paginador.
   */
  Teoria.prototype.desplazarSiFalta = function () {
    var cuerpo = this.caja.querySelector('.teoria__cuerpo');
    if (!cuerpo) return false;
    var restante = cuerpo.scrollHeight - cuerpo.scrollTop - cuerpo.clientHeight;
    if (restante <= 8) return false;
    cuerpo.scrollBy({ top: cuerpo.clientHeight * 0.85, behavior: 'smooth' });
    return true;
  };

  Teoria.prototype.cerrar = function () {
    if (!this.visible()) return;
    this.el.classList.add('oculto');
    this.alCerrar();
  };

  Teoria.prototype.alternar = function (id) {
    if (this.visible()) this.cerrar();
    else this.mostrar(id);
  };

  /* ── Construcción del contenido ──────────────────────────── */

  function elem(tag, clase, html) {
    var e = document.createElement(tag);
    if (clase) e.className = clase;
    if (html !== undefined) e.innerHTML = html;
    return e;
  }

  function construir(d) {
    var frag = document.createDocumentFragment();

    /* Cabecera */
    var cab = elem('header', 'teoria__cabecera');
    cab.appendChild(elem('span', 'teoria__numero', d.numero));
    var textos = elem('div', 'teoria__titulos');
    textos.appendChild(elem('h2', 'teoria__titulo', d.titulo));
    if (d.subtitulo) textos.appendChild(elem('p', 'teoria__subtitulo', d.subtitulo));
    cab.appendChild(textos);
    if (d.destacado) cab.appendChild(elem('span', 'teoria__insignia', 'clave'));
    frag.appendChild(cab);

    /* Cuerpo en dos columnas: prosa a la izquierda, código a la derecha.
       tabIndex lo vuelve enfocable para poder desplazarlo con el teclado. */
    var cuerpo = elem('div', 'teoria__cuerpo');
    cuerpo.tabIndex = 0;

    var izq = elem('div', 'teoria__prosa');
    (d.parrafos || []).forEach(function (p) {
      izq.appendChild(elem('p', null, p));
    });
    if (d.diagrama) izq.appendChild(diagrama(d.diagrama));
    cuerpo.appendChild(izq);

    var der = elem('div', 'teoria__lateral');
    if (d.codigo) {
      der.appendChild(elem('h3', 'teoria__sub', 'Ejemplo'));
      var pre = elem('pre', 'teoria__codigo');
      pre.innerHTML = SQLSim.resaltarSQL(d.codigo);
      der.appendChild(pre);
    }
    if (d.avisos && d.avisos.length) {
      der.appendChild(elem('h3', 'teoria__sub', d.avisosTitulo || 'Errores comunes'));
      d.avisos.forEach(function (a) {
        var caja = elem('div', 'aviso');
        caja.appendChild(elem('strong', 'aviso__titulo', a.titulo));
        caja.appendChild(elem('p', 'aviso__texto', a.texto));
        der.appendChild(caja);
      });
    }
    if (d.comoUsar && d.comoUsar.length) {
      der.appendChild(elem('h3', 'teoria__sub', 'Cómo moverte'));
      var ul = elem('ul', 'teoria__lista');
      d.comoUsar.forEach(function (t) { ul.appendChild(elem('li', null, t)); });
      der.appendChild(ul);
    }
    cuerpo.appendChild(der);
    frag.appendChild(cuerpo);

    /* Pie */
    var pie = elem('footer', 'teoria__pie');
    pie.appendChild(elem('span', 'teoria__mas oculto',
      '&darr; Sigue hacia abajo, hay m&aacute;s'));
    pie.appendChild(elem('span', 'teoria__atajo',
      'Pulsa <kbd>T</kbd> para volver a abrir esta pantalla'));
    var btn = elem('button', 'btn btn--primario teoria__ir', 'Ir al ejercicio &rarr;');
    pie.appendChild(btn);
    frag.appendChild(pie);

    return frag;
  }

  /* ── Diagramas ───────────────────────────────────────────── */

  function diagrama(d) {
    var caja = elem('figure', 'diagrama');
    if (d.tipo === 'flujo') caja.appendChild(diagramaFlujo(d));
    else if (d.tipo === 'linea') caja.appendChild(diagramaLinea(d));
    if (d.pie) caja.appendChild(elem('figcaption', 'diagrama__pie', d.pie));
    return caja;
  }

  function diagramaFlujo(d) {
    var fila = elem('div', 'flujo');
    var conector = d.conector || '→';

    d.nodos.forEach(function (n, i) {
      if (i > 0) fila.appendChild(elem('span', 'flujo__conector', conector));
      var nodo = elem('div', 'flujo__nodo' + (n.clase ? ' flujo__nodo--' + n.clase : ''));
      // El salto de linea en el texto se respeta con white-space: pre-line
      nodo.appendChild(elem('span', 'flujo__texto', n.texto.replace(/\n/g, '<br>')));
      if (n.sub) nodo.appendChild(elem('span', 'flujo__sub', n.sub));
      fila.appendChild(nodo);
    });

    return fila;
  }

  function diagramaLinea(d) {
    var cont = elem('div', 'linea-t');

    d.pasos.forEach(function (p, i) {
      if (i > 0) cont.appendChild(elem('span', 'linea-t__union', ''));
      cont.appendChild(paso(p));
    });

    if (d.ramas && d.ramas.length) {
      var bif = elem('div', 'linea-t__bifurcacion');
      d.ramas.forEach(function (r) {
        var rama = elem('div', 'linea-t__rama');
        rama.appendChild(elem('span', 'linea-t__union linea-t__union--rama', ''));
        rama.appendChild(paso(r));
        bif.appendChild(rama);
      });
      cont.appendChild(bif);
    }

    return cont;
  }

  function paso(p) {
    var e = elem('div', 'linea-t__paso linea-t__paso--' + (p.estado || 'neutro'));
    e.appendChild(elem('span', 'linea-t__texto', p.texto));
    if (p.nota) e.appendChild(elem('span', 'linea-t__nota', p.nota));
    return e;
  }

  SQLSim.Teoria = Teoria;

})();
