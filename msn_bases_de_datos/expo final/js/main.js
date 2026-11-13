/* ============================================================
   Exposición final — navegación de diapositivas y fondo animado
   ============================================================ */

/* ── Navegación ───────────────────────────────────────────── */
const slides   = [...document.querySelectorAll('.slide')];
const btnAnt   = document.getElementById('btn-ant');
const btnSig   = document.getElementById('btn-sig');
const progreso = document.getElementById('progreso');
let actual = 0;

document.getElementById('total').textContent = slides.length;

function irA(indice) {
  if (indice < 0 || indice >= slides.length || indice === actual) return;

  const anterior = slides[actual];
  if (anterior) {
    const direccion = indice > actual ? 'izq' : 'der';
    anterior.classList.remove('activa');
    anterior.classList.add('saliendo-' + direccion);
    setTimeout(() => anterior.classList.remove('saliendo-izq', 'saliendo-der'), 900);
  }

  actual = indice;
  slides[actual].classList.add('activa');

  document.getElementById('actual').textContent = actual + 1;
  btnAnt.disabled = actual === 0;
  btnSig.disabled = actual === slides.length - 1;
  progreso.style.width = ((actual + 1) / slides.length * 100) + '%';
  history.replaceState(null, '', '#' + (actual + 1));

  escribirTerminal(slides[actual]);
}

btnAnt.addEventListener('click', () => irA(actual - 1));
btnSig.addEventListener('click', () => irA(actual + 1));

document.addEventListener('keydown', (e) => {
  if (e.ctrlKey || e.metaKey || e.altKey) return;   // no estorbar Ctrl+C, etc.

  if (!indice.hidden) {
    if (e.key === 'Escape' || e.key === 'i' || e.key === 'I') { e.preventDefault(); cerrarIndice(); }
    return;
  }
  if (e.key === 'i' || e.key === 'I') { e.preventDefault(); abrirIndice(); return; }

  // Enter sobre una sentencia enfocada la resalta en lugar de avanzar
  if (e.key === 'Enter' && document.activeElement?.classList.contains('bloque')) {
    e.preventDefault(); marcarBloque(document.activeElement); return;
  }

  switch (e.key) {
    case 'ArrowRight': case 'PageDown': case ' ': case 'Enter':
      e.preventDefault(); irA(actual + 1); break;
    case 'ArrowLeft': case 'PageUp': case 'Backspace':
      e.preventDefault(); irA(actual - 1); break;
    case 'Home': irA(0); break;
    case 'End':  irA(slides.length - 1); break;
    case 'f': case 'F':
      if (document.fullscreenElement) document.exitFullscreen();
      else document.documentElement.requestFullscreen?.();
      break;
  }
});

// Deslizar en pantallas táctiles
let toqueX = null;
document.addEventListener('touchstart', (e) => { toqueX = e.touches[0].clientX; }, { passive: true });
document.addEventListener('touchend', (e) => {
  if (toqueX === null) return;
  const dx = e.changedTouches[0].clientX - toqueX;
  if (Math.abs(dx) > 60) irA(actual + (dx < 0 ? 1 : -1));
  toqueX = null;
});

/* ── Resaltado de sintaxis SQL ────────────────────────────── */
const RE_SQL = /(--[^\n]*)|('(?:[^'\\]|\\.)*')|(@\w+)|(\b\d+(?:\.\d+)?\b)|(\b[A-Z_][A-Z0-9_]+\b)|(\b[a-z_][a-z0-9_]*\b)/g;
const CLASES = [null, 't-com', 't-str', 't-var', 't-num', 't-kw', 't-id'];

function escapar(t) {
  return t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function resaltar(pre) {
  const texto = pre.textContent;
  let html = '', ultimo = 0;
  texto.replace(RE_SQL, (m, ...grupos) => {
    const pos = grupos[grupos.length - 2];
    const g = grupos.slice(0, 6).findIndex((x) => x !== undefined) + 1;
    html += escapar(texto.slice(ultimo, pos)) + `<span class="${CLASES[g]}">${escapar(m)}</span>`;
    ultimo = pos + m.length;
    return m;
  });
  pre.innerHTML = html + escapar(texto.slice(ultimo));
}
document.querySelectorAll('pre.sql').forEach(resaltar);

/* ── Ir a la declaración desde cada CALL ──────────────────── */
const declaraciones = new Map();   // nombre del procedimiento → bloque CREATE PROCEDURE
document.querySelectorAll('.bloque--sql pre').forEach((pre) => {
  const m = pre.textContent.match(/^CREATE PROCEDURE (\w+)/);
  if (m) declaraciones.set(m[1], pre.closest('.bloque'));
});
document.querySelectorAll('.bloque--sql pre').forEach((pre) => {
  const m = pre.textContent.match(/^CALL (\w+)/);
  if (!m || !declaraciones.has(m[1])) return;
  const btn = document.createElement('button');
  btn.className = 'copiar ir-declaracion';
  btn.type = 'button';
  btn.dataset.proc = m[1];
  btn.textContent = 'Ir a la declaración';
  const bloque = pre.closest('.bloque');
  bloque.classList.add('bloque--call');
  bloque.appendChild(btn);
});

// Un solo botón de regreso; se coloca en la declaración a la que se saltó
const btnVolver = document.createElement('button');
btnVolver.className = 'copiar volver-call';
btnVolver.type = 'button';
btnVolver.textContent = 'Volver al CALL';
let origenCall = null;

function irABloque(bloque) {
  irA(slides.indexOf(bloque.closest('.slide')));
  marcarBloque(bloque, true);
  const cuerpo = bloque.closest('.codigo__cuerpo');
  const arriba = bloque.getBoundingClientRect().top - cuerpo.getBoundingClientRect().top;
  cuerpo.scrollTo({ top: cuerpo.scrollTop + arriba - 8, behavior: 'smooth' });
}

function irADeclaracion(nombre, origen) {
  const destino = declaraciones.get(nombre);
  origenCall = origen;
  destino.appendChild(btnVolver);
  irABloque(destino);
}

function volverAlCall() {
  btnVolver.remove();
  if (origenCall) irABloque(origenCall);
  origenCall = null;
}

/* ── Copiar al portapapeles ───────────────────────────────── */
const avisoCopia = document.getElementById('aviso-copia');
let temporizadorAviso;

async function copiarTexto(texto, mensaje) {
  try {
    await navigator.clipboard.writeText(texto);
  } catch {
    // Respaldo para navegadores que bloquean la API en file://
    const area = document.createElement('textarea');
    area.value = texto;
    area.style.cssText = 'position:fixed;opacity:0';
    document.body.appendChild(area);
    area.select();
    document.execCommand('copy');
    area.remove();
  }
  avisoCopia.textContent = mensaje;
  avisoCopia.classList.add('visible');
  clearTimeout(temporizadorAviso);
  temporizadorAviso = setTimeout(() => avisoCopia.classList.remove('visible'), 1600);
}

function copiarBloque(bloque) {
  const esCmd = bloque.classList.contains('bloque--cmd');
  copiarTexto(bloque.querySelector('pre').textContent,
    esCmd ? 'Comando copiado · pégalo en PowerShell' : 'Sentencia copiada · Ctrl+V en DBeaver');
  bloque.classList.add('copiado');
  setTimeout(() => bloque.classList.remove('copiado'), 1400);
}

document.addEventListener('click', (e) => {
  const todo = e.target.closest('.copiar--todo');
  if (todo) {
    const cuerpo = todo.closest('.codigo').querySelector('.codigo__cuerpo');
    let pres = cuerpo.querySelectorAll('.bloque--sql pre');
    if (!pres.length) pres = cuerpo.querySelectorAll('.bloque--cmd pre');
    copiarTexto([...pres].map((p) => p.textContent).join('\n\n'), `${pres.length} sentencias copiadas`);
    todo.blur();
    return;
  }
  const ir = e.target.closest('.ir-declaracion');
  if (ir) {
    irADeclaracion(ir.dataset.proc, ir.closest('.bloque'));
    ir.blur();
    return;
  }
  if (e.target.closest('.volver-call')) {
    volverAlCall();
    return;
  }
  const bloque = e.target.closest('.bloque');
  if (!bloque) return;
  // Sólo el botón copia; un clic en el resto del bloque únicamente lo resalta
  if (e.target.closest('.copiar')) {
    copiarBloque(bloque);
    marcarBloque(bloque, true);
    e.target.blur();
    return;
  }
  // Si el usuario está seleccionando texto con el ratón, no cambiar el resaltado
  if (String(window.getSelection()).length) return;
  marcarBloque(bloque);
});

/* Resaltado persistente: un bloque marcado a la vez; otro clic lo desmarca */
function marcarBloque(bloque, forzar = false) {
  const yaMarcado = bloque.classList.contains('marcado');
  document.querySelectorAll('.bloque.marcado').forEach((b) => b.classList.remove('marcado'));
  if (forzar || !yaMarcado) bloque.classList.add('marcado');
}

/* ── Índice ───────────────────────────────────────────────── */
const indice = document.getElementById('indice');
const listaIndice = document.getElementById('indice-lista');

slides.forEach((s, i) => {
  const li = document.createElement('li');
  if (s.classList.contains('slide--seccion')) li.className = 'indice__seccion';
  const b = document.createElement('button');
  b.innerHTML = `<span class="indice__n">${i + 1}</span><span></span>`;
  b.lastChild.textContent = s.dataset.titulo || `Diapositiva ${i + 1}`;
  b.addEventListener('click', () => { cerrarIndice(); irA(i); });
  li.appendChild(b);
  listaIndice.appendChild(li);
});

function abrirIndice() {
  indice.hidden = false;
  const botones = listaIndice.querySelectorAll('button');
  botones.forEach((b, i) => b.classList.toggle('actual', i === actual));
  botones[actual]?.focus();
  botones[actual]?.scrollIntoView({ block: 'center' });
}
function cerrarIndice() { indice.hidden = true; }

document.getElementById('btn-indice').addEventListener('click', (e) => { e.currentTarget.blur(); abrirIndice(); });
document.getElementById('btn-cerrar-indice').addEventListener('click', cerrarIndice);
indice.addEventListener('click', (e) => { if (e.target === indice) cerrarIndice(); });

/* ── Efecto máquina de escribir en la terminal ────────────── */
function escribirTerminal(slide) {
  slide.querySelectorAll('[data-escribir]').forEach((el) => {
    const texto = el.dataset.escribir;
    clearInterval(el._intervalo);
    el.textContent = '';
    let i = 0;
    setTimeout(() => {
      el._intervalo = setInterval(() => {
        el.textContent = texto.slice(0, ++i);
        if (i >= texto.length) clearInterval(el._intervalo);
      }, 85);
    }, 1000);
  });
}

/* ── Fondo: rejilla en perspectiva + palabras SQL flotando ── */
const canvas = document.getElementById('fondo');
const ctx = canvas.getContext('2d');
const PALABRAS = [
  'SELECT', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK', 'CREATE ROLE', 'BEGIN',
  'CALL', 'SAVEPOINT', 'mysqldump', 'INSERT', 'UPDATE', 'DECLARE', 'HANDLER',
  'START TRANSACTION', 'FLUSH PRIVILEGES', 'SOURCE', 'WITH ADMIN OPTION'
];
let ancho, alto, tokens = [];

function redimensionar() {
  const dpr = window.devicePixelRatio || 1;
  ancho = window.innerWidth;
  alto = window.innerHeight;
  canvas.width = ancho * dpr;
  canvas.height = alto * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const cantidad = Math.round(ancho / 70);
  tokens = Array.from({ length: cantidad }, () => nuevoToken(true));
}

function nuevoToken(aleatorioY) {
  return {
    texto: PALABRAS[Math.floor(Math.random() * PALABRAS.length)],
    x: Math.random() * ancho,
    y: aleatorioY ? Math.random() * alto : alto + 20,
    vel: 0.15 + Math.random() * 0.35,
    tam: 10 + Math.random() * 6,
    alfa: 0.05 + Math.random() * 0.12,
    naranja: Math.random() < 0.18
  };
}

let desplazamiento = 0;
function dibujar() {
  ctx.clearRect(0, 0, ancho, alto);

  // Rejilla inferior en perspectiva
  const horizonte = alto * 0.62;
  ctx.strokeStyle = 'rgba(63, 184, 214, 0.06)';
  ctx.lineWidth = 1;
  for (let i = -20; i <= 20; i++) {
    ctx.beginPath();
    ctx.moveTo(ancho / 2 + i * 40, horizonte);
    ctx.lineTo(ancho / 2 + i * ancho * 0.12, alto);
    ctx.stroke();
  }
  desplazamiento = (desplazamiento + 0.4) % 40;
  for (let j = 0; j < 14; j++) {
    const t = ((j * 40 + desplazamiento) / (14 * 40));
    const y = horizonte + Math.pow(t, 2) * (alto - horizonte);
    ctx.globalAlpha = t;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(ancho, y);
    ctx.stroke();
  }
  ctx.globalAlpha = 1;

  // Palabras SQL que ascienden
  for (let i = 0; i < tokens.length; i++) {
    const t = tokens[i];
    t.y -= t.vel;
    if (t.y < -20) tokens[i] = nuevoToken(false);
    ctx.font = `${t.tam}px "JetBrains Mono", monospace`;
    ctx.fillStyle = t.naranja
      ? `rgba(242, 145, 17, ${t.alfa})`
      : `rgba(63, 184, 214, ${t.alfa})`;
    ctx.fillText(t.texto, t.x, t.y);
  }

  requestAnimationFrame(dibujar);
}

window.addEventListener('resize', redimensionar);
redimensionar();
if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) dibujar();

/* ── Inicio: respeta el #número de la URL ─────────────────── */
const inicial = Math.min(Math.max(parseInt(location.hash.slice(1), 10) - 1 || 0, 0), slides.length - 1);
actual = -1;
irA(inicial);
