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
  const activityLabels = ['Reading a source', 'Following the connections', 'Checking the context', 'Preparing a review question'];
  const activity = document.createElement('div');
  activity.className = 'agent-activity';
  activity.setAttribute('aria-hidden', 'true');
  const activityLight = document.createElement('span');
  activityLight.className = 'activity-light';
  const activityText = document.createElement('span');
  const activityTag = document.createElement('span');
  activityTag.className = 'activity-tag';
  activityTag.textContent = 'WORKFLOW PREVIEW';
  activity.append(activityLight, activityText, activityTag);
  panel.querySelector('.graph-tabs').after(activity);
  const ring = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  ring.setAttribute('cx', '290'); ring.setAttribute('cy', '190'); ring.setAttribute('r', '71');
  ring.setAttribute('class', 'scan-ring'); ring.setAttribute('aria-hidden', 'true');
  svg.appendChild(ring);
  const routes = paths.slice(0, 4).map(path => {
    const route = path.cloneNode(false);
    route.setAttribute('class', 'signal-route'); route.setAttribute('aria-hidden', 'true');
    // Keep signal trails underneath the node cards.
    panel.querySelector('#graph-paths').appendChild(route);
    return route;
  });
  const dots = [0, 1].map(() => {
    const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    dot.setAttribute('r', '5.5'); dot.setAttribute('class', 'travel-pulse'); dot.setAttribute('aria-hidden', 'true');
    svg.appendChild(dot); return dot;
  });
  let paused = false, visible = true, frame = null, lastTime = null, elapsed = 0, phase = -1;

  function setPhase(next) {
    if (phase === next) return;
    phase = next; panel.dataset.phase = String(next); stageLabel.textContent = stages[next];
    activityText.textContent = activityLabels[next];
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
    // Visible from the first frame, throughout the cycle—no static opening wait.
    const progress = ((elapsed + 420) % 2600) / 2600;
    const start = phase < 2 ? 0 : 2;
    position(dots[0], paths[start], progress);
    position(dots[1], paths[start + 1], (progress + 0.26) % 1);
    routes.forEach((route, index) => {
      route.style.opacity = index >= start && index < start + 2 ? '0.8' : '0.12';
      route.style.strokeDashoffset = String(-elapsed / 35);
    });
    ring.setAttribute('transform', `rotate(${elapsed / 35} 290 190)`);
    activityLight.style.opacity = String(0.45 + 0.55 * (1 + Math.sin(elapsed / 400)) / 2);
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
    activityTag.textContent = reduced ? 'MOTION OFF' : paused ? 'PAUSED' : 'WORKFLOW PREVIEW';
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
