let mediaRecorder = null;
let isRecording = false;
let streamHandle = null;

const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const statusEl = document.getElementById('status');
const zhStream = document.getElementById('zhStream');
const esStream = document.getElementById('esStream');

const socket = io();

socket.on('connect', () => {
  console.log('Socket connected');
});

socket.on('subtitle', payload => {
  // payload: { timestamp, source_lang, zh, es, raw }
  const time = new Date(payload.timestamp);
  const timePart = time.toLocaleTimeString([], { hour12: false });

  appendLine(zhStream, `[${timePart}] ${payload.zh || ''}`);
  appendLine(esStream, `[${timePart}] ${payload.es || ''}`);
});

function appendLine(container, text) {
  const div = document.createElement('div');
  div.className = 'line';
  div.textContent = text;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

startBtn.addEventListener('click', async () => {
  if (isRecording) return;
  try {
    streamHandle = await navigator.mediaDevices.getUserMedia({ audio: true });
    const options = { mimeType: 'audio/webm; codecs=opus' };
    mediaRecorder = new MediaRecorder(streamHandle, options);

    mediaRecorder.addEventListener('dataavailable', async (event) => {
      if (!event.data || event.data.size === 0) return;
      try {
        await fetch('/upload', {
          method: 'POST',
          headers: { 'Content-Type': 'audio/webm' },
          body: event.data,
        });
      } catch (e) {
        console.error('Upload failed', e);
      }
    });

    mediaRecorder.start(1000); // deliver a chunk every 1s
    isRecording = true;
    startBtn.disabled = true;
    stopBtn.disabled = false;
    statusEl.textContent = '录音中…';
  } catch (e) {
    console.error('Mic error', e);
    alert('无法访问麦克风：' + e.message);
  }
});

stopBtn.addEventListener('click', () => {
  if (!isRecording) return;
  try {
    mediaRecorder.stop();
  } catch {}
  if (streamHandle) {
    for (const track of streamHandle.getTracks()) track.stop();
  }
  isRecording = false;
  startBtn.disabled = false;
  stopBtn.disabled = true;
  statusEl.textContent = '已停止';
});