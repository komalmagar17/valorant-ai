/**
 * ============================================================================
 * Tactix 3D — Client Application Logic
 * ============================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide Icons
  if (window.lucide) {
    window.lucide.createIcons();
  }

  // State
  let allCards = [];
  let selectedAttackCards = [];   // Max 2
  let selectedDefenceCards = [];  // Max 2
  let activeTab = 'all';
  let searchQuery = '';

  // DOM Elements
  const cardsGrid = document.getElementById('cardsGrid');
  const cardSearchInput = document.getElementById('cardSearchInput');
  const tabButtons = document.querySelectorAll('.tab-btn');
  const atkCount = document.getElementById('atkCount');
  const defCount = document.getElementById('defCount');
  const atkCounterBadge = document.getElementById('atkCounterBadge');
  const defCounterBadge = document.getElementById('defCounterBadge');
  const btnSubmitMatch = document.getElementById('btnSubmitMatch');
  const btnClearSelection = document.getElementById('btnClearSelection');
  const btnQuickRandom = document.getElementById('btnQuickRandom');
  const playerNameInput = document.getElementById('playerNameInput');
  const processingModal = document.getElementById('processingModal');
  const btnCloseModal = document.getElementById('btnCloseModal');
  const modalSubmittedSummary = document.getElementById('modalSubmittedSummary');
  const matchesTableBody = document.getElementById('matchesTableBody');

  // Slots
  const slotAtk1 = document.getElementById('slotAtk1');
  const slotAtk2 = document.getElementById('slotAtk2');
  const slotDef1 = document.getElementById('slotDef1');
  const slotDef2 = document.getElementById('slotDef2');

  // Initialize System
  initThreeJSMascot();
  initCustomCursor();
  loadCards();
  loadDatabaseMatches();

  // Polling for match records every 10 seconds
  setInterval(loadDatabaseMatches, 10000);

  // ==========================================================================
  // SECTION 1: THREE.JS 3D MASCOT (Boba-Bot)
  // ==========================================================================
  function initThreeJSMascot() {
    const container = document.getElementById('canvasContainer');
    if (!container || !window.THREE) return;

    const width = container.clientWidth;
    const height = container.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 6;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Group for the robot
    const botGroup = new THREE.Group();
    scene.add(botGroup);

    // 1. Robot Sphere Body (Soft rounded lavender)
    const bodyGeo = new THREE.SphereGeometry(1.4, 64, 64);
    const bodyMat = new THREE.MeshStandardMaterial({
      color: 0x8b6bf7,
      roughness: 0.25,
      metalness: 0.15,
      emissive: 0x221255,
      emissiveIntensity: 0.4
    });
    const bodyMesh = new THREE.Mesh(bodyGeo, bodyMat);
    botGroup.add(bodyMesh);

    // 2. Visor / Screen Face
    const visorGeo = new THREE.SphereGeometry(1.1, 32, 32);
    const visorMat = new THREE.MeshStandardMaterial({
      color: 0x0c0919,
      roughness: 0.1,
      metalness: 0.8
    });
    const visorMesh = new THREE.Mesh(visorGeo, visorMat);
    visorMesh.position.set(0, 0, 0.45);
    visorMesh.scale.set(0.85, 0.55, 0.6);
    botGroup.add(visorMesh);

    // 3. Cute Glowing Eyes
    const eyeGeo = new THREE.CapsuleGeometry(0.12, 0.22, 16, 16);
    const eyeMat = new THREE.MeshBasicMaterial({ color: 0x00f0b5 });

    const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
    leftEye.position.set(-0.35, 0.05, 0.98);
    leftEye.rotation.z = -0.1;
    botGroup.add(leftEye);

    const rightEye = new THREE.Mesh(eyeGeo, eyeMat);
    rightEye.position.set(0.35, 0.05, 0.98);
    rightEye.rotation.z = 0.1;
    botGroup.add(rightEye);

    // 4. Floating Hologram Card Orbit Ring
    const ringGeo = new THREE.TorusGeometry(2.1, 0.04, 16, 100);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0xff6584, transparent: true, opacity: 0.5 });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.rotation.x = Math.PI / 3;
    botGroup.add(ringMesh);

    // 5. Orbiting Holo-Card Miniatures
    const cardBoxGeo = new THREE.BoxGeometry(0.35, 0.5, 0.04);
    const cardAtkMat = new THREE.MeshStandardMaterial({ color: 0xff4772, roughness: 0.3 });
    const cardDefMat = new THREE.MeshStandardMaterial({ color: 0x38b6ff, roughness: 0.3 });

    const orbitCard1 = new THREE.Mesh(cardBoxGeo, cardAtkMat);
    const orbitCard2 = new THREE.Mesh(cardBoxGeo, cardDefMat);
    scene.add(orbitCard1);
    scene.add(orbitCard2);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const mainLight = new THREE.DirectionalLight(0xffffff, 1.2);
    mainLight.position.set(4, 5, 6);
    scene.add(mainLight);

    const pointLight1 = new THREE.PointLight(0x00f0b5, 2, 8);
    pointLight1.position.set(-3, 2, 3);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0xff6584, 2, 8);
    pointLight2.position.set(3, -2, 2);
    scene.add(pointLight2);

    // Mouse Tracking
    let mouseTargetX = 0;
    let mouseTargetY = 0;
    window.addEventListener('mousemove', (e) => {
      const rect = container.getBoundingClientRect();
      const x = (e.clientX - (rect.left + rect.width / 2)) / (rect.width / 2);
      const y = (e.clientY - (rect.top + rect.height / 2)) / (rect.height / 2);
      mouseTargetX = Math.max(-1, Math.min(1, x));
      mouseTargetY = Math.max(-1, Math.min(1, y));
    });

    // Animation Loop
    let clock = new THREE.Clock();
    function animate() {
      requestAnimationFrame(animate);
      const t = clock.getElapsedTime();

      // Idle float (sine wave)
      botGroup.position.y = Math.sin(t * 1.5) * 0.18;

      // Mouse tilt with damping
      botGroup.rotation.y += (mouseTargetX * 0.45 - botGroup.rotation.y) * 0.08;
      botGroup.rotation.x += (-mouseTargetY * 0.3 - botGroup.rotation.x) * 0.08;

      // Ring rotation
      ringMesh.rotation.z = t * 0.5;

      // Orbiting cards
      const orbitRadius = 2.1;
      const angle1 = t * 1.2;
      const angle2 = t * 1.2 + Math.PI;

      orbitCard1.position.set(
        Math.cos(angle1) * orbitRadius,
        botGroup.position.y + Math.sin(angle1) * 0.6,
        Math.sin(angle1) * orbitRadius
      );
      orbitCard1.rotation.y = -angle1;

      orbitCard2.position.set(
        Math.cos(angle2) * orbitRadius,
        botGroup.position.y + Math.sin(angle2) * 0.6,
        Math.sin(angle2) * orbitRadius
      );
      orbitCard2.rotation.y = -angle2;

      renderer.render(scene, camera);
    }
    animate();

    // Resize
    window.addEventListener('resize', () => {
      if (!container) return;
      const newW = container.clientWidth;
      const newH = container.clientHeight;
      camera.aspect = newW / newH;
      camera.updateProjectionMatrix();
      renderer.setSize(newW, newH);
    });
  }

  // ==========================================================================
  // SECTION 2: CUSTOM MAGNETIC CURSOR
  // ==========================================================================
  function initCustomCursor() {
    const cursor = document.getElementById('customCursor');
    const trail = document.getElementById('cursorTrail');
    if (!cursor || !trail) return;

    let mouseX = 0, mouseY = 0;
    let cx = 0, cy = 0;
    let tx = 0, ty = 0;

    window.addEventListener('mousemove', (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    });

    function cursorLoop() {
      cx += (mouseX - cx) * 0.35;
      cy += (mouseY - cy) * 0.35;
      cursor.style.left = `${cx}px`;
      cursor.style.top = `${cy}px`;

      tx += (mouseX - tx) * 0.15;
      ty += (mouseY - ty) * 0.15;
      trail.style.left = `${tx}px`;
      trail.style.top = `${ty}px`;

      requestAnimationFrame(cursorLoop);
    }
    cursorLoop();

    // Magnetic growth on interactive items
    document.addEventListener('mouseover', (e) => {
      if (e.target.closest('button, .tactical-card, a, input, .dock-slot')) {
        cursor.classList.add('is-hovering');
      }
    });
    document.addEventListener('mouseout', (e) => {
      if (e.target.closest('button, .tactical-card, a, input, .dock-slot')) {
        cursor.classList.remove('is-hovering');
      }
    });
  }

  // ==========================================================================
  // SECTION 3: LOAD & RENDER CARDS (NO TIERS SHOWN)
  // ==========================================================================
  async function loadCards() {
    try {
      const response = await fetch('/api/cards');
      const data = await response.json();
      allCards = data.cards || [];
      updateTabCounts();
      renderCards();
    } catch (err) {
      console.error('Failed to load cards:', err);
      cardsGrid.innerHTML = `
        <div class="empty-state">
          <p>⚠️ Could not connect to API server. Please ensure server.py is running.</p>
        </div>
      `;
    }
  }

  function updateTabCounts() {
    const atks = allCards.filter(c => c.category === 'attack').length;
    const defs = allCards.filter(c => c.category === 'defence').length;
    document.getElementById('countAll').textContent = allCards.length;
    document.getElementById('countAtk').textContent = atks;
    document.getElementById('countDef').textContent = defs;
  }

  function renderCards() {
    let filtered = allCards.filter(card => {
      const matchesTab = (activeTab === 'all') || (card.category === activeTab);
      const matchesSearch = !searchQuery || 
        card.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
        card.description.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesTab && matchesSearch;
    });

    if (filtered.length === 0) {
      cardsGrid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1; text-align: center; padding: 40px;">
          <p style="color: var(--ink-muted);">No tactics found matching your search.</p>
        </div>
      `;
      return;
    }

    cardsGrid.innerHTML = filtered.map(card => {
      const isSelected = selectedAttackCards.includes(card.id) || selectedDefenceCards.includes(card.id);
      const icon = card.category === 'attack' ? 'swords' : 'shield';
      const catLabel = card.category === 'attack' ? 'Attack' : 'Defence';

      return `
        <div class="tactical-card ${isSelected ? 'selected' : ''}" data-id="${card.id}" data-category="${card.category}">
          <div>
            <div class="card-header-row">
              <span class="card-category-badge ${card.category}">
                <i data-lucide="${icon}"></i> ${catLabel}
              </span>
              <div class="card-select-icon">
                <i data-lucide="check"></i>
              </div>
            </div>
            <h3 class="card-title">${escapeHtml(card.name)}</h3>
            <p class="card-description">${escapeHtml(card.description)}</p>
          </div>
        </div>
      `;
    }).join('');

    if (window.lucide) {
      window.lucide.createIcons();
    }

    // Attach card click handlers
    document.querySelectorAll('.tactical-card').forEach(el => {
      el.addEventListener('click', () => {
        const cardId = el.getAttribute('data-id');
        const category = el.getAttribute('data-category');
        toggleCardSelection(cardId, category);
      });
    });
  }

  // ==========================================================================
  // SECTION 4: CARD SELECTION LOGIC (STRICT 2 ATTACK + 2 DEFENCE)
  // ==========================================================================
  function toggleCardSelection(cardId, category) {
    if (category === 'attack') {
      if (selectedAttackCards.includes(cardId)) {
        selectedAttackCards = selectedAttackCards.filter(id => id !== cardId);
      } else {
        if (selectedAttackCards.length >= 2) {
          showFloatingNotice('⚔️ You can only select 2 Attack cards! Please unselect one first.');
          return;
        }
        selectedAttackCards.push(cardId);
      }
    } else if (category === 'defence') {
      if (selectedDefenceCards.includes(cardId)) {
        selectedDefenceCards = selectedDefenceCards.filter(id => id !== cardId);
      } else {
        if (selectedDefenceCards.length >= 2) {
          showFloatingNotice('🛡️ You can only select 2 Defence cards! Please unselect one first.');
          return;
        }
        selectedDefenceCards.push(cardId);
      }
    }

    updateDock();
    renderCards();
  }

  function updateDock() {
    // 1. Update Counters
    atkCount.textContent = `${selectedAttackCards.length}/2`;
    defCount.textContent = `${selectedDefenceCards.length}/2`;

    if (selectedAttackCards.length === 2) {
      atkCounterBadge.classList.add('ready');
    } else {
      atkCounterBadge.classList.remove('ready');
    }

    if (selectedDefenceCards.length === 2) {
      defCounterBadge.classList.add('ready');
    } else {
      defCounterBadge.classList.remove('ready');
    }

    // 2. Render Slots
    renderSlot(slotAtk1, selectedAttackCards[0], 'attack', 1);
    renderSlot(slotAtk2, selectedAttackCards[1], 'attack', 2);
    renderSlot(slotDef1, selectedDefenceCards[0], 'defence', 1);
    renderSlot(slotDef2, selectedDefenceCards[1], 'defence', 2);

    if (window.lucide) {
      window.lucide.createIcons();
    }

    // 3. Enable Submit Button iff exactly 2 Attack & 2 Defence selected
    const isReady = selectedAttackCards.length === 2 && selectedDefenceCards.length === 2;
    btnSubmitMatch.disabled = !isReady;
  }

  function renderSlot(slotElement, cardId, category, slotNumber) {
    if (!cardId) {
      slotElement.className = `dock-slot slot-${category}`;
      const icon = category === 'attack' ? 'swords' : 'shield';
      const label = category === 'attack' ? `Attack Card #${slotNumber}` : `Defence Card #${slotNumber}`;
      slotElement.innerHTML = `
        <div class="slot-placeholder">
          <i data-lucide="${icon}"></i>
          <span>${label}</span>
          <small>Click any ${category} card below</small>
        </div>
      `;
      return;
    }

    const card = allCards.find(c => c.id === cardId);
    if (!card) return;

    slotElement.className = `dock-slot slot-${category} filled`;
    slotElement.innerHTML = `
      <div class="dock-card-content">
        <div class="dock-card-header">
          <span class="dock-card-type ${category}">${category.toUpperCase()} #${slotNumber}</span>
          <button class="btn-remove-card" data-id="${card.id}" data-category="${category}" title="Remove card">
            <i data-lucide="x"></i>
          </button>
        </div>
        <div class="dock-card-title">${escapeHtml(card.name)}</div>
        <div class="dock-card-desc">${escapeHtml(card.description)}</div>
      </div>
    `;

    const removeBtn = slotElement.querySelector('.btn-remove-card');
    if (removeBtn) {
      removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleCardSelection(card.id, category);
      });
    }
  }

  // ==========================================================================
  // SECTION 5: RANDOM PICK & CLEAR HELPERS
  // ==========================================================================
  function pickRandomLoadout() {
    const atks = allCards.filter(c => c.category === 'attack');
    const defs = allCards.filter(c => c.category === 'defence');

    if (atks.length < 2 || defs.length < 2) return;

    const shuffledAtk = [...atks].sort(() => 0.5 - Math.random());
    const shuffledDef = [...defs].sort(() => 0.5 - Math.random());

    selectedAttackCards = [shuffledAtk[0].id, shuffledAtk[1].id];
    selectedDefenceCards = [shuffledDef[0].id, shuffledDef[1].id];

    updateDock();
    renderCards();

    // Scroll to dock smoothly
    document.getElementById('match-dock').scrollIntoView({ behavior: 'smooth' });
  }

  function clearAllSelections() {
    selectedAttackCards = [];
    selectedDefenceCards = [];
    updateDock();
    renderCards();
  }

  btnQuickRandom.addEventListener('click', pickRandomLoadout);
  btnClearSelection.addEventListener('click', clearAllSelections);

  // Filter Tabs
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeTab = btn.getAttribute('data-tab');
      renderCards();
    });
  });

  // Search Input
  cardSearchInput.addEventListener('input', (e) => {
    searchQuery = e.target.value.trim();
    renderCards();
  });

  // ==========================================================================
  // SECTION 6: MATCH SUBMISSION & 'PROCESSING THE RESULT' MODAL
  // ==========================================================================
  async function submitMatch() {
    if (selectedAttackCards.length !== 2 || selectedDefenceCards.length !== 2) {
      showFloatingNotice('Please select exactly 2 Attack and 2 Defence cards!');
      return;
    }

    const playerName = (playerNameInput.value.trim() || 'Agent Alpha');

    // Build payload
    const payload = {
      player_name: playerName,
      attack_cards: selectedAttackCards,
      defence_cards: selectedDefenceCards
    };

    // Show processing modal immediately
    openProcessingModal(payload);

    try {
      const response = await fetch('/api/submit-match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      console.log('[MATCH SUBMITTED TO DATABASE]:', result);

      // Trigger celebration confetti
      if (window.confetti) {
        window.confetti({
          particleCount: 60,
          spread: 70,
          origin: { y: 0.6 }
        });
      }

      // Refresh database table
      loadDatabaseMatches();

    } catch (err) {
      console.error('Error submitting match:', err);
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
      <div><strong>Agent:</strong> ${escapeHtml(payload.player_name)}</div>
      <div><strong>⚔️ Attack Tactics:</strong> ${escapeHtml(atkNames)}</div>
      <div><strong>🛡️ Defence Tactics:</strong> ${escapeHtml(defNames)}</div>
    `;

    processingModal.classList.add('active');
  }

  btnCloseModal.addEventListener('click', () => {
    processingModal.classList.remove('active');
    clearAllSelections();
  });

  btnSubmitMatch.addEventListener('click', submitMatch);

  // ==========================================================================
  // SECTION 7: DATABASE MATCH QUEUE
  // ==========================================================================
  async function loadDatabaseMatches() {
    try {
      const response = await fetch('/api/matches');
      const data = await response.json();
      const matches = data.matches || [];

      if (matches.length === 0) {
        matchesTableBody.innerHTML = `
          <tr>
            <td colspan="5" class="empty-table-msg">No match records yet. Submit a tactical loadout above to start!</td>
          </tr>
        `;
        return;
      }

      matchesTableBody.innerHTML = matches.slice(0, 10).map(m => {
        const pA = m.player_a ? m.player_a.name : 'Player A';
        const pB = m.player_b ? m.player_b.name : 'AI Opponent';
        const status = m.status || 'processing';

        return `
          <tr>
            <td><code>${m.match_id}</code></td>
            <td>${m.created_at || 'Just now'}</td>
            <td><strong>${escapeHtml(pA)}</strong></td>
            <td>${escapeHtml(pB)}</td>
            <td><span class="badge-status ${status}">${status}</span></td>
          </tr>
        `;
      }).join('');

    } catch (err) {
      console.error('Failed to load database matches:', err);
    }
  }

  // ==========================================================================
  // HELPER UTILITIES
  // ==========================================================================
  function showFloatingNotice(msg) {
    const notice = document.createElement('div');
    notice.style.position = 'fixed';
    notice.style.bottom = '24px';
    notice.style.right = '24px';
    notice.style.background = 'linear-gradient(135deg, #7b5cfa 0%, #ff6584 100%)';
    notice.style.color = '#ffffff';
    notice.style.padding = '14px 22px';
    notice.style.borderRadius = '9999px';
    notice.style.fontSize = '0.92rem';
    notice.style.fontWeight = '700';
    notice.style.boxShadow = '0 12px 30px rgba(0,0,0,0.5)';
    notice.style.zIndex = '999999';
    notice.style.animation = 'fadeInUp 0.3s ease';
    notice.textContent = msg;

    document.body.appendChild(notice);
    setTimeout(() => {
      notice.style.opacity = '0';
      notice.style.transition = 'opacity 0.4s ease';
      setTimeout(() => notice.remove(), 400);
    }, 3200);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
});
