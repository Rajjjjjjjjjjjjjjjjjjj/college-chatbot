// Change this if your backend runs on a different host/port
const API_BASE_URL = "http://127.0.0.1:5000";

const chatWindow = document.getElementById("chatWindow");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const statusDot = document.getElementById("statusDot");
const quickChips = document.getElementById("quickChips");

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

function showTyping() {
  const wrapper = document.createElement("div");
  wrapper.className = "message bot typing";
  wrapper.id = "typingIndicator";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = "Typing...";

  wrapper.appendChild(bubble);
  chatWindow.appendChild(wrapper);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

async function sendMessage(text) {
  if (!text.trim()) return;

  addMessage(text, "user");
  messageInput.value = "";
  sendBtn.disabled = true;
  showTyping();

  try {
    const res = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    if (!res.ok) throw new Error("Backend error");

    const data = await res.json();
    hideTyping();
    addMessage(data.reply, "bot");
  } catch (err) {
    hideTyping();
    addMessage(
      "Sorry, I couldn't reach the server. Please make sure the backend is running.",
      "bot"
    );
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
    const res = await fetch(`${API_BASE_URL}/api/health`);
    if (res.ok) {
      statusDot.classList.add("online");
      statusDot.title = "Backend connected";
    } else {
      throw new Error("not ok");
    }
  } catch {
    statusDot.classList.add("offline");
    statusDot.title = "Backend not reachable";
  }
}

checkBackendStatus();
