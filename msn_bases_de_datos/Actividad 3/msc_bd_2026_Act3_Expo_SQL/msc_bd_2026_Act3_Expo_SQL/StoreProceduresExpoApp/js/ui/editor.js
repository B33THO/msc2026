/* ============================================================
   editor.js — el script como lista de instancias de bloque

   Cada línea del editor produce exactamente una línea de SQL, así que
   el número de línea que reporta el motor sirve tal cual para resaltar
   la línea correcta y para señalar errores.
   ============================================================ */

window.SQLSim = window.SQLSim || {};

(function () {
  'use strict';

  var siguienteId = 1;

  function Editor(elLista, elVacio, db) {
    this.lista = elLista;
    this.vacio = elVacio;
    this.db = db;
    this.lineas = [];          // { id, bloque, huecos }
    this.alCambiar = function () {};
  }

  /* ── Modelo ──────────────────────────────────────────────── */

  Editor.prototype.crearInstancia = function (bloqueId) {
    var bloque = SQLSim.bloquePorId(bloqueId);
    if (!bloque) return null;
    var huecos = {};
    bloque.partes.forEach(function (p) {
      if (p.t !== 'hueco') return;
      var pordef = bloque.valoresPorDefecto && bloque.valoresPorDefecto[p.nombre];
      huecos[p.nombre] = pordef !== undefined ? pordef : null;
    });
    return { id: siguienteId++, bloque: bloque, huecos: huecos };
  };

  Editor.prototype.insertar = function (bloqueId, posicion) {
    var inst = this.crearInstancia(bloqueId);
    if (!inst) return null;
    if (posicion === undefined || posicion === null || posicion > this.lineas.length) {
      posicion = this.lineas.length;
    }
    this.lineas.splice(posicion, 0, inst);
    this.render();
    this.alCambiar();
    return inst;
  };

  Editor.prototype.quitar = function (id) {
    var i = this.indiceDe(id);
    if (i === -1) return;
    this.lineas.splice(i, 1);
    this.render();
    this.alCambiar();
  };

  Editor.prototype.mover = function (id, destino) {
    var i = this.indiceDe(id);
    if (i === -1) return;
    var inst = this.lineas.splice(i, 1)[0];
    if (destino > i) destino--;
    if (destino < 0) destino = 0;
    if (destino > this.lineas.length) destino = this.lineas.length;
    this.lineas.splice(destino, 0, inst);
    this.render();
    this.alCambiar();
  };

  Editor.prototype.indiceDe = function (id) {
    for (var i = 0; i < this.lineas.length; i++) {
      if (this.lineas[i].id === id) return i;
    }
    return -1;
  };

  Editor.prototype.vaciar = function () {
    this.lineas = [];
    this.render();
    this.alCambiar();
  };

  /**
   * Instantanea del script actual en el mismo formato que acepta cargar(),
   * para poder guardarlo y reponerlo tal cual. Los huecos se copian: si no,
   * seguir editando la linea mutaria tambien la copia guardada.
   */
  Editor.prototype.serializar = function () {
    return this.lineas.map(function (inst) {
      return { id: inst.bloque.id, huecos: Object.assign({}, inst.huecos) };
    });
  };

  /** Carga un guion inicial: lista de ids de bloque, o {id, huecos} */
  Editor.prototype.cargar = function (guion) {
    var self = this;
    this.lineas = [];
    (guion || []).forEach(function (item) {
      var bloqueId = typeof item === 'string' ? item : item.id;
      var inst = self.crearInstancia(bloqueId);
      if (!inst) return;
      if (typeof item === 'object' && item.huecos) {
        Object.keys(item.huecos).forEach(function (k) { inst.huecos[k] = item.huecos[k]; });
      }
      self.lineas.push(inst);
    });
    this.render();
    this.alCambiar();
  };

  /* ── Sangría automática ──────────────────────────────────── */

  Editor.prototype.calcularNiveles = function () {
    var nivel = 0;
    return this.lineas.map(function (inst) {
      var b = inst.bloque;
      if (b.cierra) nivel = Math.max(0, nivel - 1);
      var mio = nivel;
      if (b.abre) nivel++;
      return mio;
    });
  };

  /* ── Generación del SQL ──────────────────────────────────── */

  Editor.prototype.lineaATexto = function (inst) {
    var huecos = inst.huecos;
    return inst.bloque.partes.map(function (p) {
      if (p.t === 'texto') return p.v;
      var v = huecos[p.nombre];
      return (v === null || v === undefined || v === '') ? '?' : v;
    }).join('');
  };

  /* Sangria de 4 espacios, como se acostumbra formatear MySQL.
     El ancho visual (PX_SANGRIA) se mantiene equivalente. */
  Editor.ESPACIOS_SANGRIA = 4;
  Editor.PX_SANGRIA = 26;

  Editor.prototype.aSQL = function () {
    var niveles = this.calcularNiveles();
    var self = this;
    var sangria = ' '.repeat(Editor.ESPACIOS_SANGRIA);
    return this.lineas.map(function (inst, i) {
      return sangria.repeat(niveles[i]) + self.lineaATexto(inst);
    }).join('\n');
  };

  /** Huecos sin rellenar: [{ linea, bloque, hueco }] */
  Editor.prototype.huecosVacios = function () {
    var faltantes = [];
    this.lineas.forEach(function (inst, i) {
      Object.keys(inst.huecos).forEach(function (nombre) {
        var v = inst.huecos[nombre];
        if (v === null || v === undefined || v === '') {
          faltantes.push({ linea: i + 1, bloque: inst.bloque, hueco: nombre });
        }
      });
    });
    return faltantes;
  };

  /* ── Render ──────────────────────────────────────────────── */

  /* Colorea las palabras reservadas del texto literal de la plantilla */
  function pintarTexto(texto) {
    return texto.replace(/[A-Za-z_][A-Za-z0-9_]*|'[^']*'|\d+(\.\d+)?/g, function (tok) {
      if (tok[0] === "'") return '<span class="txt">' + escapar(tok) + '</span>';
      if (/^\d/.test(tok)) return '<span class="num">' + tok + '</span>';
      var clase = SQLSim.claseDePalabra(tok);
      return clase ? '<span class="' + clase + '">' + tok + '</span>' : escapar(tok);
    });
  }

  function escapar(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  Editor.prototype.render = function () {
    var self = this;
    var niveles = this.calcularNiveles();
    this.lista.innerHTML = '';

    this.lineas.forEach(function (inst, i) {
      var li = document.createElement('li');
      li.className = 'linea';
      li.dataset.id = inst.id;
      li.dataset.indice = i;
      li.draggable = true;

      var cuerpo = document.createElement('span');
      cuerpo.className = 'linea__cuerpo';
      cuerpo.style.paddingLeft = (niveles[i] * Editor.PX_SANGRIA) + 'px';

      inst.bloque.partes.forEach(function (p) {
        if (p.t === 'texto') {
          var s = document.createElement('span');
          s.innerHTML = pintarTexto(p.v);
          cuerpo.appendChild(s);
        } else {
          cuerpo.appendChild(self.crearHueco(inst, p));
        }
      });

      var quitar = document.createElement('button');
      quitar.className = 'linea__quitar';
      quitar.textContent = '×';
      quitar.title = 'Quitar esta linea';
      quitar.addEventListener('click', function (e) {
        e.stopPropagation();
        self.quitar(inst.id);
      });

      li.appendChild(cuerpo);
      li.appendChild(quitar);
      self.lista.appendChild(li);
    });

    this.vacio.classList.toggle('oculto', this.lineas.length > 0);
  };

  /* ── Huecos rellenables ──────────────────────────────────── */

  Editor.prototype.opcionesDeHueco = function (inst, parte) {
    if (parte.clase === 'tabla') return SQLSim.ordenTablas.slice();

    if (parte.clase === 'opcion') {
      return (inst.bloque.opciones && inst.bloque.opciones[parte.nombre]) || [];
    }

    if (parte.clase === 'columna') {
      // Columnas de la tabla que indique el hueco referenciado
      var nombreTabla = parte.refTabla ? inst.huecos[parte.refTabla] : null;
      var canon = nombreTabla ? this.db.resolverTabla(nombreTabla) : null;
      if (canon) return this.db.columnasDe(canon);
      // Sin tabla resuelta: se ofrecen todas las columnas conocidas
      var todas = [];
      SQLSim.ordenTablas.forEach(function (t) {
        SQLSim.esquema[t].columnas.forEach(function (c) {
          if (todas.indexOf(c.nombre) === -1) todas.push(c.nombre);
        });
      });
      return todas;
    }

    return null;   // clase libre: se edita con un input
  };

  Editor.prototype.crearHueco = function (inst, parte) {
    var self = this;
    var valor = inst.huecos[parte.nombre];
    var span = document.createElement('span');
    span.className = 'hueco' + (valor ? ' hueco--lleno' : '');
    span.textContent = valor || parte.nombre;
    span.title = 'Clic para editar (' + parte.clase + ')';
    span.dataset.hueco = parte.nombre;

    span.addEventListener('click', function (e) {
      e.stopPropagation();
      self.editarHueco(span, inst, parte);
    });

    return span;
  };

  Editor.prototype.editarHueco = function (span, inst, parte) {
    var self = this;
    var opciones = this.opcionesDeHueco(inst, parte);
    var valor = inst.huecos[parte.nombre];

    function confirmar(nuevo) {
      inst.huecos[parte.nombre] = (nuevo === '' ? null : nuevo);
      self.render();
      self.alCambiar();
    }

    if (opciones) {
      var sel = document.createElement('select');
      sel.className = 'hueco-select';
      opciones.forEach(function (o) {
        var op = document.createElement('option');
        op.value = o; op.textContent = o;
        if (o === valor) op.selected = true;
        sel.appendChild(op);
      });
      span.replaceWith(sel);
      sel.focus();
      // Si aún no había valor, deja seleccionada la primera opción
      if (!valor && opciones.length) sel.value = opciones[0];
      sel.addEventListener('change', function () { confirmar(sel.value); });
      sel.addEventListener('blur',   function () { confirmar(sel.value); });
      return;
    }

    var input = document.createElement('input');
    input.className = 'hueco-input';
    input.value = valor || '';
    input.placeholder = parte.nombre;
    span.replaceWith(input);
    input.focus();
    input.select();

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); input.blur(); }
      if (e.key === 'Escape') { e.preventDefault(); self.render(); }
    });
    input.addEventListener('blur', function () { confirmar(input.value.trim()); });
  };

  /* ── Marcas de línea ─────────────────────────────────────── */

  Editor.prototype.elementoLinea = function (numeroLinea) {
    return this.lista.querySelectorAll('.linea')[numeroLinea - 1] || null;
  };

  Editor.prototype.marcarActiva = function (numeroLinea) {
    this.limpiarMarcas('linea--activa');
    if (!numeroLinea) return;
    var li = this.elementoLinea(numeroLinea);
    if (li) {
      li.classList.add('linea--activa');
      var cont = li.parentElement.parentElement;   // el .editor con scroll
      if (li.offsetTop < cont.scrollTop ||
          li.offsetTop + li.offsetHeight > cont.scrollTop + cont.clientHeight) {
        cont.scrollTo({ top: Math.max(0, li.offsetTop - 60), behavior: 'smooth' });
      }
    }
  };

  Editor.prototype.marcarError = function (numeroLinea) {
    this.limpiarMarcas('linea--error');
    if (!numeroLinea) return;
    var li = this.elementoLinea(numeroLinea);
    if (li) li.classList.add('linea--error');
  };

  Editor.prototype.limpiarMarcas = function (clase) {
    var clases = clase ? [clase] : ['linea--activa', 'linea--error'];
    this.lista.querySelectorAll('.linea').forEach(function (li) {
      clases.forEach(function (c) { li.classList.remove(c); });
    });
  };

  SQLSim.Editor = Editor;

})();
