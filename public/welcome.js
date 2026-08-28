/**
 * ============================================================================
 * VALORANT TACTICAL MASTERCLASS — PURE WELCOME SCREEN INTERACTION (welcome.js)
 * ============================================================================
 * Tapping or clicking anywhere on the screen navigates immediately to arena.html
 */

document.addEventListener('DOMContentLoaded', () => {
  const warpLayer = document.getElementById('warpLayer');
  let isNavigating = false;

  // Web Audio Synth for instant sci-fi audio cue
  const audioCtx = window.AudioContext ? new (window.AudioContext || window.webkitAudioContext)() : null;

  function playWarpSound() {
    if (!audioCtx) return;
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    try {
      const now = audioCtx.currentTime;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(140, now);
      osc.frequency.exponentialRampToValueAtTime(800, now + 0.28);
      gain.gain.setValueAtTime(0.01, now);
      gain.gain.linearRampToValueAtTime(0.2, now + 0.1);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start(now);
      osc.stop(now + 0.35);
    } catch (e) {
      // Audio autoplay policy fallback
    }
  }

  function handleTapToEnter() {
    if (isNavigating) return;
    isNavigating = true;

    playWarpSound();
    if (warpLayer) {
      warpLayer.classList.add('active');
    }

    setTimeout(() => {
      window.location.href = 'arena.html';
    }, 280);
  }

  // Bind to entire window for universal tap/click anywhere
  window.addEventListener('click', handleTapToEnter);
  window.addEventListener('touchstart', handleTapToEnter, { passive: true });
  window.addEventListener('keydown', handleTapToEnter);
});
