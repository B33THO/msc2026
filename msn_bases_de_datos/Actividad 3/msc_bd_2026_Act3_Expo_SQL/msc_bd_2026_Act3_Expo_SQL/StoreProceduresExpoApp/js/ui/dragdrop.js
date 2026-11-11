/* ============================================================
   dragdrop.js — arrastre desde el toolbox y reordenamiento

   La API de arrastre de HTML5 es caprichosa y en una exposición en
   vivo no conviene depender sólo de ella: cada bloque del toolbox
   responde también al clic, insertando al final del script.
   ============================================================ */

window.SQLSim = window.SQLSim || {};

(function () {
  'use strict';

  function DragDrop(elToolbox, elEditor, elLista, editor) {
    this.toolbox = elToolbox;
    this.zona = elEditor;
    this.lista = elLista;
    this.editor = editor;
    this.marca = null;          // indicador visual de dónde caería
    this.arrastrandoId = null;  // id de línea si se reordena
    this.permitidos = null;     // null = todos
    this.conectar();
  }

  /* ── Toolbox ─────────────────────────────────────────────── */

  /** ids permitidos en el nivel actual; null = sin restricción */
  DragDrop.prototype.fijarPermitidos = function (ids) {
    this.permitidos = ids && ids.length ? ids : null;
    this.pintarToolbox();
  };

  DragDrop.prototype.pintarToolbox = function () {
    var self = this;
    this.toolbox.innerHTML = '';

    SQLSim.gruposBloques.forEach(function (grupo) {
      var ids = grupo.ids.filter(function (id) {
        return !self.permitidos || self.permitidos.indexOf(id) !== -1;
      });
      if (!ids.length) return;

      var titulo = document.createElement('div');
      titulo.className = 'toolbox__grupo';
      titulo.textContent = grupo.titulo;
      self.toolbox.appendChild(titulo);

      ids.forEach(function (id) {
        var bloque = SQLSim.bloquePorId(id);
        if (!bloque) return;

        var btn = document.createElement('button');
        btn.className = 'bloque bloque--' + bloque.categoria;
        btn.draggable = true;
        btn.dataset.bloque = id;
        btn.textContent = etiqueta(bloque);
        btn.title = 'Arrastra al editor o haz clic para agregar al final';

        btn.addEventListener('dragstart', function (e) {
          e.dataTransfer.setData('text/plain', 'bloque:' + id);
          e.dataTransfer.effectAllowed = 'copy';
          btn.classList.add('bloque--arrastrando');
        });
        btn.addEventListener('dragend', function () {
          btn.classList.remove('bloque--arrastrando');
          self.quitarMarca();
        });
        btn.addEventListener('click', function () {
          self.editor.insertar(id, self.editor.lineas.length);
        });

        self.toolbox.appendChild(btn);
      });
    });
  };

  /* Texto corto y legible para el botón del toolbox */
  function etiqueta(bloque) {
    if (bloque.etiquetaCorta) return bloque.etiquetaCorta;
    return bloque.plantilla
      .replace(/\{([a-z0-9_]+):[a-z]+(?::[a-z0-9_]+)?\}/gi, '…')
      .replace(/…(,\s*…)+/g, '…')      // colapsa listas de huecos
      .replace(/\s+/g, ' ')
      .trim();
  }

  /* ── Zona de suelte ──────────────────────────────────────── */

  DragDrop.prototype.conectar = function () {
    var self = this;

    // Reordenar: se arranca desde una línea ya colocada
    this.lista.addEventListener('dragstart', function (e) {
      var li = e.target.closest('.linea');
      if (!li) return;
      self.arrastrandoId = Number(li.dataset.id);
      e.dataTransfer.setData('text/plain', 'linea:' + self.arrastrandoId);
      e.dataTransfer.effectAllowed = 'move';
      li.classList.add('bloque--arrastrando');
    });

    this.lista.addEventListener('dragend', function (e) {
      var li = e.target.closest('.linea');
      if (li) li.classList.remove('bloque--arrastrando');
      self.arrastrandoId = null;
      self.quitarMarca();
    });

    this.zona.addEventListener('dragover', function (e) {
      e.preventDefault();
      e.dataTransfer.dropEffect = self.arrastrandoId ? 'move' : 'copy';
      self.zona.classList.add('editor--recibiendo');
      self.mostrarMarca(self.posicionDeSuelte(e.clientY));
    });

    this.zona.addEventListener('dragleave', function (e) {
      if (!self.zona.contains(e.relatedTarget)) {
        self.zona.classList.remove('editor--recibiendo');
        self.quitarMarca();
      }
    });

    this.zona.addEventListener('drop', function (e) {
      e.preventDefault();
      self.zona.classList.remove('editor--recibiendo');
      var destino = self.posicionDeSuelte(e.clientY);
      self.quitarMarca();

      var dato = e.dataTransfer.getData('text/plain') || '';
      if (dato.indexOf('bloque:') === 0) {
        self.editor.insertar(dato.slice(7), destino);
      } else if (dato.indexOf('linea:') === 0) {
        self.editor.mover(Number(dato.slice(6)), destino);
      }
      self.arrastrandoId = null;
    });

    this.pintarToolbox();
  };

  /** Índice donde caería el bloque según la posición vertical del cursor */
  DragDrop.prototype.posicionDeSuelte = function (y) {
    // El marcador vive dentro de la lista, así que se excluye del conteo
    var lineas = this.lista.querySelectorAll('.linea');
    for (var i = 0; i < lineas.length; i++) {
      var r = lineas[i].getBoundingClientRect();
      if (y < r.top + r.height / 2) return i;
    }
    return lineas.length;
  };

  DragDrop.prototype.mostrarMarca = function (indice) {
    if (!this.marca) {
      this.marca = document.createElement('div');
      this.marca.className = 'marca-suelte';
    }
    var ref = this.lista.children[indice];
    if (ref) this.lista.insertBefore(this.marca, ref);
    else this.lista.appendChild(this.marca);
  };

  DragDrop.prototype.quitarMarca = function () {
    if (this.marca && this.marca.parentElement) this.marca.remove();
  };

  SQLSim.DragDrop = DragDrop;

})();
