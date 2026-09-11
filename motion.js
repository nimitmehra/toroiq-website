'use strict';

// An illustrative, local animation. No source fetching or agent activity occurs.
(() => {
  const panel = document.querySelector('.graph-window');
  const svg = panel.querySelector('.network');
  panel.querySelector('#node-one').parentElement.classList.add('source-node');
  const paths = [...panel.querySelectorAll('#graph-paths path')];
  const toggle = document.querySelector('#motion-toggle');
  const stageLabel = document.querySelector('#motion-stage');
  const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
  const stages = ['01 / OBSERVE A SOURCE', '02 / TRACE RELATIONSHIPS', '03 / REVIEW THE CONTEXT', '04 / QUEUE A QUESTION'];
  const dots = [0, 1].map(() => {
    const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    dot.setAttribute('r', '3.5'); dot.setAttribute('class', 'travel-pulse'); dot.setAttribute('aria-hidden', 'true');
    svg.appendChild(dot); return dot;
  });
  let paused = false, visible = true, frame = null, lastTime = null, elapsed = 0, phase = -1;

  function setPhase(next) {
    if (phase === next) return;
    phase = next; panel.dataset.phase = String(next); stageLabel.textContent = stages[next];
  }
  function position(dot, path, progress) {
    const point = path.getPointAtLength(path.getTotalLength() * progress);
    dot.setAttribute('cx', point.x); dot.setAttribute('cy', point.y);
    dot.style.opacity = String(Math.min(1, progress * 8, (1 - progress) * 8));
  }
  function running() { return !paused && !preference.matches && visible && !document.hidden; }
  function tick(time) {
    frame = null;
    if (!running()) return;
    if (lastTime !== null) elapsed += Math.min(time - lastTime, 100);
    lastTime = time;
    const cycle = elapsed % 14000;
    setPhase(Math.floor(cycle / 3500));
    dots.forEach(dot => { dot.style.opacity = '0'; });
    if (phase === 1) {
      const progress = (cycle - 3500) / 3500;
      position(dots[0], paths[0], progress); position(dots[1], paths[1], progress);
    } else if (phase === 2) {
      const progress = (cycle - 7000) / 3500;
      position(dots[0], paths[2], progress); position(dots[1], paths[3], progress);
    }
    frame = requestAnimationFrame(tick);
  }
  function sync() {
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null; lastTime = null;
    const reduced = preference.matches;
    toggle.disabled = reduced;
    toggle.setAttribute('aria-pressed', String(paused || reduced));
    toggle.textContent = reduced ? 'Reduced motion enabled' : paused ? 'Play animation' : 'Pause animation';
    panel.dataset.motion = running() ? 'playing' : 'paused';
    if (reduced) { setPhase(0); dots.forEach(dot => { dot.style.opacity = '0'; }); }
    if (running()) frame = requestAnimationFrame(tick);
  }
  toggle.hidden = false;
  toggle.addEventListener('click', () => { paused = !paused; sync(); });
  preference.addEventListener('change', sync);
  document.addEventListener('visibilitychange', sync);
  panel.addEventListener('graphchange', () => { elapsed = 0; setPhase(0); dots.forEach(dot => { dot.style.opacity = '0'; }); sync(); });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => { visible = entries[0].isIntersecting; sync(); }, {threshold: 0.05}).observe(panel);
  }
  setPhase(0); sync();
})();
