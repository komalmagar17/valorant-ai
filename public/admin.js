/**
 * ============================================================================
 * CLEAN ADMIN DASHBOARD SCRIPT (admin.js)
 * ============================================================================
 * Focuses strictly on real player data, real submissions queue, and manual
 * match adjudication with Godot sequence generation.
 * Protected by passcode: K0lst@rno.1
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
  let registeredPlayers = [];
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
  const btnClearAllData = document.getElementById('btnClearAllData');

  // DOM Elements - Tables
  const submissionsTableBody = document.getElementById('submissionsTableBody');
  const matchesTableBody = document.getElementById('matchesTableBody');
  const playersTableBody = document.getElementById('playersTableBody');
  const btnClearQueue = document.getElementById('btnClearQueue');

  // DOM Elements - Matchmaking Slot View
  const slotNameA = document.getElementById('slotNameA');
  const slotCardsA = document.getElementById('slotCardsA');
  const slotNameB = document.getElementById('slotNameB');
  const slotCardsB = document.getElementById('slotCardsB');
  const selectCharA = document.getElementById('selectCharA');
  const selectCharB = document.getElementById('selectCharB');

  // DOM Elements - Form & Outcome Controls
  const formManualAdjudicate = document.getElementById('formManualAdjudicate');
  const inputScoreA = document.getElementById('inputScoreA');
  const inputScoreB = document.getElementById('inputScoreB');
  const btnRunManualAdj = document.getElementById('btnRunManualAdj');

  // DOM Elements - Godot Result Card
  const godotResultCard = document.getElementById('godotResultCard');
  const resMatchSummaryTitle = document.getElementById('resMatchSummaryTitle');
  const godotRawJsonDisplay = document.getElementById('godotRawJsonDisplay');
  const btnCopyGodotJson = document.getElementById('btnCopyGodotJson');
  const btnDownloadGodotJson = document.getElementById('btnDownloadGodotJson');

  // Custom Cursor
  const cursor = document.getElementById('customCursor');
  if (cursor) {
    window.addEventListener('mousemove', (e) => {
      cursor.style.left = `${e.clientX}px`;
      cursor.style.top = `${e.clientY}px`;
    });
  }

  // ==========================================================================
  // 1. SECURITY PASSCODE AUTHENTICATION (PASSWORD GATE)
  // ==========================================================================
  function getAdminToken() {
    return sessionStorage.getItem('valorant_admin_auth_token') || '';
  }

  function setAdminToken(token) {
    if (token) {
      sessionStorage.setItem('valorant_admin_auth_token', token);
    } else {
      sessionStorage.removeItem('valorant_admin_auth_token');
    }
  }

  async function checkSecurityGate() {
    const token = getAdminToken();
    if (!token) {
      securityGateOverlay.style.display = 'flex';
      gatePasswordInput.focus();
      return;
    }

    try {
      const res = await fetch('/api/admin/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': token
        },
        body: JSON.stringify({})
      });
      const data = await res.json();
      if (res.ok && data.valid) {
        securityGateOverlay.style.display = 'none';
        initializeAdminData();
      } else {
        setAdminToken('');
        securityGateOverlay.style.display = 'flex';
        gatePasswordInput.focus();
      }
    } catch (err) {
      securityGateOverlay.style.display = 'flex';
      gatePasswordInput.focus();
    }
  }

  formGateAuth.addEventListener('submit', async (e) => {
    e.preventDefault();
    const entered = gatePasswordInput.value.trim();
    if (!entered) return;

    const unlockBtn = document.getElementById('btnGateUnlock');
    if (unlockBtn) {
      unlockBtn.disabled = true;
      unlockBtn.textContent = 'Verifying...';
    }

    try {
      const res = await fetch('/api/admin/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': entered
        },
        body: JSON.stringify({})
      });

      const data = await res.json();
      if (res.ok && data.valid) {
        gateErrorMsg.style.display = 'none';
        setAdminToken(entered);
        securityGateOverlay.style.display = 'none';
        initializeAdminData();
      } else {
        throw new Error('Invalid passcode');
      }
    } catch (err) {
      gateErrorMsg.style.display = 'block';
      gatePasswordInput.classList.add('input-error-shake');
      setTimeout(() => {
        gatePasswordInput.classList.remove('input-error-shake');
      }, 500);
      gatePasswordInput.select();
    } finally {
      if (unlockBtn) {
        unlockBtn.disabled = false;
        unlockBtn.textContent = 'Unlock Dashboard';
      }
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

  if (btnClearAllData) {
    btnClearAllData.addEventListener('click', async () => {
      const confirmed = confirm('⚠️ DANGER: This will permanently wipe ALL player submissions, match history, and registered players from the database.\n\nAre you sure you want to reset the admin panel to a completely clean state?');
      if (!confirmed) return;

      try {
        const res = await adminFetch('/api/admin/clear-all-data', { method: 'POST' });
        const data = await res.json();
        if (res.ok && data.status === 'cleared') {
          selectedSubA = null;
          selectedSubB = null;
          currentGodotSequence = null;
          if (godotResultCard) godotResultCard.style.display = 'none';
          loadSubmissions();
          loadMatchesHistory();
          loadPlayers();
          alert('✓ All admin panel data has been completely cleared and reset.');
        } else {
          alert('Error: ' + (data.error || 'Failed to clear database data.'));
        }
      } catch (err) {
        alert('Error clearing data: ' + err.message);
      }
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
  // 2. REAL SUBMISSIONS QUEUE
  // ==========================================================================
  async function fetchCards() {
    // 1. Immediate preloaded dataset
    if (window.TACTICAL_CARDS_DATA && Array.isArray(window.TACTICAL_CARDS_DATA)) {
      window.TACTICAL_CARDS_DATA.forEach(c => {
        allCardsMap[c.id] = c;
      });
    }

    // 2. Network fetch
    try {
      const res = await fetch('/api/cards');
      if (res.ok) {
        const data = await res.json();
        if (data.cards) {
          data.cards.forEach(c => {
            allCardsMap[c.id] = c;
          });
          return;
        }
      }
    } catch (e) {
      console.warn('Live /api/cards fetch error:', e);
    }

    try {
      const res2 = await fetch('/cards.json');
      if (res2.ok) {
        const data2 = await res2.json();
        if (data2.cards) {
          data2.cards.forEach(c => {
            allCardsMap[c.id] = c;
          });
        }
      }
    } catch (e) {
      console.warn('Static /cards.json fetch error:', e);
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
      queuedSubmissions = (data.submissions || []).filter(s => s.status === 'queued');

      statQueuedPlayers.textContent = queuedSubmissions.length;
      queueCountBadge.textContent = queuedSubmissions.length;

      renderSubmissionsTable(queuedSubmissions);
      updateSlotDisplay();

    } catch (e) {
      console.error('Failed to load submissions:', e);
    }
  }

  function renderSubmissionsTable(subs) {
    if (subs.length === 0) {
      submissionsTableBody.innerHTML = `
        <tr>
          <td colspan="7" class="text-center empty-state-row">
            No player submissions currently in queue. Submissions entered on <a href="arena.html" target="_blank" style="color:#00f2ff; text-decoration:underline;">arena.html</a> will appear here.
          </td>
        </tr>
      `;
      return;
    }

    submissionsTableBody.innerHTML = subs.map((sub, idx) => {
      const isSelA = selectedSubA && selectedSubA.submission_id === sub.submission_id;
      const isSelB = selectedSubB && selectedSubB.submission_id === sub.submission_id;
      const atkNames = (sub.attack_cards || []).map(id => getCardName(id)).join(', ');
      const defNames = (sub.defence_cards || []).map(id => getCardName(id)).join(', ');

      return `
        <tr class="${isSelA ? 'row-selected-a' : ''} ${isSelB ? 'row-selected-b' : ''}">
          <td><strong>#${idx + 1}</strong></td>
          <td><strong style="color:#ffffff; font-size:0.95rem;">${escapeHtml(sub.full_name || '—')}</strong></td>
          <td><strong style="color:#00f2ff; font-size:0.92rem;">${escapeHtml(sub.player_name)}</strong></td>
          <td><span class="card-pill atk">⚔️ ${escapeHtml(atkNames)}</span></td>
          <td><span class="card-pill def">🛡️ ${escapeHtml(defNames)}</span></td>
          <td style="color:var(--text-muted); font-size:0.8rem;">${escapeHtml(sub.created_at || '')}</td>
          <td>
            <div class="action-btn-group">
              <button class="btn btn-xs ${isSelA ? 'btn-primary' : 'btn-secondary'}" onclick="window.selectSlot('A', '${escapeHtml(sub.submission_id)}')">
                ${isSelA ? '✓ Selected (A)' : 'Set Player A'}
              </button>
              <button class="btn btn-xs ${isSelB ? 'btn-primary' : 'btn-secondary'}" onclick="window.selectSlot('B', '${escapeHtml(sub.submission_id)}')">
                ${isSelB ? '✓ Selected (B)' : 'Set Player B'}
              </button>
              <button class="btn btn-secondary btn-xs" onclick="window.deleteSub('${escapeHtml(sub.submission_id)}')" title="Remove submission">
                <i data-lucide="trash-2"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    if (window.lucide) window.lucide.createIcons();
  }

  window.selectSlot = function(slot, subId) {
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

    updateSlotDisplay();
    renderSubmissionsTable(queuedSubmissions);
  };

  window.deleteSub = async function(subId) {
    if (!confirm('Remove this player submission from queue?')) return;
    try {
      await adminFetch(`/api/submissions/${subId}`, { method: 'DELETE' });
      if (selectedSubA && selectedSubA.submission_id === subId) selectedSubA = null;
      if (selectedSubB && selectedSubB.submission_id === subId) selectedSubB = null;
      loadSubmissions();
    } catch (e) {
      alert('Failed to remove submission');
    }
  };

  btnClearQueue.addEventListener('click', async () => {
    if (!confirm('Clear all queued submissions?')) return;
    try {
      await adminFetch('/api/submissions/clear', { method: 'POST' });
      selectedSubA = null;
      selectedSubB = null;
      loadSubmissions();
    } catch (e) {
      alert('Failed to clear queue');
    }
  });

  function updateSlotDisplay() {
    if (selectedSubA) {
      const displayName = selectedSubA.full_name 
        ? `${escapeHtml(selectedSubA.full_name)} (${escapeHtml(selectedSubA.player_name)})`
        : escapeHtml(selectedSubA.player_name);
      slotNameA.innerHTML = displayName;
      const atks = (selectedSubA.attack_cards || []).map(id => getCardName(id)).join(', ');
      const defs = (selectedSubA.defence_cards || []).map(id => getCardName(id)).join(', ');
      slotCardsA.innerHTML = `<div>⚔️ ${escapeHtml(atks)}</div><div>🛡️ ${escapeHtml(defs)}</div>`;
    } else {
      slotNameA.textContent = 'None Selected';
      slotCardsA.textContent = 'Select from queue above';
    }

    if (selectedSubB) {
      const displayName = selectedSubB.full_name 
        ? `${escapeHtml(selectedSubB.full_name)} (${escapeHtml(selectedSubB.player_name)})`
        : escapeHtml(selectedSubB.player_name);
      slotNameB.innerHTML = displayName;
      const atks = (selectedSubB.attack_cards || []).map(id => getCardName(id)).join(', ');
      const defs = (selectedSubB.defence_cards || []).map(id => getCardName(id)).join(', ');
      slotCardsB.innerHTML = `<div>⚔️ ${escapeHtml(atks)}</div><div>🛡️ ${escapeHtml(defs)}</div>`;
    } else {
      slotNameB.textContent = 'None Selected';
      slotCardsB.textContent = 'Select from queue above';
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
  // 3. MANUAL MATCH ADJUDICATION
  // ==========================================================================
  formManualAdjudicate.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!selectedSubA && !selectedSubB && queuedSubmissions.length >= 2) {
      alert('Please select Player A and Player B from the queue table above first!');
      return;
    }

    const pAName = selectedSubA ? selectedSubA.player_name : 'Player A';
    const pAFull = selectedSubA ? (selectedSubA.full_name || '') : '';
    const pBName = selectedSubB ? selectedSubB.player_name : 'Player B';
    const pBFull = selectedSubB ? (selectedSubB.full_name || '') : '';

    const pAAtk = selectedSubA ? selectedSubA.attack_cards : ['atk_quick_peek', 'atk_flash_entry'];
    const pADef = selectedSubA ? selectedSubA.defence_cards : ['def_basic_hold', 'def_defensive_smoke'];

    const pBAtk = selectedSubB ? selectedSubB.attack_cards : ['atk_split_pressure', 'atk_double_peek'];
    const pBDef = selectedSubB ? selectedSubB.defence_cards : ['def_layered_defense', 'def_antirush_setup'];

    const winnerRadio = document.querySelector('input[name="manualWinner"]:checked');
    const winnerId = winnerRadio ? winnerRadio.value : 'player_a';

    const payload = {
      submission_a_id: selectedSubA ? selectedSubA.submission_id : null,
      submission_b_id: selectedSubB ? selectedSubB.submission_id : null,
      player_a_name: pAName,
      player_a_full_name: pAFull,
      player_a_attack_cards: pAAtk,
      player_a_defence_cards: pADef,
      player_a_character_id: selectCharA.value,
      player_b_name: pBName,
      player_b_full_name: pBFull,
      player_b_attack_cards: pBAtk,
      player_b_defence_cards: pBDef,
      player_b_character_id: selectCharB.value,
      winner_id: winnerId,
      player_a_score: parseInt(inputScoreA.value, 10) || 13,
      player_b_score: parseInt(inputScoreB.value, 10) || 9,
      win_reason: 'Decisive tactical utility and angle execution.',
      mvp_combo: 'Quick Peek + Defensive Smoke'
    };

    btnRunManualAdj.disabled = true;
    btnRunManualAdj.innerHTML = `Recording match & compiling sequence...`;

    try {
      const res = await adminFetch('/api/admin/manual-adjudicate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Adjudication failed');

      currentGodotSequence = data.godot_sequence;
      showGodotResultCard(currentGodotSequence);

      selectedSubA = null;
      selectedSubB = null;
      loadSubmissions();
      loadMatchesHistory();
      loadPlayers();

    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      btnRunManualAdj.disabled = false;
      btnRunManualAdj.innerHTML = `<i data-lucide="play"></i> Record Match & Generate Sequence`;
      if (window.lucide) window.lucide.createIcons();
    }
  });

  function showGodotResultCard(seq) {
    if (!seq) return;
    godotResultCard.style.display = 'block';
    resMatchSummaryTitle.textContent = `${seq.winner_name} Victory (${seq.player_a_score} - ${seq.player_b_score})`;
    godotRawJsonDisplay.textContent = JSON.stringify(seq, null, 2);
    godotResultCard.scrollIntoView({ behavior: 'smooth' });
  }

  btnCopyGodotJson.addEventListener('click', () => {
    if (!currentGodotSequence) return;
    navigator.clipboard.writeText(JSON.stringify(currentGodotSequence, null, 2)).then(() => {
      alert('✓ Sequence JSON copied to clipboard!');
    });
  });

  btnDownloadGodotJson.addEventListener('click', () => {
    if (!currentGodotSequence) return;
    const blob = new Blob([JSON.stringify(currentGodotSequence, null, 2)], { type: 'application/json' });
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
  // 4. REAL MATCHES HISTORY ARCHIVE
  // ==========================================================================
  async function loadMatchesHistory() {
    try {
      const res = await fetch('/api/matches');
      const data = await res.json();
      storedMatches = data.matches || [];

      statCompletedMatches.textContent = storedMatches.length;
      historyCountBadge.textContent = storedMatches.length;

      if (storedMatches.length === 0) {
        matchesTableBody.innerHTML = `
          <tr>
            <td colspan="7" class="text-center empty-state-row">
              No matches recorded yet. Recorded matches will appear here.
            </td>
          </tr>
        `;
        return;
      }

      matchesTableBody.innerHTML = storedMatches.map(m => {
        const evalData = m.evaluation || {};
        const pA = m.player_a || {};
        const pB = m.player_b || {};
        const pAName = pA.name || 'Player A';
        const pAFull = pA.full_name || '';
        const pBName = pB.name || 'Player B';
        const pBFull = pB.full_name || '';
        const winner = evalData.winner_name || (m.winner_name || 'Completed');
        const scoreA = evalData.player_a_score ? evalData.player_a_score.total_score : (m.player_a_score ?? '-');
        const scoreB = evalData.player_b_score ? evalData.player_b_score.total_score : (m.player_b_score ?? '-');

        const pACell = pAFull 
          ? `<div><strong>${escapeHtml(pAFull)}</strong></div><div style="color:#00f2ff; font-size:0.8rem; font-family:var(--font-mono);">${escapeHtml(pAName)}</div>`
          : `<strong>${escapeHtml(pAName)}</strong>`;

        const pBCell = pBFull 
          ? `<div><strong>${escapeHtml(pBFull)}</strong></div><div style="color:#00f2ff; font-size:0.8rem; font-family:var(--font-mono);">${escapeHtml(pBName)}</div>`
          : `<strong>${escapeHtml(pBName)}</strong>`;

        return `
          <tr>
            <td><code>${escapeHtml(m.match_id)}</code></td>
            <td style="color:var(--text-muted); font-size:0.82rem;">${escapeHtml(m.created_at || '')}</td>
            <td>${pACell}</td>
            <td>${pBCell}</td>
            <td><span class="table-winner-pill">🏆 ${escapeHtml(winner)}</span></td>
            <td><strong>${scoreA} - ${scoreB}</strong></td>
            <td>
              <button class="btn btn-secondary btn-xs" onclick="window.downloadMatchSeq('${escapeHtml(m.match_id)}')">
                <i data-lucide="download"></i> JSON
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

  window.downloadMatchSeq = async function(matchId) {
    try {
      const res = await fetch(`/api/matches/${matchId}/godot-sequence`);
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `godot_match_sequence_${matchId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      alert('Failed to download sequence');
    }
  };

  // ==========================================================================
  // 5. REAL REGISTERED PLAYERS DIRECTORY
  // ==========================================================================
  async function loadPlayers() {
    try {
      const res = await fetch('/api/players');
      const data = await res.json();
      registeredPlayers = data.players || [];

      statRegisteredPlayers.textContent = registeredPlayers.length;
      playerCountBadge.textContent = registeredPlayers.length;

      if (registeredPlayers.length === 0) {
        playersTableBody.innerHTML = `
          <tr>
            <td colspan="7" class="text-center empty-state-row">
              No registered players in database yet.
            </td>
          </tr>
        `;
        return;
      }

      playersTableBody.innerHTML = registeredPlayers.map(p => `
        <tr>
          <td><strong style="color:#ffffff; font-size:0.92rem;">${escapeHtml(p.full_name || '—')}</strong></td>
          <td><strong style="color:#00f2ff;">${escapeHtml(p.username)}</strong></td>
          <td>${p.matches_played}</td>
          <td><span style="color:#22c55e;">${p.wins}W</span> / <span style="color:#ef4444;">${p.losses}L</span> / <span style="color:#94a3b8;">${p.draws}D</span></td>
          <td><strong>${p.win_rate_pct}%</strong></td>
          <td><span class="stat-pts-badge">★ ${p.total_score}</span></td>
          <td style="color:var(--text-muted); font-size:0.8rem;">${escapeHtml(p.last_active)}</td>
        </tr>
      `).join('');

      if (window.lucide) window.lucide.createIcons();

    } catch (e) {
      console.error('Failed to load players leaderboard:', e);
    }
  }

  // Refresh All Data
  btnRefreshAll.addEventListener('click', () => {
    loadSubmissions();
    loadMatchesHistory();
    loadPlayers();
  });

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
      loadMatchesHistory();
      loadPlayers();
    });
  }

  // Initial check
  checkSecurityGate();

  // Auto-refresh submissions every 5 seconds
  setInterval(() => {
    if (getAdminToken() === CORRECT_PASSCODE) {
      loadSubmissions();
    }
  }, 5000);

});
