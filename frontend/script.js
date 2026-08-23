// Change this if your backend runs on a different host/port (e.g. your Render backend URL)
const API_BASE_URL =
  window.location.origin && window.location.origin.startsWith("http") && !window.location.origin.includes(":5500")
    ? window.location.origin
    : "http://127.0.0.1:5000";

const chatWindow = document.getElementById("chatWindow");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const statusDot = document.getElementById("statusDot");
const quickChips = document.getElementById("quickChips");

// 65-second timeout to comfortably handle Render free-tier cold starts (30-50s)
const REQUEST_TIMEOUT_MS = 65000;

function addMessage(text, sender) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${sender}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  wrapper.appendChild(bubble);
  chatWindow.appendChild(wrapper);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return wrapper;
}

function showTyping(text = "Typing...") {
  let wrapper = document.getElementById("typingIndicator");
  if (!wrapper) {
    wrapper = document.createElement("div");
    wrapper.className = "message bot typing";
    wrapper.id = "typingIndicator";

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.id = "typingBubble";
    bubble.textContent = text;

    wrapper.appendChild(bubble);
    chatWindow.appendChild(wrapper);
  } else {
    const bubble = document.getElementById("typingBubble");
    if (bubble) bubble.textContent = text;
  }
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

/**
 * Fetch wrapper with AbortController timeout
 */
async function fetchWithTimeout(url, options = {}, timeoutMs = REQUEST_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Sends chat message with cold-start progress message, 60s+ timeout, and automatic 1x retry
 */
async function sendChatWithRetry(text) {
  const requestOptions = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text }),
  };

  // Attempt 1
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/api/chat`, requestOptions, REQUEST_TIMEOUT_MS);
    if (!res.ok) throw new Error(`Server returned HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("First request attempt failed / timed out. Retrying once...", err);
    
    // Update indicator to let user know retry is in progress
    showTyping("Connecting to server, this may take up to a minute...");

    // Wait 2 seconds before retry
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // Attempt 2 (automatic retry)
    const retryRes = await fetchWithTimeout(`${API_BASE_URL}/api/chat`, requestOptions, REQUEST_TIMEOUT_MS);
    if (!retryRes.ok) throw new Error(`Retry returned HTTP ${retryRes.status}`);
    return await retryRes.json();
  }
}

async function sendMessage(text) {
  if (!text.trim()) return;

  addMessage(text, "user");
  messageInput.value = "";
  sendBtn.disabled = true;

  // Start with default typing indicator
  showTyping("Typing...");

  // If the server takes more than 3 seconds (cold start), update to friendly connecting message
  const coldStartTimer = setTimeout(() => {
    showTyping("Connecting to server, this may take up to a minute...");
  }, 3000);

  try {
    const data = await sendChatWithRetry(text);
    clearTimeout(coldStartTimer);
    hideTyping();
    addMessage(data.reply, "bot");

    // Update status indicator to online
    if (statusDot) {
      statusDot.className = "status-dot online";
      statusDot.title = "Backend connected";
    }
  } catch (err) {
    clearTimeout(coldStartTimer);
    hideTyping();
    addMessage(
      "Sorry, I couldn't reach the server. The backend may still be starting up. Please try sending your message again in a few seconds.",
      "bot"
    );

    if (statusDot) {
      statusDot.className = "status-dot offline";
      statusDot.title = "Backend not reachable";
    }
  } finally {
    sendBtn.disabled = false;
    messageInput.focus();
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage(messageInput.value);
});

quickChips.addEventListener("click", (e) => {
  if (e.target.classList.contains("chip")) {
    sendMessage(e.target.textContent);
  }
});

async function checkBackendStatus() {
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/api/health`, {}, 15000);
    if (res.ok) {
      statusDot.className = "status-dot online";
      statusDot.title = "Backend connected";
    } else {
      throw new Error("Health check failed");
    }
  } catch {
    statusDot.className = "status-dot offline";
    statusDot.title = "Backend waking up / not reachable";
  }
}

checkBackendStatus();
