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
