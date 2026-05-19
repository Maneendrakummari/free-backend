// ─────────────────────────────────────────────────────────────────────────────
// Replace the existing handleSend() function in your portfolio HTML with this.
// Set API_BASE to wherever you deploy the FastAPI backend.
// ─────────────────────────────────────────────────────────────────────────────

const API_BASE = "http://localhost:8000/api/v1"; // ← change to your deployed URL

async function handleSend(e) {
  e.preventDefault();
  const btn = document.getElementById("sendBtn");

  const name    = document.getElementById("fn").value.trim();
  const email   = document.getElementById("em").value.trim();
  const budget  = document.getElementById("bud").value || null;
  const message = document.getElementById("msg").value.trim();

  // Basic client-side guard
  if (!name || !email || !message) return;

  btn.textContent = "Sending…";
  btn.disabled = true;
  btn.style.opacity = "0.7";

  try {
    const res = await fetch(`${API_BASE}/contact`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, budget, message }),
    });

    const data = await res.json();

    if (res.ok && data.success) {
      btn.textContent = "✓ Message Sent!";
      btn.style.background = "#22c55e";
      btn.style.boxShadow = "0 4px 20px rgba(34,197,94,.3)";
      e.target.reset();

      setTimeout(() => {
        btn.textContent = "Send Message →";
        btn.style.background = "";
        btn.style.boxShadow = "";
        btn.disabled = false;
        btn.style.opacity = "";
      }, 3200);

    } else if (res.status === 429) {
      showError(btn, "Too many requests — please wait a minute.");
    } else {
      const detail = data.detail || "Something went wrong. Please try again.";
      showError(btn, detail);
    }

  } catch (err) {
    showError(btn, "Network error — please check your connection.");
  }
}

function showError(btn, msg) {
  btn.textContent = "✗ " + msg;
  btn.style.background = "#ef4444";
  btn.style.boxShadow = "0 4px 20px rgba(239,68,68,.3)";
  setTimeout(() => {
    btn.textContent = "Send Message →";
    btn.style.background = "";
    btn.style.boxShadow = "";
    btn.disabled = false;
    btn.style.opacity = "";
  }, 3500);
}
