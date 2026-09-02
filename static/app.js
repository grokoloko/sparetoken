const log = document.getElementById("log");
const form = document.getElementById("form");
const input = document.getElementById("input");
const send = document.getElementById("send");
const hint = document.getElementById("hint");
const payBtn = document.getElementById("pay");
const payNote = document.getElementById("pay-note");
const blockWrap = document.getElementById("block-wrap");
const blockCode = document.getElementById("block-code");
const claimForm = document.getElementById("claim");
const claimCode = document.getElementById("claim-code");
const claimStatus = document.getElementById("claim-status");
const clock = document.getElementById("hero-clock") || document.querySelector(".clock");
const heroUsed = document.getElementById("hero-used");
const usedRow = document.getElementById("used-row");
const clockWrap = document.getElementById("clock-wrap");
const clockBtn = document.getElementById("clock-btn");
const clockBtnTitle = document.getElementById("clock-btn-title");
const clockMenu = document.getElementById("clock-menu");
const clockRows = document.getElementById("clock-rows");
const clockFoot = document.getElementById("clock-foot");
const btnNew = document.getElementById("btn-new");
const btnCopy = document.getElementById("btn-copy");
const resumeSheet = document.getElementById("resume-sheet");
const resumeName = document.getElementById("resume-name");
const resumeMeta = document.getElementById("resume-meta");
const resumeWebCmd = document.getElementById("resume-web-cmd");
const resumeSshCmd = document.getElementById("resume-ssh-cmd");
const resumeBack = document.getElementById("resume-back");
const resumeCopyWeb = document.getElementById("resume-copy-web");
const resumeOpenWeb = document.getElementById("resume-open-web");
const resumeCopySsh = document.getElementById("resume-copy-ssh");
const payModal = document.getElementById("pay-modal");
let paidTimer = 0;
let lastSession = null;
let menuOpen = false;
let resumeView = null;

function addBubble(role, text) {
  const el = document.createElement("div");
  el.className = `bubble ${role}`;
  el.textContent = text;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  return el;
}

function resetLog() {
  log.innerHTML = "";
  addBubble("sys", "Comece por qualquer coisa. Uma ideia, um texto, um problema.");
}

function renderMessages(messages) {
  log.innerHTML = "";
  if (!messages || !messages.length) {
    addBubble("sys", "Comece por qualquer coisa. Uma ideia, um texto, um problema.");
    return;
  }
  messages.forEach((item) => {
    const role = item.role === "assistant" ? "ai" : item.role === "user" ? "you" : "sys";
    addBubble(role, item.body || "");
  });
}

function setResumeUrl(code, id) {
  if (!code || !id) return;
  const next = new URL(location.href);
  next.searchParams.set("code", code);
  next.searchParams.set("resume", id);
  history.replaceState({}, "", `${next.pathname}${next.search}${next.hash}`);
}

function resumeHref(data) {
  return (data && data.return_url) || (data && data.block_code
    ? `https://wdtsot.shop/?code=${data.block_code}`
    : location.href);
}

function webResumeUrl(code, id) {
  return `https://wdtsot.shop/?code=${encodeURIComponent(code)}&resume=${encodeURIComponent(id)}`;
}

function sshResumeCmd(id) {
  return `ssh -t agent-guest@wdtsot.shop resume ${id}`;
}

async function copyLabel(btn, text, label) {
  if (!btn || !text) return;
  try {
    await navigator.clipboard.writeText(text);
    btn.textContent = "copiado";
    setTimeout(() => {
      btn.textContent = label;
    }, 1400);
  } catch (_) {
    btn.textContent = "selecione e copie";
  }
}

function closeResume() {
  resumeView = null;
  if (resumeSheet) resumeSheet.hidden = true;
}

function openResume(chat, title, code) {
  if (!resumeSheet || !chat || !code) return;
  resumeView = { id: chat.id, title, code, used: chat.used_seconds };
  if (resumeName) resumeName.textContent = title;
  if (resumeMeta) {
    resumeMeta.textContent = `${minutesLabel(chat.used_seconds)} nesta linha · ${code}`;
  }
  if (resumeWebCmd) resumeWebCmd.textContent = webResumeUrl(code, chat.id);
  if (resumeSshCmd) resumeSshCmd.textContent = sshResumeCmd(chat.id);
  resumeSheet.hidden = false;
  setMenu(false);
}

function setRemaining(n) {
  if (typeof n !== "number") return;
  if (hint.dataset.paid === "1") return;
  hint.textContent =
    n <= 0
      ? "você usou as 50 mensagens desta experiência. pague R$5 para 5h."
      : n === 1
        ? "1 mensagem para experimentar"
        : `${n} mensagens para experimentar`;
}

function showInvite(code, urlFromApi) {
  const wrap = document.getElementById("invite-wrap");
  const urlEl = document.getElementById("invite-url");
  const copyBtn = document.getElementById("invite-copy");
  if (!wrap || !urlEl) return;
  let url = urlFromApi || "";
  if (!url) {
    const clean = (code || "").trim();
    if (/^wdtsot-[A-Za-z0-9]{3,16}$/.test(clean)) {
      url = `https://sparetoken.shop/?code=${encodeURIComponent(clean)}`;
    }
  }
  if (!url) {
    wrap.hidden = true;
    return;
  }
  urlEl.textContent = url;
  wrap.hidden = false;
  if (copyBtn) copyBtn.dataset.copy = url;
}

function showBlock(code, inviteFromApi) {
  if (!code || !blockWrap || !blockCode) return;
  blockCode.textContent = code;
  blockWrap.hidden = false;
  if (claimCode && !claimCode.value) claimCode.value = code;
  showInvite(code, inviteFromApi);
}

function isGenericLabel(label) {
  const s = (label || "").trim();
  return !s || s === "web" || s === "ssh" || /^session-\d{8}-\d{6}-/i.test(s) || /^web-\d+$/i.test(s);
}

function titlesFor(chats) {
  const chrono = [...(chats || [])].reverse();
  const map = {};
  (chats || []).forEach((chat) => {
    if (!isGenericLabel(chat.label)) {
      map[chat.id] = chat.label;
      return;
    }
    map[chat.id] = `Chat ${chrono.findIndex((c) => c.id === chat.id) + 1}`;
  });
  return map;
}

function minutesLabel(seconds) {
  const n = Math.max(0, Math.floor((seconds || 0) / 60));
  return n === 1 ? "1 min" : `${n} min`;
}

function setMenu(open) {
  menuOpen = !!open;
  if (clockMenu) clockMenu.hidden = !menuOpen;
  if (clockBtn) clockBtn.setAttribute("aria-expanded", menuOpen ? "true" : "false");
}

function renderClock(data) {
  const paid = !!(data && (data.paid || data.exhausted) && data.block_code);
  if (clockWrap) clockWrap.hidden = !paid;
  if (!paid) {
    setMenu(false);
    closeResume();
    return;
  }
  const chats = data.chats || [];
  const names = titlesFor(chats);
  const activeId = data.active_chat_id;
  const active = chats.find((c) => c.id === activeId) || chats[0];
  if (clockBtnTitle) clockBtnTitle.textContent = active ? names[active.id] : "Chat 1";
  if (clockRows) {
    clockRows.innerHTML = "";
    chats.forEach((chat) => {
      const li = document.createElement("li");
      if (chat.id === activeId) li.className = "active";
      if (chat.id === activeId) {
        const field = document.createElement("input");
        field.className = "rename";
        field.value = names[chat.id];
        field.maxLength = 80;
        field.setAttribute("aria-label", "Nome deste chat");
        field.addEventListener("click", (event) => event.stopPropagation());
        field.addEventListener("keydown", (event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            field.blur();
          }
        });
        field.addEventListener("blur", () => {
          const next = field.value.trim();
          if (!next || next === names[chat.id]) {
            field.value = names[chat.id];
            return;
          }
          clockAction("rename", { id: chat.id, title: next });
        });
        li.appendChild(field);
      } else {
        const pick = document.createElement("button");
        pick.type = "button";
        pick.textContent = names[chat.id];
        pick.addEventListener("click", () => {
          clockAction("use", { id: chat.id });
        });
        li.appendChild(pick);
      }
      const mins = document.createElement("span");
      mins.className = "mins";
      mins.textContent = minutesLabel(chat.used_seconds);
      li.appendChild(mins);
      const go = document.createElement("button");
      go.type = "button";
      go.className = "go";
      go.textContent = "↗";
      go.setAttribute("aria-label", `Resume de ${names[chat.id]}`);
      go.title = "web e ssh";
      go.addEventListener("click", (event) => {
        event.stopPropagation();
        openResume(chat, names[chat.id], data.block_code);
      });
      li.appendChild(go);
      clockRows.appendChild(li);
    });
  }
  if (clockFoot) {
    const n = chats.length;
    const noun = n === 1 ? "chat" : "chats";
    clockFoot.textContent = `${n} ${noun} neste código · ${minutesLabel(data.used_seconds)} / 5h`;
  }
}

function applySession(data) {
  if (!data) return;
  lastSession = data;
  if (data.exhausted) {
    hint.dataset.paid = "1";
    hint.className = "hint exhausted";
    hint.textContent = "as 5h deste bloco acabaram. pague R$5 para outro.";
    if (clock) clock.textContent = "00:00:00";
    if (send) send.disabled = true;
    if (input) {
      input.disabled = true;
      input.placeholder = "bloco esgotado — pague R$5 para continuar";
    }
    renderClock(data);
    stopPaidLoop();
    if (payNote) payNote.textContent = "saldo zero. o mesmo Pix de R$5 abre outro bloco de 5h.";
    if (data.block_code) showBlock(data.block_code, data.invite_url);
    return;
  }
  if (data.ok === false) return;
  if (data.paid) {
    hint.dataset.paid = "1";
    hint.className = data.warn ? "hint warn" : "hint";
    const busy = data.processing ? " · GROK processando" : "";
    hint.textContent = data.warn
      ? `faltam ${data.remaining_clock} de processamento. o bloco vai encerrar.`
      : `GROK 4.6 High Fast · ${data.remaining_clock} restantes${busy}`;
    if (clock && data.remaining_clock) clock.textContent = data.remaining_clock;
    if (heroUsed && data.used_clock) heroUsed.textContent = data.used_clock;
    if (usedRow) usedRow.hidden = false;
    renderClock(data);
    if (send) send.disabled = false;
    if (input) {
      input.disabled = false;
      input.placeholder = "Pergunte ou peça o que quiser...";
    }
    if (payNote) {
      payNote.textContent = "bloco liberado. só desconta enquanto o GROK responde. o código retoma web e SSH.";
    }
    startPaidLoop();
  } else if (data.remaining_messages != null) {
    hint.dataset.paid = "";
    hint.className = "hint";
    renderClock(data);
    setRemaining(data.remaining_messages);
  }
  if (data.block_code) showBlock(data.block_code, data.invite_url);
}

async function clockAction(action, extra) {
  try {
    const res = await fetch("/api/clock", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, ...(extra || {}) }),
    });
    const data = await res.json();
    applySession(data);
    if (!res.ok && data.error) setClaimStatus(data.error, "err");
    return data;
  } catch (_) {
    return null;
  }
}

function stopPaidLoop() {
  if (paidTimer) {
    clearInterval(paidTimer);
    paidTimer = 0;
  }
}

function startPaidLoop() {
  if (paidTimer) return;
  paidTimer = setInterval(() => {
    if (document.visibilityState === "visible") clockAction("tick");
  }, 15000);
}

function setClaimStatus(text, kind) {
  if (!claimStatus) return;
  claimStatus.textContent = text;
  claimStatus.className = `claim-status ${kind || ""}`.trim();
}

function blockCodeFromPage() {
  const params = new URLSearchParams(location.search);
  return (params.get("code") || "").trim();
}

async function loadSession() {
  try {
    const params = new URLSearchParams(location.search);
    const code = (params.get("code") || "").trim();
    const resume = (params.get("resume") || "").trim();
    const qs = new URLSearchParams();
    if (code) qs.set("code", code);
    if (resume) qs.set("resume", resume);
    const url = qs.toString() ? `/api/session?${qs}` : "/api/session";
    const res = await fetch(url, { credentials: "same-origin" });
    const data = await res.json();
    applySession(data);
    return data;
  } catch (_) {
    return null;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text || send.disabled) return;
  input.value = "";
  resize();
  addBubble("you", text);
  const ai = addBubble("ai", "");
  send.disabled = true;
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    if (!res.ok || !res.body) {
      let err = "não foi agora.";
      try {
        const data = await res.json();
        err = data.error || err;
        if (data.exhausted || data.remaining_clock) applySession(data);
        else if (data.remaining_messages != null) setRemaining(data.remaining_messages);
      } catch (_) {}
      ai.textContent = err;
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";
      for (const part of parts) {
        const line = part.split("\n").find((l) => l.startsWith("data:"));
        if (!line) continue;
        let payload;
        try {
          payload = JSON.parse(line.slice(5).trim());
        } catch (_) {
          continue;
        }
        if (payload.remaining_clock || payload.exhausted) applySession(payload);
        else if (payload.remaining_messages != null) setRemaining(payload.remaining_messages);
        if (payload.text) ai.textContent += payload.text;
        if (payload.error) ai.textContent = payload.error;
        log.scrollTop = log.scrollHeight;
      }
    }
    if (!ai.textContent) ai.textContent = "silêncio do outro lado. tente de novo.";
  } catch (_) {
    ai.textContent = "a rede falhou no meio do caminho.";
  } finally {
    send.disabled = false;
    input.focus();
  }
});

function resize() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 140) + "px";
}
input.addEventListener("input", resize);
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

const TRACK_KEYS = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "code"];

function captureLanding() {
  const params = new URLSearchParams(location.search);
  let bag = {};
  try {
    bag = JSON.parse(localStorage.getItem("st_utm") || "{}") || {};
  } catch (_) {
    bag = {};
  }
  TRACK_KEYS.forEach((key) => {
    const val = params.get(key);
    if (val) bag[key] = String(val).slice(0, 64);
  });
  bag.landed_at = Date.now();
  try {
    localStorage.setItem("st_utm", JSON.stringify(bag));
  } catch (_) {}
  return bag;
}

function ping(event) {
  const bag = (() => {
    try {
      return JSON.parse(localStorage.getItem("st_utm") || "{}") || {};
    } catch (_) {
      return {};
    }
  })();
  const body = { event };
  TRACK_KEYS.forEach((key) => {
    if (bag[key]) body[key] = bag[key];
  });
  fetch("/api/track", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    keepalive: true,
  }).catch(() => {});
}

async function openCheckout() {
  if (!payBtn) return;
  payBtn.disabled = true;
  ping("pay_click");
  try {
    const res = await fetch("/api/pay", {
      method: "POST",
      credentials: "same-origin",
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      setClaimStatus(data.error || "não abri o pagamento agora.", "err");
      return;
    }
    showBlock(data.block_code);
    setClaimStatus("pague o Pix, espere confirmar, volte e clique em Já paguei.", "");
    if (data.pay_url) window.open(data.pay_url, "_blank", "noopener");
  } catch (_) {
    setClaimStatus("a rede falhou. tente de novo.", "err");
  } finally {
    payBtn.disabled = false;
  }
}

if (payBtn) {
  payBtn.addEventListener("click", () => {
    if (payModal && typeof payModal.showModal === "function") payModal.showModal();
    else openCheckout();
  });
}
if (payModal) {
  payModal.addEventListener("close", () => {
    if (payModal.returnValue === "ok") openCheckout();
  });
}

if (claimForm) {
  claimForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    setClaimStatus("conferindo…", "");
    try {
      const res = await fetch("/api/claim", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: claimCode ? claimCode.value.trim() : "",
        }),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        setClaimStatus(data.error || "não liberou.", "err");
        return;
      }
      applySession(data);
      if (data.paid) {
        ping("claim_ok");
        startPaidLoop();
      }
      setClaimStatus(
        data.paid
          ? `sessão liberada. ${data.remaining_clock} neste bloco.`
          : "ainda sem saldo neste bloco.",
        data.paid ? "ok" : "err",
      );
    } catch (_) {
      setClaimStatus("a rede falhou. tente de novo.", "err");
    }
  });
}

document.querySelectorAll("[data-copy]").forEach((btn) => {
  btn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(btn.dataset.copy);
      btn.textContent = "copiado";
      setTimeout(() => {
        btn.textContent = "copiar";
      }, 1400);
    } catch (_) {
      btn.textContent = "selecione e copie";
    }
  });
});

if (clockBtn) {
  clockBtn.addEventListener("click", (event) => {
    event.stopPropagation();
    setMenu(!menuOpen);
  });
}
if (btnNew) {
  btnNew.addEventListener("click", async () => {
    const data = await clockAction("new");
    if (data && data.ok) resetLog();
    setMenu(false);
  });
}
if (btnCopy) {
  btnCopy.addEventListener("click", () => copyLabel(btnCopy, resumeHref(lastSession), "Copiar link"));
}
if (resumeBack) {
  resumeBack.addEventListener("click", closeResume);
}
if (resumeCopyWeb) {
  resumeCopyWeb.addEventListener("click", () => {
    copyLabel(resumeCopyWeb, resumeWebCmd ? resumeWebCmd.textContent : "", "copiar");
  });
}
if (resumeCopySsh) {
  resumeCopySsh.addEventListener("click", () => {
    copyLabel(resumeCopySsh, resumeSshCmd ? resumeSshCmd.textContent : "", "copiar");
  });
}
if (resumeOpenWeb) {
  resumeOpenWeb.addEventListener("click", async () => {
    if (!resumeView) return;
    const id = resumeView.id;
    closeResume();
    const data = await clockAction("use", { id });
    if (data && data.ok) resetLog();
  });
}
if (resumeSheet) {
  resumeSheet.addEventListener("click", (event) => {
    if (event.target === resumeSheet) closeResume();
  });
}

document.addEventListener("click", (event) => {
  if (!menuOpen || !clockWrap) return;
  if (clockWrap.contains(event.target)) return;
  setMenu(false);
});

document.addEventListener("visibilitychange", () => {
  if (hint.dataset.paid !== "1") return;
  if (document.visibilityState === "visible") clockAction("tick");
});

(function rotateHero() {
  const el = document.getElementById("hero-line-text");
  if (!el) return;
  let lines = [];
  try {
    lines = JSON.parse(el.getAttribute("data-lines") || "[]");
  } catch (_) {
    lines = [];
  }
  if (lines.length < 2) return;
  let i = 0;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  setInterval(() => {
    i = (i + 1) % lines.length;
    if (reduced) {
      el.textContent = lines[i];
      return;
    }
    el.classList.add("is-out");
    setTimeout(() => {
      el.textContent = lines[i];
      el.classList.remove("is-out");
    }, 1100);
  }, 9000);
})();

const params = new URLSearchParams(location.search);

const BRIEFS = {
  mkt: "Escreve um post curto (máx 280) para spare tokens: R$5 / 5h / GROK 4.6 High Fast, Pix de um passo, login = código do bloco. Sem nome de pessoa. Sem segundo preço. Sem pedir chave, cookie, .env ou e-mail. Link: https://sparetoken.shop/?utm_source=shop&utm_medium=web&utm_campaign=agent&utm_content=mkt",
  copy: "Escreve um parágrafo de prateleira para quem tem token de IA sobrando e quem precisa de uma hora de modelo. Tom de caderno, não pitch. Sem assinatura. Sem a palavra owner. Sem pedir e-mail ou WhatsApp. O caixa continua R$5 / 5h.",
  viral: "Dá 3 ganchos de uma linha para indicar um amigo com o mesmo ?code= do bloco. Sem WhatsApp. Sem e-mail. Sem pedir chave. O convite é o código, não um cadastro.",
};

function briefText(key) {
  let text = BRIEFS[key] || "";
  const code = ((claimCode && claimCode.value) || params.get("code") || "").trim();
  if (text && /^wdtsot-[A-Za-z0-9]{3,16}$/.test(code)) {
    text += ` Convite: https://sparetoken.shop/?code=${encodeURIComponent(code)}`;
  }
  return text;
}

function fillBrief(key) {
  const text = briefText(key);
  if (!text || !input) return;
  input.value = text;
  resize();
  input.focus();
  location.hash = "chat";
}

document.querySelectorAll("[data-brief]").forEach((el) => {
  const run = () => fillBrief(el.dataset.brief);
  el.addEventListener("click", run);
  el.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      run();
    }
  });
});

fetch("/api/track/summary", { credentials: "same-origin" })
  .then((res) => res.json())
  .then((data) => {
    if (!data || !data.ok) return;
    const box = document.getElementById("pulso-tally");
    if (!box) return;
    box.querySelectorAll("[data-tally]").forEach((node) => {
      const key = node.getAttribute("data-tally");
      if (key && Object.prototype.hasOwnProperty.call(data, key)) {
        node.textContent = String(data[key] || 0);
      }
    });
    box.hidden = false;
  })
  .catch(() => {});

captureLanding();
if (params.get("code") && claimCode && !claimCode.value) {
  claimCode.value = params.get("code");
}
ping("visit");

loadSession().then(() => {
  if (hint.dataset.paid === "1") startPaidLoop();
});
