/* ============================================================
   app.js — arranque y cableado

   Aqui vive el consumidor del generador de eventos: avanza el
   interprete a un ritmo controlado, traduce cada evento a una
   animacion y, al terminar, valida el objetivo del nivel.
   ============================================================ */

(function () {
  'use strict';

  var $ = function (id) { return document.getElementById(id); };

  document.addEventListener('DOMContentLoaded', function () {

    /* ── Piezas ───────────────────────────────────────────── */

    var db      = new SQLSim.BaseDeDatos(SQLSim.esquema);
    var consola = new SQLSim.Consola($('consola'), $('led-consola'));
    var tablas  = new SQLSim.Tablas($('tablas'), db);
    var editor  = new SQLSim.Editor($('editor-lineas'), $('editor-vacio'), db);
    var dnd     = new SQLSim.DragDrop($('toolbox'), $('editor'), $('editor-lineas'), editor);
    var teoria  = new SQLSim.Teoria($('teoria'), $('teoria-caja'));

    tablas.construir();

    // La portada tapa la aplicacion hasta que se entra al simulador
    var portadaVisible = true;

    var niveles = new SQLSim.Niveles({
      pasos: $('pasos'), titulo: $('reto-titulo'),
      desc: $('reto-desc'), descAmplia: $('reto-objetivo'),
      editor: editor, dragdrop: dnd, consola: consola, tablas: tablas,
      alCambiar: function (nivel) {
        reiniciarBD(false);
        // El desplegable no se queda abierto tapando el tablero del nivel nuevo
        alternarObjetivo(false);
        // La teoria se abre sola la primera vez que se entra a cada nivel.
        // Con la portada puesta se aplaza: si no, quedaria abierta detras.
        if (!portadaVisible) teoria.mostrarSiEsNueva(nivel.id);
        $('btn-teoria').disabled = !teoria.hayPara(nivel.id);
      }
    });

    /* ── Desplegable del objetivo ─────────────────────────── */

    // Sin argumento alterna; con uno fuerza el estado.
    function alternarObjetivo(abrir) {
      var pie = $('reto');
      var abierto = abrir === undefined ? !pie.classList.contains('reto--abierto') : abrir;
      pie.classList.toggle('reto--abierto', abierto);
      $('btn-reto').setAttribute('aria-expanded', String(abierto));
    }

    /* ── Portada ──────────────────────────────────────────── */

    /* Se retira con una transicion y recien entonces se muestra la teoria
       del nivel 1, que quedo aplazada. Para volver a verla: recargar. */
    function cerrarPortada() {
      if (!portadaVisible) return;
      portadaVisible = false;

      var portada = $('portada');
      var sinMovimiento = window.matchMedia &&
                          window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      if (sinMovimiento) {
        portada.classList.add('oculto');
      } else {
        portada.classList.add('portada--saliendo');
        setTimeout(function () { portada.classList.add('oculto'); }, 420);
      }

      teoria.mostrarSiEsNueva(niveles.actual().id);
    }

    $('btn-entrar').addEventListener('click', cerrarPortada);
    $('portada').addEventListener('click', cerrarPortada);

    /* El titulo de la cabecera vuelve a mostrar la portada en cualquier momento */
    function abrirPortada() {
      if (portadaVisible) return;
      portadaVisible = true;
      var portada = $('portada');
      portada.classList.remove('portada--saliendo', 'oculto');
    }

    $('btn-portada').addEventListener('click', abrirPortada);

    /* ── Estado de ejecucion ──────────────────────────────── */

    var ejecutando = false;
    var pasoAPaso  = false;
    var esperandoPaso = null;   // resolve() pendiente en modo paso a paso

    function ritmo() {
      var v = Number($('sel-velocidad').value);
      if (v === 0) return 0;      // instantaneo
      return 400 / v;             // 1x = 400ms, 2x = 200ms
    }

    function aplicarRitmo() {
      var ms = ritmo();
      document.documentElement.style.setProperty('--ritmo', (ms || 1) + 'ms');
      tablas.fijarRitmo(ms || 1);
    }

    function esperar(factor) {
      var ms = ritmo() * (factor === undefined ? 1 : factor);

      if (pasoAPaso) {
        $('btn-paso').disabled = false;
        return new Promise(function (resolve) { esperandoPaso = resolve; });
      }
      if (!ms) return Promise.resolve();
      return new Promise(function (resolve) { setTimeout(resolve, ms); });
    }

    /* ── Reinicio de la base ──────────────────────────────── */

    function reiniciarBD(avisar) {
      db.reiniciar();
      tablas.construir();
      tablas.limpiarInconsistencia();
      $('insignia-tx').classList.add('oculto');
      editor.limpiarMarcas();
      if (avisar) consola.escribir('Base de datos restaurada a su estado inicial.', 'info');
    }

    /* ── Verificacion de sintaxis ─────────────────────────── */

    function verificar(silencioso) {
      editor.limpiarMarcas('linea--error');

      if (!editor.lineas.length) {
        if (!silencioso) consola.escribir('El editor esta vacio: arrastra algunos bloques primero.', 'aviso');
        return null;
      }

      // Los huecos sin rellenar se reportan antes de intentar parsear
      var faltantes = editor.huecosVacios();
      if (faltantes.length) {
        var f = faltantes[0];
        editor.marcarError(f.linea);
        consola.escribir('Linea ' + f.linea + ': falta rellenar el hueco "' + f.hueco +
                         '"' + (faltantes.length > 1 ? ' (y ' + (faltantes.length - 1) + ' mas).' : '.'),
                         'error');
        return null;
      }

      var sql = editor.aSQL();
      try {
        var ast = SQLSim.parsear(sql);
        if (!silencioso) {
          consola.escribir('Sintaxis correcta. El script tiene ' + editor.lineas.length + ' linea(s).', 'ok');
          consola.estado('ok');
        }
        return ast;
      } catch (e) {
        if (e.linea) editor.marcarError(e.linea);
        consola.escribir((e.linea ? 'Linea ' + e.linea + ': ' : '') + e.message, 'error');
        return null;
      }
    }

    /* ── Ejecucion ────────────────────────────────────────── */

    function ejecutar() {
      if (ejecutando) return;

      var ast = verificar(true);
      if (!ast) return;

      ejecutando = true;
      aplicarRitmo();
      $('btn-ejecutar').disabled = true;
      $('btn-verificar').disabled = true;
      consola.separador('Ejecucion');
      consola.estado('trabajando');
      tablas.limpiarInconsistencia();
      editor.limpiarMarcas();

      var eventos = [];
      var generador = SQLSim.ejecutar(db, ast);

      bucle();

      function bucle() {
        var paso;
        try {
          paso = generador.next();
        } catch (e) {
          return terminar(e);
        }

        if (paso.done) return terminar(null);

        var ev = paso.value;
        eventos.push(ev);

        var espera = manejar(ev);
        espera.then(bucle);
      }

      function manejar(ev) {
        switch (ev.tipo) {

          case 'line-enter':
            editor.marcarActiva(ev.linea);
            return esperar(0.6);

          case 'log':
            consola.escribir(ev.texto, ev.nivel);
            return esperar(0.35);

          case 'resultado':
            consola.resultado(ev.columnas, ev.filas);
            return esperar(0.5);

          case 'row-insert':
          case 'row-update':
          case 'row-delete':
            tablas.aplicarEvento(ev);
            return esperar(ev.deshaciendo ? 0.9 : 1.2);

          case 'tx-begin':
            $('insignia-tx').classList.remove('oculto');
            return esperar(0.5);

          case 'tx-commit':
            $('insignia-tx').classList.add('oculto');
            tablas.cartel('COMMIT', 'commit');
            return esperar(1.6);

          case 'tx-rollback':
            if (!ev.savepoint) $('insignia-tx').classList.add('oculto');
            tablas.cartel(ev.savepoint ? 'ROLLBACK A ' + ev.savepoint : 'ROLLBACK', 'rollback');
            return esperar(1.8);

          case 'savepoint':
            return esperar(0.4);

          default:
            return esperar(0.2);
        }
      }

      function terminar(error) {
        ejecutando = false;
        esperandoPaso = null;
        $('btn-ejecutar').disabled = false;
        $('btn-verificar').disabled = false;
        $('btn-paso').disabled = true;
        editor.limpiarMarcas('linea--activa');

        // La transaccion pudo quedar abierta al terminar el script
        $('insignia-tx').classList.toggle('oculto', !db.enTransaccion);
        tablas.sincronizarTodo();

        if (error) {
          if (error.esErrorSQL) {
            if (error.linea) editor.marcarError(error.linea);
            consola.escribir((error.linea ? 'Linea ' + error.linea + ': ' : '') + error.message, 'error');
          } else {
            consola.escribir('Error inesperado del simulador: ' + error.message, 'error');
            if (window.console) window.console.error(error);
          }
          consola.estado('error');
          return;
        }

        if (db.enTransaccion) {
          consola.escribir('Aviso: el script termino con una transaccion abierta. ' +
                           'Los cambios siguen pendientes de COMMIT.', 'aviso');
        }

        consola.estado('ok');
        // La validacion se hace despues de que terminen las animaciones
        setTimeout(function () { niveles.evaluar(db, eventos); }, Math.max(60, ritmo() * 1.8));
      }
    }

    /* ── Controles ────────────────────────────────────────── */

    $('btn-ejecutar').addEventListener('click', ejecutar);
    $('btn-verificar').addEventListener('click', function () { verificar(false); });
    $('btn-reiniciar').addEventListener('click', function () { reiniciarBD(true); });
    $('btn-limpiar').addEventListener('click', function () { editor.vaciar(); });

    $('btn-siguiente').addEventListener('click', function () { niveles.siguiente(); });
    $('btn-anterior').addEventListener('click', function () { niveles.anterior(); });
    $('btn-pista').addEventListener('click', function () { niveles.pista(); });

    $('btn-reto').addEventListener('click', function () { alternarObjetivo(); });

    $('sel-velocidad').addEventListener('change', aplicarRitmo);

    $('chk-paso').addEventListener('change', function () {
      pasoAPaso = this.checked;
      $('btn-paso').disabled = !(pasoAPaso && ejecutando);
      if (!pasoAPaso && esperandoPaso) {   // al desactivarlo, seguir de corrido
        var r = esperandoPaso; esperandoPaso = null; r();
      }
    });

    $('btn-paso').addEventListener('click', function () {
      if (!esperandoPaso) return;
      var r = esperandoPaso;
      esperandoPaso = null;
      $('btn-paso').disabled = true;
      r();
    });

    // Teoria
    $('btn-teoria').addEventListener('click', function () {
      teoria.alternar(niveles.actual().id);
    });
    // El boton "Ir al ejercicio" se crea dinamicamente en cada apertura
    $('teoria-caja').addEventListener('click', function (e) {
      if (e.target.closest('.teoria__ir')) teoria.cerrar();
    });

    // Ayuda
    $('btn-ayuda').addEventListener('click', function () { $('modal-ayuda').classList.remove('oculto'); });
    $('btn-cerrar-ayuda').addEventListener('click', function () { $('modal-ayuda').classList.add('oculto'); });
    $('modal-ayuda').addEventListener('click', function (e) {
      if (e.target === this) this.classList.add('oculto');
    });

    /* ── Atajos de expositor ──────────────────────────────── */

    document.addEventListener('keydown', function (e) {
      // No secuestrar el teclado mientras se rellena un hueco
      var t = e.target.tagName;
      if (t === 'INPUT' || t === 'SELECT' || t === 'TEXTAREA') return;

      // Con la portada arriba, cualquier tecla de avance entra al simulador
      // y el resto no hace nada: el teclado todavia no es de la aplicacion.
      if (portadaVisible) {
        if (e.key === 'Enter' || e.key === ' ' || e.key === 'Escape') {
          e.preventDefault();
          cerrarPortada();
        }
        return;
      }

      // Con la teoria abierta el teclado le pertenece a ella.
      if (teoria.visible()) {
        // Espacio funciona como paginador: baja mientras quede texto por leer
        // y solo cierra cuando ya se llego al final.
        if (e.key === ' ') {
          e.preventDefault();
          if (!teoria.desplazarSiFalta()) teoria.cerrar();
          return;
        }
        // Estas si cierran de inmediato: son un avance explicito
        if (['Escape', 't', 'T', 'Enter', 'ArrowRight', 'ArrowLeft'].indexOf(e.key) !== -1) {
          e.preventDefault();
          teoria.cerrar();
        }
        // El resto (flechas verticales, AvPag, Inicio, Fin) desplaza el cuerpo,
        // que es quien tiene el foco.
        return;
      }

      if (e.key === 't' || e.key === 'T') {
        teoria.mostrar(niveles.actual().id);
        return;
      }

      if (e.key === 'Escape') {
        $('modal-ayuda').classList.add('oculto');
        alternarObjetivo(false);
        return;
      }
      if (e.key === ' ')      { e.preventDefault(); ejecutar(); return; }
      if (e.key === 'ArrowRight') { niveles.siguiente(); return; }
      if (e.key === 'ArrowLeft')  { niveles.anterior();  return; }
      if (e.key === 'r' || e.key === 'R') { reiniciarBD(true); return; }
      if (e.key === 'Enter' && pasoAPaso && esperandoPaso) { $('btn-paso').click(); }
    });

    /* ── Arranque ─────────────────────────────────────────── */

    aplicarRitmo();
    niveles.cargar();
    // Enter entra directo, sin tocar el raton. Sin preventScroll el navegador
    // desplaza la portada para "traer a la vista" el boton y recorta los logos.
    $('btn-entrar').focus({ preventScroll: true });

    // Expuesto para poder trastear desde la consola del navegador
    window.sim = { db: db, editor: editor, tablas: tablas, niveles: niveles, consola: consola };
  });

})();
