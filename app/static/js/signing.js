// SignCert — Mobile-first signing flow
let signaturePad = null;
let currentMode = 'drawn';
let otpVerified = false;
let currentStep = 1;

document.addEventListener('DOMContentLoaded', () => {
  initCanvas();
});

// ── Step navigation ───────────────────────────────────────────────────────────

function goToStep(step) {
  document.getElementById(`section-${currentStep}`).classList.add('hidden');
  currentStep = step;
  const section = document.getElementById(`section-${step}`);
  section.classList.remove('hidden');
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });
  updateProgressBar(step);
  if (step === 3) {
    document.getElementById('floating-submit').classList.remove('hidden');
    setTimeout(initCanvas, 50); // re-init after layout
  }
}

function updateProgressBar(active) {
  for (let i = 1; i <= 3; i++) {
    const circle = document.getElementById(`step-circle-${i}`);
    const label = document.getElementById(`step-label-${i}`);
    if (i < active) {
      circle.className = circle.className.replace('bg-gray-200 text-gray-400', 'bg-green-500 text-white');
      circle.textContent = '✓';
    } else if (i === active) {
      circle.className = circle.className
        .replace('bg-gray-200 text-gray-400', 'bg-indigo-600 text-white')
        .replace('bg-green-500 text-white', 'bg-indigo-600 text-white');
      label.className = label.className.replace('text-gray-400', 'text-indigo-600 font-medium');
    }
    if (i < active) {
      const line = document.getElementById(`step-line-${i}`);
      if (line) line.classList.add('step-line-active');
    }
  }
}

// ── OTP ───────────────────────────────────────────────────────────────────────

async function requestOtp() {
  const btn = document.getElementById('btn-request-otp');
  btn.disabled = true;
  btn.innerHTML = '<span class="animate-spin inline-block mr-2">⏳</span>Enviando...';

  const resp = await fetch(`/sign/${TOKEN}/request-otp`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCsrf() },
  });
  const data = await resp.json();
  btn.disabled = false;
  btn.innerHTML = '<span>📧</span> Reenviar Código';

  if (data.success) {
    document.getElementById('otp-sent-msg').textContent = `✅ ${data.message}`;
    document.getElementById('otp-input-area').classList.remove('hidden');
    document.getElementById('otp-error').classList.add('hidden');
    setTimeout(() => document.getElementById('otp-code').focus(), 100);
  } else {
    showError('otp-error', data.message);
  }
}

async function verifyOtp() {
  const code = document.getElementById('otp-code').value.replace(/\D/g, '');
  if (code.length !== 6) {
    showError('otp-error', 'Digite os 6 dígitos do código.');
    return;
  }
  const btn = document.getElementById('btn-verify-otp');
  btn.disabled = true;
  btn.textContent = 'Verificando...';

  const resp = await fetch(`/sign/${TOKEN}/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
    body: JSON.stringify({ code }),
  });
  const data = await resp.json();

  if (data.success) {
    otpVerified = true;
    document.getElementById('otp-error').classList.add('hidden');
    goToStep(3);
  } else {
    btn.disabled = false;
    btn.textContent = '✅ Verificar Código';
    showError('otp-error', data.message);
    document.getElementById('otp-code').value = '';
    document.getElementById('otp-code').focus();
  }
}

// Allow pressing Enter on OTP input
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('otp-code');
  if (input) input.addEventListener('keydown', e => { if (e.key === 'Enter') verifyOtp(); });
});

// ── Signature canvas ──────────────────────────────────────────────────────────

function initCanvas() {
  const canvas = document.getElementById('signature-canvas');
  if (!canvas) return;
  // Skip if already initialized with a valid width
  if (signaturePad && canvas.offsetWidth > 0 && canvas.width > 0) return;
  if (signaturePad) {
    signaturePad.off();
    signaturePad = null;
  }
  const ratio = Math.max(window.devicePixelRatio || 1, 1);
  canvas.width = canvas.offsetWidth * ratio;
  canvas.height = 160 * ratio;
  canvas.getContext('2d').scale(ratio, ratio);
  signaturePad = new SignaturePad(canvas, {
    penColor: '#1e3a5f',
    minWidth: 1.5,
    maxWidth: 3,
    velocityFilterWeight: 0.7,
  });
  signaturePad.addEventListener('endStroke', toggleSubmit);
}

function setMode(mode) {
  currentMode = mode;
  const isDrawn = mode === 'drawn';
  document.getElementById('pad-drawn').classList.toggle('hidden', !isDrawn);
  document.getElementById('pad-typed').classList.toggle('hidden', isDrawn);
  const activeClass = 'flex-1 py-2.5 text-sm font-medium bg-indigo-600 text-white transition';
  const inactiveClass = 'flex-1 py-2.5 text-sm font-medium bg-white text-gray-600 transition';
  document.getElementById('tab-drawn').className = isDrawn ? activeClass : inactiveClass;
  document.getElementById('tab-typed').className = isDrawn ? inactiveClass : activeClass;
  toggleSubmit();
}

function clearPad() {
  if (signaturePad) signaturePad.clear();
  toggleSubmit();
}

function renderTyped() {
  const input = document.getElementById('typed-signature').value;
  const canvas = document.getElementById('typed-canvas');
  canvas.width = 500; canvas.height = 80;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, 500, 80);
  ctx.font = 'italic 38px Georgia, serif';
  ctx.fillStyle = '#1e3a5f';
  ctx.fillText(input, 10, 55);
  toggleSubmit();
}

function getSignatureDataUrl() {
  if (currentMode === 'drawn') {
    if (!signaturePad || signaturePad.isEmpty()) return null;
    return signaturePad.toDataURL('image/png');
  }
  const input = document.getElementById('typed-signature').value.trim();
  if (!input) return null;
  renderTyped();
  return document.getElementById('typed-canvas').toDataURL('image/png');
}

function toggleSubmit() {
  const hasSignature = currentMode === 'drawn'
    ? signaturePad && !signaturePad.isEmpty()
    : (document.getElementById('typed-signature')?.value.trim().length > 1);
  const agreed = document.getElementById('agree-checkbox')?.checked;
  const btn = document.getElementById('btn-submit');
  if (btn) btn.disabled = !(hasSignature && agreed);
}

// ── Submit ────────────────────────────────────────────────────────────────────

async function submitSignature() {
  if (!otpVerified) return;
  const dataUrl = getSignatureDataUrl();
  if (!dataUrl) return;

  const btn = document.getElementById('btn-submit');
  btn.disabled = true;
  btn.textContent = '⏳ Enviando...';

  const resp = await fetch(`/sign/${TOKEN}/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
    body: JSON.stringify({ signature_data: dataUrl, type: currentMode }),
  });
  const data = await resp.json();
  if (data.success) {
    window.location.href = data.redirect;
  } else {
    btn.disabled = false;
    btn.textContent = '✅ Confirmar Assinatura';
    alert(data.message || 'Erro ao enviar assinatura.');
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function showError(id, msg) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.classList.remove('hidden');
}

function getCsrf() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : '';
}

// Handle window resize — rescale canvas (clears existing drawing)
window.addEventListener('resize', () => {
  if (!signaturePad || currentMode !== 'drawn') return;
  const canvas = document.getElementById('signature-canvas');
  const ratio = Math.max(window.devicePixelRatio || 1, 1);
  canvas.width = canvas.offsetWidth * ratio;
  canvas.height = 160 * ratio;
  canvas.getContext('2d').scale(ratio, ratio);
  signaturePad.clear();
  toggleSubmit();
});
