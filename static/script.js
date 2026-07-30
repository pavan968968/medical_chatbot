const chatLog = document.getElementById("chatLog");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const quickActions = document.getElementById("quickActions");
const disclaimer = document.getElementById("disclaimer");

function appendMessage(role, text, severity = "info") {
  const bubble = document.createElement("div");
  bubble.className = `message ${role}${severity === "emergency" ? " emergency" : ""}`;
  bubble.textContent = text;

  const meta = document.createElement("span");
  meta.className = "meta";
  meta.textContent = role === "user" ? "You" : "Medical chatbot";
  bubble.appendChild(meta);

  chatLog.appendChild(bubble);
  chatLog.scrollTop = chatLog.scrollHeight;
  return bubble;
}

function renderSuggestions(suggestions = []) {
  quickActions.innerHTML = "";
  suggestions.slice(0, 4).forEach((suggestion) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = suggestion;
    button.addEventListener("click", () => {
      messageInput.value = suggestion;
      chatForm.requestSubmit();
    });
    quickActions.appendChild(button);
  });
}

async function sendMessage(message) {
  appendMessage("user", message);
  renderSuggestions([]);
  messageInput.value = "";
  messageInput.focus();

  const typingBubble = appendMessage("assistant", "Thinking about your symptoms...");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();

    appendMessage("assistant", data.reply, data.severity || "info");
    disclaimer.textContent = data.disclaimer || disclaimer.textContent;
    renderSuggestions(data.suggestions || []);
  } finally {
    typingBubble.remove();
  }
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) {
    return;
  }

  try {
    await sendMessage(message);
  } catch (error) {
    appendMessage(
      "system",
      "The chatbot could not reach the backend. Check that Flask is running, then try again."
    );
  }
});

appendMessage(
  "assistant",
  "Hello. Tell me your symptoms, how long they have been happening, and whether anything feels severe. If you have chest pain, trouble breathing, fainting, or severe bleeding, go to a hospital now.",
  "info"
);
renderSuggestions(["I have a fever", "I have chest pain", "I have stomach pain"]);