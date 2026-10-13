const messageInput = document.querySelector("#message-input");
const chatForm = document.querySelector("#chat-form");
const sendButton = document.querySelector("#send-button");
const newChatButton = document.querySelector("#new-chat");
const messages = document.querySelector("#messages");
const sessionState = document.querySelector("#session-state");
const serviceStatus = document.querySelector("#service-status");
const serviceStatusText = document.querySelector("#service-status-text");

const userStorageKey = "mall-concierge-guest-user-id";
const threadStorageKey = "mall-concierge-thread-id";
let userId = sessionStorage.getItem(userStorageKey) || "";
let threadId = sessionStorage.getItem(threadStorageKey) || "";
sendButton.disabled = !userId;

function addMessage(text, role, extraClass = "") {
  const row = document.createElement("div");
  row.className = `message-row ${role} ${extraClass}`.trim();

  const avatar = document.createElement("span");
  avatar.className = `message-avatar ${role === "user" ? "user-avatar" : ""}`.trim();
  avatar.setAttribute("aria-hidden", "true");
  const icon = document.createElement("i");
  icon.className = role === "user" ? "bi bi-person-fill" : "bi bi-stars";
  avatar.append(icon);

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = text;
  row.append(avatar, bubble);
  messages.append(row);
  messages.scrollTop = messages.scrollHeight;
  return row;
}

function resetMessages() {
  messages.replaceChildren();
  const welcome = document.createElement("div");
  welcome.className = "welcome-message";
  welcome.innerHTML = '<span class="welcome-mark"><i class="bi bi-stars" aria-hidden="true"></i></span><div><h2>What are you looking for?</h2><p>Ask about a product, an order, or your seller account.</p></div>';
  messages.append(welcome);
}

function startNewChat() {
  threadId = "";
  sessionStorage.removeItem(threadStorageKey);
  resetMessages();
  messageInput.focus();
}

async function checkService() {
  try {
    const response = await fetch("/health");
    if (!response.ok) throw new Error("Unavailable");
    serviceStatus.classList.add("is-online");
    serviceStatus.classList.remove("is-offline");
    serviceStatusText.textContent = "Service online";
  } catch {
    serviceStatus.classList.add("is-offline");
    serviceStatus.classList.remove("is-online");
    serviceStatusText.textContent = "Service offline";
  }
}

newChatButton.addEventListener("click", startNewChat);

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    messageInput.value = button.dataset.prompt;
    messageInput.focus();
  });
});

messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!userId || !message || sendButton.disabled) return;

  addMessage(message, "user");
  messageInput.value = "";
  sendButton.disabled = true;
  sendButton.innerHTML = '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span>';
  const pendingMessage = addMessage("Thinking...", "assistant", "typing");

  try {
    const response = await fetch("/api/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, message, thread_id: threadId || null }),
    });
    const data = await response.json();
    if (!response.ok) {
      const detail = typeof data.detail === "string" ? data.detail : "The message could not be sent.";
      throw new Error(detail);
    }

    threadId = data.thread_id;
    sessionStorage.setItem(threadStorageKey, threadId);
    pendingMessage.remove();
    addMessage(data.response, "assistant");
  } catch (error) {
    pendingMessage.remove();
    addMessage(error.message || "The service could not be reached.", "assistant", "error");
  } finally {
    sendButton.disabled = false;
    sendButton.innerHTML = '<i class="bi bi-arrow-up" aria-hidden="true"></i>';
    messageInput.focus();
  }
});

async function initializeGuestSession() {
  if (userId) {
    sessionState.textContent = "Guest account ready";
    sendButton.disabled = false;
    return;
  }

  try {
    const response = await fetch("/api/v1/sessions", { method: "POST" });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Guest account could not be created.");
    }
    userId = data.user_id;
    sessionStorage.setItem(userStorageKey, userId);
    sessionState.textContent = "Guest account ready";
    sendButton.disabled = false;
  } catch (error) {
    sessionState.textContent = "Could not create guest account. Reload to retry.";
    addMessage(error.message || "The service could not be reached.", "assistant", "error");
  }
}

checkService();
initializeGuestSession();
