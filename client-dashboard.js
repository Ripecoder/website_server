// ───────────────────────────────────────
// VERBE — CLIENT DASHBOARD (FIXED)
// ───────────────────────────────────────

// ── ELEMENTS ───────────────────────────

const leadsContainer = document.getElementById("leadsContainer");

const leadsTodayEl = document.getElementById("leadsToday");
const totalLeadsEl = document.getElementById("totalLeads");
const attendedLeadsEl = document.getElementById("attendedLeads");

const trialDaysEl = document.getElementById("trialDays");
const trialFillEl = document.getElementById("trialFill");

const upgradeBtn = document.getElementById("upgradeBtn");

// ── CLIENT DATA (SOURCE OF TRUTH) ───────

const rawClientData = sessionStorage.getItem("client_data");

if (!rawClientData) {
  window.location.href = "login.html";
}

const clientData = JSON.parse(rawClientData);
const apiKey = clientData.api_key;



// ── SUBSCRIPTION LOADER (DB TRUTH) ─────

async function loadSubscriptionTime() {
  try {

    const res = await fetch(
      `https://website-server-9b3o.onrender.com/api/client/time?api_key=${apiKey}`
    );

    const data = await res.json();

    if (!data.success) {
      console.log("Subscription fetch failed");
      return;
    }

    const days = data.subscription_time ?? 0;

    sessionStorage.setItem("subscription_time", days);

    updateTrialFromDB(days);

  } catch (err) {
    console.log("Subscription error:", err);
  }
}

// ── TRIAL UI (DB DRIVEN) ───────────────

function updateTrialFromDB(daysRemaining) {

  updateSubscriptionBadge(daysRemaining);

  if (daysRemaining <= 0) {
    trialDaysEl.textContent = "Trial Expired";
    trialFillEl.style.width = "0%";
    return;
  }

  trialDaysEl.textContent = `${daysRemaining} days remaining`;

  const percentage = Math.max(0, (daysRemaining / 30) * 100);
  trialFillEl.style.width = `${percentage}%`;
}

// ── FORMAT TIME ─────────────────────────

function formatTime(timestamp) {
  if (!timestamp) return "Just now";

  const seconds = Math.floor(
    (Date.now() - new Date(timestamp)) / 1000
  );

  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  return `${Math.floor(hours / 24)}d ago`;
}

// ── UPDATE LEAD STATUS (BACKEND) ────────

async function updateLeadStatus(leadId, attended) {
  try {
    const res = await fetch(
      "https://website-server-9b3o.onrender.com/api/client/updateLeadStatus",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          api_key: apiKey,
          lead_id: leadId,
          attended: attended
        })
      }
    );
    const data = await res.json();
    if (!data.success) {
      console.log("Failed to update lead status:", data);
    }
  } catch (err) {
    console.log("updateLeadStatus error:", err);
  }
}

// ── CREATE LEAD CARD ────────────────────

function createLeadCard(lead) {

  const card = document.createElement("div");
  card.className = "lead-card";

  card.innerHTML = `
    <div class="lead-top">

      <div>
        <div class="lead-name">
          ${lead.intent || "New Lead"}
        </div>

        <div class="lead-time">
          Lead arrived ${formatTime(lead.created_at)}
        </div>
      </div>

      <label class="attended-wrap">
        <input type="checkbox" class="attended-checkbox" ${lead.attended ? "checked" : ""}>
        <span>Attended</span>
      </label>

    </div>

    <div class="lead-details">

      <div class="lead-item">📞 ${lead.phone || "N/A"}</div>
      <div class="lead-item">💰 ${lead.budget || "N/A"}</div>
      <div class="lead-item">📍 ${lead.location || "N/A"}</div>
      <div class="lead-item">🏠 ${lead.bhk || "N/A"}</div>
      <div class="lead-item">✨ ${lead.special_preferences || "None"}</div>

    </div>
  `;

  const checkbox = card.querySelector(".attended-checkbox");

  checkbox.addEventListener("change", () => {
    updateLeadStatus(lead.id, checkbox.checked);
    updateStats();
  });

  leadsContainer.prepend(card);
}

// ── LOAD LEADS ──────────────────────────

let loading = false;

async function loadLeads() {

  if (loading) return;
  loading = true;

  try {

    const res = await fetch(
      "https://website-server-9b3o.onrender.com/api/client/leads",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey })
      }
    );

    const data = await res.json();

    leadsContainer.innerHTML = "";

    if (!data.leads || data.leads.length === 0) {

      leadsContainer.innerHTML = `
        <div class="lead-card">
          <div class="lead-name">No leads yet</div>
          <div class="lead-time">Waiting for visitors...</div>
        </div>
      `;

      leadsTodayEl.textContent = "0";
      totalLeadsEl.textContent = "0";
      updateStats();
      return;
    }

    data.leads.reverse().forEach(createLeadCard);

    leadsTodayEl.textContent = data.leads.length;
    totalLeadsEl.textContent = data.leads.length;

    updateStats();

  } catch (err) {
    console.log("FAILED TO LOAD LEADS", err);

    leadsContainer.innerHTML = `
      <div class="lead-card">
        <div class="lead-name">Server Error</div>
        <div class="lead-time">Could not load leads</div>
      </div>
    `;
  } finally {
    loading = false;
  }
}

// ── STATS ───────────────────────────────

function updateStats() {
  const checked = document.querySelectorAll(".attended-checkbox:checked").length;
  attendedLeadsEl.textContent = checked;
}

// ── UPGRADE BUTTON ──────────────────────

upgradeBtn.addEventListener("click", () => {
  window.location.href = "payment.html";
});

// ── BOOTSTRAP (CRITICAL FIX) ─────────────

async function initDashboard() {

  if (!apiKey) {
    window.location.href = "login.html";
    return;
  }

  await loadSubscriptionTime();
  await loadLeads();
  updateStats();
}

document.addEventListener("DOMContentLoaded", initDashboard);


// ── CLIENT NAME + SUBSCRIPTION BADGE ───

const clientNameDisplay = document.getElementById("clientNameDisplay");
const subscriptionBadge = document.getElementById("subscriptionBadge");

const storedClientName = clientData.client_name || sessionStorage.getItem("verbe_website") || "Client";
if (clientNameDisplay) clientNameDisplay.textContent = storedClientName;

function updateSubscriptionBadge(days) {
  if (!subscriptionBadge) return;
  if (days > 14) {
    subscriptionBadge.textContent = "Active Plan";
    subscriptionBadge.classList.add("paid");
  } else {
    subscriptionBadge.textContent = "Free Trial";
    subscriptionBadge.classList.remove("paid");
  }
}



const websiteName = sessionStorage.getItem("verbe_website");

if (websiteName) {
  document.getElementById("websiteName").textContent = websiteName;
}

// ── MODAL + BUTTONS (DOM SAFE) ──────────

document.addEventListener("DOMContentLoaded", () => {

  const modalOverlay = document.getElementById("modalOverlay");
  const modalTitle   = document.getElementById("modalTitle");
  const modalClose   = document.getElementById("modalClose");
  const apiKeyView   = document.getElementById("apiKeyView");
  const scriptView   = document.getElementById("scriptView");
  const apiKeyCode   = document.getElementById("apiKeyCode");
  const scriptCode   = document.getElementById("scriptCode");

  // ── MODAL OPEN/CLOSE ──────────────────

  function openModal(type) {
    if (!modalOverlay) return;

    apiKeyView.classList.remove("active");
    scriptView.classList.remove("active");

    const key     = apiKey || "DEMO-API-KEY-XXXX-1234";
    const website = sessionStorage.getItem("verbe_website") || "your-site";

    if (type === "apikey") {
      modalTitle.textContent  = "Your API Key";
      apiKeyCode.textContent  = key;
      apiKeyView.classList.add("active");
    } else {
      modalTitle.textContent = "Embed Script";
      scriptCode.textContent =
`<script\n  src="https://chatbot-connect.vercel.app/chatbot.js"\n  data-key="${key}"\n  data-client_name="${website}">\n<\/script>`;
      scriptView.classList.add("active");
    }

    modalOverlay.classList.add("open");
  }

  function closeModal() {
    if (!modalOverlay) return;
    modalOverlay.classList.remove("open");
  }

  if (modalClose)   modalClose.addEventListener("click", closeModal);
  if (modalOverlay) modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) closeModal();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });

  // ── QUICK ACTION BUTTONS ──────────────

  document.getElementById("viewScriptBtn")?.addEventListener("click", () => {
    openModal("script");
  });

  document.getElementById("copyApiKeyBtn")?.addEventListener("click", () => {
    openModal("apikey");
  });

  document.getElementById("whatsappSetupBtn")?.addEventListener("click", () => {
    alert("WhatsApp integration is under development.");
  });

  // ── IN-MODAL COPY BUTTONS ─────────────

  async function copyToClipboard(text, btn) {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    btn.textContent = "Copied!";
    btn.classList.add("copied");
    setTimeout(() => {
      btn.textContent = "Copy";
      btn.classList.remove("copied");
    }, 1500);
  }

  document.getElementById("apiKeyCopyBtn")?.addEventListener("click", () => {
    copyToClipboard(apiKeyCode.textContent, document.getElementById("apiKeyCopyBtn"));
  });

  document.getElementById("scriptCopyBtn")?.addEventListener("click", () => {
    copyToClipboard(scriptCode.textContent, document.getElementById("scriptCopyBtn"));
  });

});