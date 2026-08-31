/**
 * ============================================================================
 * ADMIN COMMAND CENTER SCRIPT (admin.js)
 * ============================================================================
 * Orchestrates 3 AI API Keys, Player Submissions Queue, Deterministic 1v1
 * Matchmaking, Sequential Tournament Execution, and Real-time Results.
 * Hardened with XSS prevention and X-Admin-Token authentication.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide Icons
  if (window.lucide) {
    window.lucide.createIcons();
  }

  // State
  let allCardsMap = {};
  let queuedSubmissions = [];
  let storedMatches = [];
  let selectedSubA = null; // { submission_id, player_name, attack_cards, defence_cards }
  let selectedSubB = null;

  // DOM Elements - Metrics
  const statQueuedPlayers = document.getElementById('statQueuedPlayers');
  const statRegisteredPlayers = document.getElementById('statRegisteredPlayers');
  const statCompletedMatches = document.getElementById('statCompletedMatches');
  const statConfiguredKeys = document.getElementById('statConfiguredKeys');
  const queueCountBadge = document.getElementById('queueCountBadge');
  const playerCountBadge = document.getElementById('playerCountBadge');
  const historyCountBadge = document.getElementById('historyCountBadge');
  const btnRefreshAll = document.getElementById('btnRefreshAll');
  const btnAdminPasscode = document.getElementById('btnAdminPasscode');
  const playersTableBody = document.getElementById('playersTableBody');

  // DOM Elements - API Keys
  const formApiKeys = document.getElementById('formApiKeys');
  const inputAttackKey = document.getElementById('inputAttackKey');
  const inputDefenceKey = document.getElementById('inputDefenceKey');
  const inputEvalKey = document.getElementById('inputEvalKey');
  const badgeAttackKey = document.getElementById('badgeAttackKey');
  const badgeDefenceKey = document.getElementById('badgeDefenceKey');
  const badgeEvalKey = document.getElementById('badgeEvalKey');
  const previewAttackKey = document.getElementById('previewAttackKey');
  const previewDefenceKey = document.getElementById('previewDefenceKey');
  const previewEvalKey = document.getElementById('previewEvalKey');
  const keysSavedNotice = document.getElementById('keysSavedNotice');

  // DOM Elements - Matchmaking
  const chipPlayerA = document.getElementById('chipPlayerA');
  const chipPlayerB = document.getElementById('chipPlayerB');
  const btnExecuteSelectedMatch = document.getElementById('btnExecuteSelectedMatch');
  const btnExecuteSequence = document.getElementById('btnExecuteSequence');
  const btnClearQueue = document.getElementById('btnClearQueue');
  const submissionsListContainer = document.getElementById('submissionsListContainer');

  // DOM Elements - Live Combat Console
  const combatStatusBadge = document.getElementById('combatStatusBadge');
  const aiStepper = document.getElementById('aiStepper');
  const step1 = document.getElementById('step1');
  const step2 = document.getElementById('step2');
  const step3 = document.getElementById('step3');
  const matchResultView = document.getElementById('matchResultView');

  const resWinnerName = document.getElementById('resWinnerName');
  const resWinReason = document.getElementById('resWinReason');
  const resMvpCombo = document.getElementById('resMvpCombo');
  const resPlayerAName = document.getElementById('resPlayerAName');
  const resPlayerBName = document.getElementById('resPlayerBName');
  const resScoreA = document.getElementById('resScoreA');
  const resScoreB = document.getElementById('resScoreB');
  const resSynergyValA = document.getElementById('resSynergyValA');
  const resSynergyValB = document.getElementById('resSynergyValB');
  const resSynergyFillA = document.getElementById('resSynergyFillA');
  const resSynergyFillB = document.getElementById('resSynergyFillB');
  const resLoadoutA = document.getElementById('resLoadoutA');
  const resLoadoutB = document.getElementById('resLoadoutB');
  const resSeqTitleA = document.getElementById('resSeqTitleA');
  const resSeqTitleB = document.getElementById('resSeqTitleB');
  const resSequenceListA = document.getElementById('resSequenceListA');
  const resSequenceListB = document.getElementById('resSequenceListB');
  const resCommentaryText = document.getElementById('resCommentaryText');
  const resCombatLogs = document.getElementById('resCombatLogs');

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

  // Toggle Password Visibility
  document.querySelectorAll('.btn-toggle-vis').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (input) {
        input.type = input.type === 'password' ? 'text' : 'password';
      }
    });
  });

  // ==========================================================================
  // SECTION 0: ADMIN AUTHENTICATION TOKEN HELPERS
  // ==========================================================================
  function getAdminToken() {
    return localStorage.getItem('veer_admin_token') || '';
  }

  function setAdminToken(token) {
    if (token && token.trim()) {
      localStorage.setItem('veer_admin_token', token.trim());
    } else {
      localStorage.removeItem('veer_admin_token');
    }
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
      const pass = prompt('🔐 Admin Passcode Required:\nPlease enter the admin passcode:');
      if (pass !== null) {
        setAdminToken(pass.trim());
        options.headers['X-Admin-Token'] = pass.trim();
        options.headers['Authorization'] = `Bearer ${pass.trim()}`;
        return fetch(url, options);
      }
    }
    return res;
  }

  if (btnAdminPasscode) {
    btnAdminPasscode.addEventListener('click', async () => {
      const current = getAdminToken();
      const newPass = prompt(
        '🔐 Configure Admin Passcode:\nEnter your ADMIN_PASSWORD (or leave blank to clear saved token):',
        current
      );
      if (newPass !== null) {
        setAdminToken(newPass);
        // Verify with backend
        try {
          const res = await adminFetch('/api/admin/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
          });
          const data = await res.json();
          if (res.ok && data.valid) {
            alert('✓ Admin authentication verified successfully!');
          } else {
            alert('⚠️ Passcode saved locally, but server rejected verification.');
          }
        } catch (err) {
          alert('Passcode saved locally.');
        }
        loadApiKeys();
      }
    });
  }

  // ==========================================================================
  // SECTION 1: FETCH CARDS DATABASE
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

  // ==========================================================================
  // SECTION 2: 3 AI API KEYS MANAGEMENT
  // ==========================================================================
  async function loadApiKeys() {
    try {
      const res = await adminFetch('/api/admin/keys');
      if (res.status === 401) {
        statConfiguredKeys.textContent = 'Auth Req';
        return;
      }
      const data = await res.json();

      let activeCount = 0;

      // 1. Attack Key
      if (data.attack_ai) {
        const isAct = data.attack_ai.configured;
        if (isAct) activeCount++;
        badgeAttackKey.textContent = isAct ? '✓ Live Gemini' : 'Offline Mock';
        badgeAttackKey.className = `key-status-badge ${isAct ? 'active' : 'mock'}`;
        previewAttackKey.textContent = `Current: ${data.attack_ai.preview}`;
      }

      // 2. Defence Key
      if (data.defence_ai) {
        const isAct = data.defence_ai.configured;
        if (isAct) activeCount++;
        badgeDefenceKey.textContent = isAct ? '✓ Live Gemini' : 'Offline Mock';
        badgeDefenceKey.className = `key-status-badge ${isAct ? 'active' : 'mock'}`;
        previewDefenceKey.textContent = `Current: ${data.defence_ai.preview}`;
      }

      // 3. Evaluation Key
      if (data.evaluation_ai) {
        const isAct = data.evaluation_ai.configured;
        if (isAct) activeCount++;
        badgeEvalKey.textContent = isAct ? '✓ Live Gemini' : 'Offline Mock';
        badgeEvalKey.className = `key-status-badge ${isAct ? 'active' : 'mock'}`;
        previewEvalKey.textContent = `Current: ${data.evaluation_ai.preview}`;
      }

      statConfiguredKeys.textContent = `${activeCount}/3`;

    } catch (e) {
      console.error('Failed to load API keys:', e);
    }
  }

  formApiKeys.addEventListener('submit', async (e) => {
    e.preventDefault();

    const payload = {};
    const atkVal = inputAttackKey.value.trim();
    const defVal = inputDefenceKey.value.trim();
    const evalVal = inputEvalKey.value.trim();

    if (atkVal) payload.attack_key = atkVal;
    if (defVal) payload.defence_key = defVal;
    if (evalVal) payload.evaluation_key = evalVal;

    try {
      const res = await adminFetch('/api/admin/keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (data.status === 'success') {
        keysSavedNotice.style.display = 'block';
        setTimeout(() => { keysSavedNotice.style.display = 'none'; }, 4000);
        inputAttackKey.value = '';
        inputDefenceKey.value = '';
        inputEvalKey.value = '';
        loadApiKeys();
      } else {
        alert(data.error || 'Failed to save API keys');
      }
    } catch (e) {
      alert('Error updating API keys');
    }
  });

  // ==========================================================================
  // SECTION 3: PLAYER SUBMISSIONS QUEUE & MATCHMAKING
  // ==========================================================================
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
      updateMatchmakingActionState();

    } catch (e) {
      console.error('Failed to load submissions:', e);
    }
  }

  function renderSubmissionsList(activeSubs) {
    if (activeSubs.length === 0) {
      submissionsListContainer.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 36px 20px; text-align: center; color: var(--text-muted); background: rgba(0,0,0,0.2); border-radius: 8px; border: 1px dashed rgba(255,255,255,0.1);">
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
    updateMatchmakingActionState();
  };

  window.deleteSub = async function(subId) {
    if (!confirm('Remove this player from the queue?')) return;
    try {
      await adminFetch(`/api/submissions/${subId}`, { method: 'DELETE' });
      if (selectedSubA && selectedSubA.submission_id === subId) selectedSubA = null;
      if (selectedSubB && selectedSubB.submission_id === subId) selectedSubB = null;
      renderChips();
      loadSubmissions();
      updateMatchmakingActionState();
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
      updateMatchmakingActionState();
    } catch (e) {
      alert('Failed to clear queue');
    }
  });

  function renderChips() {
    if (selectedSubA) {
      chipPlayerA.innerHTML = `<strong>${escapeHtml(selectedSubA.player_name)}</strong> <small style="cursor:pointer;" onclick="window.pickForSlot('A', '${escapeHtml(selectedSubA.submission_id)}')">✕</small>`;
      chipPlayerA.className = 'selected-player-chip filled';
    } else {
      chipPlayerA.innerHTML = `<span class="chip-placeholder">None Selected (Click below)</span>`;
      chipPlayerA.className = 'selected-player-chip';
    }

    if (selectedSubB) {
      chipPlayerB.innerHTML = `<strong>${escapeHtml(selectedSubB.player_name)}</strong> <small style="cursor:pointer;" onclick="window.pickForSlot('B', '${escapeHtml(selectedSubB.submission_id)}')">✕</small>`;
      chipPlayerB.className = 'selected-player-chip filled';
    } else {
      chipPlayerB.innerHTML = `<span class="chip-placeholder">None Selected (Click below)</span>`;
      chipPlayerB.className = 'selected-player-chip';
    }
  }

  function updateMatchmakingActionState() {
    btnExecuteSelectedMatch.disabled = !(selectedSubA && selectedSubB);
  }

  // ==========================================================================
  // SECTION 4: 1v1 MATCH EXECUTION & SEQUENCE RUNNER
  // ==========================================================================
  btnExecuteSelectedMatch.addEventListener('click', async () => {
    if (!selectedSubA || !selectedSubB) {
      alert('Please select both Player A and Player B from the queue!');
      return;
    }

    document.getElementById('liveCombatSection').scrollIntoView({ behavior: 'smooth' });
    startStepperAnim();

    try {
      combatStatusBadge.textContent = 'Adjudicating with 3 AIs...';
      combatStatusBadge.className = 'panel-badge live';

      const response = await adminFetch('/api/admin/execute-match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          submission_a_id: selectedSubA.submission_id,
          submission_b_id: selectedSubB.submission_id
        })
      });

      const resData = await response.json();
      if (!response.ok) throw new Error(resData.error || 'Adjudication failed');

      finishStepperAnim();

      if (resData.match && resData.match.evaluation) {
        renderMatchResult(resData.match, resData.execution ? resData.execution.result : null);
        if (window.confetti) {
          window.confetti({ particleCount: 100, spread: 90, origin: { y: 0.6 } });
        }
      }

      selectedSubA = null;
      selectedSubB = null;
      renderChips();
      loadSubmissions();
      loadPlayers();
      loadMatchesHistory();

    } catch (err) {
      combatStatusBadge.textContent = 'Adjudication Error';
      alert('AI Execution Error: ' + err.message);
      resetStepper();
    }
  });

  btnExecuteSequence.addEventListener('click', async () => {
    const activeQueued = queuedSubmissions.filter(s => s.status === 'queued');
    if (activeQueued.length < 2) {
      alert(`At least 2 queued players are required to run a sequence tournament! (Currently have ${activeQueued.length})`);
      return;
    }

    if (!confirm(`Run tournament rounds for all ${activeQueued.length} queued players in sequential order?`)) return;

    document.getElementById('liveCombatSection').scrollIntoView({ behavior: 'smooth' });
    startStepperAnim();

    try {
      combatStatusBadge.textContent = 'Sequencing Tournament Rounds...';
      const response = await adminFetch('/api/admin/execute-sequence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });

      const resData = await response.json();
      if (!response.ok) throw new Error(resData.error || 'Sequence failed');

      finishStepperAnim();

      if (resData.matches && resData.matches.length > 0) {
        renderMatchResult(resData.matches[resData.matches.length - 1]);
        if (window.confetti) {
          window.confetti({ particleCount: 120, spread: 100, origin: { y: 0.6 } });
        }
      }

      selectedSubA = null;
      selectedSubB = null;
      renderChips();
      loadSubmissions();
      loadPlayers();
      loadMatchesHistory();

    } catch (err) {
      combatStatusBadge.textContent = 'Sequence Error';
      alert('Sequence Execution Error: ' + err.message);
      resetStepper();
    }
  });

  function startStepperAnim() {
    aiStepper.style.display = 'flex';
    matchResultView.style.display = 'none';

    step1.className = 'stepper-step active';
    step2.className = 'stepper-step';
    step3.className = 'stepper-step';

    setTimeout(() => {
      step1.className = 'stepper-step done';
      step2.className = 'stepper-step active';
    }, 900);

    setTimeout(() => {
      step2.className = 'stepper-step done';
      step3.className = 'stepper-step active';
    }, 1800);
  }

  function finishStepperAnim() {
    step1.className = 'stepper-step done';
    step2.className = 'stepper-step done';
    step3.className = 'stepper-step done';
  }

  function resetStepper() {
    aiStepper.style.display = 'none';
  }

  function renderMatchResult(match, execDetails) {
    const evalData = match.evaluation || {};
    combatStatusBadge.textContent = `Match Completed: ${match.match_id}`;
    combatStatusBadge.className = 'panel-badge live';

    matchResultView.style.display = 'block';

    // Summary
    resWinnerName.textContent = evalData.winner_name || match.winner_name || 'Match Complete';
    resWinReason.textContent = evalData.win_reason || 'Tactical superiority established.';
    resMvpCombo.textContent = `MVP Combo: ${evalData.mvp_combo || evalData.mvp_card_combo || 'Tactical Coordination'}`;

    // Player comparison
    const pAName = match.player_a ? match.player_a.name : 'Player A';
    const pBName = match.player_b ? match.player_b.name : 'Player B';
    resPlayerAName.textContent = pAName;
    resPlayerBName.textContent = pBName;

    const scoreA = evalData.player_a_score ? evalData.player_a_score.total_score : (match.player_a_score || 0);
    const scoreB = evalData.player_b_score ? evalData.player_b_score.total_score : (match.player_b_score || 0);
    resScoreA.textContent = `${scoreA} PTS`;
    resScoreB.textContent = `${scoreB} PTS`;

    const synA = evalData.player_a_score ? (evalData.player_a_score.synergy_score || 70) : 70;
    const synB = evalData.player_b_score ? (evalData.player_b_score.synergy_score || 70) : 70;
    resSynergyValA.textContent = `${synA}%`;
    resSynergyValB.textContent = `${synB}%`;
    resSynergyFillA.style.width = `${synA}%`;
    resSynergyFillB.style.width = `${synB}%`;

    // Loadouts
    const pAAtks = (match.player_a.attack_cards || []).map(id => `<span class="card-tag atk">${escapeHtml(getCardName(id))}</span>`).join(' ');
    const pADefs = (match.player_a.defence_cards || []).map(id => `<span class="card-tag def">${escapeHtml(getCardName(id))}</span>`).join(' ');
    resLoadoutA.innerHTML = `${pAAtks} ${pADefs}`;

    const pBAtks = (match.player_b.attack_cards || []).map(id => `<span class="card-tag atk">${escapeHtml(getCardName(id))}</span>`).join(' ');
    const pBDefs = (match.player_b.defence_cards || []).map(id => `<span class="card-tag def">${escapeHtml(getCardName(id))}</span>`).join(' ');
    resLoadoutB.innerHTML = `${pBAtks} ${pBDefs}`;

    // Tactical sequences
    resSeqTitleA.textContent = `${pAName}'s Execution Sequence`;
    resSeqTitleB.textContent = `${pBName}'s Execution Sequence`;

    const execAAtk = (execDetails && execDetails.player_a_attack_sequence) ? execDetails.player_a_attack_sequence : [];
    const execADef = (execDetails && execDetails.player_a_defence_sequence) ? execDetails.player_a_defence_sequence : [];
    const execBAtk = (execDetails && execDetails.player_b_attack_sequence) ? execDetails.player_b_attack_sequence : [];
    const execBDef = (execDetails && execDetails.player_b_defence_sequence) ? execDetails.player_b_defence_sequence : [];

    function formatSequenceList(atkSeq, defSeq, pObj) {
      let html = '';
      if (atkSeq.length > 0) {
        atkSeq.forEach(act => {
          html += `<div style="padding:4px 8px; background:rgba(255,94,0,0.1); border-radius:4px;"><strong>Step ${act.order}:</strong> ${escapeHtml(getCardName(act.card_id))} &rarr; <em>${escapeHtml(act.target)}</em> (${escapeHtml(act.reason)})</div>`;
        });
      } else {
        (pObj.attack_cards || []).forEach((cid, i) => {
          html += `<div style="padding:4px 8px; background:rgba(255,94,0,0.1); border-radius:4px;"><strong>Action ${i+1}:</strong> Execute ${escapeHtml(getCardName(cid))}</div>`;
        });
      }

      if (defSeq.length > 0) {
        defSeq.forEach(act => {
          html += `<div style="padding:4px 8px; background:rgba(0,242,255,0.1); border-radius:4px;"><strong>Reaction ${act.order}:</strong> ${escapeHtml(getCardName(act.card_id))} &rarr; <em>${escapeHtml(act.target)}</em> (${escapeHtml(act.reason)})</div>`;
        });
      } else {
        (pObj.defence_cards || []).forEach((cid, i) => {
          html += `<div style="padding:4px 8px; background:rgba(0,242,255,0.1); border-radius:4px;"><strong>Reaction ${i+1}:</strong> Deploy ${escapeHtml(getCardName(cid))}</div>`;
        });
      }
      return html;
    }

    resSequenceListA.innerHTML = formatSequenceList(execAAtk, execADef, match.player_a);
    resSequenceListB.innerHTML = formatSequenceList(execBAtk, execBDef, match.player_b);

    // Commentary & Combat Logs
    resCommentaryText.textContent = evalData.play_by_play_commentary || 'Both players executed high-tempo rounds with strategic utility usage.';
    if (evalData.combat_log && evalData.combat_log.length > 0) {
      resCombatLogs.innerHTML = evalData.combat_log.map(log => `
        <div class="combat-log-item">${escapeHtml(log)}</div>
      `).join('');
    } else {
      resCombatLogs.innerHTML = `<div class="combat-log-item">${escapeHtml(evalData.tactical_breakdown || 'Combat complete.')}</div>`;
    }

    if (window.lucide) window.lucide.createIcons();
  }

  // ==========================================================================
  // SECTION 5: DEDICATED PLAYER DATABASE & LEADERBOARD
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
  // SECTION 6: MATCHES HISTORY ARCHIVE
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
            </td>
          </tr>
        `;
      }).join('');

      if (window.lucide) window.lucide.createIcons();

    } catch (e) {
      console.error('Failed to load matches history:', e);
    }
  }

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
    loadApiKeys();
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

  // Initial Load
  fetchCards().then(() => {
    loadApiKeys();
    loadSubmissions();
    loadPlayers();
    loadMatchesHistory();
  });

  // Auto-polling for new web submissions every 5 seconds
  setInterval(() => {
    loadSubmissions();
  }, 5000);

});
