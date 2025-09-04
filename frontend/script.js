let sessionId = null;
const chatEl = document.getElementById("chat");
const form = document.getElementById("form");
const input = document.getElementById("input");

function addMessage(role, text) {
  const wrap = document.createElement("div");
  wrap.className = "msg " + (role === "user" ? "user" : "bot");
  const b = document.createElement("div");
  b.className = "bubble";
  b.innerText = text;
  wrap.appendChild(b);
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function addChoices(choices) {
  if (!choices || !choices.length) return;
  const container = document.createElement("div");
  container.className = "msg bot";
  const b = document.createElement("div");
  b.className = "bubble";
  choices.forEach(c => {
    const chip = document.createElement("span");
    chip.className = "choice";
    chip.innerText = c;
    chip.onclick = () => {
      input.value = c;
      form.dispatchEvent(new Event("submit"));
    };
    b.appendChild(chip);
  });
  container.appendChild(b);
  chatEl.appendChild(container);
  chatEl.scrollTop = chatEl.scrollHeight;
}

async function send(message) {
  addMessage("user", message);
  input.value = "";
  const res = await fetch("/chat", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ message, session_id: sessionId })
  });
  const data = await res.json();
  sessionId = data.session_id || sessionId;
  addMessage("bot", data.reply || "(sense resposta)");
  if (data.choices) addChoices(data.choices);
  if (data.checkout_url) {
    window.open(data.checkout_url, "_blank"); // Stripe o mock
  }
  chatEl.scrollTop = chatEl.scrollHeight;
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const msg = input.value.trim();
  if (!msg) return;
  send(msg);
});

// Seed a hello
addMessage("bot", "Hola! En què t'ajudo a comprar avui? Ex: «Vull eliminar una colònia de formigues».");