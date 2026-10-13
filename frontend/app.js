const messageInput = document.querySelector("#message-input");
const chatForm = document.querySelector("#chat-form");
const sendButton = document.querySelector("#send-button");
const newChatButton = document.querySelector("#new-chat");
const messages = document.querySelector("#messages");
const modeTitle = document.querySelector("#mode-title");
const shopperSession = document.querySelector("#shopper-session");
const shopperSessionState = document.querySelector("#shopper-session-state");
const shopkeeperLogin = document.querySelector("#shopkeeper-login");
const shopkeeperIdInput = document.querySelector("#shopkeeper-id");
const shopkeeperConnect = document.querySelector("#shopkeeper-connect");
const shopkeeperSession = document.querySelector("#shopkeeper-session");
const shopkeeperChange = document.querySelector("#shopkeeper-change");
const shopkeeperSessionState = document.querySelector("#shopkeeper-session-state");
const shopkeeperReadyState = document.querySelector("#shopkeeper-ready-state");
const serviceStatus = document.querySelector("#service-status");
const serviceStatusText = document.querySelector("#service-status-text");
const roleTabs = document.querySelectorAll("[data-role].role-tab");

const userStorageKeys = {
  shopper: "mall-concierge-guest-user-id",
  shopkeeper: "mall-concierge-shopkeeper-user-id",
};
let activeRole = "shopper";
let userId = "";
let threadId = "";
sendButton.disabled = true;

function threadStorageKey(role = activeRole, accountId = userId) {
  return `mall-concierge-thread-${role}-${accountId}`;
}

function transcriptStorageKey(role = activeRole, accountId = userId) {
  return `mall-concierge-messages-${role}-${accountId}`;
}

function loadTranscript(role = activeRole, accountId = userId) {
  if (!accountId) return [];
  try {
    const transcript = JSON.parse(
      sessionStorage.getItem(transcriptStorageKey(role, accountId)) || "[]",
    );
    return Array.isArray(transcript)
      ? transcript.filter((message) => typeof message.text === "string")
      : [];
  } catch {
    return [];
  }
}

function saveTranscriptMessage(text, role, extraClass = "") {
  if (!userId || extraClass === "typing") return;
  const transcript = loadTranscript();
  transcript.push({ text, role, extraClass });
  sessionStorage.setItem(
    transcriptStorageKey(),
    JSON.stringify(transcript.slice(-100)),
  );
}

async function readApiResponse(response) {
  const body = await response.text();
  if (!body) return {};
  try {
    return JSON.parse(body);
  } catch {
    return { detail: body };
  }
}

function appendMessage(text, role, extraClass = "") {
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

function addMessage(text, role, extraClass = "") {
  const row = appendMessage(text, role, extraClass);
  saveTranscriptMessage(text, role, extraClass);
  return row;
}

function resetMessages() {
  messages.replaceChildren();
  const welcome = document.createElement("div");
  const heading = document.createElement("h2");
  const description = document.createElement("p");
  welcome.className = "welcome-message";
  welcome.innerHTML = '<span class="welcome-mark"><i class="bi bi-stars" aria-hidden="true"></i></span><div class="welcome-copy"></div>';
  heading.textContent = activeRole === "shopper" ? "What are you looking for?" : "What needs your attention?";
  description.textContent = activeRole === "shopper"
    ? "Find products, place orders, or check a purchase."
    : "Review sales, restock products, or update an order.";
  welcome.querySelector(".welcome-copy").append(heading, description);
  messages.append(welcome);
}

function restoreMessages() {
  resetMessages();
  loadTranscript().forEach(({ text, role, extraClass }) => {
    appendMessage(text, role, extraClass);
  });
}

function startNewChat() {
  if (userId) {
    sessionStorage.removeItem(threadStorageKey());
    sessionStorage.removeItem(transcriptStorageKey());
  }
  threadId = "";
  restoreMessages();
  messageInput.focus();
}

function showRole(role) {
  activeRole = role;
  userId = sessionStorage.getItem(userStorageKeys[role]) || "";
  threadId = userId ? sessionStorage.getItem(threadStorageKey(role, userId)) || "" : "";
  const isShopper = role === "shopper";

  roleTabs.forEach((tab) => {
    const isActive = tab.dataset.role === role;
    tab.classList.toggle("active", isActive);
    tab.setAttribute("aria-selected", String(isActive));
  });
  modeTitle.textContent = isShopper ? "Shop" : "Shopkeeper desk";
  shopperSession.hidden = !isShopper;
  shopkeeperLogin.hidden = isShopper || Boolean(userId);
  shopkeeperSession.hidden = isShopper || !userId;
  shopkeeperSessionState.textContent = userId
    ? "Use sales, stock, and order tools"
    : "Use your existing shopkeeper account ID.";
  if (userId) shopkeeperReadyState.textContent = `Connected as ${userId}`;
  sendButton.disabled = !userId;
  document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.hidden = button.dataset.role !== role;
  });
  restoreMessages();

  if (isShopper) {
    shopperSessionState.textContent = userId ? "Guest account ready" : "Preparing your account...";
    initializeShopperSession();
  } else if (!userId) {
    shopkeeperSessionState.textContent = "Use your existing vendor account ID.";
  }
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

async function initializeShopperSession() {
  if (userId || activeRole !== "shopper") return;
  try {
    const response = await fetch("/api/v1/sessions", { method: "POST" });
    const data = await readApiResponse(response);
    if (!response.ok) throw new Error(data.detail || "Guest account could not be created.");
    sessionStorage.setItem(userStorageKeys.shopper, data.user_id);
    if (activeRole !== "shopper") return;
    userId = data.user_id;
    shopperSessionState.textContent = "Guest account ready";
    sendButton.disabled = false;
  } catch (error) {
    if (activeRole !== "shopper") return;
    shopperSessionState.textContent = "Could not create your guest account.";
    addMessage(error.message || "The service could not be reached.", "assistant", "error");
  }
}

roleTabs.forEach((tab) => {
  tab.addEventListener("click", () => showRole(tab.dataset.role));
});

shopkeeperChange.addEventListener("click", () => {
  if (userId) {
    sessionStorage.removeItem(userStorageKeys.shopkeeper);
  }
  shopkeeperIdInput.value = userId;
  userId = "";
  threadId = "";
  shopkeeperSession.hidden = true;
  shopkeeperLogin.hidden = false;
  shopkeeperSessionState.textContent = "Enter a different shopkeeper account ID.";
  sendButton.disabled = true;
  resetMessages();
  shopkeeperIdInput.focus();
});

shopkeeperLogin.addEventListener("submit", async (event) => {
  event.preventDefault();
  const requestedUserId = shopkeeperIdInput.value.trim();
  if (!requestedUserId || shopkeeperConnect.disabled) return;

  shopkeeperConnect.disabled = true;
  shopkeeperSessionState.textContent = "Checking shopkeeper account...";
  try {
    const response = await fetch("/api/v1/sessions/shopkeeper", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: requestedUserId }),
    });
    const data = await readApiResponse(response);
    if (!response.ok) throw new Error(data.detail || "Shopkeeper account could not be verified.");

    userId = data.user_id;
    sessionStorage.setItem(userStorageKeys.shopkeeper, userId);
    threadId = sessionStorage.getItem(threadStorageKey("shopkeeper", userId)) || "";
    shopkeeperLogin.hidden = true;
    shopkeeperSession.hidden = false;
    shopkeeperReadyState.textContent = `Connected as ${userId}`;
    sendButton.disabled = false;
    restoreMessages();
    messageInput.focus();
  } catch (error) {
    shopkeeperSessionState.textContent = error.message || "The service could not be reached.";
  } finally {
    shopkeeperConnect.disabled = false;
  }
});

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
    const data = await readApiResponse(response);
    if (!response.ok) {
      const detail = typeof data.detail === "string" ? data.detail : "The message could not be sent.";
      throw new Error(detail);
    }

    threadId = data.thread_id;
    sessionStorage.setItem(threadStorageKey(), threadId);
    pendingMessage.remove();
    addMessage(data.response, "assistant");
  } catch (error) {
    pendingMessage.remove();
    addMessage(error.message || "The service could not be reached.", "assistant", "error");
  } finally {
    sendButton.disabled = !userId;
    sendButton.innerHTML = '<i class="bi bi-arrow-up" aria-hidden="true"></i>';
    messageInput.focus();
  }
});

checkService();
showRole("shopper");
