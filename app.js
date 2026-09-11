'use strict';

const examples = {
  macro: {nodes: ['Shipping disruption', 'Freight costs', 'Input costs', 'Operating margins', 'Your watchlist'], types: ['EVENT', 'OBSERVATION', 'EXPOSURE'], question: 'Which companies are exposed to higher input costs?', explanation: 'Follow a possible transmission path, then ask your agent to check the evidence.'},
  nse: {nodes: ['Capacity expansion', 'Company disclosure', 'Execution risk', 'Supplier exposure', 'Your NSE watchlist'], types: ['MANAGEMENT PLAN', 'EVIDENCE TO REVIEW', 'RELATIONSHIP'], question: 'Has a management commitment changed since last quarter?', explanation: 'Compare the original disclosure with new evidence before changing your thesis.'},
  us: {nodes: ['Customer spending', 'Quarterly filing', 'Revenue drivers', 'Supplier outlook', 'Your US watchlist'], types: ['BUSINESS DRIVER', 'EVIDENCE TO REVIEW', 'EXPOSURE'], question: 'Which supplier assumptions depend on this customer?', explanation: 'Keep the relationship explicit. A customer headline alone is not proof of supplier impact.'},
  crypto: {nodes: ['Token incentives', 'Network usage', 'Adoption quality', 'Unlock exposure', 'Your crypto watchlist'], types: ['INCENTIVES', 'OBSERVATION', 'SUPPLY'], question: 'Is usage growing independently of token incentives?', explanation: 'Separate observed activity from an interpretation of sustainable adoption.'}
};
const configForm = document.querySelector('#config-form');
const market = document.querySelector('#market');
const cadence = document.querySelector('#cadence');
const question = document.querySelector('#question');
const preview = document.querySelector('#config-preview');
const status = document.querySelector('#config-status');

function getConfig() {
  return {schema_version: '0.1.0', mode: 'demo', market: market.value, cadence: cadence.value, research_question: question.value.trim(), review_rule: {field: 'change_pct', operator: 'gte', threshold: 10}};
}
function renderConfig() {
  question.setCustomValidity(question.value.trim() ? '' : 'Enter a research question before downloading.');
  preview.textContent = JSON.stringify(getConfig(), null, 2);
  status.textContent = '';
}
function showGraph(key) {
  const example = examples[key];
  ['node-one', 'node-two', 'node-center', 'node-three', 'node-four'].forEach((id, index) => { document.getElementById(id).textContent = example.nodes[index]; });
  ['type-one', 'type-two', 'type-three'].forEach((id, index) => { document.getElementById(id).textContent = example.types[index]; });
  document.getElementById('network-title').textContent = `Illustrative ${key} research graph`;
  document.getElementById('network-desc').textContent = `${example.nodes.join(' connects to ')}. Illustrative research hypotheses, not current market signals.`;
  document.getElementById('graph-question').textContent = example.question;
  document.getElementById('graph-explanation').textContent = example.explanation;
  document.getElementById('edge-one').textContent = key === 'macro' ? 'transmits through' : 'informs research';
  document.querySelectorAll('[data-market]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.market === key)));
}
document.querySelectorAll('[data-market]').forEach(button => button.addEventListener('click', () => { market.value = button.dataset.market; showGraph(market.value); renderConfig(); }));
market.addEventListener('change', () => { showGraph(market.value); renderConfig(); });
cadence.addEventListener('change', renderConfig);
question.addEventListener('input', renderConfig);
configForm.addEventListener('submit', event => {
  event.preventDefault();
  const url = URL.createObjectURL(new Blob([JSON.stringify(getConfig(), null, 2) + '\n'], {type: 'application/json'}));
  const link = document.createElement('a');
  link.href = url; link.download = 'research.config.json'; document.body.appendChild(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  status.textContent = 'Configuration downloaded. Follow the GitHub setup guide to run the local demo.';
});
document.querySelector('#copy-config').addEventListener('click', async () => {
  if (!configForm.reportValidity()) return;
  try { await navigator.clipboard.writeText(JSON.stringify(getConfig(), null, 2)); status.textContent = 'JSON copied. No schedule has been activated.'; }
  catch { const selection = window.getSelection(); const range = document.createRange(); range.selectNodeContents(preview); selection.removeAllRanges(); selection.addRange(range); preview.focus(); status.textContent = 'Select and copy the highlighted JSON with your keyboard.'; }
});
renderConfig();
