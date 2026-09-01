/**
 * ============================================================================
 * VALORANT TACTICAL ARENA — APPLICATION SCRIPT (app.js)
 * ============================================================================
 * Manages 4 Blank Boxes, Interactive Modal Card Picker, Unique Username,
 * and Persistent Database Match Submissions.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide Icons
  if (window.lucide) {
    window.lucide.createIcons();
  }

  // Application State
  let allCards = [];
  let currentActiveSlotKey = null; // 'atk-0', 'atk-1', 'def-0', 'def-1'
  let currentActiveCategory = 'all'; // 'attack', 'defence', 'all'
  let activeModalFilter = 'all';
  let modalSearchQuery = '';

  // 4 Slot Selections
  const slotsState = {
    'atk-0': null, // Attack Card 1
    'atk-1': null, // Attack Card 2
    'def-0': null, // Defence Card 1
    'def-1': null  // Defence Card 2
  };

  // DOM Elements
  const fullNameInput = document.getElementById('fullNameInput');
  const fullNameValidationMsg = document.getElementById('fullNameValidationMsg');
  const uniqueUsernameInput = document.getElementById('uniqueUsernameInput');
  const btnRandomizeName = document.getElementById('btnRandomizeName');
  const userValidationMsg = document.getElementById('userValidationMsg');
  const atkCount = document.getElementById('atkCount');
  const defCount = document.getElementById('defCount');
  const atkCounterBadge = document.getElementById('atkCounterBadge');
  const defCounterBadge = document.getElementById('defCounterBadge');
  const btnSubmitLoadout = document.getElementById('btnSubmitLoadout');
  const btnClearAll = document.getElementById('btnClearAll');
  const btnQuickRandom = document.getElementById('btnQuickRandom');

  // 4 Box DOM Elements
  const boxAtk1 = document.getElementById('boxAtk1');
  const boxAtk2 = document.getElementById('boxAtk2');
  const boxDef1 = document.getElementById('boxDef1');
  const boxDef2 = document.getElementById('boxDef2');

  const slotBoxes = {
    'atk-0': boxAtk1,
    'atk-1': boxAtk2,
    'def-0': boxDef1,
    'def-1': boxDef2
  };

  // Modal Elements
  const cardPickerModal = document.getElementById('cardPickerModal');
  const btnClosePickerModal = document.getElementById('btnClosePickerModal');
  const pickerModalTitle = document.getElementById('pickerModalTitle');
  const pickerModalSubtitle = document.getElementById('pickerModalSubtitle');
  const pickerSearchInput = document.getElementById('pickerSearchInput');
  const pickerCardsGrid = document.getElementById('pickerCardsGrid');
  const pickerPills = document.querySelectorAll('.picker-pill-btn');

  // Processing Modal
  const processingModal = document.getElementById('processingModal');
  const btnCloseProcessingModal = document.getElementById('btnCloseProcessingModal');
  const modalSubmittedSummary = document.getElementById('modalSubmittedSummary');

  // Custom Cursor
  const cursor = document.getElementById('customCursor');
  if (cursor) {
    window.addEventListener('mousemove', (e) => {
      cursor.style.left = `${e.clientX}px`;
      cursor.style.top = `${e.clientY}px`;
    });
  }

  // ==========================================================================
  // SECTION 1: PLAYER FULL NAME & UNIQUE USERNAME MANAGEMENT
  // ==========================================================================
  const RANDOM_NAMES = [
    "TenZ#NA1", "Chronicle#EMEA", "Derke#FNTC", "Aspas#LEV",
    "Boaster#IGL", "ScreaM#ONE", "Yay#DIABLO", "Forsaken#PRX",
    "Jinggg#DUEL", "Cned#FUT", "cNed#ACEND", "ShahZaM#SEN",
    "Agent-Radiant-7", "GhostWalker#99", "VandalKing#01", "PhantomQueen#42"
  ];

  function loadSavedUserData() {
    const savedFull = localStorage.getItem('valorant_player_full_name');
    if (savedFull && savedFull.trim() && fullNameInput) {
      fullNameInput.value = savedFull.trim();
      if (fullNameValidationMsg) {
        fullNameValidationMsg.textContent = '✓ Ready';
        fullNameValidationMsg.style.color = '#00f2ff';
      }
    }

    const saved = localStorage.getItem('valorant_agent_unique_name');
    if (saved && saved.trim()) {
      uniqueUsernameInput.value = saved.trim();
    } else {
      generateRandomUsername();
    }
    validateForm();
  }

  function generateRandomUsername() {
    const randomPick = RANDOM_NAMES[Math.floor(Math.random() * RANDOM_NAMES.length)];
    const uniqueSuffix = Math.floor(10 + Math.random() * 90);
    const generated = `${randomPick.split('#')[0]}#${uniqueSuffix}`;
    uniqueUsernameInput.value = generated;
    localStorage.setItem('valorant_agent_unique_name', generated);
    validateForm();
  }

  btnRandomizeName.addEventListener('click', generateRandomUsername);

  if (fullNameInput) {
    fullNameInput.addEventListener('input', () => {
      const val = fullNameInput.value.trim();
      if (val) {
        localStorage.setItem('valorant_player_full_name', val);
        if (fullNameValidationMsg) {
          fullNameValidationMsg.textContent = '✓ Ready';
          fullNameValidationMsg.style.color = '#00f2ff';
        }
      } else {
        if (fullNameValidationMsg) {
          fullNameValidationMsg.textContent = '⚠️ Full name required';
          fullNameValidationMsg.style.color = '#ff5e00';
        }
      }
      validateForm();
    });
  }

  uniqueUsernameInput.addEventListener('input', () => {
    const val = uniqueUsernameInput.value.trim();
    if (val) {
      localStorage.setItem('valorant_agent_unique_name', val);
      userValidationMsg.textContent = '✓ Unique tag ready';
      userValidationMsg.style.color = '#00f2ff';
    } else {
      userValidationMsg.textContent = '⚠️ Username required';
      userValidationMsg.style.color = '#ff5e00';
    }
    validateForm();
  });

  // ==========================================================================
  // SECTION 2: FETCH ALL 120 TACTICAL CARDS
  // ==========================================================================
  async function fetchCardDatabase() {
    try {
      const res = await fetch('/api/cards');
      const data = await res.json();
      allCards = data.cards || [];
      console.log(`[ARENA] Loaded ${allCards.length} master tactical cards.`);
    } catch (e) {
      console.error('[ARENA ERROR] Failed to fetch tactical cards:', e);
    }
  }

  // ==========================================================================
  // SECTION 3: 4 BLANK BOXES INTERACTION (OPENING CARD CHOICES MODAL)
  // ==========================================================================
  Object.keys(slotBoxes).forEach(slotKey => {
    const boxEl = slotBoxes[slotKey];
    boxEl.addEventListener('click', () => {
      openCardPickerModal(slotKey);
    });
  });

  function openCardPickerModal(slotKey) {
    currentActiveSlotKey = slotKey;
    const isAtk = slotKey.startsWith('atk');
    currentActiveCategory = isAtk ? 'attack' : 'defence';
    activeModalFilter = currentActiveCategory;
    modalSearchQuery = '';
    pickerSearchInput.value = '';

    // Update Modal Header Text
    const slotNum = slotKey.endsWith('0') ? '1' : '2';
    if (isAtk) {
      pickerModalTitle.innerHTML = `<i data-lucide="swords" style="color: #ff5e00;"></i> Choose Attack Tactic #${slotNum}`;
      pickerModalSubtitle.textContent = 'Select an offensive card from 60 Attack Tactics';
    } else {
      pickerModalTitle.innerHTML = `<i data-lucide="shield" style="color: #00f2ff;"></i> Choose Defence Tactic #${slotNum}`;
      pickerModalSubtitle.textContent = 'Select a defensive card from 60 Defence Tactics';
    }

    // Sync Filter Pills
    pickerPills.forEach(pill => {
      const filter = pill.getAttribute('data-filter');
      if (filter === activeModalFilter) {
        pill.classList.add('active');
      } else {
        pill.classList.remove('active');
      }
    });

    renderPickerCards();
    cardPickerModal.classList.add('active');

    if (window.lucide) {
      window.lucide.createIcons();
    }
  }

  function closeCardPickerModal() {
    cardPickerModal.classList.remove('active');
    currentActiveSlotKey = null;
  }

  btnClosePickerModal.addEventListener('click', closeCardPickerModal);

  // Close modal when clicking backdrop outside card
  cardPickerModal.addEventListener('click', (e) => {
    if (e.target === cardPickerModal) {
      closeCardPickerModal();
    }
  });

  // Filter Pill buttons
  pickerPills.forEach(pill => {
    pill.addEventListener('click', () => {
      pickerPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeModalFilter = pill.getAttribute('data-filter');
      renderPickerCards();
    });
  });

  // Search input
  pickerSearchInput.addEventListener('input', (e) => {
    modalSearchQuery = e.target.value.trim().toLowerCase();
    renderPickerCards();
  });

  // ==========================================================================
  // SECTION 4: RENDER CARD CHOICES INSIDE MODAL
  // ==========================================================================
  function renderPickerCards() {
    // Determine which cards are already equipped in OTHER slots
    const currentlyEquippedIds = Object.entries(slotsState)
      .filter(([k, card]) => k !== currentActiveSlotKey && card !== null)
      .map(([_, card]) => card.id);

    const filtered = allCards.filter(card => {
      // Category filter
      const matchCategory = (activeModalFilter === 'all') || (card.category === activeModalFilter);
      // Search filter
      const matchSearch = !modalSearchQuery || 
        card.name.toLowerCase().includes(modalSearchQuery) || 
        card.description.toLowerCase().includes(modalSearchQuery);

      return matchCategory && matchSearch;
    });

    if (filtered.length === 0) {
      pickerCardsGrid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-muted);">
          <p>No tactics found matching "${escapeHtml(modalSearchQuery)}".</p>
        </div>
      `;
      return;
    }

    pickerCardsGrid.innerHTML = filtered.map(card => {
      const isEquippedElsewhere = currentlyEquippedIds.includes(card.id);
      const isEquippedInCurrent = slotsState[currentActiveSlotKey]?.id === card.id;
      const icon = card.category === 'attack' ? 'swords' : 'shield';
      const catBadge = card.category === 'attack' ? 'Attack' : 'Defence';

      return `
        <div class="choice-card-item ${card.category} ${isEquippedInCurrent ? 'selected' : ''}" data-id="${card.id}">
          <div class="choice-card-header">
            <span class="slot-category-tag ${card.category === 'attack' ? 'atk' : 'def'}">
              <i data-lucide="${icon}"></i> ${catBadge}
            </span>
            ${isEquippedInCurrent ? '<span style="color:#00f2ff; font-size:11px; font-weight:700;">✓ EQUIPPED</span>' : ''}
          </div>
          <div>
            <div class="choice-card-title">${escapeHtml(card.name)}</div>
            <div class="choice-card-desc">${escapeHtml(card.description)}</div>
          </div>
          <button class="choice-equip-btn" ${isEquippedElsewhere ? 'disabled title="Already equipped in another slot"' : ''}>
            ${isEquippedInCurrent ? 'Selected' : isEquippedElsewhere ? 'In Other Slot' : 'Equip This Tactic'}
          </button>
        </div>
      `;
    }).join('');

    if (window.lucide) {
      window.lucide.createIcons();
    }

    // Attach click handlers to choices
    pickerCardsGrid.querySelectorAll('.choice-card-item').forEach(el => {
      el.addEventListener('click', () => {
        const cardId = el.getAttribute('data-id');
        const card = allCards.find(c => c.id === cardId);
        if (card) {
          equipCardIntoSlot(currentActiveSlotKey, card);
        }
      });
    });
  }

  // ==========================================================================
  // SECTION 5: EQUIP CARD INTO ACTIVE BLANK BOX
  // ==========================================================================
  function equipCardIntoSlot(slotKey, card) {
    if (!slotKey || !card) return;
    slotsState[slotKey] = card;
    renderSlotBox(slotKey);
    closeCardPickerModal();
    validateForm();
  }

  function removeCardFromSlot(slotKey, e) {
    if (e) e.stopPropagation();
    slotsState[slotKey] = null;
    renderSlotBox(slotKey);
    validateForm();
  }

  function renderSlotBox(slotKey) {
    const boxEl = slotBoxes[slotKey];
    const card = slotsState[slotKey];
    const isAtk = slotKey.startsWith('atk');
    const slotIndex = slotKey.endsWith('0') ? '1' : '2';

    if (!card) {
      // Blank Box State
      boxEl.className = `tactical-box ${isAtk ? 'slot-atk' : 'slot-def'}`;
      boxEl.innerHTML = `
        <div class="blank-box-state">
          <div class="plus-icon-circle">
            <i data-lucide="plus"></i>
          </div>
          <div class="blank-box-title">${isAtk ? 'Attack' : 'Defence'} Tactic #${slotIndex}</div>
          <div class="blank-box-desc">Tap to select from 60 ${isAtk ? 'Attack' : 'Defence'} Tactics</div>
          <span class="slot-category-tag ${isAtk ? 'atk' : 'def'}">
            <i data-lucide="${isAtk ? 'swords' : 'shield'}"></i> ${isAtk ? 'Attack' : 'Defence'} Slot
          </span>
        </div>
      `;
    } else {
      // Filled Box State
      boxEl.className = `tactical-box filled ${isAtk ? 'slot-atk' : 'slot-def'}`;
      boxEl.innerHTML = `
        <div class="filled-header">
          <span class="slot-category-tag ${isAtk ? 'atk' : 'def'}">
            <i data-lucide="${isAtk ? 'swords' : 'shield'}"></i> ${isAtk ? 'Attack' : 'Defence'} #${slotIndex}
          </span>
          <button class="btn-remove-slot" title="Remove tactic" data-slot="${slotKey}">
            <i data-lucide="x"></i>
          </button>
        </div>
        <div>
          <div class="filled-card-title">${escapeHtml(card.name)}</div>
          <div class="filled-card-desc">${escapeHtml(card.description)}</div>
        </div>
        <div class="filled-change-prompt">
          <i data-lucide="refresh-cw"></i> Tap to change tactic
        </div>
      `;

      const removeBtn = boxEl.querySelector('.btn-remove-slot');
      if (removeBtn) {
        removeBtn.addEventListener('click', (e) => removeCardFromSlot(slotKey, e));
      }
    }

    if (window.lucide) {
      window.lucide.createIcons();
    }
  }

  // ==========================================================================
  // SECTION 6: FORM VALIDATION & RANDOM LOADOUT HELPER
  // ==========================================================================
  function validateForm() {
    const atk1 = slotsState['atk-0'];
    const atk2 = slotsState['atk-1'];
    const def1 = slotsState['def-0'];
    const def2 = slotsState['def-1'];

    const totalAtk = (atk1 ? 1 : 0) + (atk2 ? 1 : 0);
    const totalDef = (def1 ? 1 : 0) + (def2 ? 1 : 0);

    atkCount.textContent = `${totalAtk}/2`;
    defCount.textContent = `${totalDef}/2`;

    if (totalAtk === 2) {
      atkCounterBadge.classList.add('ready');
    } else {
      atkCounterBadge.classList.remove('ready');
    }

    if (totalDef === 2) {
      defCounterBadge.classList.add('ready');
    } else {
      defCounterBadge.classList.remove('ready');
    }

    const hasFullName = Boolean(fullNameInput && fullNameInput.value.trim());
    const hasUsername = Boolean(uniqueUsernameInput && uniqueUsernameInput.value.trim());
    const isComplete = (totalAtk === 2 && totalDef === 2 && hasFullName && hasUsername);

    btnSubmitLoadout.disabled = !isComplete;
  }

  function pickRandomLoadout() {
    const atks = allCards.filter(c => c.category === 'attack');
    const defs = allCards.filter(c => c.category === 'defence');

    if (atks.length < 2 || defs.length < 2) return;

    const shuffledAtk = [...atks].sort(() => 0.5 - Math.random());
    const shuffledDef = [...defs].sort(() => 0.5 - Math.random());

    slotsState['atk-0'] = shuffledAtk[0];
    slotsState['atk-1'] = shuffledAtk[1];
    slotsState['def-0'] = shuffledDef[0];
    slotsState['def-1'] = shuffledDef[1];

    renderSlotBox('atk-0');
    renderSlotBox('atk-1');
    renderSlotBox('def-0');
    renderSlotBox('def-1');

    validateForm();
  }

  function clearAllSlots() {
    slotsState['atk-0'] = null;
    slotsState['atk-1'] = null;
    slotsState['def-0'] = null;
    slotsState['def-1'] = null;

    renderSlotBox('atk-0');
    renderSlotBox('atk-1');
    renderSlotBox('def-0');
    renderSlotBox('def-1');

    validateForm();
  }

  btnQuickRandom.addEventListener('click', pickRandomLoadout);
  btnClearAll.addEventListener('click', clearAllSlots);

  // ==========================================================================
  // SECTION 7: SUBMIT MATCH & AI ADJUDICATION
  // ==========================================================================
  async function submitMatchLoadout() {
    const atk1 = slotsState['atk-0'];
    const atk2 = slotsState['atk-1'];
    const def1 = slotsState['def-0'];
    const def2 = slotsState['def-1'];
    const fullName = (fullNameInput ? fullNameInput.value.trim() : '');
    const username = (uniqueUsernameInput.value.trim() || 'Agent Alpha');

    if (!fullName) {
      alert('Please enter your Full Name!');
      if (fullNameInput) fullNameInput.focus();
      return;
    }

    if (!atk1 || !atk2 || !def1 || !def2) {
      alert('Please fill all 4 tactical slots before submitting!');
      return;
    }

    const payload = {
      player_name: username,
      full_name: fullName,
      attack_cards: [atk1.id, atk2.id],
      defence_cards: [def1.id, def2.id]
    };

    // Show processing modal
    openProcessingModal(payload);

    try {
      const response = await fetch('/api/submit-match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const resData = await response.json();
      console.log('[MATCH SUBMISSION VERDICT]:', resData);

      // Trigger Confetti Celebration
      if (window.confetti) {
        window.confetti({
          particleCount: 70,
          spread: 80,
          origin: { y: 0.6 }
        });
      }

    } catch (e) {
      console.error('[SUBMISSION ERROR]:', e);
    }
  }

  function openProcessingModal(payload) {
    const atkNames = payload.attack_cards.map(id => {
      const c = allCards.find(card => card.id === id);
      return c ? c.name : id;
    }).join(' + ');

    const defNames = payload.defence_cards.map(id => {
      const c = allCards.find(card => card.id === id);
      return c ? c.name : id;
    }).join(' + ');

    modalSubmittedSummary.innerHTML = `
      <div><strong>👤 Full Name:</strong> <span style="color:#ffffff; font-weight:700;">${escapeHtml(payload.full_name || '—')}</span></div>
      <div><strong>🎯 Agent Tag:</strong> <span style="color:#00f2ff;">${escapeHtml(payload.player_name)}</span></div>
      <div><strong>⚔️ Attack Tactics:</strong> ${escapeHtml(atkNames)}</div>
      <div><strong>🛡️ Defence Tactics:</strong> ${escapeHtml(defNames)}</div>
    `;

    processingModal.classList.add('active');
  }

  btnCloseProcessingModal.addEventListener('click', () => {
    processingModal.classList.remove('active');
  });

  btnSubmitLoadout.addEventListener('click', submitMatchLoadout);

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


  // Initialize
  fetchCardDatabase().then(() => {
    loadSavedUserData();
  });
});
