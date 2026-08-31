/**
 * ============================================================================
 * ADMIN COMMAND CENTER SCRIPT (admin.js)
 * ============================================================================
 * - Security Gate Passcode Protection: K0lst@rno.1
 * - 100% Manual Match Adjudication (No AI predictions)
 * - AI Godot Keyframe Combat Sequence Generation & REST Export
 * - Interactive 2-Character Showcase & Emote Stage
 */

document.addEventListener('DOMContentLoaded', () => {
  const CORRECT_PASSCODE = 'K0lst@rno.1';

  // Initialize Lucide Icons
  if (window.lucide) {
    window.lucide.createIcons();
  }

  // State
  let allCardsMap = {};
  let queuedSubmissions = [];
  let storedMatches = [];
  let selectedSubA = null;
  let selectedSubB = null;
  let currentGodotSequence = null;

  // DOM Elements - Security Gate
  const securityGateOverlay = document.getElementById('securityGateOverlay');
  const formGateAuth = document.getElementById('formGateAuth');
  const gatePasswordInput = document.getElementById('gatePasswordInput');
  const gateErrorMsg = document.getElementById('gateErrorMsg');
  const btnToggleGatePass = document.getElementById('btnToggleGatePass');
  const btnLockAdmin = document.getElementById('btnLockAdmin');

  // DOM Elements - Metrics
  const statQueuedPlayers = document.getElementById('statQueuedPlayers');
  const statRegisteredPlayers = document.getElementById('statRegisteredPlayers');
  const statCompletedMatches = document.getElementById('statCompletedMatches');
  const queueCountBadge = document.getElementById('queueCountBadge');
  const playerCountBadge = document.getElementById('playerCountBadge');
  const historyCountBadge = document.getElementById('historyCountBadge');
  const btnRefreshAll = document.getElementById('btnRefreshAll');
  const playersTableBody = document.getElementById('playersTableBody');

  // DOM Elements - Matchmaking Queue
  const chipPlayerA = document.getElementById('chipPlayerA');
  const chipPlayerB = document.getElementById('chipPlayerB');
  const btnClearQueue = document.getElementById('btnClearQueue');
  const submissionsListContainer = document.getElementById('submissionsListContainer');

  // DOM Elements - Manual Adjudication Form
  const formManualAdjudicate = document.getElementById('formManualAdjudicate');
  const selectCharA = document.getElementById('selectCharA');
  const selectCharB = document.getElementById('selectCharB');
  const inputScoreA = document.getElementById('inputScoreA');
  const inputScoreB = document.getElementById('inputScoreB');
  const inputWinReason = document.getElementById('inputWinReason');
  const inputMvpCombo = document.getElementById('inputMvpCombo');
  const btnRunManualAdj = document.getElementById('btnRunManualAdj');

  // DOM Elements - Godot Timeline & Export
  const godotTimelineList = document.getElementById('godotTimelineList');
  const godotRawJsonDisplay = document.getElementById('godotRawJsonDisplay');
  const btnCopyGodotJson = document.getElementById('btnCopyGodotJson');
  const btnDownloadGodotJson = document.getElementById('btnDownloadGodotJson');

  // DOM Elements - Matches History
  const matchesTableBody = document.getElementById('matchesTableBody');
  const matchDetailModal = document.getElementById('matchDetailModal');
  const btnCloseMatchModal = document.getElementById('btnCloseMatchModal');
  const modalMatchTitle = document.getElementById('modalMatchTitle');
  const modalMatchSub = document.getElementById('modalMatchSub');
  const modalMatchContent = document.getElementById('modalMatchContent');

  // Custom Cursor
  const cursor = document.getElementById('customCursor');
  if (cursor) {
    window.addEventListener('mousemove', (e) => {
      cursor.style.left = `${e.clientX}px`;
      cursor.style.top = `${e.clientY}px`;
    });
  }

  // Audio Synthesizer for SFX & Emotes
  const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
  const audioCtx = AudioCtxClass ? new AudioCtxClass() : null;

  function playSynthSfx(type) {
    if (!audioCtx) return;
    if (audioCtx.state === 'suspended') audioCtx.resume();
    try {
      const now = audioCtx.currentTime;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      if (type === 'unlock') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.2);
        gain.gain.setValueAtTime(0.15, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.3);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now);
        osc.stop(now + 0.3);
      } else if (type === 'sfx_blade_whoosh') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(900, now);
        osc.frequency.exponentialRampToValueAtTime(200, now + 0.25);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.25);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now);
        osc.stop(now + 0.25);
      } else if (type === 'sfx_victory_fanfare') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(523.25, now);
        osc.frequency.setValueAtTime(659.25, now + 0.12);
        osc.frequency.setValueAtTime(783.99, now + 0.24);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.5);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now);
        osc.stop(now + 0.5);
      } else if (type === 'sfx_furnace_blast' || type === 'sfx_molten_burst') {
        osc.type = 'square';
        osc.frequency.setValueAtTime(120, now);
        osc.frequency.exponentialRampToValueAtTime(60, now + 0.35);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.35);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now);
        osc.stop(now + 0.35);
      } else {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(600, now);
        osc.frequency.linearRampToValueAtTime(900, now + 0.15);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.2);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now);
        osc.stop(now + 0.2);
      }
    } catch (e) {}
  }

  // ==========================================================================
  // SECTION 1: SECURITY GATE AUTHENTICATION (K0lst@rno.1)
  // ==========================================================================
  function getAdminToken() {
    return localStorage.getItem('veer_admin_token') || sessionStorage.getItem('veer_admin_token') || '';
  }

  function setAdminToken(token) {
    if (token) {
      localStorage.setItem('veer_admin_token', token);
      sessionStorage.setItem('veer_admin_token', token);
    } else {
      localStorage.removeItem('veer_admin_token');
      sessionStorage.removeItem('veer_admin_token');
    }
  }

  function checkSecurityGate() {
    const token = getAdminToken();
    if (token === CORRECT_PASSCODE) {
      securityGateOverlay.style.display = 'none';
      initializeAdminData();
    } else {
      securityGateOverlay.style.display = 'flex';
      gatePasswordInput.focus();
    }
  }

  formGateAuth.addEventListener('submit', (e) => {
    e.preventDefault();
    const entered = gatePasswordInput.value.trim();
    if (entered === CORRECT_PASSCODE) {
      gateErrorMsg.style.display = 'none';
      setAdminToken(entered);
      playSynthSfx('unlock');
      securityGateOverlay.classList.add('fade-out');
      setTimeout(() => {
        securityGateOverlay.style.display = 'none';
        securityGateOverlay.classList.remove('fade-out');
      }, 400);
      initializeAdminData();
    } else {
      gateErrorMsg.style.display = 'block';
      gatePasswordInput.classList.add('input-error-shake');
      setTimeout(() => {
        gatePasswordInput.classList.remove('input-error-shake');
      }, 500);
    }
  });

  if (btnToggleGatePass) {
    btnToggleGatePass.addEventListener('click', () => {
      gatePasswordInput.type = gatePasswordInput.type === 'password' ? 'text' : 'password';
    });
  }

  if (btnLockAdmin) {
    btnLockAdmin.addEventListener('click', () => {
      setAdminToken('');
      securityGateOverlay.style.display = 'flex';
      gatePasswordInput.value = '';
      gateErrorMsg.style.display = 'none';
      gatePasswordInput.focus();
    });
  }

  async function adminFetch(url, options = {}) {
    const token = getAdminToken();
    options.headers = options.headers || {};
    if (token) {
      options.headers['X-Admin-Token'] = token;
      options.headers['Authorization'] = `Bearer ${token}`;
    }
    const res = await fetch(url, options);
    if (res.status === 401) {
      securityGateOverlay.style.display = 'flex';
    }
    return res;
  }

  // ==========================================================================
  // SECTION 2: INTERACTIVE CHARACTER EMOTE STAGE
  // ==========================================================================
  window.triggerCharEmote = function(charId, emoteId, emoteName, dialogue, soundCue) {
    playSynthSfx(soundCue || 'sfx_friendly_chime');

    const stageId = charId === 'char_phantom_9' ? 'stagePhantom' : 'stageVanguard';
    const actorId = charId === 'char_phantom_9' ? 'visualActorPhantom' : 'visualActorVanguard';
    const bubbleId = charId === 'char_phantom_9' ? 'bubblePhantom' : 'bubbleVanguard';

    const stageEl = document.getElementById(stageId);
    const actorEl = document.getElementById(actorId);
    const bubbleEl = document.getElementById(bubbleId);

    if (!stageEl || !actorEl || !bubbleEl) return;

    // Visual effect on stage
    stageEl.classList.remove('emote-active');
    void stageEl.offsetWidth; // trigger reflow
    stageEl.classList.add('emote-active');

    actorEl.textContent = `⚡ [${emoteName.toUpperCase()}] ACTIVE`;
    bubbleEl.textContent = dialogue;

    setTimeout(() => {
      stageEl.classList.remove('emote-active');
      actorEl.textContent = charId === 'char_phantom_9' ? '🗡️ PHANTOM-9 READY' : '🛡️ SOL-VANGUARD READY';
    }, 2800);
  };

  // ==========================================================================
  // SECTION 3: QUEUED PLAYERS & MATCHMAKING
  // ==========================================================================
  async function fetchCards() {
    try {
      const res = await fetch('/api/cards');
      const data = await res.json();
      if (data.cards) {
        data.cards.forEach(c => {
          allCardsMap[c.id] = c;
        });
      }
    } catch (e) {
      console.error('Failed to load cards:', e);
    }
  }

  function getCardName(cardId) {
    if (allCardsMap[cardId]) return allCardsMap[cardId].name;
    return cardId;
  }

  async function loadSubmissions() {
    try {
      const res = await fetch('/api/submissions');
      const data = await res.json();
      queuedSubmissions = data.submissions || [];

      const activeSubs = queuedSubmissions.filter(s => s.status === 'queued');
      statQueuedPlayers.textContent = activeSubs.length;
      queueCountBadge.textContent = `${activeSubs.length} Queued`;

      renderSubmissionsList(activeSubs);
      renderChips();

    } catch (e) {
      console.error('Failed to load submissions:', e);
    }
  }

  function renderSubmissionsList(activeSubs) {
    if (activeSubs.length === 0) {
      submissionsListContainer.innerHTML = `
        <div style="padding: 36px 20px; text-align: center; color: var(--text-muted); background: rgba(0,0,0,0.2); border-radius: 8px; border: 1px dashed rgba(255,255,255,0.1);">
          <i data-lucide="inbox" style="font-size: 2rem; margin-bottom: 8px; opacity: 0.5;"></i>
          <p style="font-size: 0.95rem; margin-bottom: 4px;">No player loadouts currently queued.</p>
          <p style="font-size: 0.8rem; opacity: 0.7;">Submit tactics from <a href="arena.html" style="color:#00f2ff; text-decoration:underline;">Player Arena</a> to populate queue.</p>
        </div>
      `;
      if (window.lucide) window.lucide.createIcons();
      return;
    }

    submissionsListContainer.innerHTML = activeSubs.map((sub, idx) => {
      const isSelectedA = selectedSubA && selectedSubA.submission_id === sub.submission_id;
      const isSelectedB = selectedSubB && selectedSubB.submission_id === sub.submission_id;
      const atkNames = (sub.attack_cards || []).map(id => getCardName(id)).join(' + ');
      const defNames = (sub.defence_cards || []).map(id => getCardName(id)).join(' + ');

      return `
        <div class="sub-item ${isSelectedA ? 'selected-a' : ''} ${isSelectedB ? 'selected-b' : ''}">
          <div class="sub-item-header">
            <div class="sub-agent-info">
              <span class="sub-badge">#${idx + 1}</span>
              <h4 class="sub-name">${escapeHtml(sub.player_name)}</h4>
            </div>
            <button class="btn btn-secondary btn-xs btn-delete-sub" onclick="window.deleteSub('${escapeHtml(sub.submission_id)}')" title="Remove from queue">
              <i data-lucide="trash-2"></i>
            </button>
          </div>
          <div class="sub-cards-preview">
            <div class="card-line atk"><i data-lucide="swords"></i> ${escapeHtml(atkNames)}</div>
            <div class="card-line def"><i data-lucide="shield"></i> ${escapeHtml(defNames)}</div>
          </div>
          <div class="sub-actions">
            <button class="btn btn-secondary btn-xs ${isSelectedA ? 'btn-active-slot' : ''}" onclick="window.pickForSlot('A', '${escapeHtml(sub.submission_id)}')">
              ${isSelectedA ? '✓ Selected as Player A' : 'Set as Player A'}
            </button>
            <button class="btn btn-secondary btn-xs ${isSelectedB ? 'btn-active-slot' : ''}" onclick="window.pickForSlot('B', '${escapeHtml(sub.submission_id)}')">
              ${isSelectedB ? '✓ Selected as Player B' : 'Set as Player B'}
            </button>
          </div>
        </div>
      `;
    }).join('');

    if (window.lucide) window.lucide.createIcons();
  }

  window.pickForSlot = function(slot, subId) {
    const sub = queuedSubmissions.find(s => s.submission_id === subId);
    if (!sub) return;

    if (slot === 'A') {
      if (selectedSubA && selectedSubA.submission_id === subId) {
        selectedSubA = null;
      } else {
        selectedSubA = sub;
        if (selectedSubB && selectedSubB.submission_id === subId) selectedSubB = null;
      }
    } else if (slot === 'B') {
      if (selectedSubB && selectedSubB.submission_id === subId) {
        selectedSubB = null;
      } else {
        selectedSubB = sub;
        if (selectedSubA && selectedSubA.submission_id === subId) selectedSubA = null;
      }
    }

    renderChips();
    const activeSubs = queuedSubmissions.filter(s => s.status === 'queued');
    renderSubmissionsList(activeSubs);
  };

  window.deleteSub = async function(subId) {
    if (!confirm('Remove this player from the queue?')) return;
    try {
      await adminFetch(`/api/submissions/${subId}`, { method: 'DELETE' });
      if (selectedSubA && selectedSubA.submission_id === subId) selectedSubA = null;
      if (selectedSubB && selectedSubB.submission_id === subId) selectedSubB = null;
      renderChips();
      loadSubmissions();
    } catch (e) {
      alert('Failed to delete submission');
    }
  };

  btnClearQueue.addEventListener('click', async () => {
    if (!confirm('Clear all queued submissions?')) return;
    try {
      await adminFetch('/api/submissions/clear', { method: 'POST' });
      selectedSubA = null;
      selectedSubB = null;
      renderChips();
      loadSubmissions();
    } catch (e) {
      alert('Failed to clear queue');
    }
  });

  function renderChips() {
    if (selectedSubA) {
      chipPlayerA.innerHTML = `<strong>${escapeHtml(selectedSubA.player_name)}</strong> <small style="cursor:pointer;" onclick="window.pickForSlot('A', '${escapeHtml(selectedSubA.submission_id)}')">✕</small>`;
      chipPlayerA.className = 'selected-player-chip filled';
    } else {
      chipPlayerA.innerHTML = `<span class="chip-placeholder">None Selected (Click queue below)</span>`;
      chipPlayerA.className = 'selected-player-chip';
    }

    if (selectedSubB) {
      chipPlayerB.innerHTML = `<strong>${escapeHtml(selectedSubB.player_name)}</strong> <small style="cursor:pointer;" onclick="window.pickForSlot('B', '${escapeHtml(selectedSubB.submission_id)}')">✕</small>`;
      chipPlayerB.className = 'selected-player-chip filled';
    } else {
      chipPlayerB.innerHTML = `<span class="chip-placeholder">None Selected (Click queue below)</span>`;
      chipPlayerB.className = 'selected-player-chip';
    }
  }

  // Radio button styling for winner
  document.querySelectorAll('input[name="manualWinner"]').forEach(radio => {
    radio.addEventListener('change', () => {
      document.querySelectorAll('.winner-radio-btn').forEach(btn => btn.classList.remove('active'));
      radio.closest('.winner-radio-btn').classList.add('active');
    });
  });

  // ==========================================================================
  // SECTION 4: MANUAL MATCH ADJUDICATION & GODOT SEQUENCE GENERATION
  // ==========================================================================
  formManualAdjudicate.addEventListener('submit', async (e) => {
    e.preventDefault();

    const pAName = selectedSubA ? selectedSubA.player_name : 'Agent Alpha';
    const pBName = selectedSubB ? selectedSubB.player_name : 'Agent Omega';

    const atkPool = Object.keys(allCardsMap).filter(k => allCardsMap[k].category === 'attack');
    const defPool = Object.keys(allCardsMap).filter(k => allCardsMap[k].category === 'defence');

    const pAAtk = selectedSubA ? selectedSubA.attack_cards : [atkPool[0] || 'atk_quick_peek', atkPool[1] || 'atk_flash_entry'];
    const pADef = selectedSubA ? selectedSubA.defence_cards : [defPool[0] || 'def_basic_hold', defPool[1] || 'def_defensive_smoke'];

    const pBAtk = selectedSubB ? selectedSubB.attack_cards : [atkPool[2] || 'atk_double_peek', atkPool[3] || 'atk_split_pressure'];
    const pBDef = selectedSubB ? selectedSubB.defence_cards : [defPool[2] || 'def_layered_defense', defPool[3] || 'def_antirush_setup'];

    const winnerRadio = document.querySelector('input[name="manualWinner"]:checked');
    const winnerId = winnerRadio ? winnerRadio.value : 'player_a';

    const payload = {
      submission_a_id: selectedSubA ? selectedSubA.submission_id : null,
      submission_b_id: selectedSubB ? selectedSubB.submission_id : null,
      player_a_name: pAName,
      player_a_attack_cards: pAAtk,
      player_a_defence_cards: pADef,
      player_a_character_id: selectCharA.value,
      player_b_name: pBName,
      player_b_attack_cards: pBAtk,
      player_b_defence_cards: pBDef,
      player_b_character_id: selectCharB.value,
      winner_id: winnerId,
      player_a_score: parseInt(inputScoreA.value, 10) || 13,
      player_b_score: parseInt(inputScoreB.value, 10) || 9,
      win_reason: inputWinReason.value.trim() || 'Tactical superiority and decisive ability coordination.',
      mvp_combo: inputMvpCombo.value.trim() || 'Quick Peek + Flash Entry'
    };

    btnRunManualAdj.disabled = true;
    btnRunManualAdj.innerHTML = `<i data-lucide="loader-2" class="spin"></i> Compiling Godot Combat Sequence...`;
    if (window.lucide) window.lucide.createIcons();

    try {
      const res = await adminFetch('/api/admin/manual-adjudicate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Manual adjudication failed');

      currentGodotSequence = data.godot_sequence;
      renderGodotTimeline(currentGodotSequence);

      if (window.confetti) {
        window.confetti({ particleCount: 100, spread: 90, origin: { y: 0.6 } });
      }

      playSynthSfx('sfx_victory_fanfare');

      // Scroll to Godot section
      document.getElementById('godotExportSection').scrollIntoView({ behavior: 'smooth' });

      // Clear selected players & refresh
      selectedSubA = null;
      selectedSubB = null;
      renderChips();
      loadSubmissions();
      loadPlayers();
      loadMatchesHistory();

    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      btnRunManualAdj.disabled = false;
      btnRunManualAdj.innerHTML = `<i data-lucide="play"></i> Generate AI Godot Combat Sequence & Record Match`;
      if (window.lucide) window.lucide.createIcons();
    }
  });

  // ==========================================================================
  // SECTION 5: GODOT TIMELINE RENDERING & JSON EXPORT
  // ==========================================================================
  function renderGodotTimeline(seq) {
    if (!seq || !seq.timeline) return;

    godotRawJsonDisplay.textContent = JSON.stringify(seq, null, 2);

    godotTimelineList.innerHTML = `
      <div class="godot-timeline-header-card">
        <div class="godot-meta-left">
          <span class="godot-badge">🏆 Winner: ${escapeHtml(seq.winner_name)} (${seq.player_a_score}-${seq.player_b_score})</span>
          <h3 style="margin-top:4px; font-size:1.1rem; color:#ffd700;">MVP: ${escapeHtml(seq.mvp_combo)}</h3>
          <p style="color:var(--text-muted); font-size:0.85rem;">${escapeHtml(seq.win_reason)}</p>
        </div>
        <div class="godot-meta-right">
          <div style="font-family:var(--font-mono); font-size:0.85rem; color:#00f2ff;">⏱️ Total Duration: ${seq.total_duration_sec}s</div>
          <div style="font-family:var(--font-mono); font-size:0.85rem; color:var(--text-muted);">${seq.timeline.length} Keyframe Events</div>
        </div>
      </div>
      <div class="godot-steps-list">
        ${seq.timeline.map((step, idx) => {
          const isPlayerA = step.actor === 'player_a';
          const actorBadgeColor = isPlayerA ? '#00f2ff' : '#ff5e00';
          return `
            <div class="godot-step-row ${isPlayerA ? 'actor-a' : 'actor-b'}">
              <div class="step-time-col">
                <span class="step-badge">#${step.step}</span>
                <span class="step-timestamp">${step.timestamp_sec.toFixed(1)}s</span>
              </div>
              <div class="step-content-col">
                <div class="step-actor-line">
                  <strong style="color:${actorBadgeColor};">${isPlayerA ? 'PLAYER A' : 'PLAYER B'} (${escapeHtml(step.character_name || step.character_id)})</strong>
                  <span class="action-type-tag">${escapeHtml(step.action_type)}</span>
                  ${step.emote_trigger ? `<span class="emote-active-tag">🎭 ${escapeHtml(step.emote_trigger)}</span>` : ''}
                </div>
                <p class="step-commentary">${escapeHtml(step.commentary)}</p>
                <div class="step-godot-tags">
                  <code>Trigger: ${escapeHtml(step.animation_trigger)}</code>
                  ${step.sound_cue ? `<code>SFX: ${escapeHtml(step.sound_cue)}</code>` : ''}
                  ${step.damage_dealt ? `<code style="color:#ef4444;">💥 -${step.damage_dealt} HP</code>` : ''}
                </div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;

    if (window.lucide) window.lucide.createIcons();
  }

  btnCopyGodotJson.addEventListener('click', () => {
    if (!currentGodotSequence) {
      alert('Please adjudicate a match first to generate the Godot sequence!');
      return;
    }
    const jsonStr = JSON.stringify(currentGodotSequence, null, 2);
    navigator.clipboard.writeText(jsonStr).then(() => {
      alert('✓ Godot Timeline JSON copied to clipboard! Ready to paste into Godot.');
    }).catch(() => {
      alert('Failed to copy. Please expand the Raw JSON box below and copy manually.');
    });
  });

  btnDownloadGodotJson.addEventListener('click', () => {
    if (!currentGodotSequence) {
      alert('Please adjudicate a match first to generate the Godot sequence!');
      return;
    }
    const jsonStr = JSON.stringify(currentGodotSequence, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `godot_match_sequence_${currentGodotSequence.match_id || 'latest'}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  // ==========================================================================
  // SECTION 6: DEDICATED PLAYERS LEADERBOARD
  // ==========================================================================
  async function loadPlayers() {
    try {
      const res = await fetch('/api/players');
      const data = await res.json();
      const players = data.players || [];

      statRegisteredPlayers.textContent = players.length;
      playerCountBadge.textContent = `${players.length} Players`;

      if (players.length === 0) {
        playersTableBody.innerHTML = `
          <tr>
            <td colspan="7" class="text-center" style="padding: 24px; color: var(--text-muted);">
              No player records found. Players will be automatically registered when submitting loadouts.
            </td>
          </tr>
        `;
        return;
      }

      playersTableBody.innerHTML = players.map((p, idx) => {
        const medal = idx === 0 ? '🥇' : (idx === 1 ? '🥈' : (idx === 2 ? '🥉' : `#${idx + 1}`));
        return `
          <tr>
            <td><strong>${medal}</strong></td>
            <td><strong style="color:#00f2ff;">${escapeHtml(p.username)}</strong></td>
            <td>${p.matches_played}</td>
            <td><span style="color:#22c55e;">${p.wins}W</span> / <span style="color:#ef4444;">${p.losses}L</span> / <span style="color:#94a3b8;">${p.draws}D</span></td>
            <td><strong>${p.win_rate_pct}%</strong></td>
            <td><span class="table-winner-pill" style="background:rgba(168,85,247,0.15); color:#c084fc; border-color:rgba(168,85,247,0.3); font-weight:700;">★ ${p.total_score}</span></td>
            <td style="color:var(--text-muted); font-size:0.85rem;">${escapeHtml(p.last_active)}</td>
          </tr>
        `;
      }).join('');

      if (window.lucide) window.lucide.createIcons();

    } catch (e) {
      console.error('Failed to load players leaderboard:', e);
    }
  }

  // ==========================================================================
  // SECTION 7: MATCHES HISTORY ARCHIVE
  // ==========================================================================
  async function loadMatchesHistory() {
    try {
      const res = await fetch('/api/matches');
      const data = await res.json();
      storedMatches = data.matches || [];

      statCompletedMatches.textContent = storedMatches.length;
      historyCountBadge.textContent = `${storedMatches.length} Records`;

      if (storedMatches.length === 0) {
        matchesTableBody.innerHTML = `
          <tr>
            <td colspan="7" class="text-center" style="padding: 24px; color: var(--text-muted);">
              No matches evaluated yet. Run a match above to populate the archive.
            </td>
          </tr>
        `;
        return;
      }

      matchesTableBody.innerHTML = storedMatches.map(m => {
        const evalData = m.evaluation || {};
        const pAName = m.player_a ? m.player_a.name : 'Player A';
        const pBName = m.player_b ? m.player_b.name : 'Player B';
        const winner = evalData.winner_name || (m.winner_name || 'Evaluating...');
        const scoreA = evalData.player_a_score ? evalData.player_a_score.total_score : (m.player_a_score ?? '-');
        const scoreB = evalData.player_b_score ? evalData.player_b_score.total_score : (m.player_b_score ?? '-');

        return `
          <tr>
            <td><code>${escapeHtml(m.match_id)}</code></td>
            <td style="color:var(--text-muted);">${escapeHtml(m.created_at || '')}</td>
            <td><strong>${escapeHtml(pAName)}</strong></td>
            <td><strong>${escapeHtml(pBName)}</strong></td>
            <td><span class="table-winner-pill">🏆 ${escapeHtml(winner)}</span></td>
            <td>${scoreA} - ${scoreB}</td>
            <td>
              <button class="btn btn-secondary btn-xs" onclick="window.viewMatchDetails('${escapeHtml(m.match_id)}')">
                <i data-lucide="eye"></i> View
              </button>
              <button class="btn btn-secondary btn-xs" onclick="window.loadMatchGodotSequence('${escapeHtml(m.match_id)}')" title="Load in Godot Timeline view">
                <i data-lucide="gamepad-2"></i> Godot
              </button>
            </td>
          </tr>
        `;
      }).join('');

      if (window.lucide) window.lucide.createIcons();

    } catch (e) {
      console.error('Failed to load matches history:', e);
    }
  }

  window.loadMatchGodotSequence = async function(matchId) {
    try {
      const res = await fetch(`/api/matches/${matchId}/godot-sequence`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load sequence');
      currentGodotSequence = data;
      renderGodotTimeline(data);
      document.getElementById('godotExportSection').scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      alert('Error loading Godot sequence: ' + err.message);
    }
  };

  window.viewMatchDetails = function(matchId) {
    const match = storedMatches.find(m => m.match_id === matchId);
    if (!match) return;

    const evalData = match.evaluation;
    modalMatchTitle.innerHTML = `<i data-lucide="file-text"></i> Match ${escapeHtml(match.match_id)}`;
    modalMatchSub.textContent = `Created: ${match.created_at} • Status: ${match.status}`;

    if (!evalData) {
      modalMatchContent.innerHTML = `<p style="padding:20px; color:var(--text-muted);">Match record has no detailed evaluation data.</p>`;
    } else {
      modalMatchContent.innerHTML = `
        <div style="margin-bottom:16px;">
          <h3 style="font-family:var(--font-display); font-size:1.4rem; color:#ffd700;">Winner: ${escapeHtml(evalData.winner_name)}</h3>
          <p style="color:var(--text-muted);">${escapeHtml(evalData.win_reason)}</p>
        </div>
        <div style="background:rgba(0,0,0,0.4); padding:12px; border-radius:8px; margin-bottom:14px; font-family:var(--font-mono); font-size:0.85rem;">
          <div><strong>🎙️ Commentary:</strong></div>
          <p style="margin-top:6px; color:#ddd;">${escapeHtml(evalData.play_by_play_commentary)}</p>
        </div>
        <div style="background:rgba(0,0,0,0.4); padding:12px; border-radius:8px; font-family:var(--font-mono); font-size:0.85rem;">
          <div><strong>📜 Combat Log:</strong></div>
          <ul style="margin-top:6px; padding-left:16px; color:#ddd;">
            ${(evalData.combat_log || []).map(l => `<li>${escapeHtml(l)}</li>`).join('')}
          </ul>
        </div>
      `;
    }

    matchDetailModal.classList.add('active');
    if (window.lucide) window.lucide.createIcons();
  };

  btnCloseMatchModal.addEventListener('click', () => {
    matchDetailModal.classList.remove('active');
  });

  // Refresh All
  btnRefreshAll.addEventListener('click', () => {
    loadSubmissions();
    loadPlayers();
    loadMatchesHistory();
  });

  // Helper Escape
  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function initializeAdminData() {
    fetchCards().then(() => {
      loadSubmissions();
      loadPlayers();
      loadMatchesHistory();
    });
  }

  // Check gate upon load
  checkSecurityGate();

  // Auto-polling for new submissions every 5 seconds
  setInterval(() => {
    if (getAdminToken() === CORRECT_PASSCODE) {
      loadSubmissions();
    }
  }, 5000);

});
