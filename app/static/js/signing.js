let signaturePad = null;
let currentMode = 'drawn';
let otpVerified = false;

document.addEventListener('DOMContentLoaded', () => {
  const canvas = document.getElementById('signature-canvas');
  if (canvas) {
    signaturePad = new SignaturePad(canvas, { penColor: '#1e3a5f' });
    window.addEventListener('resize', resizePad);
    resizePad();
  }
});

function resizePad() {
  const canvas = document.getElementById('signature-canvas');
  if (!canvas || !signaturePad) return;
  const ratio = Math.max(window.devicePixelRatio || 1, 1);
  canvas.width = canvas.offsetWidth * ratio;
  canvas.height = 150 * ratio;
  canvas.getContext('2d').scale(ratio, ratio);
  signaturePad.clear();
}

function setMode(mode) {
  currentMode = mode;
  document.getElementById('pad-drawn').classList.toggle('hidden', mode !== 'drawn');
  document.getElementById('pad-typed').classList.toggle('hidden', mode !== 'typed');
  document.getElementById('tab-drawn').className = mode === 'drawn'
    ? 'px-3 py-1.5 text-sm rounded-lg bg-indigo-100 text-indigo-700 font-medium'
    : 'px-3 py-1.5 text-sm rounded-lg text-gray-500 hover:bg-gray-100';
  document.getElementById('tab-typed').className = mode === 'typed'
    ? 'px-3 py-1.5 text-sm rounded-lg bg-indigo-100 text-indigo-700 font-medium'
    : 'px-3 py-1.5 text-sm rounded-lg text-gray-500 hover:bg-gray-100';
}

function clearPad() {
  if (signaturePad) signaturePad.clear();
}

function renderTyped() {
  const input = document.getElementById('typed-signature').value;
  const canvas = document.getElementById('typed-canvas');
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.font = 'italic 32px Georgia, serif';
  ctx.fillStyle = '#1e3a5f';
  ctx.fillText(input, 10, 55);
}

function getSignatureDataUrl() {
  if (currentMode === 'drawn') {
    if (!signaturePad || signaturePad.isEmpty()) return null;
    return signaturePad.toDataURL('image/png');
  }
  const canvas = document.getElementById('typed-canvas');
  const input = document.getElementById('typed-signature').value.trim();
  if (!input) return null;
  renderTyped();
  return canvas.toDataURL('image/png');
}

async function requestOtp() {
  const btn = document.getElementById('btn-request-otp');
  btn.disabled = true;
  btn.textContent = 'Enviando...';
  const resp = await fetch(`/sign/${TOKEN}/request-otp`, { method: 'POST',
    headers: {'X-CSRFToken': getCsrf()} });
  const data = await resp.json();
  setMsg('otp-msg', data.message, data.success ? 'green' : 'red');
  if (data.success) {
    document.getElementById('otp-input').classList.remove('hidden');
    btn.textContent = 'Reenviar Código';
  }
  btn.disabled = false;
}

async function verifyOtp() {
  const code = document.getElementById('otp-code').value.trim();
  const resp = await fetch(`/sign/${TOKEN}/verify-otp`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrf()},
    body: JSON.stringify({ code }),
  });
  const data = await resp.json();
  if (data.success) {
    setMsg('otp-msg', '✅ Código verificado! Agora assine abaixo.', 'green');
    document.getElementById('step-sign').classList.remove('opacity-40', 'pointer-events-none');
    document.getElementById('btn-submit').classList.remove('hidden');
    otpVerified = true;
  } else {
    setMsg('otp-msg', data.message, 'red');
  }
}

async function submitSignature() {
  if (!otpVerified) return alert('Verifique o código OTP primeiro.');
  const dataUrl = getSignatureDataUrl();
  if (!dataUrl) return alert('Por favor, assine o documento antes de confirmar.');
  const btn = document.getElementById('btn-submit');
  btn.disabled = true;
  btn.textContent = 'Enviando...';
  const resp = await fetch(`/sign/${TOKEN}/submit`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrf()},
    body: JSON.stringify({ signature_data: dataUrl, type: currentMode }),
  });
  const data = await resp.json();
  if (data.success) {
    window.location.href = data.redirect;
  } else {
    alert(data.message || 'Erro ao enviar assinatura.');
    btn.disabled = false;
    btn.textContent = '✅ Confirmar Assinatura';
  }
}

function setMsg(id, msg, color) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.className = `text-sm mt-2 text-${color}-600`;
}

function getCsrf() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : '';
}
