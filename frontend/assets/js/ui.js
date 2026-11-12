(function () {
  const api = window.nexusApi;
  const config = window.PRABHASHA_CONFIG || {};
  const fallback = config.ownerFallback || {};

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    }[character]));
  }

  function formatDate(value, options = {}) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return escapeHtml(value);
    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      ...options
    });
  }

  function initials(name) {
    return String(name || "PN")
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0].toUpperCase())
      .join("");
  }

  function truncate(value, length = 160) {
    const text = String(value || "");
    return text.length > length ? `${text.slice(0, length - 1).trimEnd()}…` : text;
  }

  function markdown(value) {
    const source = escapeHtml(value || "");
    const lines = source.split(/\r?\n/);
    let html = "";
    let inList = false;
    let inCode = false;
    const inline = (text) =>
      text
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
        .replace(/\*([^*]+)\*/g, "<em>$1</em>")
        .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

    lines.forEach((line) => {
      if (line.startsWith("```")) {
        inCode = !inCode;
        html += inCode ? "<pre><code>" : "</code></pre>";
        return;
      }
      if (inCode) {
        html += `${line}\n`;
        return;
      }
      const listMatch = line.match(/^\s*[-*]\s+(.+)/);
      if (listMatch) {
        if (!inList) {
          html += "<ul>";
          inList = true;
        }
        html += `<li>${inline(listMatch[1])}</li>`;
        return;
      }
      if (inList) {
        html += "</ul>";
        inList = false;
      }
      const heading = line.match(/^(#{1,4})\s+(.+)/);
      if (heading) {
        const level = Math.min(4, heading[1].length + 1);
        html += `<h${level}>${inline(heading[2])}</h${level}>`;
        return;
      }
      if (!line.trim()) {
        html += "";
        return;
      }
      html += `<p>${inline(line)}</p>`;
    });
    if (inList) html += "</ul>";
    if (inCode) html += "</code></pre>";
    return html;
  }

  let toastTimer = null;
  function toast(message, type = "info") {
    let container = $(".toast-stack");
    if (!container) {
      container = document.createElement("div");
      container.className = "toast-stack";
      document.body.appendChild(container);
    }
    const item = document.createElement("div");
    item.className = `toast toast-${type}`;
    item.innerHTML = `<span class="toast-dot"></span><span>${escapeHtml(message)}</span>`;
    container.appendChild(item);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => item.classList.add("toast-out"), 3600);
    setTimeout(() => item.remove(), 4200);
  }

  function errorState(container, message, retry) {
    if (!container) return;
    container.innerHTML = `<div class="state state-error"><strong>Unable to load this section</strong><p>${escapeHtml(message)}</p>${
      retry ? '<button class="btn btn-ghost" type="button" data-retry>Try again</button>' : ""
    }</div>`;
    if (retry) $("[data-retry]", container).addEventListener("click", retry);
  }

  function emptyState(title, message) {
    return `<div class="state state-empty"><div class="state-icon">◇</div><strong>${escapeHtml(title)}</strong><p>${escapeHtml(message)}</p></div>`;
  }

  function skeletonCards(count = 3) {
    return Array.from({ length: count })
      .map(
        () => `<div class="card skeleton-card"><div class="skeleton skeleton-line short"></div><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-block"></div></div>`
      )
      .join("");
  }

  function tagList(items, className = "tag") {
    return (items || []).map((item) => `<span class="${className}">${escapeHtml(item)}</span>`).join("");
  }

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("nexus_theme", theme);
    const button = $("[data-theme-toggle]");
    if (button) button.setAttribute("aria-label", theme === "light" ? "Switch to dark theme" : "Switch to light theme");
  }

  function initTheme() {
    const saved = localStorage.getItem("nexus_theme");
    const preferred = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
    applyTheme(saved || preferred);
  }

  function toggleTheme() {
    applyTheme(document.documentElement.dataset.theme === "light" ? "dark" : "light");
  }

  const navItems = [
    ["home", "index.html", "Home"],
    ["about", "about.html", "About"],
    ["projects", "projects.html", "Projects"],
    ["research", "research.html", "Research"],
    ["blog", "blog.html", "Writing"],
    ["certificates", "certificates.html", "Credentials"],
    ["contact", "contact.html", "Contact"]
  ];

  function renderChrome(profile) {
    const name = profile?.full_name || fallback.full_name;
    const title = profile?.professional_title || fallback.professional_title;
    const email = profile?.email || fallback.email;
    const github = profile?.github_url || fallback.github_url;
    const linkedin = profile?.linkedin_url || fallback.linkedin_url;
    const activePage = document.body.dataset.page || "home";

    const header = document.createElement("header");
    header.className = "site-header";
    header.innerHTML = `
      <div class="container nav-shell">
        <a class="brand" href="index.html" aria-label="Prabhasha Nexus home">
          <span class="brand-mark">PN</span>
          <span class="brand-text"><strong>Prabhasha</strong><small>Nexus</small></span>
        </a>
        <nav class="site-nav" id="site-nav" aria-label="Primary navigation">
          ${navItems.map(([key, href, label]) => `<a href="${href}" class="${key === activePage ? "active" : ""}">${label}</a>`).join("")}
        </nav>
        <div class="nav-actions">
          <button class="icon-btn" type="button" data-theme-toggle aria-label="Toggle theme">◐</button>
          <button class="btn btn-ghost btn-sm" type="button" data-resume>Download CV</button>
          <a class="btn btn-primary btn-sm" href="contact.html">Let's talk</a>
          <button class="menu-btn" type="button" aria-label="Open menu" aria-expanded="false">☰</button>
        </div>
      </div>`;
    document.body.prepend(header);

    const footer = document.createElement("footer");
    footer.className = "site-footer";
    footer.innerHTML = `
      <div class="container footer-grid">
        <div>
          <a class="brand" href="index.html"><span class="brand-mark">PN</span><span class="brand-text"><strong>Prabhasha</strong><small>Nexus</small></span></a>
          <p class="muted footer-blurb">${escapeHtml(truncate(profile?.summary || fallback.summary, 170))}</p>
        </div>
        <div>
          <h3>Explore</h3>
          ${navItems.slice(1).map(([, href, label]) => `<a href="${href}">${label}</a>`).join("")}
        </div>
        <div>
          <h3>Connect</h3>
          ${linkedin ? `<a href="${escapeHtml(linkedin)}" target="_blank" rel="noopener">LinkedIn ↗</a>` : ""}
          ${github ? `<a href="${escapeHtml(github)}" target="_blank" rel="noopener">GitHub ↗</a>` : ""}
          ${email ? `<a href="mailto:${escapeHtml(email)}">${escapeHtml(email)}</a>` : ""}
          <a href="contact.html">Contact form</a>
        </div>
      </div>
      <div class="container footer-bottom">
        <p>© <span data-year></span> ${escapeHtml(name)}. Built with a Flask API and a privacy-conscious analytics layer.</p>
        <p class="muted">${escapeHtml(title)}</p>
      </div>`;
    document.body.appendChild(footer);
    $("[data-year]").textContent = new Date().getFullYear();

    $("[data-theme-toggle]").addEventListener("click", toggleTheme);
    $("[data-resume]").addEventListener("click", downloadResume);
    const menu = $(".menu-btn");
    const nav = $("#site-nav");
    menu?.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      menu.setAttribute("aria-expanded", String(open));
      menu.textContent = open ? "✕" : "☰";
    });
    $$("#site-nav a").forEach((link) => link.addEventListener("click", () => nav.classList.remove("open")));

    document.dispatchEvent(new CustomEvent("chrome:ready", { detail: { profile } }));
  }

  async function downloadResume() {
    try {
      const result = await api.get("/resumes");
      const resumes = result.data || [];
      if (!resumes.length) {
        toast("No CV has been published yet. Please use the contact form.", "warning");
        return;
      }
      const resume = resumes.find((item) => item.is_default) || resumes[0];
      const response = await api.get(`/resumes/${resume.id}/download`);
      const url = response.data?.download_url;
      if (url) {
        trackEvent("cv_download", { content_type: "resume", content_id: resume.id, path: "/resume/download" });
        window.open(url, "_blank", "noopener");
      }
    } catch (error) {
      toast(error.message || "Unable to download CV", "error");
    }
  }

  function visitorId() {
    let id = localStorage.getItem("nexus_visitor");
    if (!id) {
      id = (crypto.randomUUID && crypto.randomUUID()) || `v-${Date.now()}-${Math.random().toString(16).slice(2)}`;
      localStorage.setItem("nexus_visitor", id);
    }
    return id;
  }

  function trackEvent(eventType, extra = {}) {
    api
      .post("/analytics/events", {
        event_type: eventType,
        path: extra.path || window.location.pathname + window.location.search,
        page_type: extra.page_type || document.body.dataset.page || "page",
        visitor_id: visitorId(),
        referrer: document.referrer || null,
        device: window.innerWidth < 720 ? "mobile" : window.innerWidth < 1100 ? "tablet" : "desktop",
        ...extra
      })
      .catch(() => {});
  }

  function initTracking() {
    trackEvent("page_view");
    document.addEventListener("click", (event) => {
      const link = event.target.closest('a[href*="github.com"]');
      if (link) trackEvent("github_click", { path: link.href });
    });
  }

  function initChat() {
    const launcher = document.createElement("button");
    launcher.className = "chat-launcher";
    launcher.type = "button";
    launcher.setAttribute("aria-label", "Open portfolio assistant");
    launcher.innerHTML = '<span class="chat-pulse"></span><span>Ask AI</span>';
    document.body.appendChild(launcher);

    const panel = document.createElement("section");
    panel.className = "chat-panel";
    panel.setAttribute("aria-live", "polite");
    panel.innerHTML = `
      <header class="chat-head">
        <div><strong>Portfolio Assistant</strong><small>Grounded in verified content</small></div>
        <button class="icon-btn" type="button" data-chat-close aria-label="Close chat">✕</button>
      </header>
      <div class="chat-messages" data-chat-messages>
        <div class="chat-bubble assistant">Hi! I can answer questions about Prabhasha's verified projects, skills, education and research. What would you like to know?</div>
      </div>
      <form class="chat-form" data-chat-form>
        <input name="message" placeholder="Ask about projects, skills, research…" autocomplete="off" maxlength="1000" required />
        <button class="btn btn-primary btn-sm" type="submit">Send</button>
      </form>
      <p class="chat-note">Answers use portfolio data only. No account required.</p>`;
    document.body.appendChild(panel);

    let sessionId = localStorage.getItem("nexus_chat_session");
    if (!sessionId) {
      sessionId = (crypto.randomUUID && crypto.randomUUID()) || `s-${Date.now()}`;
      localStorage.setItem("nexus_chat_session", sessionId);
    }
    const messages = $("[data-chat-messages]", panel);
    const form = $("[data-chat-form]", panel);
    const input = $("input", form);

    const toggle = (open) => {
      panel.classList.toggle("open", open);
      launcher.classList.toggle("hidden", open);
      if (open) input.focus();
    };
    launcher.addEventListener("click", () => toggle(true));
    $("[data-chat-close]", panel).addEventListener("click", () => toggle(false));

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const message = input.value.trim();
      if (!message) return;
      input.value = "";
      messages.insertAdjacentHTML("beforeend", `<div class="chat-bubble user">${escapeHtml(message)}</div>`);
      messages.insertAdjacentHTML("beforeend", `<div class="chat-bubble assistant typing" data-typing>Thinking…</div>`);
      messages.scrollTop = messages.scrollHeight;
      const button = $("button", form);
      button.disabled = true;
      try {
        const result = await api.post("/ai/chat", { message, session_id: sessionId });
        $("[data-typing]", messages)?.remove();
        const data = result.data;
        const sources = (data.sources || [])
          .slice(0, 4)
          .map((source) =>
            source.source && source.source.startsWith("knowledge:")
              ? `<span class="chat-source">${escapeHtml(source.title)}</span>`
              : `<a class="chat-source" href="${escapeHtml(source.source)}">${escapeHtml(source.title)}</a>`
          )
          .join("");
        messages.insertAdjacentHTML(
          "beforeend",
          `<div class="chat-bubble assistant">${escapeHtml(data.answer).replace(/\n/g, "<br>")}${sources ? `<div class="chat-sources">${sources}</div>` : ""}</div>`
        );
      } catch (error) {
        $("[data-typing]", messages)?.remove();
        messages.insertAdjacentHTML(
          "beforeend",
          `<div class="chat-bubble assistant error">${escapeHtml(error.message || "The assistant is unavailable right now.")}</div>`
        );
      } finally {
        button.disabled = false;
        messages.scrollTop = messages.scrollHeight;
      }
    });
  }

  async function initChrome() {
    initTheme();
    let profile = null;
    try {
      const result = await api.get("/profile");
      profile = result.data;
    } catch (_error) {
      profile = fallback;
    }
    renderChrome(profile);
    initChat();
    initTracking();
    return profile;
  }

  window.nexusUI = {
    $,
    $$,
    escapeHtml,
    formatDate,
    initials,
    truncate,
    markdown,
    toast,
    errorState,
    emptyState,
    skeletonCards,
    tagList,
    trackEvent,
    downloadResume,
    initChrome,
    initTheme,
    applyTheme
  };
})();
