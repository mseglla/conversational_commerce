let sessionId = null;
const chatEl = document.getElementById("chat");
const form = document.getElementById("form");
const input = document.getElementById("input");
const submitBtn = form.querySelector('button');

function addMessage(role, text) {
  const wrap = document.createElement("div");
  wrap.className = "msg " + (role === "user" ? "user" : "bot");

  const b = document.createElement("div");
  b.className = "bubble";

  // Usuari: text literal (evitem HTML injectat)
  // Bot: permet HTML (<b>, <br>, etc.)
  if (role === "user") {
    b.innerText = text ?? "";
  } else {
    b.innerHTML = text ?? "";
  }

  wrap.appendChild(b);
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
  return wrap;
}

let typingEl = null;
function showTyping() {
  if (typingEl) return;
  typingEl = document.createElement("div");
  typingEl.className = "msg bot";
  const b = document.createElement("div");
  b.className = "bubble";
  b.innerText = "…";
  typingEl.appendChild(b);
  chatEl.appendChild(typingEl);
  chatEl.scrollTop = chatEl.scrollHeight;
}
function hideTyping() {
  if (typingEl) {
    typingEl.remove();
    typingEl = null;
  }
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
      // envia directament la tria (sense omplir l'input)
      send(c);
    };
    b.appendChild(chip);
  });

  container.appendChild(b);
  chatEl.appendChild(container);
  chatEl.scrollTop = chatEl.scrollHeight;
}

async function send(message) {
  // No enviïs buit o si ja estem esperant resposta
  if (!message || submitBtn.disabled) return;

  addMessage("user", message);
  input.value = "";

  // bloqueja el formulari i mostra "escrivint"
  submitBtn.disabled = true;
  input.disabled = true;
  showTyping();

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ message, session_id: sessionId })
    });

    let data;
    try {
      data = await res.json();
    } catch {
      throw new Error("Resposta no vàlida del servidor");
    }

    hideTyping();
    sessionId = data.session_id || sessionId;

    addMessage("bot", data.reply || "(sense resposta)");
    if (data.choices) addChoices(data.choices);

    if (data.checkout_url) {
      // Obre Stripe o el pagament simulat
      window.open(data.checkout_url, "_blank");
    }
  } catch (err) {
    hideTyping();
    addMessage("bot", "⚠️ <b>Error de connexió</b>. Torna-ho a provar.");
    console.error(err);
  } finally {
    submitBtn.disabled = false;
    input.disabled = false;
    input.focus();
    chatEl.scrollTop = chatEl.scrollHeight;
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const msg = input.value.trim();
  if (!msg) return;
  send(msg);
});

// Missatge inicial
addMessage("bot", "Hola! En què t'ajudo a comprar avui? Ex: «Vull eliminar una colònia de formigues»."); 
