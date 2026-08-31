/**
 * ============================================================================
 * LOCAL COMBAT DISPLAY SCREEN SCRIPT (local_screen.js)
 * ============================================================================
 * Drives the live 2D local combat playback on external displays / monitors:
 * - Fetches chronological Godot action timeline from /api/matches/latest/godot-sequence
 * - Animates character model movements, shields, and damage popups
 * - Plays character emotes (Dance, Taunt, Celebrate, Flex, Salute, GG, Defeat)
 * - Auto-Sync Poll: Automatically plays newly adjudicated matches
 */

document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) window.lucide.createIcons();

  // State
  let currentMatchData = null;
  let timelineEvents = [];
  let currentStepIndex = 0;
  let isPlaying = false;
  let elapsedMatchTime = 0.0;
  let totalMatchDuration = 14.5;
  let autoPollEnabled = true;
  let lastPlayedMatchId = null;
  let playbackTimer = null;

  // Max Stats
  const MAX_HP = 100;
  const MAX_SHD = 50;
  let pAHp = 100, pAShd = 50;
  let pBHp = 100, pBShd = 50;

  // DOM Elements - Header
  const screenMatchTitle = document.getElementById('screenMatchTitle');
  const screenScoreA = document.getElementById('screenScoreA');
  const screenScoreB = document.getElementById('screenScoreB');
  const screenStatusIndicator = document.getElementById('screenStatusIndicator');
  const autoPollStatus = document.getElementById('autoPollStatus');
  const btnToggleAutoPoll = document.getElementById('btnToggleAutoPoll');
  const btnFetchLatest = document.getElementById('btnFetchLatest');
  const btnToggleFullscreen = document.getElementById('btnToggleFullscreen');
  const timelineProgressFill = document.getElementById('timelineProgressFill');

  // DOM Elements - Player A
  const actorNameA = document.getElementById('actorNameA');
  const actorCharTagA = document.getElementById('actorCharTagA');
  const barHpA = document.getElementById('barHpA');
  const numHpA = document.getElementById('numHpA');
  const barShdA = document.getElementById('barShdA');
  const numShdA = document.getElementById('numShdA');
  const spriteA = document.getElementById('spriteA');
  const bubbleA = document.getElementById('bubbleA');
  const bubbleIconA = document.getElementById('bubbleIconA');
  const bubbleTextA = document.getElementById('bubbleTextA');
  const floatingA = document.getElementById('floatingA');

  // DOM Elements - Player B
  const actorNameB = document.getElementById('actorNameB');
  const actorCharTagB = document.getElementById('actorCharTagB');
  const barHpB = document.getElementById('barHpB');
  const numHpB = document.getElementById('numHpB');
  const barShdB = document.getElementById('barShdB');
  const numShdB = document.getElementById('numShdB');
  const spriteB = document.getElementById('spriteB');
  const bubbleB = document.getElementById('bubbleB');
  const bubbleIconB = document.getElementById('bubbleIconB');
  const bubbleTextB = document.getElementById('bubbleTextB');
  const floatingB = document.getElementById('floatingB');

  // DOM Elements - Commentary
  const commentaryTime = document.getElementById('commentaryTime');
  const commentaryText = document.getElementById('commentaryText');

  // Audio Synthesizer
  const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
  const audioCtx = AudioCtxClass ? new AudioCtxClass() : null;

  function playSynthSfx(type) {
    if (!audioCtx) return;
    if (audioCtx.state === 'suspended') audioCtx.resume();
    try {
      const now = audioCtx.currentTime;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      if (type === 'sfx_gunfire_burst' || type === 'sfx_energy_blast') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(600, now);
        osc.frequency.exponentialRampToValueAtTime(100, now + 0.2);
        gain.gain.setValueAtTime(0.18, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.2);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now);
        osc.stop(now + 0.2);
      } else if (type === 'sfx_critical_hit') {
        osc.type = 'square';
        osc.frequency.setValueAtTime(800, now);
        osc.frequency.exponentialRampToValueAtTime(80, now + 0.4);
        gain.gain.setValueAtTime(0.25, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.4);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now);
        osc.stop(now + 0.4);
      } else if (type === 'sfx_victory_fanfare') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(523.25, now);
        osc.frequency.setValueAtTime(659.25, now + 0.15);
        osc.frequency.setValueAtTime(783.99, now + 0.3);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.6);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now);
        osc.stop(now + 0.6);
      } else {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.linearRampToValueAtTime(880, now + 0.15);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.2);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now);
        osc.stop(now + 0.2);
      }
    } catch (e) {}
  }

  // --------------------------------------------------------------------------
  // 1. FETCH SEQUENCE FROM LOCAL SERVER
  // --------------------------------------------------------------------------
  async function fetchLatestMatchSequence(forceReplay = false) {
    try {
      const res = await fetch('/api/matches/latest/godot-sequence');
      if (!res.ok) {
        screenStatusIndicator.textContent = 'STATUS: WAITING FOR MATCH';
        return;
      }
      const data = await res.json();
      if (!data || !data.timeline) return;

      if (!forceReplay && data.match_id === lastPlayedMatchId && !isPlaying) {
        return; // Already played this match
      }

      loadMatchData(data);

    } catch (err) {
      console.error('Failed to fetch match sequence:', err);
    }
  }

  function loadMatchData(data) {
    currentMatchData = data;
    lastPlayedMatchId = data.match_id;
    timelineEvents = data.timeline || [];
    totalMatchDuration = parseFloat(data.total_duration_sec) || 14.5;

    const pA = data.player_a || {};
    const pB = data.player_b || {};

    screenMatchTitle.textContent = `${pA.name || 'Player A'} vs ${pB.name || 'Player B'}`;
    screenScoreA.textContent = pA.score ?? 13;
    screenScoreB.textContent = pB.score ?? 9;

    actorNameA.textContent = pA.name || 'Player A';
    actorCharTagA.textContent = pA.character || 'PHANTOM-9';

    actorNameB.textContent = pB.name || 'Player B';
    actorCharTagB.textContent = pB.character || 'SOL-VANGUARD';

    startMatchPlayback();
  }

  // --------------------------------------------------------------------------
  // 2. TIMELINE PLAYBACK ENGINE
  // --------------------------------------------------------------------------
  function resetActorStates() {
    pAHp = 100; pAShd = 50;
    pBHp = 100; pBShd = 50;
    updateHealthUI();

    spriteA.className = 'actor-sprite-wrapper';
    spriteB.className = 'actor-sprite-wrapper';

    bubbleA.style.display = 'none';
    bubbleB.style.display = 'none';

    floatingA.innerHTML = '';
    floatingB.innerHTML = '';

    timelineProgressFill.style.width = '0%';
  }

  function updateHealthUI() {
    barHpA.style.width = `${Math.max(0, pAHp)}%`;
    numHpA.textContent = Math.max(0, Math.round(pAHp));
    barShdA.style.width = `${Math.max(0, (pAShd / MAX_SHD) * 100)}%`;
    numShdA.textContent = Math.max(0, Math.round(pAShd));

    barHpB.style.width = `${Math.max(0, pBHp)}%`;
    numHpB.textContent = Math.max(0, Math.round(pBHp));
    barShdB.style.width = `${Math.max(0, (pBShd / MAX_SHD) * 100)}%`;
    numShdB.textContent = Math.max(0, Math.round(pBShd));
  }

  function startMatchPlayback() {
    if (playbackTimer) clearInterval(playbackTimer);
    resetActorStates();

    currentStepIndex = 0;
    elapsedMatchTime = 0.0;
    isPlaying = true;
    screenStatusIndicator.textContent = 'STATUS: BATTLE IN PROGRESS';
    commentaryTime.textContent = '[00.0s]';
    commentaryText.textContent = 'Round begins! Tactical agents engage on site.';

    const stepIntervalMs = 50;
    const stepDeltaSec = stepIntervalMs / 1000.0;

    playbackTimer = setInterval(() => {
      elapsedMatchTime += stepDeltaSec;
      timelineProgressFill.style.width = `${Math.min(100, (elapsedMatchTime / totalMatchDuration) * 100)}%`;

      if (currentStepIndex < timelineEvents.length) {
        const nextEvt = timelineEvents[currentStepIndex];
        if (elapsedMatchTime >= nextEvt.timestamp_sec) {
          executeKeyframeEvent(nextEvt);
          currentStepIndex++;
        }
      }

      if (elapsedMatchTime >= totalMatchDuration) {
        clearInterval(playbackTimer);
        isPlaying = false;
        screenStatusIndicator.textContent = 'STATUS: MATCH CONCLUDED';
        const winnerName = currentMatchData.winner_name || 'Champion';
        const winReason = currentMatchData.win_reason || '';
        commentaryText.textContent = `🏆 VICTORY: ${winnerName} takes the round! ${winReason}`;

        if (window.confetti) {
          window.confetti({ particleCount: 120, spread: 100, origin: { y: 0.5 } });
        }
      }
    }, stepIntervalMs);
  }

  // --------------------------------------------------------------------------
  // 3. EXECUTE KEYFRAME EVENT
  // --------------------------------------------------------------------------
  function executeKeyframeEvent(event) {
    const isPlayerA = event.actor === 'player_a';
    const actorSprite = isPlayerA ? spriteA : spriteB;
    const enemySprite = isPlayerA ? spriteB : spriteA;
    const actorBubble = isPlayerA ? bubbleA : bubbleB;
    const actorBubbleIcon = isPlayerA ? bubbleIconA : bubbleIconB;
    const actorBubbleText = isPlayerA ? bubbleTextA : bubbleTextB;
    const damage = parseInt(event.damage_dealt, 10) || 0;

    commentaryTime.textContent = `[${event.timestamp_sec.toFixed(1)}s]`;
    commentaryText.textContent = event.commentary || '';

    if (event.sound_cue) {
      playSynthSfx(event.sound_cue);
    }

    // A. Handle Emotes
    if (event.emote_trigger) {
      handleEmoteTrigger(event.emote_trigger, actorSprite, actorBubble, actorBubbleIcon, actorBubbleText);
      return;
    }

    // B. Handle Combat Actions
    if (event.action_type === 'cast_attack' || event.action_type === 'climax_strike') {
      actorSprite.classList.remove('anim-dash-attack-a', 'anim-dash-attack-b');
      void actorSprite.offsetWidth;
      actorSprite.classList.add(isPlayerA ? 'anim-dash-attack-a' : 'anim-dash-attack-b');

      if (damage > 0) {
        setTimeout(() => {
          applyDamageToEnemy(!isPlayerA, damage);
          enemySprite.classList.remove('anim-hit-reaction');
          void enemySprite.offsetWidth;
          enemySprite.classList.add('anim-hit-reaction');
        }, 200);
      }
    } else if (event.action_type === 'deploy_defence') {
      actorSprite.classList.remove('anim-barrier-active');
      void actorSprite.offsetWidth;
      actorSprite.classList.add('anim-barrier-active');
      spawnFloatingText(isPlayerA ? floatingA : floatingB, '🛡️ DEFENCE UP', '#00f2ff');
    } else if (event.action_type === 'defeat_reaction') {
      actorSprite.classList.add('anim-defeat-fall');
      spawnFloatingText(isPlayerA ? floatingA : floatingB, '💔 DEFEAT', '#ef4444');
    } else if (event.action_type === 'victory_celebration') {
      actorSprite.classList.add('anim-victory-champion');
      spawnFloatingText(isPlayerA ? floatingA : floatingB, '🏆 VICTORY!', '#ffd700');
    }
  }

  function handleEmoteTrigger(emoteId, sprite, bubble, iconEl, textEl) {
    bubble.style.display = 'flex';
    sprite.classList.remove('anim-dance-loop', 'anim-taunt-shake', 'anim-victory-champion');

    switch (emoteId) {
      case 'emote_dance':
        iconEl.textContent = '🕺';
        textEl.textContent = 'CYBER BREAKDANCE!';
        sprite.classList.add('anim-dance-loop');
        break;
      case 'emote_taunt':
        iconEl.textContent = '🗡️';
        textEl.textContent = 'STEP FORWARD IF YOU DARE!';
        sprite.classList.add('anim-taunt-shake');
        break;
      case 'emote_celebrate':
        iconEl.textContent = '🎉';
        textEl.textContent = 'CHAMPION STATUS!';
        sprite.classList.add('anim-victory-champion');
        break;
      case 'emote_flex':
        iconEl.textContent = '💪';
        textEl.textContent = 'MOLTEN TITAN FLEX!';
        sprite.classList.add('anim-taunt-shake');
        break;
      case 'emote_salute':
        iconEl.textContent = '🫡';
        textEl.textContent = 'HONORABLE WARRIOR SALUTE.';
        break;
      case 'emote_gg':
        iconEl.textContent = '👋';
        textEl.textContent = 'RESPECT! GOOD GAME.';
        break;
      case 'emote_defeat':
        iconEl.textContent = '🤦';
        textEl.textContent = 'SHIELDS EXHAUSTED...';
        sprite.classList.add('anim-defeat-fall');
        break;
      default:
        iconEl.textContent = '⚡';
        textEl.textContent = emoteId;
    }

    setTimeout(() => {
      bubble.style.display = 'none';
      sprite.classList.remove('anim-dance-loop', 'anim-taunt-shake');
    }, 2800);
  }

  function applyDamageToEnemy(isPlayerAEnemy, dmg) {
    if (isPlayerAEnemy) {
      if (pAShd > 0) {
        const absorb = Math.min(pAShd, dmg);
        pAShd -= absorb;
        dmg -= absorb;
      }
      pAHp = Math.max(0, pAHp - dmg);
      spawnFloatingText(floatingA, `💥 -${dmg} HP`, '#ef4444');
    } else {
      if (pBShd > 0) {
        const absorb = Math.min(pBShd, dmg);
        pBShd -= absorb;
        dmg -= absorb;
      }
      pBHp = Math.max(0, pBHp - dmg);
      spawnFloatingText(floatingB, `💥 -${dmg} HP`, '#ef4444');
    }
    updateHealthUI();
  }

  function spawnFloatingText(container, text, color) {
    const el = document.createElement('div');
    el.className = 'floating-action-text';
    el.style.color = color;
    el.textContent = text;
    container.appendChild(el);
    setTimeout(() => el.remove(), 1000);
  }

  // --------------------------------------------------------------------------
  // 4. UI CONTROLS & AUTO POLL
  // --------------------------------------------------------------------------
  btnFetchLatest.addEventListener('click', () => {
    fetchLatestMatchSequence(true);
  });

  btnToggleAutoPoll.addEventListener('click', () => {
    autoPollEnabled = !autoPollEnabled;
    autoPollStatus.textContent = autoPollEnabled ? 'ON' : 'OFF';
    btnToggleAutoPoll.classList.toggle('btn-primary', autoPollEnabled);
    btnToggleAutoPoll.classList.toggle('btn-secondary', !autoPollEnabled);
  });

  btnToggleFullscreen.addEventListener('click', () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  });

  // Auto-sync poll interval every 3 seconds
  setInterval(() => {
    if (autoPollEnabled && !isPlaying) {
      fetchLatestMatchSequence(false);
    }
  }, 3000);

  // Initial fetch on page load
  fetchLatestMatchSequence(true);
});
