const $ = (selector) => document.querySelector(selector);
const form = $('#quest-form');
const generateButton = $('#generate-btn');
const buttonLabel = $('#button-label');
const stepsList = $('#steps-list');
let currentQuest = null;
let timerInterval = null;
let secondsRemaining = 0;
let timerRunning = false;

const titleCase = (value) => String(value || '').replace(/\b\w/g, (character) => character.toUpperCase());

function getFormData() {
  const formData = new FormData(form);
  return {
    location: formData.get('location') || 'My local area',
    environment: formData.get('environment') || 'park',
    duration: Number(formData.get('duration') || 30),
    interest: formData.get('interest') || 'surprise',
    language: formData.get('language') || 'English',
    energy: formData.get('energy') || 'gentle'
  };
}

function updateMode(mode, model, notice) {
  const badge = $('#mode-badge');
  const label = $('#mode-label');
  const isLive = mode === 'local-ai';
  badge.classList.toggle('live', isLive);
  badge.classList.toggle('preview', !isLive);
  label.textContent = isLive ? 'LOCAL AI ACTIVE' : 'SAMPLE PREVIEW';
  $('#mode-notice').textContent = notice || (isLive
    ? `Generated locally with ${model || 'an open-weight model'}. No hosted AI service was used.`
    : 'Sample preview. Start Ollama and install the local model to generate a fresh AI mission on this device.');
}

function renderQuest(quest) {
  currentQuest = quest;
  $('#quest-location').textContent = String(quest.location_label || 'OUTDOOR MISSION').toUpperCase();
  $('#quest-duration').textContent = `◷ ${quest.duration || 30} MIN`;
  $('#quest-title').textContent = quest.title || 'Your nature quest';
  $('#quest-intro').textContent = quest.intro || 'Notice something new around you.';
  $('#quest-supplies').textContent = quest.supplies || 'Just your curiosity; a notebook is optional.';
  $('#quest-takeaway').textContent = quest.takeaway || 'Name one thing you noticed.';
  $('#quest-safety').textContent = quest.safety_note || 'Stay in a familiar, permitted place and observe nature from a safe distance.';
  stepsList.innerHTML = '';
  (quest.steps || []).forEach((step, index) => {
    const row = document.createElement('label');
    row.className = 'step-row';
    const checkbox = document.createElement('input');
    checkbox.className = 'step-check';
    checkbox.type = 'checkbox';
    checkbox.setAttribute('aria-label', `Mark ${step.title} complete`);
    const content = document.createElement('span');
    content.className = 'step-content';
    const title = document.createElement('strong');
    title.textContent = `${String(index + 1).padStart(2, '0')} / ${step.title || 'Observe'}`;
    const description = document.createElement('span');
    description.textContent = step.instruction || '';
    content.append(title, description);
    const minutes = document.createElement('span');
    minutes.className = 'step-minutes';
    minutes.textContent = `${step.minutes || 5} MIN`;
    row.append(checkbox, content, minutes);
    checkbox.addEventListener('change', () => {
      row.classList.toggle('done', checkbox.checked);
      updateProgress();
    });
    stepsList.append(row);
  });
  updateProgress();
  updateMode(quest.mode, quest.model, quest.notice);
  resetTimer();
}

function updateProgress() {
  const all = [...stepsList.querySelectorAll('.step-check')];
  const completed = all.filter((item) => item.checked).length;
  $('#progress-label').textContent = `${completed} / ${all.length} COMPLETE`;
  $('#progress-fill').style.width = all.length ? `${(completed / all.length) * 100}%` : '0%';
  if (all.length > 0 && completed === all.length) {
    $('#start-label').textContent = 'Quest complete — well noticed!';
  } else if (!timerRunning) {
    $('#start-label').textContent = 'Start my quest';
  }
}

async function createQuest(event) {
  event.preventDefault();
  generateButton.disabled = true;
  buttonLabel.textContent = 'Preparing your quest…';
  try {
    const response = await fetch('/api/quest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(getFormData())
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || 'Could not create the mission');
    renderQuest(body);
  } catch (error) {
    $('#mode-notice').textContent = `Couldn't reach the local app server (${error.message}). Make sure app.py is running, then refresh this page.`;
  } finally {
    generateButton.disabled = false;
    buttonLabel.textContent = 'Create my nature quest';
  }
}

function updateStatus() {
  fetch('/api/status').then((response) => response.json()).then((status) => {
    const footer = $('#connection-footer');
    if (status.ollama_reachable && status.model_installed) {
      footer.textContent = `LOCAL MODEL READY · ${status.model}`;
      footer.style.color = '#47724c';
    } else if (status.ollama_reachable) {
      footer.textContent = 'OLLAMA FOUND · MODEL NOT INSTALLED';
      footer.style.color = '#967a43';
    } else {
      footer.textContent = 'PREVIEW READY · LOCAL AI OPTIONAL';
      footer.style.color = '#8a8c78';
    }
  }).catch(() => {
    $('#connection-footer').textContent = 'START THE LOCAL APP TO CONNECT';
  });
}

function buildMissionText() {
  if (!currentQuest) return '';
  const lines = [
    `TRAILQUEST AI — ${currentQuest.title}`,
    `${currentQuest.location_label} · ${currentQuest.duration} minutes`,
    '', currentQuest.intro, '',
    'FIELD CHECKLIST',
    ...(currentQuest.steps || []).map((step, index) => `${index + 1}. ${step.title} (${step.minutes} min)\n   ${step.instruction}`),
    '', `BEFORE YOU HEAD BACK: ${currentQuest.takeaway}`,
    `SAFETY: ${currentQuest.safety_note}`,
    '', `AI mode: ${currentQuest.mode === 'local-ai' ? `Local open-weight model (${currentQuest.model})` : 'Sample preview'}`
  ];
  return lines.join('\n');
}

async function copyQuest() {
  const text = buildMissionText();
  try {
    await navigator.clipboard.writeText(text);
    $('#copy-btn').innerHTML = '✓ <span>Copied to clipboard</span>';
  } catch {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed'; textarea.style.opacity = '0';
    document.body.appendChild(textarea); textarea.select();
    const copied = document.execCommand('copy'); textarea.remove();
    $('#copy-btn').innerHTML = copied ? '✓ <span>Copied to clipboard</span>' : '↗ <span>Select and copy manually</span>';
  }
  setTimeout(() => { $('#copy-btn').innerHTML = '↗ <span>Take it with me</span>'; }, 2200);
}

function resetTimer() {
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = null;
  timerRunning = false;
  secondsRemaining = Number(currentQuest?.duration || 30) * 60;
  $('#timer-strip').hidden = true;
  $('#start-icon').textContent = '▷';
  $('#start-label').textContent = 'Start my quest';
  $('#timer-readout').textContent = formatTime(secondsRemaining);
}

function formatTime(seconds) {
  const mins = Math.floor(Math.max(0, seconds) / 60).toString().padStart(2, '0');
  const secs = (Math.max(0, seconds) % 60).toString().padStart(2, '0');
  return `${mins}:${secs}`;
}

function startOrPauseTimer() {
  if (!currentQuest) return;
  if (secondsRemaining <= 0) secondsRemaining = Number(currentQuest.duration || 30) * 60;
  $('#timer-strip').hidden = false;
  if (timerRunning) {
    clearInterval(timerInterval);
    timerInterval = null;
    timerRunning = false;
    $('#start-icon').textContent = '▷';
    $('#start-label').textContent = 'Resume my quest';
    return;
  }
  timerRunning = true;
  $('#start-icon').textContent = 'Ⅱ';
  $('#start-label').textContent = 'Pause timer';
  timerInterval = setInterval(() => {
    secondsRemaining -= 1;
    $('#timer-readout').textContent = formatTime(secondsRemaining);
    if (secondsRemaining <= 0) {
      clearInterval(timerInterval);
      timerInterval = null;
      timerRunning = false;
      $('#start-icon').textContent = '✓';
      $('#start-label').textContent = 'Time’s up — look around';
    }
  }, 1000);
}

form.addEventListener('submit', createQuest);
$('#start-btn').addEventListener('click', startOrPauseTimer);
$('#copy-btn').addEventListener('click', copyQuest);
$('#timer-reset').addEventListener('click', resetTimer);
document.querySelectorAll('.interest-row input').forEach((input) => input.addEventListener('change', () => {
  document.querySelectorAll('.interest-row').forEach((row) => row.classList.toggle('selected', row.querySelector('input').checked));
}));

// Load a sample mission immediately; it keeps the interface demonstrable without a model.
renderQuest({
  title: 'The Curiosity Loop',
  intro: 'Find three small details in nature that you would normally walk past.',
  duration: 30,
  location_label: 'PARK · GUWAHATI, ASSAM',
  supplies: 'Just your curiosity; a notebook is optional.',
  steps: [
    { title: 'Find something tiny', instruction: 'Notice a small natural detail you would usually overlook. Observe without touching it.', minutes: 7 },
    { title: 'Find a repeating pattern', instruction: 'Look for repeated leaves, branches, stones, clouds, or shadows.', minutes: 7 },
    { title: 'Compare two places', instruction: 'Notice how light, sound, or plant cover differs between two nearby safe spots.', minutes: 8 },
    { title: 'Ask a question', instruction: 'Write down one question your observations sparked. You do not need to answer it today.', minutes: 8 }
  ],
  takeaway: 'Name one detail you noticed and one question you want to explore later.',
  safety_note: 'Stay in a familiar, permitted area during daylight. Keep to paths, watch for traffic, do not touch or eat unknown plants, and observe wildlife from a distance. Let someone know where you are going.',
  mode: 'preview',
  model: 'qwen2.5:1.5b',
  notice: 'Sample preview. Start Ollama and install the local model to generate a fresh AI mission on this device.'
});
updateStatus();
