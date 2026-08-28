/**
 * ============================================================================
 * VALORANT TACTICAL MASTERCLASS — CINEMATIC INTERACTIVE SCRIPT (welcome.js)
 * ============================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide Icons if loaded
  if (window.lucide) {
    window.lucide.createIcons();
  }

  const cursor = document.getElementById('tacticalCursor');
  const warpOverlay = document.getElementById('warpOverlay');
  const canvas = document.getElementById('particleCanvas');
  let isTransitioning = false;

  // ==========================================================================
  // SECTION 1: PROCEDURAL SCI-FI AUDIO SYNTHESIZER (No external audio files)
  // ==========================================================================
  const audioCtx = window.AudioContext ? new (window.AudioContext || window.webkitAudioContext)() : null;

  function playWarpSound() {
    if (!audioCtx) return;
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }

    try {
      const now = audioCtx.currentTime;

      // 1. High energy charging laser sweep
      const osc1 = audioCtx.createOscillator();
      const gain1 = audioCtx.createGain();
      osc1.type = 'sawtooth';
      osc1.frequency.setValueAtTime(120, now);
      osc1.frequency.exponentialRampToValueAtTime(880, now + 0.35);

      gain1.gain.setValueAtTime(0.01, now);
      gain1.gain.linearRampToValueAtTime(0.25, now + 0.15);
      gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.5);

      osc1.connect(gain1);
      gain1.connect(audioCtx.destination);
      osc1.start(now);
      osc1.stop(now + 0.5);

      // 2. Sub-bass sonic boom
      const osc2 = audioCtx.createOscillator();
      const gain2 = audioCtx.createGain();
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(180, now);
      osc2.frequency.exponentialRampToValueAtTime(35, now + 0.45);

      gain2.gain.setValueAtTime(0.3, now);
      gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.5);

      osc2.connect(gain2);
      gain2.connect(audioCtx.destination);
      osc2.start(now);
      osc2.stop(now + 0.5);

    } catch (e) {
      console.warn('Audio synthesis failed:', e);
    }
  }

  // ==========================================================================
  // SECTION 2: TRANSITION TO ARENA.HTML (CLICK ANYWHERE)
  // ==========================================================================
  function navigateToArena(e) {
    if (isTransitioning) return;
    isTransitioning = true;

    // Trigger visual warp and sound
    playWarpSound();
    if (warpOverlay) {
      warpOverlay.classList.add('active');
    }

    // Spawn burst particles at click location if available
    if (e && e.clientX) {
      spawnClickExplosion(e.clientX, e.clientY);
    }

    // Redirect to arena page smoothly after transition
    setTimeout(() => {
      window.location.href = 'arena.html';
    }, 350);
  }

  // Bind to entire window for universal tap/click anywhere
  window.addEventListener('click', (e) => {
    navigateToArena(e);
  });

  // Touch support for mobile / tablets
  window.addEventListener('touchstart', (e) => {
    if (e.touches && e.touches[0]) {
      navigateToArena(e.touches[0]);
    } else {
      navigateToArena(e);
    }
  }, { passive: true });

  // Keyboard shortcut support (Space, Enter, etc.)
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowRight') {
      navigateToArena(null);
    }
  });

  // ==========================================================================
  // SECTION 3: TACTICAL CROSSHAIR CURSOR
  // ==========================================================================
  if (cursor) {
    window.addEventListener('mousemove', (e) => {
      cursor.style.left = `${e.clientX}px`;
      cursor.style.top = `${e.clientY}px`;
    });

    window.addEventListener('mousedown', () => {
      cursor.style.transform = 'translate(-50%, -50%) scale(0.8)';
    });

    window.addEventListener('mouseup', () => {
      cursor.style.transform = 'translate(-50%, -50%) scale(1)';
    });
  }

  // ==========================================================================
  // SECTION 4: CLASH PARTICLES (Cyan Rift vs Orange Fire Sparks)
  // ==========================================================================
  if (canvas) {
    const ctx = canvas.getContext('2d');
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    window.addEventListener('resize', () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    });

    const particles = [];
    const MAX_PARTICLES = 70;

    class Particle {
      constructor(isBurst = false, x = null, y = null) {
        this.reset(isBurst, x, y);
      }

      reset(isBurst = false, x = null, y = null) {
        if (isBurst && x !== null) {
          this.x = x;
          this.y = y;
          const angle = Math.random() * Math.PI * 2;
          const speed = 4 + Math.random() * 8;
          this.vx = Math.cos(angle) * speed;
          this.vy = Math.sin(angle) * speed;
          this.color = Math.random() > 0.5 ? '#00f2ff' : '#ff5e00';
          this.size = 2 + Math.random() * 4;
          this.life = 1;
          this.decay = 0.03 + Math.random() * 0.04;
          return;
        }

        // Spawn left (Cyan) or right (Fire) or Center
        const side = Math.random();
        if (side < 0.45) {
          // Left Rift
          this.x = Math.random() * (width * 0.4);
          this.y = height * 0.3 + Math.random() * (height * 0.6);
          this.vx = (Math.random() - 0.2) * 1.5;
          this.vy = (Math.random() - 0.5) * 1.5;
          this.color = '#00f2ff';
        } else if (side < 0.9) {
          // Right Flame
          this.x = width * 0.6 + Math.random() * (width * 0.4);
          this.y = height * 0.3 + Math.random() * (height * 0.6);
          this.vx = (Math.random() - 0.8) * 1.5;
          this.vy = (Math.random() - 0.5) * 1.5;
          this.color = '#ff5e00';
        } else {
          // Center Clash
          this.x = width * 0.45 + Math.random() * (width * 0.1);
          this.y = height * 0.4 + Math.random() * (height * 0.3);
          this.vx = (Math.random() - 0.5) * 2.5;
          this.vy = (Math.random() - 0.5) * 2.5;
          this.color = Math.random() > 0.5 ? '#ffffff' : '#00f2ff';
        }

        this.size = 1 + Math.random() * 2.5;
        this.life = 0.4 + Math.random() * 0.6;
        this.decay = 0.005 + Math.random() * 0.01;
      }

      update() {
        this.x += this.vx;
        this.y += this.vy;
        this.life -= this.decay;
      }

      draw() {
        if (this.life <= 0) return;
        ctx.save();
        ctx.globalAlpha = this.life;
        ctx.fillStyle = this.color;
        ctx.shadowColor = this.color;
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    }

    for (let i = 0; i < MAX_PARTICLES; i++) {
      particles.push(new Particle());
    }

    function spawnClickExplosion(cx, cy) {
      for (let i = 0; i < 30; i++) {
        particles.push(new Particle(true, cx, cy));
      }
    }

    function animateParticles() {
      ctx.clearRect(0, 0, width, height);

      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.update();
        p.draw();
        if (p.life <= 0) {
          if (particles.length > MAX_PARTICLES) {
            particles.splice(i, 1);
          } else {
            p.reset();
          }
        }
      }

      requestAnimationFrame(animateParticles);
    }

    animateParticles();
  }
});
