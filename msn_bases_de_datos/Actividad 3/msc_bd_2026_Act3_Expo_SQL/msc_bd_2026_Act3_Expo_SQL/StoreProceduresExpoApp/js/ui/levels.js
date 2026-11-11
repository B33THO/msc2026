/* ============================================================
   levels.js (ui) — progresion entre niveles, retos y pistas
   ============================================================ */

window.SQLSim = window.SQLSim || {};

(function () {
  'use strict';

  function Niveles(opciones) {
    this.pasos      = opciones.pasos;
    this.titulo     = opciones.titulo;
    this.desc       = opciones.desc;        // resumen de una linea, en la barra
    this.descAmplia = opciones.descAmplia;  // el mismo texto, en el desplegable
    this.editor     = opciones.editor;
    this.dragdrop   = opciones.dragdrop;
    this.consola    = opciones.consola;
    this.tablas     = opciones.tablas;
    this.alCambiar  = opciones.alCambiar || function () {};

    this.lista      = SQLSim.niveles;
    this.indice     = 0;
    this.completados = {};
    this.pistaActual = 0;

    /* Script guardado de cada nivel visitado, por id. Vive solo en memoria:
       dura lo que dure la sesion y se pierde al recargar la pagina. */
    this.guiones = {};

    this.pintarPasos();
  }

  Niveles.prototype.actual = function () { return this.lista[this.indice]; };

  /* ── Barra de pasos ──────────────────────────────────────── */

  Niveles.prototype.pintarPasos = function () {
    var self = this;
    this.pasos.innerHTML = '';
    this.lista.forEach(function (nivel, i) {
      var b = document.createElement('button');
      b.className = 'paso';
      if (i === self.indice) b.classList.add('paso--actual');
      if (self.completados[nivel.id]) b.classList.add('paso--hecho');
      b.textContent = nivel.id === 'sandbox' ? '∞' : String(i + 1);
      b.title = nivel.titulo;
      b.addEventListener('click', function () { self.ir(i); });
      self.pasos.appendChild(b);
    });
  };

  /* ── Navegación ──────────────────────────────────────────── */

  Niveles.prototype.ir = function (i) {
    if (i < 0 || i >= this.lista.length) return;
    this.recordar();          // no perder el codigo del nivel que se abandona
    this.indice = i;
    this.pistaActual = 0;
    this.cargar();
  };

  /**
   * Guarda el script del nivel actual, este completado o no. Se llama al
   * salir de un nivel, que es el unico momento en que se podria perder:
   * asi un script a medio construir tampoco se pierde por cambiar de
   * nivel sin querer (las flechas ← → navegan entre niveles).
   * Para empezar de cero esta el boton Vaciar.
   */
  Niveles.prototype.recordar = function () {
    var nivel = this.actual();
    if (nivel) this.guiones[nivel.id] = this.editor.serializar();
  };

  Niveles.prototype.siguiente = function () { this.ir(this.indice + 1); };
  Niveles.prototype.anterior  = function () { this.ir(this.indice - 1); };

  /* ── Carga de un nivel ───────────────────────────────────── */

  Niveles.prototype.cargar = function () {
    var nivel = this.actual();

    this.titulo.textContent = nivel.titulo;
    this.desc.innerHTML = nivel.reto;
    this.descAmplia.innerHTML = nivel.reto;

    this.dragdrop.fijarPermitidos(nivel.bloques);

    // Si ya se estuvo en este nivel se repone su script; si no, el guion inicial
    var guardado = this.guiones[nivel.id];
    this.editor.cargar(guardado || nivel.guionInicial);

    this.consola.limpiar();
    this.consola.separador(nivel.titulo);
    if (guardado && guardado.length) {
      this.consola.escribir('Se repuso el script que tenias en este nivel' +
                            (this.completados[nivel.id] ? ', que ya estaba completado' : '') +
                            '. La base de datos si se reinicio, puedes volver a ejecutarlo. ' +
                            'Si prefieres empezar de cero, usa Vaciar.', 'ok');
    }
    if (SQLSim.teoria && SQLSim.teoria[nivel.id]) {
      this.consola.escribir('Pulsa T para volver a abrir la teoria de este nivel.', 'tx');
    }
    if (nivel.explicacion) this.consola.escribir(nivel.explicacion, 'info');

    this.tablas.limpiarInconsistencia();
    this.pintarPasos();
    this.alCambiar(nivel);
  };

  /* ── Pistas ──────────────────────────────────────────────── */

  Niveles.prototype.pista = function () {
    var nivel = this.actual();
    if (!nivel.pistas || !nivel.pistas.length) return;
    var p = nivel.pistas[Math.min(this.pistaActual, nivel.pistas.length - 1)];
    this.consola.escribir('Pista: ' + p, 'aviso');
    if (this.pistaActual < nivel.pistas.length - 1) this.pistaActual++;
  };

  /* ── Validación tras ejecutar ────────────────────────────── */

  Niveles.prototype.evaluar = function (db, eventos) {
    var nivel = this.actual();

    // Marca visual de estado inconsistente (nivel del desastre)
    if (nivel.inconsistencia) {
      this.tablas.marcarInconsistencia(nivel.inconsistencia(db));
    }

    if (!nivel.objetivo) return null;   // sandbox

    var resultado;
    try {
      resultado = nivel.objetivo({ db: db, eventos: eventos });
    } catch (e) {
      this.consola.escribir('No se pudo validar el objetivo: ' + e.message, 'error');
      return null;
    }

    if (resultado.ok) {
      var recienCompletado = !this.completados[nivel.id];
      this.completados[nivel.id] = true;
      // El script no se guarda aqui: recordar() ya lo hace al salir del nivel,
      // que es el unico punto donde se perderia.
      this.consola.escribir('Objetivo cumplido. ' + resultado.mensaje, 'ok');
      this.pintarPasos();
      if (recienCompletado) {
        var boton = this.pasos.children[this.indice];
        if (boton) {
          boton.classList.add('paso--acaba-de-completarse');
          setTimeout(function () { boton.classList.remove('paso--acaba-de-completarse'); }, 600);
        }
      }
    } else {
      this.consola.escribir('Aun no: ' + resultado.mensaje, 'aviso');
    }

    return resultado;
  };

  SQLSim.Niveles = Niveles;

})();
