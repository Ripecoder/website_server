import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm";

const supabase = createClient(
  "https://wbwmffhegokbnfgtfufz.supabase.co",
  "YOUR_ANON_KEY"
);

// ─────────────────────────────────────
// GET CLIENT STATUS
// ─────────────────────────────────────
async function getClientStatus(email) {
  try {
    const res = await fetch(
      `https://website-server-9b3o.onrender.com/api/client/status?email=${encodeURIComponent(email)}`
    );

    if (!res.ok) return { exists: false };

    return await res.json();
  } catch {
    return { exists: false };
  }
}

// ─────────────────────────────────────
// ROUTING CORE
// ─────────────────────────────────────
async function checkAuth() {
  const { data } = await supabase.auth.getSession();
  const session = data.session;

  const path = window.location.pathname;

  if (!session) {
    if (!path.includes("login.html")) {
      window.location.href = "login.html";
    }
    return;
  }

  const email = session.user.email;
  const status = await getClientStatus(email);

  if (status.exists) {
    sessionStorage.setItem("verbe_api_key", status.api_key);

    if (!path.includes("client-dashboard.html")) {
      window.location.href = "client-dashboard.html";
    }
    return;
  }

  if (!path.includes("dashboard.html")) {
    window.location.href = "dashboard.html";
  }
}

checkAuth();