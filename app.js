/* ==========================================================================
   Revenue Intelligence Inbox — Frontend Controller
   Vanilla JavaScript (ES6+), Zero external dependencies.
   ========================================================================== */

// Global State
const STATE = {
  records: [],
  metrics: {},
  taxonomy: [
    "Deal Next Steps",
    "Customer Follow-up",
    "Sales Coaching",
    "Partner Development",
    "Internal / Vendor Note",
    "Human Review"
  ],
  auditLog: [],
  lastBatchId: null,
  activeView: "overview",
  selectedRecord: null,
  filters: {
    search: "",
    sourceType: "all",
    usableText: "all",
    route: "all",
    reviewState: "all",
    override: "all",
    person: "all"
  }
};

// Routing slug mapping
const ROUTE_SLUGS = {
  "Deal Next Steps": "deal-next-steps",
  "Customer Follow-up": "customer-follow-up",
  "Sales Coaching": "sales-coaching",
  "Partner Development": "partner-development",
  "Internal / Vendor Note": "internal-vendor-note",
  "Human Review": "human-review"
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupFilterListeners();
  setupReplayControls();
  setupExportControls();
  setupModalListeners();
  
  // Load data from backend
  loadStateFromBackend();
});

// ==========================================
// API & State Synchronization
// ==========================================
async function loadStateFromBackend(notify = false) {
  try {
    const res = await fetch("/api/state");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    
    STATE.records = data.records || [];
    STATE.metrics = data.metrics || {};
    STATE.auditLog = data.audit_log || [];
    STATE.lastBatchId = data.last_batch_id;
    
    // Save to local storage as client-side backup
    try {
      localStorage.setItem("rev_inbox_cache", JSON.stringify({
        recordsCount: STATE.records.length,
        timestamp: new Date().toISOString()
      }));
    } catch (e) {}

    renderApp();
    if (notify) showToast("State synchronized with server", "info");
  } catch (err) {
    console.error("Failed to load state:", err);
    showToast("Server connection error. Using cached state.", "warning");
  }
}

function renderApp() {
  updateSidebarMetrics();
  renderOverviewView();
  renderInboxTable();
  renderExportsView();
  renderReplayView();
  
  // Update drawer if open
  if (STATE.selectedRecord) {
    const current = STATE.records.find(
      r => r.source_type === STATE.selectedRecord.source_type && 
           r.source_id === STATE.selectedRecord.source_id
    );
    if (current) {
      STATE.selectedRecord = current;
      renderDetailDrawer(current);
    }
  }
}

function updateSidebarMetrics() {
  const m = STATE.metrics;
  const total = m.total_unique_records || STATE.records.length;
  const usable = m.usable_text_count || 0;
  
  const elTotal = document.getElementById("sidebar-total-records");
  const elUsable = document.getElementById("sidebar-usable-records");
  const elBatch = document.getElementById("sidebar-last-batch");
  
  if (elTotal) elTotal.textContent = total;
  if (elUsable) elUsable.textContent = `${usable} (${m.usable_coverage_pct || 0}%)`;
  if (elBatch) elBatch.textContent = STATE.lastBatchId || "None";
}

// ==========================================
// Navigation & Views
// ==========================================
function setupNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const targetView = item.getAttribute("data-view");
      navigateToView(targetView);
    });
  });

  // Handle URL hash on load
  const hash = window.location.hash.replace("#", "");
  if (hash && ["overview", "inbox", "brief", "exports", "replay", "settings"].includes(hash)) {
    navigateToView(hash);
  }
}

function navigateToView(viewId) {
  STATE.activeView = viewId;
  window.location.hash = viewId;

  // Update navigation items
  document.querySelectorAll(".nav-item").forEach(item => {
    item.classList.toggle("active", item.getAttribute("data-view") === viewId);
  });

  // Update views
  document.querySelectorAll(".view-container").forEach(view => {
    view.classList.toggle("active", view.id === `view-${viewId}`);
  });

  // Update top bar title
  const titleEl = document.getElementById("top-bar-title");
  const titles = {
    overview: "Overview Dashboard",
    inbox: "Conversation Inbox",
    brief: "Manager Brief — 21 August 2026",
    exports: "Routing Governance & Exports",
    replay: "Import & Contract Replay Console",
    settings: "Settings, Findings & Data Definitions"
  };
  if (titleEl) titleEl.textContent = titles[viewId] || "Revenue Intelligence Inbox";

  // If opening inbox, re-render
  if (viewId === "inbox") {
    renderInboxTable();
  } else if (viewId === "exports") {
    renderExportsView();
  }
}

// ==========================================
// View 1: Overview Dashboard
// ==========================================
function renderOverviewView() {
  const m = STATE.metrics;
  const total = m.total_unique_records || 0;
  const calls = m.call_count || 0;
  const meetings = m.meeting_count || 0;
  const usable = m.usable_text_count || 0;
  const missing = m.missing_text_count || 0;
  const overrides = m.manual_overrides_count || 0;
  const stale = m.stale_warnings_count || 0;
  const reviews = m.human_review_count || 0;

  // Set card values
  setMetricCard("kpi-total-records", total, `${calls} Calls • ${meetings} Meetings`);
  setMetricCard("kpi-usable-text", usable, `${m.usable_coverage_pct || 0}% coverage of selected records`);
  setMetricCard("kpi-missing-text", missing, "Intake queue awaiting transcripts");
  setMetricCard("kpi-manual-overrides", overrides, "Preserved manager decisions");
  setMetricCard("kpi-stale-warnings", stale, "Source text updated in revision 2");
  setMetricCard("kpi-human-review", reviews, "Requires human review / verification");

  // Render activity breakdown by person
  renderPersonActivityBars();

  // Render route distribution cards
  renderRouteDistributionMeters();
}

function setMetricCard(id, value, sub) {
  const el = document.getElementById(id);
  if (!el) return;
  const valEl = el.querySelector(".metric-value");
  const subEl = el.querySelector(".metric-sub");
  if (valEl) valEl.textContent = value;
  if (subEl) subEl.textContent = sub;
}

function renderPersonActivityBars() {
  const container = document.getElementById("person-activity-container");
  if (!container) return;

  const reps = (STATE.metrics.activity_by_person && STATE.metrics.activity_by_person.reps) || {};
  const orgs = (STATE.metrics.activity_by_person && STATE.metrics.activity_by_person.organizers) || {};

  const maxRepVal = Math.max(...Object.values(reps), 1);
  const maxOrgVal = Math.max(...Object.values(orgs), 1);

  let html = `
    <div class="activity-bars-grid">
      <div>
        <div class="section-label" style="margin-bottom: 12px;">Call Representatives (Telephony Reps)</div>
  `;

  for (const [rep, count] of Object.entries(reps)) {
    const pct = Math.round((count / maxRepVal) * 100);
    html += `
      <div class="person-bar-row" style="cursor: pointer;" onclick="filterInboxByPerson('${rep}', 'call')">
        <div class="person-name" title="${rep}">${rep}</div>
        <div class="bar-track">
          <div class="bar-fill" style="width: ${pct}%;"></div>
        </div>
        <div class="person-count">${count}</div>
      </div>
    `;
  }

  html += `
      </div>
      <div>
        <div class="section-label" style="margin-bottom: 12px;">Meeting Organizers (Calendar Creators)</div>
  `;

  for (const [org, count] of Object.entries(orgs)) {
    const pct = Math.round((count / maxOrgVal) * 100);
    html += `
      <div class="person-bar-row" style="cursor: pointer;" onclick="filterInboxByPerson('${org}', 'meeting')">
        <div class="person-name" title="${org}">${org}</div>
        <div class="bar-track">
          <div class="bar-fill bar-org" style="width: ${pct}%;"></div>
        </div>
        <div class="person-count">${count}</div>
      </div>
    `;
  }

  html += `
      </div>
    </div>
  `;

  container.innerHTML = html;
}

function renderRouteDistributionMeters() {
  const container = document.getElementById("route-distribution-overview");
  if (!container) return;

  const routeCounts = STATE.metrics.route_counts || {};
  const totalRoutesAssigned = Object.values(routeCounts).reduce((a, b) => a + b, 0);

  let html = `
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;">
  `;

  for (const route of STATE.taxonomy) {
    const count = routeCounts[route] || 0;
    const slug = ROUTE_SLUGS[route] || "human-review";
    html += `
      <div class="metric-card" style="padding: 12px 14px;" onclick="filterInboxByRoute('${route}')">
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <span class="badge badge-${slug}">${route}</span>
          <strong style="font-size: 18px;">${count}</strong>
        </div>
      </div>
    `;
  }

  html += `</div>`;
  container.innerHTML = html;
}

// Quick filter triggers from overview
function filterInboxByPerson(person, type) {
  STATE.filters.person = person;
  STATE.filters.sourceType = type;
  const selectPerson = document.getElementById("filter-person");
  const selectType = document.getElementById("filter-source-type");
  if (selectPerson) selectPerson.value = person;
  if (selectType) selectType.value = type;
  navigateToView("inbox");
}

function filterInboxByRoute(route) {
  STATE.filters.route = route;
  const selectRoute = document.getElementById("filter-route");
  if (selectRoute) selectRoute.value = route;
  navigateToView("inbox");
}

function filterInboxByCondition(key, val) {
  STATE.filters[key] = val;
  navigateToView("inbox");
}

// ==========================================
// View 2: Conversation Inbox
// ==========================================
function setupFilterListeners() {
  const searchInput = document.getElementById("filter-search");
  const selectType = document.getElementById("filter-source-type");
  const selectUsable = document.getElementById("filter-usable");
  const selectRoute = document.getElementById("filter-route");
  const selectReview = document.getElementById("filter-review-state");
  const selectOverride = document.getElementById("filter-override");
  const btnReset = document.getElementById("btn-reset-filters");

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      STATE.filters.search = e.target.value.toLowerCase().trim();
      renderInboxTable();
    });
  }

  if (selectType) {
    selectType.addEventListener("change", (e) => {
      STATE.filters.sourceType = e.target.value;
      renderInboxTable();
    });
  }

  if (selectUsable) {
    selectUsable.addEventListener("change", (e) => {
      STATE.filters.usableText = e.target.value;
      renderInboxTable();
    });
  }

  if (selectRoute) {
    selectRoute.addEventListener("change", (e) => {
      STATE.filters.route = e.target.value;
      renderInboxTable();
    });
  }

  if (selectReview) {
    selectReview.addEventListener("change", (e) => {
      STATE.filters.reviewState = e.target.value;
      renderInboxTable();
    });
  }

  if (selectOverride) {
    selectOverride.addEventListener("change", (e) => {
      STATE.filters.override = e.target.value;
      renderInboxTable();
    });
  }

  if (btnReset) {
    btnReset.addEventListener("click", () => {
      STATE.filters = {
        search: "",
        sourceType: "all",
        usableText: "all",
        route: "all",
        reviewState: "all",
        override: "all",
        person: "all"
      };
      if (searchInput) searchInput.value = "";
      if (selectType) selectType.value = "all";
      if (selectUsable) selectUsable.value = "all";
      if (selectRoute) selectRoute.value = "all";
      if (selectReview) selectReview.value = "all";
      if (selectOverride) selectOverride.value = "all";
      renderInboxTable();
    });
  }
}

function getFilteredRecords() {
  return STATE.records.filter(r => {
    const f = STATE.filters;
    const p = r.payload || {};

    // Search filter
    if (f.search) {
      const term = f.search;
      const ref = (r.record_ref || "").toLowerCase();
      const rep = (p.rep_name || p.rep_email || p.organizer_email || "").toLowerCase();
      const title = (p.title || p.to_number || "").toLowerCase();
      const summary = (r.analysis && r.analysis.summary ? r.analysis.summary : "").toLowerCase();
      const contact = (r.analysis && r.analysis.company_or_contact ? r.analysis.company_or_contact : "").toLowerCase();
      
      const match = ref.includes(term) || rep.includes(term) || title.includes(term) || 
                    summary.includes(term) || contact.includes(term);
      if (!match) return false;
    }

    // Source Type
    if (f.sourceType !== "all" && r.source_type !== f.sourceType) {
      return false;
    }

    // Usable Text
    if (f.usableText === "usable" && !r.has_usable_text) return false;
    if (f.usableText === "missing" && r.has_usable_text) return false;

    // Route
    if (f.route !== "all" && !(r.effective_routes && r.effective_routes.includes(f.route))) {
      return false;
    }

    // Review State
    if (f.reviewState !== "all" && r.review_state !== f.reviewState) {
      return false;
    }

    // Override
    if (f.override === "override" && !r.is_manual_override) return false;
    if (f.override === "automated" && r.is_manual_override) return false;

    // Person
    if (f.person !== "all") {
      const rep = p.rep_name || p.rep_email || p.organizer_email || "";
      if (rep !== f.person) return false;
    }

    return true;
  });
}

function renderInboxTable() {
  const tbody = document.getElementById("inbox-table-body");
  const countEl = document.getElementById("inbox-filtered-count");
  if (!tbody) return;

  const filtered = getFilteredRecords();
  if (countEl) countEl.textContent = `Showing ${filtered.length} of ${STATE.records.length} records`;

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="10" style="text-align: center; padding: 32px; color: var(--text-muted);">
          No records match the current filter criteria.
        </td>
      </tr>
    `;
    return;
  }

  // Sort by ref
  filtered.sort((a, b) => a.record_ref.localeCompare(b.record_ref));

  tbody.innerHTML = filtered.map(r => {
    const p = r.payload || {};
    const ref = r.record_ref;
    const st = r.source_type;
    const isCall = st === "call";
    const repOrg = isCall 
      ? (p.rep_name || p.rep_email || "Rep: Unknown") 
      : (p.organizer_email || "Org: Unknown");

    const contactTitle = isCall 
      ? (r.analysis?.company_or_contact || p.to_number || "Direct Call")
      : (p.title || "Meeting");

    const dt = isCall ? p.started_at : p.starts_at;
    const formattedDt = formatIST(dt);

    const isSelected = STATE.selectedRecord && 
      STATE.selectedRecord.source_type === r.source_type && 
      STATE.selectedRecord.source_id === r.source_id;

    // Route Badges
    const effectiveBadges = (r.effective_routes || []).map(rt => {
      const slug = ROUTE_SLUGS[rt] || "human-review";
      return `<span class="badge badge-${slug}">${rt}</span>`;
    }).join(" ");

    return `
      <tr class="${isSelected ? 'row-selected' : ''}" onclick="selectRecord('${r.source_type}', '${r.source_id}')" style="cursor: pointer;">
        <td>
          <strong style="color: var(--primary); font-size: 13.5px;">${ref}</strong>
        </td>
        <td>
          <span class="badge ${isCall ? 'badge-call' : 'badge-meeting'}">${st.toUpperCase()}</span>
        </td>
        <td>
          <div style="font-weight: 600; font-size: 12.5px;">${escapeHtml(repOrg)}</div>
          <div style="font-size: 11px; color: var(--text-muted);">${isCall ? 'Telephony Rep' : 'Calendar Organizer'}</div>
        </td>
        <td>
          <div style="font-weight: 500; font-size: 12.5px;" title="${escapeHtml(contactTitle)}">
            ${escapeHtml(truncate(contactTitle, 32))}
          </div>
        </td>
        <td style="font-size: 12px; color: var(--text-secondary); white-space: nowrap;">
          ${formattedDt}
        </td>
        <td>
          <span class="badge ${r.applied_revision === 2 ? 'badge-rev2' : 'badge-rev1'}">
            v${r.applied_revision}
          </span>
        </td>
        <td>
          ${r.has_usable_text 
            ? `<span class="badge badge-deal-next-steps" style="font-size: 11px;">✓ Available (${r.transcript_turns || 'Text'})</span>` 
            : `<span class="badge badge-human-review" style="font-size: 11px;">✗ Missing (Intake)</span>`}
        </td>
        <td>
          <div style="display: flex; flex-wrap: wrap; gap: 4px;">
            ${effectiveBadges}
          </div>
        </td>
        <td>
          ${r.is_manual_override 
            ? `<span class="badge badge-override" title="Route modified by human manager">Manual Override</span>` 
            : `<span style="font-size: 11px; color: var(--text-muted);">Automated</span>`}
        </td>
        <td>
          <span class="badge ${r.analysis_freshness === 'Stale - Source Updated' ? 'badge-stale' : 'badge-call'}" style="font-size: 11px;">
            ${r.review_state}
          </span>
        </td>
      </tr>
    `;
  }).join("");
}

// ==========================================
// Detail Drawer (Conversation Inspector)
// ==========================================
function selectRecord(sourceType, sourceId) {
  const rec = STATE.records.find(r => r.source_type === sourceType && r.source_id === sourceId);
  if (!rec) return;

  STATE.selectedRecord = rec;
  renderDetailDrawer(rec);
  openDrawer();
}

function openDrawer() {
  const overlay = document.getElementById("detail-drawer-overlay");
  if (overlay) overlay.classList.add("open");
}

function closeDrawer() {
  const overlay = document.getElementById("detail-drawer-overlay");
  if (overlay) overlay.classList.remove("open");
  STATE.selectedRecord = null;
  renderInboxTable();
}

function renderDetailDrawer(record) {
  const drawerBody = document.getElementById("drawer-content");
  const refEl = document.getElementById("drawer-record-ref");
  const typeEl = document.getElementById("drawer-source-type");
  const revEl = document.getElementById("drawer-revision-badge");
  
  if (!drawerBody) return;

  const p = record.payload || {};
  const ref = record.record_ref;
  const st = record.source_type;
  const rev = record.applied_revision;
  const analysis = record.analysis || {};
  const isCall = st === "call";

  if (refEl) refEl.textContent = ref;
  if (typeEl) {
    typeEl.textContent = st.toUpperCase();
    typeEl.className = `badge ${isCall ? 'badge-call' : 'badge-meeting'}`;
  }
  if (revEl) {
    revEl.textContent = `Revision ${rev}`;
    revEl.className = `badge ${rev === 2 ? 'badge-rev2' : 'badge-rev1'}`;
  }

  // Stale Analysis Warning Banner
  let warningBanner = "";
  if (record.analysis_freshness === "Stale - Source Updated") {
    warningBanner = `
      <div class="analysis-box stale-box" style="margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <strong style="color: #991b1b; font-size: 13px;">⚠️ Source Revision Updated to v2 (Late Transcript)</strong>
        </div>
        <p style="font-size: 12.5px; color: #7f1d1d; margin-top: 6px;">
          New conversation text was supplied in delivery update-002. Automated analysis is marked <em>Pending Review</em>.
          Your manual route override remains preserved per data contract.
        </p>
      </div>
    `;
  }

  // Route Multi-Select Control
  const effectiveRoutes = record.effective_routes || [];
  let routeCheckboxes = STATE.taxonomy.map(route => {
    const checked = effectiveRoutes.includes(route) ? "checked" : "";
    return `
      <label class="checkbox-label">
        <input type="checkbox" name="drawer-route" value="${route}" ${checked}>
        <span>${route}</span>
      </label>
    `;
  }).join("");

  // Supporting Citations HTML
  let citationsHtml = "";
  if (analysis.evidence_citations && analysis.evidence_citations.length > 0) {
    citationsHtml = analysis.evidence_citations.map(c => `
      <div class="citation-item">
        <div class="citation-quote">"${escapeHtml(c.quote)}"</div>
        <div class="citation-context">Source context: ${escapeHtml(c.context)}</div>
      </div>
    `).join("");
  } else {
    citationsHtml = `<p style="font-size: 12.5px; color: var(--text-muted);">No supporting citations available.</p>`;
  }

  // Transcript / Turns HTML
  let transcriptHtml = "";
  if (isCall) {
    const rawTranscript = p.transcript;
    if (rawTranscript) {
      transcriptHtml = `
        <div style="background-color: #f8fafc; border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 14px; font-size: 13px; line-height: 1.6; max-height: 300px; overflow-y: auto;">
          ${escapeHtml(rawTranscript).replace(/\n/g, '<br>')}
        </div>
      `;
    } else {
      transcriptHtml = `
        <div class="analysis-box" style="background: #f8fafc;">
          <strong style="font-size: 13px; color: var(--text-secondary);">No conversation audio/transcript supplied</strong>
          <p style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">
            This is an intake metadata record (B-series background call). Substantive analysis is withheld per data contract.
          </p>
        </div>
      `;
    }
  } else {
    // Meeting turns
    const tp = record.transcript_payload;
    const turns = (tp && tp.turns) || [];
    if (turns.length > 0) {
      transcriptHtml = `
        <div class="turns-container" style="max-height: 380px; overflow-y: auto;">
          ${turns.map((t, idx) => `
            <div class="turn-card">
              <div class="turn-header">
                <span class="turn-speaker">${escapeHtml(t.speaker || 'Speaker')} (Turn ${idx + 1})</span>
                <span style="font-family: monospace;">${t.timecode || '00:00:00'}</span>
              </div>
              <div class="turn-text">${escapeHtml(t.text)}</div>
            </div>
          `).join("")}
        </div>
      `;
    } else {
      const reason = (tp && tp.unavailable_reason) || "No transcript turns supplied";
      transcriptHtml = `
        <div class="analysis-box" style="background: #f8fafc;">
          <strong style="font-size: 13px; color: var(--text-secondary);">No spoken transcript available</strong>
          <p style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">
            Reason: <em>${escapeHtml(reason)}</em>
          </p>
        </div>
      `;
    }
  }

  // Assemble Drawer HTML
  drawerBody.innerHTML = `
    ${warningBanner}

    <!-- Route Editor -->
    <div class="route-editor-box">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <span class="section-label">Effective Routing Destination(s)</span>
        ${record.is_manual_override ? '<span class="badge badge-override">Manual Override Active</span>' : '<span style="font-size: 11px; color: var(--text-muted);">Automated Suggestion</span>'}
      </div>
      <div class="route-checkbox-grid">
        ${routeCheckboxes}
      </div>
      <div style="display: flex; gap: 8px;">
        <button class="btn btn-primary btn-sm" onclick="saveManualRouteFromDrawer()">Save Route Correction</button>
        ${record.is_manual_override ? '<button class="btn btn-secondary btn-sm" onclick="resetRouteFromDrawer()">Reset to Suggestion</button>' : ''}
      </div>
    </div>

    <!-- Candidate Analysis -->
    <div class="analysis-box">
      <div class="section-label">Candidate-Derived Analysis (SpendNest Engine)</div>
      <h4 style="font-size: 14px; margin-bottom: 6px;">Executive Summary</h4>
      <p style="font-size: 13px; color: var(--text-primary); margin-bottom: 12px; line-height: 1.5;">
        ${escapeHtml(analysis.summary || "No substantive summary.")}
      </p>

      <h4 style="font-size: 14px; margin-bottom: 6px;">Routing Rationale</h4>
      <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 12px;">
        ${escapeHtml(analysis.route_rationale || "N/A")}
      </p>

      <h4 style="font-size: 14px; margin-bottom: 6px;">Supporting Source Citations</h4>
      ${citationsHtml}
    </div>

    <!-- Critical Boundary Box -->
    <div class="analysis-box boundary-box">
      <div class="section-label boundary-label">What The Evidence Does NOT Establish (Critical Boundary)</div>
      <p style="font-size: 12.5px; color: #78350f; line-height: 1.5;">
        ${escapeHtml(analysis.what_evidence_does_not_establish || "Evidence boundaries not specified.")}
      </p>
    </div>

    <!-- Recommended Next Step & Owner -->
    <div class="analysis-box">
      <div class="section-label">Supported Action Item</div>
      <div style="display: flex; flex-direction: column; gap: 6px; font-size: 13px;">
        <div><strong>Recommended Action:</strong> ${escapeHtml(analysis.recommended_next_step || "None supported by text.")}</div>
        <div><strong>Explicitly Assigned Owner:</strong> ${escapeHtml(analysis.responsible_owner || "None established in conversation")}</div>
      </div>
    </div>

    <!-- Transcript / Turns Section -->
    <div style="margin-bottom: 20px;">
      <div class="section-label" style="margin-bottom: 8px;">Supplied Conversation Text / Turns</div>
      ${transcriptHtml}
    </div>

    <!-- Raw Source Metadata -->
    <div class="card" style="padding: 14px; background: #f8fafc;">
      <div class="section-label" style="margin-bottom: 8px;">Source Envelope & Metadata</div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 12px; font-family: monospace;">
        <div><strong>source_id:</strong> ${record.source_id.slice(0, 14)}...</div>
        <div><strong>applied_revision:</strong> ${record.applied_revision}</div>
        <div><strong>review_state:</strong> ${record.review_state}</div>
        <div><strong>analysis_freshness:</strong> ${record.analysis_freshness}</div>
        <div><strong>summary (upstream):</strong> null (withheld)</div>
        <div><strong>has_usable_text:</strong> ${record.has_usable_text}</div>
      </div>
    </div>
  `;
}

async function saveManualRouteFromDrawer() {
  if (!STATE.selectedRecord) return;
  const checkboxes = document.querySelectorAll("input[name='drawer-route']:checked");
  const selectedRoutes = Array.from(checkboxes).map(cb => cb.value);

  if (selectedRoutes.length === 0) {
    showToast("Please select at least one route destination", "warning");
    return;
  }

  try {
    const res = await fetch("/api/route", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_type: STATE.selectedRecord.source_type,
        source_id: STATE.selectedRecord.source_id,
        manual_routes: selectedRoutes
      })
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast(`Manual route saved for ${STATE.selectedRecord.record_ref}`, "success");
      await loadStateFromBackend();
    }
  } catch (err) {
    showToast("Error saving manual route: " + err.message, "warning");
  }
}

async function resetRouteFromDrawer() {
  if (!STATE.selectedRecord) return;
  try {
    const res = await fetch("/api/route/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_type: STATE.selectedRecord.source_type,
        source_id: STATE.selectedRecord.source_id
      })
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast(`Route reset to automated suggestion for ${STATE.selectedRecord.record_ref}`, "info");
      await loadStateFromBackend();
    }
  } catch (err) {
    showToast("Error resetting route: " + err.message, "warning");
  }
}

// ==========================================
// View 4: Routing & Exports
// ==========================================
function setupExportControls() {
  const btnExportZip = document.getElementById("btn-download-export-zip");
  const btnGenerateExports = document.getElementById("btn-generate-exports");

  if (btnGenerateExports) {
    btnGenerateExports.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/export", { method: "POST" });
        const data = await res.json();
        showToast(`Exports generated successfully (${data.export?.total_records || 44} records)`, "success");
        renderExportsView();
      } catch (err) {
        showToast("Export generation error: " + err.message, "warning");
      }
    });
  }

  if (btnExportZip) {
    btnExportZip.addEventListener("click", () => {
      window.location.href = "/api/export/zip";
    });
  }
}

async function renderExportsView() {
  const tbody = document.getElementById("manifest-table-body");
  if (!tbody) return;

  const records = STATE.records;
  if (!records || records.length === 0) return;

  const sorted = [...records].sort((a, b) => a.record_ref.localeCompare(b.record_ref));

  tbody.innerHTML = sorted.map(r => {
    const routes = r.effective_routes || [];
    const routeBadges = routes.map(rt => {
      const slug = ROUTE_SLUGS[rt] || "human-review";
      return `<span class="badge badge-${slug}">${rt}</span>`;
    }).join(" ");

    const outputPaths = routes.map(rt => {
      const slug = ROUTE_SLUGS[rt] || "human-review";
      return `outputs/${slug}/${r.record_ref}_${slug}.md`;
    });

    return `
      <tr>
        <td><strong>${r.record_ref}</strong></td>
        <td><span class="badge ${r.source_type === 'call' ? 'badge-call' : 'badge-meeting'}">${r.source_type}</span></td>
        <td style="font-family: monospace; font-size: 11px;">${r.source_id.slice(0, 10)}...</td>
        <td><span class="badge ${r.applied_revision === 2 ? 'badge-rev2' : 'badge-rev1'}">v${r.applied_revision}</span></td>
        <td>${routeBadges}</td>
        <td style="font-family: monospace; font-size: 11px;">
          ${outputPaths.map(p => `<div>${p}</div>`).join("")}
        </td>
        <td>
          <span class="badge ${r.is_manual_override ? 'badge-override' : 'badge-call'}">
            ${r.is_manual_override ? 'Manual' : 'Automated'}
          </span>
        </td>
        <td>${r.review_state}</td>
      </tr>
    `;
  }).join("");
}

// ==========================================
// View 5: Import & Replay Console
// ==========================================
function setupReplayControls() {
  const btnInitial = document.getElementById("btn-import-initial");
  const btnReordered = document.getElementById("btn-import-reordered");
  const btnUpdate = document.getElementById("btn-import-update");
  const btnReplayOlder = document.getElementById("btn-replay-older");
  const btnReset = document.getElementById("btn-reset-demo");
  const btnDemoFinal = document.getElementById("btn-load-demo-final");
  const btnSetM07 = document.getElementById("btn-set-m07-route");

  if (btnInitial) {
    btnInitial.addEventListener("click", async () => {
      await callReplayApi("/api/import/initial", "Initial batch (01_initial.json) imported");
    });
  }

  if (btnReordered) {
    btnReordered.addEventListener("click", async () => {
      await callReplayApi("/api/import/initial-reordered", "Reordered initial batch imported (idempotency check)");
    });
  }

  if (btnSetM07) {
    btnSetM07.addEventListener("click", async () => {
      const m07 = STATE.records.find(r => r.record_ref === "M07");
      if (!m07) {
        showToast("M07 not found in state", "warning");
        return;
      }
      try {
        const res = await fetch("/api/route", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source_type: m07.source_type,
            source_id: m07.source_id,
            manual_routes: ["Partner Development", "Deal Next Steps"]
          })
        });
        const data = await res.json();
        showToast("M07 manual route set to ['Partner Development', 'Deal Next Steps']", "success");
        await loadStateFromBackend();
      } catch (err) {
        showToast("Error setting M07 route: " + err.message, "warning");
      }
    });
  }

  if (btnUpdate) {
    btnUpdate.addEventListener("click", async () => {
      await callReplayApi("/api/import/update", "Update batch (02_update.json) imported");
    });
  }

  if (btnReplayOlder) {
    btnReplayOlder.addEventListener("click", async () => {
      await callReplayApi("/api/import/replay-older", "Older initial batch replayed (superseded revision check)");
    });
  }

  if (btnReset) {
    btnReset.addEventListener("click", async () => {
      if (confirm("Reset application state to clean? All local records will be cleared.")) {
        await callReplayApi("/api/reset", "Workspace reset to clean state");
      }
    });
  }

  if (btnDemoFinal) {
    btnDemoFinal.addEventListener("click", async () => {
      await callReplayApi("/api/demo-final", "Final demo state loaded (44 records, 18 usable texts)");
    });
  }
}

async function callReplayApi(endpoint, successMessage) {
  try {
    const res = await fetch(endpoint, { method: "POST" });
    const data = await res.json();
    showToast(successMessage, "success");
    await loadStateFromBackend();
    appendConsoleLog(endpoint, data);
  } catch (err) {
    showToast("Replay action error: " + err.message, "warning");
  }
}

function appendConsoleLog(action, data) {
  const logEl = document.getElementById("replay-console-log");
  if (!logEl) return;
  const time = new Date().toLocaleTimeString();
  const entry = document.createElement("div");
  entry.style.marginBottom = "8px";
  entry.innerHTML = `
    <span style="color: #38bdf8;">[${time}]</span> 
    <strong style="color: #a7f3d0;">${action}</strong>: 
    <span style="color: #e2e8f0;">${JSON.stringify(data.result || data.metrics || data)}</span>
  `;
  logEl.prepend(entry);
}

function renderReplayView() {
  const m = STATE.metrics;
  const m07 = STATE.records.find(r => r.record_ref === "M07");

  const totalEl = document.getElementById("replay-stat-unique");
  const usableEl = document.getElementById("replay-stat-usable");
  const m07RevEl = document.getElementById("replay-stat-m07-rev");
  const m07RouteEl = document.getElementById("replay-stat-m07-route");
  const m07OverrideEl = document.getElementById("replay-stat-m07-override");
  const m07FreshEl = document.getElementById("replay-stat-m07-freshness");

  if (totalEl) totalEl.textContent = m.total_unique_records || STATE.records.length;
  if (usableEl) usableEl.textContent = `${m.usable_text_count || 0} / ${m.total_unique_records || STATE.records.length}`;
  
  if (m07) {
    if (m07RevEl) m07RevEl.textContent = `Revision ${m07.applied_revision}`;
    if (m07RouteEl) m07RouteEl.textContent = (m07.effective_routes || []).join(", ");
    if (m07OverrideEl) m07OverrideEl.textContent = m07.is_manual_override ? "Yes (Preserved)" : "No";
    if (m07FreshEl) m07FreshEl.textContent = m07.analysis_freshness;
  }
}

// ==========================================
// Modals & Tooltips
// ==========================================
function setupModalListeners() {
  const modal = document.getElementById("methodology-modal");
  const btnClose = document.getElementById("btn-close-methodology");
  const btnOpen = document.querySelectorAll(".btn-open-methodology");

  btnOpen.forEach(b => {
    b.addEventListener("click", () => {
      if (modal) modal.classList.add("open");
    });
  });

  if (btnClose && modal) {
    btnClose.addEventListener("click", () => {
      modal.classList.remove("open");
    });
  }

  // Close on outside click
  window.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.classList.remove("open");
    }
    const drawerOverlay = document.getElementById("detail-drawer-overlay");
    if (e.target === drawerOverlay) {
      closeDrawer();
    }
  });
}

// ==========================================
// Utilities & Helpers
// ==========================================
function formatIST(isoStr) {
  if (!isoStr) return "N/A";
  try {
    const d = new Date(isoStr);
    return d.toLocaleString("en-IN", {
      timeZone: "Asia/Kolkata",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false
    }) + " IST";
  } catch (e) {
    return isoStr;
  }
}

function truncate(str, len = 28) {
  if (!str) return "";
  return str.length > len ? str.slice(0, len) + "…" : str;
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    setTimeout(() => toast.remove(), 250);
  }, 3200);
}
