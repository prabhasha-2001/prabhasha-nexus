(function () {
  "use strict";

  const ui = window.nexusUI;
  const rawApi = window.nexusApi;
  const api = {
    ...rawApi,
    get: (path, options) => rawApi.get(path, { auth: true, ...options }),
    post: (path, body, options) => rawApi.post(path, body, { auth: true, ...options }),
    put: (path, body, options) => rawApi.put(path, body, { auth: true, ...options }),
    del: (path, options) => rawApi.del(path, { auth: true, ...options })
  };
  const { $, $$, escapeHtml: esc, formatDate, initials, truncate, toast } = ui;

  const view = $("#view");
  const modalRoot = $("#modal-root");
  const baseOrigin = new URL(api.API_BASE, window.location.href).origin;
  const canWrite = () => currentUser && currentUser.role !== "viewer";
  const canAdmin = () => currentUser && currentUser.role === "admin";

  let currentUser = null;
  let activeRoute = "dashboard";

  const NAV = [
    {
      group: "Overview",
      items: [{ key: "dashboard", label: "Dashboard" }]
    },
    {
      group: "Content",
      items: [
        { key: "profile", label: "Profile" },
        { key: "projects", label: "Projects" },
        { key: "research", label: "Research" },
        { key: "blog", label: "Blog" },
        { key: "education", label: "Education" },
        { key: "experience", label: "Experience" },
        { key: "skills", label: "Skills" },
        { key: "skill-categories", label: "Skill groups" },
        { key: "certificates", label: "Certificates" },
        { key: "testimonials", label: "Testimonials" },
        { key: "achievements", label: "Achievements" },
        { key: "taxonomy", label: "Categories & tags" }
      ]
    },
    {
      group: "Inbox",
      items: [
        { key: "messages", label: "Messages" },
        { key: "newsletter", label: "Newsletter" }
      ]
    },
    {
      group: "Intelligence",
      items: [
        { key: "ai", label: "AI studio" },
        { key: "knowledge", label: "Knowledge base" },
        { key: "conversations", label: "Conversations" }
      ]
    },
    {
      group: "Growth",
      items: [
        { key: "analytics", label: "Analytics" },
        { key: "github", label: "GitHub" }
      ]
    },
    {
      group: "Operations",
      items: [
        { key: "media", label: "Media library" },
        { key: "resumes", label: "Resumes" },
        { key: "users", label: "Users" },
        { key: "automation", label: "Automation" },
        { key: "activity", label: "Activity logs" },
        { key: "settings", label: "Settings" },
        { key: "backups", label: "Backups" }
      ]
    }
  ];

  const routeMeta = {};
  NAV.forEach((group) => group.items.forEach((item) => (routeMeta[item.key] = { ...item, group: group.group })));

  /* ---------------------------------------------------------------- utils */
  function assetUrl(url) {
    if (!url) return "";
    if (/^https?:\/\//i.test(url) || url.startsWith("data:")) return url;
    return `${baseOrigin}${url.startsWith("/") ? "" : "/"}${url}`;
  }

  function fmtDateShort(value) {
    return value ? formatDate(value) : "—";
  }

  function badge(value, tone) {
    return `<span class="badge ${tone ? `badge-${tone}` : ""}">${esc(value)}</span>`;
  }

  function statusTone(status) {
    return (
      {
        published: "success",
        approved: "success",
        indexed: "success",
        completed: "success",
        confirmed: "success",
        replied: "success",
        draft: "warning",
        pending: "warning",
        processing: "info",
        new: "info",
        read: "muted",
        archived: "muted",
        rejected: "danger",
        failed: "danger",
        unsubscribed: "danger"
      }[status] || "muted"
    );
  }

  function statusBadge(status) {
    return status ? badge(status, statusTone(status)) : "—";
  }

  function boolBadge(value, labels = ["Yes", "No"], tone = "info") {
    return value ? badge(labels[0], tone) : badge(labels[1], "muted");
  }

  function bytes(value) {
    const size = Number(value || 0);
    if (size < 1024) return `${size} B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }

  function qs(params) {
    const search = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") search.set(key, value);
    });
    const text = search.toString();
    return text ? `?${text}` : "";
  }

  function loadingRows(columns) {
    return `<tr><td colspan="${columns + 1}"><div class="empty"><strong>Loading…</strong>Fetching records.</div></td></tr>`;
  }

  function emptyRow(columns, message) {
    return `<tr><td colspan="${columns + 1}"><div class="empty"><strong>Nothing here yet</strong>${esc(message || "Create the first record to get started.")}</div></td></tr>`;
  }

  function errorRow(columns, message) {
    return `<tr><td colspan="${columns + 1}"><div class="empty"><strong>Could not load data</strong>${esc(message)}</div></td></tr>`;
  }

  function hideAll() {
    $("#login-view").hidden = true;
    $("#app-view").hidden = true;
  }

  function showLogin() {
    hideAll();
    $("#login-view").hidden = false;
    $("#login-error").hidden = true;
    const form = $("#login-form");
    form.reset();
    $("#login-submit").disabled = false;
    form.querySelector("input[name='email']").focus();
  }

  async function showApp() {
    hideAll();
    $("#app-view").hidden = false;
    $("#user-name").textContent = currentUser.name || "Admin";
    $("#user-role").textContent = currentUser.role || "admin";
    $("#user-initials").textContent = initials(currentUser.name || "PN");
    renderNav();
    navigate();
  }

  function renderNav() {
    const nav = $("#sidebar-nav");
    nav.innerHTML = NAV.map(
      (group) => `
        <div class="nav-group">
          <div class="nav-group-title">${esc(group.group)}</div>
          ${group.items
            .map(
              (item) =>
                `<a class="nav-link" href="#/${item.key}" data-route="${item.key}"><span class="nav-dot"></span>${esc(item.label)}</a>`
            )
            .join("")}
        </div>`
    ).join("");
  }

  function currentRouteKey() {
    const raw = (window.location.hash || "").replace(/^#\/?/, "").split("?")[0].split("/")[0];
    return routeMeta[raw] ? raw : "dashboard";
  }

  function navigate() {
    activeRoute = currentRouteKey();
    view.onclick = null;
    $$(".nav-link").forEach((link) => link.classList.toggle("active", link.dataset.route === activeRoute));
    const meta = routeMeta[activeRoute] || routeMeta.dashboard;
    $("#page-title").textContent = meta.label;
    $("#page-subtitle").textContent = meta.group;
    $("#sidebar").classList.remove("open");
    $("#sidebar-scrim").classList.remove("open");
    const renderer = ROUTES[activeRoute] || ROUTES.dashboard;
    Promise.resolve(renderer()).catch((error) => {
      view.innerHTML = `<div class="empty"><strong>Something went wrong</strong>${esc(error.message || "Unable to render view")}</div>`;
    });
  }

  /* ---------------------------------------------------------------- modal */
  let modalResolve = null;

  function closeModal() {
    modalRoot.classList.remove("open");
    modalRoot.innerHTML = "";
    if (modalResolve) {
      modalResolve(false);
      modalResolve = null;
    }
  }

  function openModal({ title, body, submitLabel = "Save", wide = false, onSubmit, hideSubmit = false }) {
    modalRoot.innerHTML = `
      <div class="modal-backdrop" data-close></div>
      <div class="modal ${wide ? "wide" : ""}" role="dialog" aria-modal="true" aria-label="${esc(title)}">
        <div class="modal-head">
          <h2>${esc(title)}</h2>
          <button class="icon-btn" type="button" data-close aria-label="Close">✕</button>
        </div>
        <form id="modal-form" novalidate>
          <div class="modal-body">
            <div class="form-error" id="modal-error"></div>
            ${body}
          </div>
          <div class="modal-foot">
            <button class="btn btn-ghost btn-sm" type="button" data-close>Cancel</button>
            ${hideSubmit ? "" : `<button class="btn btn-primary btn-sm" type="submit">${esc(submitLabel)}</button>`}
          </div>
        </form>
      </div>`;
    modalRoot.classList.add("open");
    const form = $("#modal-form");
    const errorBox = $("#modal-error");
    modalRoot.querySelectorAll("[data-close]").forEach((el) => el.addEventListener("click", closeModal));
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!onSubmit) return;
      const button = form.querySelector("button[type='submit']");
      errorBox.classList.remove("show");
      button.disabled = true;
      try {
        await onSubmit(form);
        closeModal();
      } catch (error) {
        errorBox.textContent = error.details ? `${error.message} ${JSON.stringify(error.details)}` : error.message || "Request failed";
        errorBox.classList.add("show");
      } finally {
        button.disabled = false;
      }
    });
    setTimeout(() => {
      const first = form.querySelector("input:not([type='checkbox']), textarea, select");
      if (first) first.focus();
    }, 60);
    return form;
  }

  function confirmAction(message, confirmLabel = "Delete") {
    return new Promise((resolve) => {
      modalResolve = resolve;
      const form = openModal({
        title: "Confirm action",
        body: `<p class="muted">${esc(message)}</p>`,
        submitLabel: confirmLabel,
        onSubmit: async () => {
          modalResolve = null;
          resolve(true);
        }
      });
      form.querySelector("[data-close]")?.addEventListener("click", () => {});
      modalRoot.querySelectorAll("[data-close]").forEach((el) =>
        el.addEventListener("click", () => {
          modalResolve = null;
          resolve(false);
        })
      );
    });
  }

  /* ---------------------------------------------------------------- fields */
  function fieldHtml(field, value, index) {
    const id = `field-${index}-${field.name}`;
    const full = field.full ? " full" : "";
    if (field.type === "checkbox") {
      const checked = value === undefined ? !!field.default : !!value;
      return `<div class="form-field checkbox-row${full}">
        <input type="checkbox" id="${id}" name="${esc(field.name)}" ${checked ? "checked" : ""} />
        <label for="${id}">${esc(field.label)}</label>
      </div>`;
    }
    const current = value === undefined ? (field.default !== undefined ? field.default : "") : value;
    let control = "";
    if (field.type === "textarea" || field.type === "json") {
      const text = field.type === "json" ? (value === undefined || value === null || value === "" ? "" : JSON.stringify(value, null, 2)) : current || "";
      control = `<textarea id="${id}" name="${esc(field.name)}" class="${field.type === "json" ? "code" : ""}" rows="${field.rows || (field.type === "json" ? 6 : 3)}">${esc(text)}</textarea>`;
    } else if (field.type === "select") {
      const options = (field.options || [])
        .map(
          (option) =>
            `<option value="${esc(option.value)}" ${String(option.value) === String(current ?? "") ? "selected" : ""}>${esc(option.label)}</option>`
        )
        .join("");
      control = `<select id="${id}" name="${esc(field.name)}">${field.allowEmpty !== false ? `<option value="">—</option>` : ""}${options}</select>`;
    } else if (field.type === "tags") {
      const text = Array.isArray(current) ? current.join(", ") : current || "";
      control = `<input type="text" id="${id}" name="${esc(field.name)}" value="${esc(text)}" placeholder="${esc(field.placeholder || "Comma-separated values")}" />`;
    } else {
      const inputType = field.type === "number" ? "number" : field.type === "date" ? "date" : field.type === "password" ? "password" : field.type === "email" ? "email" : field.type === "url" ? "url" : "text";
      const attrs = [
        field.min !== undefined ? `min="${field.min}"` : "",
        field.max !== undefined ? `max="${field.max}"` : "",
        field.step !== undefined ? `step="${field.step}"` : ""
      ]
        .filter(Boolean)
        .join(" ");
      control = `<input type="${inputType}" id="${id}" name="${esc(field.name)}" value="${esc(current ?? "")}" placeholder="${esc(field.placeholder || "")}" ${attrs} />`;
    }
    return `<div class="form-field${full}">
      <label for="${id}">${esc(field.label)}</label>
      ${control}
      ${field.hint ? `<span class="hint">${esc(field.hint)}</span>` : ""}
    </div>`;
  }

  function fieldsHtml(fields, values) {
    return `<div class="field-grid">${fields.map((field, index) => fieldHtml(field, values[field.name], index)).join("")}</div>`;
  }

  function collectFields(fields, form) {
    const payload = {};
    fields.forEach((field) => {
      const el = form.elements[field.name];
      if (!el) return;
      if (field.type === "checkbox") {
        payload[field.name] = !!el.checked;
        return;
      }
      const raw = el.value;
      if (field.type === "tags") {
        payload[field.name] = raw.split(",").map((item) => item.trim()).filter(Boolean);
        return;
      }
      if (field.type === "json") {
        if (!raw.trim()) {
          payload[field.name] = [];
          return;
        }
        try {
          payload[field.name] = JSON.parse(raw);
        } catch (_error) {
          throw new Error(`${field.label} contains invalid JSON.`);
        }
        return;
      }
      if (field.type === "number") {
        if (raw !== "") payload[field.name] = Number(raw);
        return;
      }
      if (field.type === "date") {
        payload[field.name] = raw || null;
        return;
      }
      if (field.type === "select") {
        payload[field.name] = raw === "" ? null : raw;
        return;
      }
      if (raw !== "" || field.sendEmpty) payload[field.name] = raw;
    });
    return payload;
  }

  async function resolveFieldOptions(fields) {
    const resolved = [];
    for (const field of fields) {
      const copy = { ...field };
      if (field.optionsFrom) {
        try {
          const result = await api.get(field.optionsFrom + "?per_page=100");
          const items = result.data || [];
          copy.options = items.map((item) => ({
            value: item.id,
            label: item.name || item.title || item.label
          }));
        } catch (_error) {
          copy.options = [];
        }
      }
      resolved.push(copy);
    }
    return resolved;
  }

  async function resourceForm({ title, endpoint, fields, item, wide, after }) {
    const resolved = await resolveFieldOptions(fields);
    const values = item || {};
    openModal({
      title,
      wide,
      body: fieldsHtml(resolved, values),
      submitLabel: item ? "Save changes" : "Create",
      onSubmit: async (form) => {
        const payload = collectFields(resolved, form);
        if (item && item.id) await api.put(`${endpoint}/${item.id}`, payload);
        else await api.post(endpoint, payload);
        toast(item ? "Changes saved" : "Created successfully", "success");
        if (after) after();
      }
    });
  }

  /* ---------------------------------------------------------------- generic resource */
  function genericResource(config) {
    return async function render() {
      const state = { page: 1, q: "", filters: {} };
      const filterHtml = (config.filters || [])
        .map(
          (filter) =>
            `<select class="select" data-filter="${esc(filter.key)}"><option value="">All ${esc(filter.label.toLowerCase())}</option>${(filter.options || [])
              .map((option) => `<option value="${esc(option.value)}">${esc(option.label)}</option>`)
              .join("")}</select>`
        )
        .join("");

      view.innerHTML = `
        <div class="view-head">
          <div><h1>${esc(config.title)}</h1><p>${esc(config.description || "")}</p></div>
          <div class="view-actions">
            ${config.headerActions || ""}
            ${canWrite() ? `<button class="btn btn-primary btn-sm" type="button" id="new-record">+ New ${esc(config.singular)}</button>` : ""}
          </div>
        </div>
        <div class="panel">
          <div class="filter-bar">
            <div class="search-field">⌕ <input type="search" id="resource-search" placeholder="Search ${esc(config.title.toLowerCase())}…" /></div>
            ${filterHtml}
            <span class="result-count" id="resource-count"></span>
          </div>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr>${config.columns.map((column) => `<th>${esc(column.label)}</th>`).join("")}<th style="text-align:right">Actions</th></tr></thead>
              <tbody id="resource-body">${loadingRows(config.columns.length)}</tbody>
            </table>
          </div>
          <div class="pagination" id="resource-pagination"></div>
        </div>`;

      const body = $("#resource-body");
      const count = $("#resource-count");
      const pagination = $("#resource-pagination");

      async function load() {
        body.innerHTML = loadingRows(config.columns.length);
        try {
          const query = { page: state.page, per_page: config.perPage || 20, q: state.q, ...state.filters };
          if (config.query) Object.assign(query, config.query());
          const result = await api.get(config.endpoint + qs(query));
          const items = result.data || [];
          const meta = result.meta || {};
          count.textContent = `${meta.total ?? items.length} records`;
          if (!items.length) {
            body.innerHTML = emptyRow(config.columns.length, config.emptyMessage);
          } else {
            body.innerHTML = items
              .map((item) => {
                const cells = config.columns
                  .map((column) => {
                    const value = column.render ? column.render(item) : esc(item[column.key] ?? "—");
                    return `<td class="${column.className || ""}">${value}</td>`;
                  })
                  .join("");
                return `<tr data-id="${item.id}">${cells}<td><div class="row-actions">
                  ${config.edit === false || !canWrite() ? "" : `<button type="button" data-action="edit" data-id="${item.id}">Edit</button>`}
                  ${config.extraActions ? config.extraActions(item) : ""}
                  ${config.delete === false || !canWrite() ? "" : `<button type="button" class="danger" data-action="delete" data-id="${item.id}">Delete</button>`}
                </div></td></tr>`;
              })
              .join("");
            body._items = items;
          }
          pagination.innerHTML = meta.pages
            ? `<span>Page ${meta.page} of ${meta.pages} · ${meta.total} total</span>
               <div class="pagination-actions">
                 <button class="btn btn-ghost btn-sm" type="button" data-page="${meta.page - 1}" ${meta.has_prev ? "" : "disabled"}>Previous</button>
                 <button class="btn btn-ghost btn-sm" type="button" data-page="${meta.page + 1}" ${meta.has_next ? "" : "disabled"}>Next</button>
               </div>`
            : "";
        } catch (error) {
          body.innerHTML = errorRow(config.columns.length, error.message || "Request failed");
          count.textContent = "";
          pagination.innerHTML = "";
        }
      }

      $("#new-record")?.addEventListener("click", () =>
        resourceForm({ title: `New ${config.singular}`, endpoint: config.endpoint, fields: config.fields, wide: config.wide, after: load })
      );

      let timer = null;
      $("#resource-search").addEventListener("input", (event) => {
        clearTimeout(timer);
        timer = setTimeout(() => {
          state.q = event.target.value.trim();
          state.page = 1;
          load();
        }, 280);
      });
      $$("[data-filter]").forEach((select) =>
        select.addEventListener("change", () => {
          state.filters[select.dataset.filter] = select.value;
          state.page = 1;
          load();
        })
      );
      pagination.addEventListener("click", (event) => {
        const button = event.target.closest("[data-page]");
        if (!button || button.disabled) return;
        state.page = Number(button.dataset.page);
        load();
      });
      body.addEventListener("click", async (event) => {
        const action = event.target.closest("[data-action]");
        if (!action) return;
        const item = (body._items || []).find((entry) => String(entry.id) === action.dataset.id);
        if (action.dataset.action === "edit" && item) {
          let detail = item;
          try {
            const result = await api.get(`${config.endpoint}/${item.id}`);
            if (result.data) detail = { ...item, ...result.data };
          } catch (_error) {
            detail = item;
          }
          if (config.prepareItem) detail = { ...detail, ...config.prepareItem(detail) };
          resourceForm({ title: `Edit ${config.singular}`, endpoint: config.endpoint, fields: config.fields, item: detail, wide: config.wide, after: load });
        } else if (action.dataset.action === "delete" && item) {
          const label = item.title || item.name || item.label || `#${item.id}`;
          if (await confirmAction(`Delete “${label}”? This action cannot be undone from the dashboard.`)) {
            try {
              await api.del(`${config.endpoint}/${item.id}`);
              toast("Record deleted", "success");
              load();
            } catch (error) {
              toast(error.message || "Delete failed", "error");
            }
          }
        } else if (config.onAction) {
          config.onAction(action, item, load);
        }
      });

      load();
    };
  }

  /* ---------------------------------------------------------------- fields configs */
  const STATUS_OPTIONS = [
    { value: "draft", label: "Draft" },
    { value: "published", label: "Published" },
    { value: "archived", label: "Archived" }
  ];

  const projectFields = [
    { name: "title", label: "Title", full: true },
    { name: "short_description", label: "Short description", full: true, rows: 2 },
    { name: "status", label: "Status", type: "select", options: STATUS_OPTIONS, allowEmpty: false },
    { name: "project_type", label: "Project type", placeholder: "AI/ML, Data Science, Web…" },
    { name: "category_id", label: "Category", type: "select", optionsFrom: "/admin/project-categories" },
    { name: "display_order", label: "Display order", type: "number", min: 0 },
    { name: "featured", label: "Featured project", type: "checkbox" },
    { name: "thumbnail_url", label: "Thumbnail URL", type: "url", full: true },
    { name: "github_url", label: "GitHub URL", type: "url" },
    { name: "live_url", label: "Live URL", type: "url" },
    { name: "docs_url", label: "Docs URL", type: "url" },
    { name: "technologies", label: "Technologies", type: "tags", full: true, placeholder: "Python, Flask, Power BI" },
    { name: "description", label: "Description", type: "textarea", full: true, rows: 4 },
    { name: "problem_statement", label: "Problem statement", type: "textarea", full: true, rows: 3 },
    { name: "solution", label: "Solution", type: "textarea", full: true, rows: 3 },
    { name: "architecture", label: "Architecture", type: "textarea", full: true, rows: 3 },
    { name: "implementation", label: "Implementation", type: "textarea", full: true, rows: 3 },
    { name: "challenges", label: "Challenges", type: "textarea", full: true, rows: 3 },
    { name: "future_improvements", label: "Future improvements", type: "textarea", full: true, rows: 3 },
    { name: "dataset_info", label: "Dataset information", type: "textarea", full: true, rows: 3 },
    { name: "metrics", label: "Metrics (JSON array)", type: "json", full: true, hint: '[{"name":"Accuracy","value":"94.2","unit":"%"}]' },
    { name: "images", label: "Images (JSON array)", type: "json", full: true, hint: '[{"url":"/uploads/media/example.png","caption":"Dashboard"}]' }
  ];

  const blogFields = [
    { name: "title", label: "Title", full: true },
    { name: "status", label: "Status", type: "select", options: STATUS_OPTIONS, allowEmpty: false },
    { name: "category_id", label: "Category", type: "select", optionsFrom: "/admin/blog-categories" },
    { name: "featured", label: "Featured post", type: "checkbox" },
    { name: "reading_minutes", label: "Reading minutes", type: "number", min: 1, max: 180 },
    { name: "excerpt", label: "Excerpt", full: true, rows: 2 },
    { name: "cover_image_url", label: "Cover image URL", type: "url", full: true },
    { name: "tags", label: "Tags", type: "tags", full: true, placeholder: "AI, research, tutorials" },
    { name: "content", label: "Content (Markdown)", type: "textarea", full: true, rows: 14 },
    { name: "seo_title", label: "SEO title", full: true },
    { name: "seo_description", label: "SEO description", type: "textarea", full: true, rows: 2 }
  ];

  const researchFields = [
    { name: "title", label: "Title", full: true },
    { name: "status", label: "Status", type: "select", options: STATUS_OPTIONS, allowEmpty: false },
    { name: "publication_status", label: "Publication status", placeholder: "Unpublished / under review" },
    { name: "sample_size", label: "Sample size" },
    { name: "institutions_count", label: "Institutions" },
    { name: "is_featured", label: "Featured research", type: "checkbox" },
    { name: "abstract", label: "Abstract", type: "textarea", full: true, rows: 5 },
    { name: "methodology", label: "Methodology", type: "textarea", full: true, rows: 4 },
    { name: "paper_url", label: "Paper URL", type: "url" },
    { name: "dataset_url", label: "Dataset URL", type: "url" },
    { name: "notes", label: "Notes", type: "textarea", full: true, rows: 2 },
    { name: "metrics", label: "Metrics (JSON array)", type: "json", full: true, hint: '[{"name":"Accuracy","value":"0.86","unit":"score"}]' }
  ];

  const educationFields = [
    { name: "institution", label: "Institution", full: true },
    { name: "qualification", label: "Qualification", full: true },
    { name: "field_of_study", label: "Field of study" },
    { name: "location", label: "Location" },
    { name: "start_year", label: "Start year" },
    { name: "end_year", label: "End year" },
    { name: "grade", label: "Grade / class" },
    { name: "display_order", label: "Display order", type: "number", min: 0 },
    { name: "is_visible", label: "Visible on site", type: "checkbox", default: true },
    { name: "description", label: "Description", type: "textarea", full: true, rows: 3 }
  ];

  const experienceFields = [
    { name: "organization", label: "Organization", full: true },
    { name: "role", label: "Role", full: true },
    { name: "employment_type", label: "Employment type", placeholder: "Internship, Freelance…" },
    { name: "location", label: "Location" },
    { name: "start_date", label: "Start date", type: "date" },
    { name: "end_date", label: "End date", type: "date" },
    { name: "is_current", label: "Current role", type: "checkbox" },
    { name: "display_order", label: "Display order", type: "number", min: 0 },
    { name: "is_visible", label: "Visible on site", type: "checkbox", default: true },
    { name: "achievements", label: "Highlights", type: "tags", full: true, placeholder: "Built X, Improved Y" },
    { name: "description", label: "Description", type: "textarea", full: true, rows: 4 }
  ];

  const achievementFields = [
    { name: "title", label: "Title", full: true },
    { name: "category", label: "Category" },
    { name: "issuer", label: "Issuer" },
    { name: "date", label: "Date", type: "date" },
    { name: "url", label: "Reference URL", type: "url" },
    { name: "is_featured", label: "Featured", type: "checkbox" },
    { name: "is_visible", label: "Visible on site", type: "checkbox", default: true },
    { name: "description", label: "Description", type: "textarea", full: true, rows: 3 }
  ];

  const skillFields = [
    { name: "name", label: "Skill name", full: true },
    { name: "category_id", label: "Category", type: "select", optionsFrom: "/admin/skill-categories", allowEmpty: false },
    { name: "proficiency", label: "Proficiency (0–100)", type: "number", min: 0, max: 100 },
    { name: "icon", label: "Icon" },
    { name: "display_order", label: "Display order", type: "number", min: 0 },
    { name: "is_featured", label: "Featured", type: "checkbox" },
    { name: "is_visible", label: "Visible on site", type: "checkbox", default: true }
  ];

  const certificateFields = [
    { name: "title", label: "Title", full: true },
    { name: "issuer", label: "Issuer", full: true },
    { name: "category_id", label: "Category", type: "select", optionsFrom: "/admin/certificate-categories" },
    { name: "status", label: "Status", type: "select", options: STATUS_OPTIONS, allowEmpty: false },
    { name: "issue_date", label: "Issue date", type: "date" },
    { name: "expiry_date", label: "Expiry date", type: "date" },
    { name: "credential_id", label: "Credential ID" },
    { name: "file_type", label: "File type", placeholder: "pdf, png" },
    { name: "featured", label: "Featured", type: "checkbox" },
    { name: "verification_url", label: "Verification URL", type: "url", full: true },
    { name: "image_url", label: "Image URL", type: "url" },
    { name: "file_url", label: "File URL", type: "url" },
    { name: "description", label: "Description", type: "textarea", full: true, rows: 3 }
  ];

  const testimonialFields = [
    { name: "author_name", label: "Author name", full: true },
    { name: "author_role", label: "Author role" },
    { name: "organization", label: "Organization" },
    { name: "rating", label: "Rating (1–5)", type: "number", min: 1, max: 5 },
    { name: "avatar_url", label: "Avatar URL", type: "url" },
    { name: "is_approved", label: "Approved", type: "checkbox" },
    { name: "is_featured", label: "Featured", type: "checkbox" },
    { name: "content", label: "Testimonial", type: "textarea", full: true, rows: 4 }
  ];

  const ROUTES = {};

  ROUTES.dashboard = async function dashboard() {
    view.innerHTML = `<div class="empty"><strong>Loading dashboard…</strong>Gathering analytics.</div>`;
    const result = await api.get("/admin/dashboard");
    const data = result.data || {};
    const stats = data.stats || {};
    const series = data.daily_series || [];
    const max = Math.max(1, ...series.map((row) => row.page_views || 0));
    const popular = [...(data.popular?.projects || []).map((item) => ({ ...item, type: "Project" })), ...(data.popular?.blog_posts || []).map((item) => ({ ...item, type: "Article" }))].slice(0, 5);
    const sources = (data.traffic_sources || []).slice(0, 6);
    const sourceMax = Math.max(1, ...sources.map((row) => row.count || 0));

    const cards = [
      ["Visitors", stats.total_visitors || 0, "All-time unique visitors", "accent"],
      ["Page views", stats.total_page_views || 0, "Last 30 days", "info"],
      ["Messages", stats.new_contact_messages || 0, `${stats.total_contact_messages || 0} total received`, "warn"],
      ["Projects", stats.published_projects || 0, `${stats.total_projects || 0} total · ${stats.published_projects || 0} published`, ""],
      ["Blog posts", stats.published_blog_posts || 0, `${stats.total_blog_posts || 0} total`, ""],
      ["CV downloads", stats.cv_downloads || 0, "Tracked downloads", "accent"]
    ];

    view.innerHTML = `
      <div class="view-head">
        <div><h1>Dashboard</h1><p>Verified platform activity at a glance.</p></div>
        <div class="view-actions">
          <a class="btn btn-ghost btn-sm" href="#/analytics">Full analytics</a>
          <button class="btn btn-primary btn-sm" type="button" id="quick-project">+ New project</button>
        </div>
      </div>
      <div class="stat-grid">
        ${cards
          .map(
            ([label, value, meta, tone]) =>
              `<div class="stat-card ${tone}"><div class="stat-card-label">${esc(label)}</div><div class="stat-card-value">${esc(value)}</div><div class="stat-card-meta">${esc(meta)}</div></div>`
          )
          .join("")}
      </div>
      <div class="split">
        <div class="panel">
          <div class="panel-head"><div><h2>Traffic · last 30 days</h2><p>Page views by day</p></div><span class="note">${series.length} active days</span></div>
          <div class="panel-body">
            ${
              series.length
                ? `<div class="bars">${series
                    .map((row) => `<div class="bar" style="height:${Math.max(3, Math.round(((row.page_views || 0) / max) * 130))}px" title="${esc(row.date)} · ${row.page_views} views"></div>`)
                    .join("")}</div>
                   <div class="bar-label"><span>${esc(series[0].date)}</span><span>${esc(series[series.length - 1].date)}</span></div>`
                : `<div class="empty"><strong>No traffic yet</strong>Page views will appear after visitors browse the public site (analytics may be disabled).</div>`
            }
          </div>
        </div>
        <div class="panel">
          <div class="panel-head"><h2>Traffic sources</h2><a class="text-link" href="#/analytics">Details</a></div>
          <div class="panel-body">
            ${
              sources.length
                ? sources
                    .map(
                      (row) =>
                        `<div class="source-row"><span class="source-bar" style="width:${Math.max(4, Math.round((row.count / sourceMax) * 70))}px"></span><span class="source-name">${esc(row.source)}</span><span class="source-value">${row.count}</span></div>`
                    )
                    .join("")
                : `<div class="empty"><strong>No referrers recorded</strong>Traffic source attribution appears once tracked events arrive.</div>`
            }
          </div>
        </div>
      </div>
      <div class="split" style="margin-top:1rem">
        <div class="panel">
          <div class="panel-head"><h2>Popular content</h2><span class="note">By views</span></div>
          <div class="panel-body">
            ${
              popular.length
                ? `<ul class="list-simple">${popular
                    .map(
                      (item, index) =>
                        `<li><span class="list-rank">${index + 1}</span><span class="list-main"><strong>${esc(item.title)}</strong><span>${esc(item.type)}</span></span><span class="list-value">${item.views || 0}</span></li>`
                    )
                    .join("")}</ul>`
                : `<div class="empty"><strong>No content views yet</strong>Publish projects or articles to see ranking.</div>`
            }
          </div>
        </div>
        <div class="panel">
          <div class="panel-head"><h2>Recent activity</h2><a class="text-link" href="#/activity">All logs</a></div>
          <div class="panel-body tight">
            ${
              (data.recent_activity || []).length
                ? `<ul class="activity-list">${data.recent_activity
                    .map(
                      (entry) =>
                        `<li><span class="activity-dot"></span><div class="activity-main"><strong>${esc(entry.action)}</strong><span>${esc(entry.user_name || "System")}${entry.entity_type ? ` · ${esc(entry.entity_type)}` : ""}</span></div><time>${esc(fmtDateShort(entry.created_at))}</time></li>`
                    )
                    .join("")}</ul>`
                : `<div class="empty"><strong>No activity yet</strong>Actions appear here as you manage the platform.</div>`
            }
          </div>
        </div>
      </div>`;

    $("#quick-project").addEventListener("click", () =>
      resourceForm({
        title: "New project",
        endpoint: "/admin/projects",
        fields: projectFields,
        wide: true,
        after: () => {
          toast("Project created", "success");
        }
      })
    );
  };

  ROUTES.profile = async function profile() {
    view.innerHTML = `<div class="empty"><strong>Loading profile…</strong></div>`;
    const result = await api.get("/admin/profile");
    const data = result.data || {};
    const fields = [
      { name: "full_name", label: "Full name", full: true },
      { name: "professional_title", label: "Professional title", full: true },
      { name: "email", label: "Email", type: "email" },
      { name: "phone", label: "Phone" },
      { name: "location", label: "Location" },
      { name: "github_username", label: "GitHub username" },
      { name: "github_url", label: "GitHub URL", type: "url" },
      { name: "linkedin_url", label: "LinkedIn URL", type: "url" },
      { name: "website_url", label: "Website URL", type: "url" },
      { name: "avatar_url", label: "Avatar URL", type: "url" },
      { name: "resume_url", label: "Resume URL", type: "url" },
      { name: "interests", label: "Interests", type: "tags" },
      { name: "languages", label: "Languages", type: "tags" },
      { name: "summary", label: "Professional summary", type: "textarea", full: true, rows: 3 },
      { name: "about", label: "About", type: "textarea", full: true, rows: 7 },
      { name: "career_goals", label: "Career goals", type: "textarea", full: true, rows: 4 }
    ];
    view.innerHTML = `
      <div class="view-head"><div><h1>Profile</h1><p>Public identity, links and narrative. Only verified details should be published.</p></div>
        <div class="view-actions"><a class="btn btn-ghost btn-sm" href="../about.html" target="_blank" rel="noopener">Preview about page ↗</a></div>
      </div>
      <div class="panel">
        <div class="panel-head"><h2>Portfolio identity</h2><span class="note">Last saved ${esc(fmtDateShort(data.updated_at))}</span></div>
        <div class="panel-body">
          <form class="profile-form" id="profile-form">
            <div class="form-error" id="profile-error"></div>
            ${fieldsHtml(fields, data)}
            <div style="margin-top:1rem;display:flex;justify-content:flex-end">
              <button class="btn btn-primary btn-sm" type="submit" ${canWrite() ? "" : "disabled"}>Save profile</button>
            </div>
          </form>
        </div>
      </div>`;
    const form = $("#profile-form");
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const errorBox = $("#profile-error");
      errorBox.classList.remove("show");
      try {
        await api.put("/admin/profile", collectFields(fields, form));
        toast("Profile saved", "success");
      } catch (error) {
        errorBox.textContent = error.message || "Unable to save";
        errorBox.classList.add("show");
      }
    });
  };

  ROUTES.projects = genericResource({
    title: "Projects",
    singular: "project",
    description: "Case studies, metrics and technical detail.",
    endpoint: "/admin/projects",
    wide: true,
    fields: projectFields,
    prepareItem: (item) => ({ category_id: item.category?.id ?? null }),
    filters: [
      { key: "status", label: "Statuses", options: STATUS_OPTIONS },
      { key: "featured", label: "Featured state", options: [{ value: "true", label: "Featured" }, { value: "false", label: "Not featured" }] }
    ],
    columns: [
      {
        label: "Project",
        render: (item) => `<div class="cell-title">${esc(item.title)}</div><div class="cell-sub">${esc(item.project_type || item.slug)}</div>`
      },
      { label: "Status", render: (item) => statusBadge(item.status) },
      { label: "Featured", render: (item) => boolBadge(item.featured, ["Featured", "—"]) },
      { label: "Tech", render: (item) => `<div class="chip-set">${(item.technologies || []).slice(0, 4).map((tech) => `<span class="badge">${esc(tech)}</span>`).join("") || "—"}</div>` },
      { label: "Views", render: (item) => esc(item.views ?? 0) },
      { label: "Updated", render: (item) => `<span class="cell-nowrap">${esc(fmtDateShort(item.updated_at))}</span>` }
    ]
  });

  ROUTES.research = genericResource({
    title: "Research",
    singular: "research record",
    description: "Academic work, methodology and reported metrics.",
    endpoint: "/admin/research",
    wide: true,
    fields: researchFields,
    filters: [{ key: "status", label: "Statuses", options: STATUS_OPTIONS }],
    columns: [
      { label: "Research", render: (item) => `<div class="cell-title">${esc(item.title)}</div><div class="cell-sub">${esc(item.publication_status || item.slug)}</div>` },
      { label: "Status", render: (item) => statusBadge(item.status) },
      { label: "Featured", render: (item) => boolBadge(item.is_featured, ["Yes", "—"]) },
      { label: "Sample", render: (item) => esc(item.sample_size || "—") },
      { label: "Created", render: (item) => `<span class="cell-nowrap">${esc(fmtDateShort(item.created_at))}</span>` }
    ]
  });

  ROUTES.blog = genericResource({
    title: "Blog",
    singular: "post",
    description: "Articles, drafts and SEO metadata.",
    endpoint: "/admin/blogs",
    wide: true,
    fields: blogFields,
    prepareItem: (item) => ({ category_id: item.category?.id ?? null }),
    filters: [
      { key: "status", label: "Statuses", options: STATUS_OPTIONS },
      { key: "featured", label: "Featured state", options: [{ value: "true", label: "Featured" }, { value: "false", label: "Not featured" }] }
    ],
    columns: [
      { label: "Post", render: (item) => `<div class="cell-title">${esc(item.title)}</div><div class="cell-sub">${esc(item.slug)}</div>` },
      { label: "Status", render: (item) => statusBadge(item.status) },
      { label: "Tags", render: (item) => `<div class="chip-set">${(item.tags || []).slice(0, 3).map((tag) => `<span class="badge">${esc(tag)}</span>`).join("") || "—"}</div>` },
      { label: "Reading", render: (item) => `${esc(item.reading_minutes || 1)} min` },
      { label: "Views", render: (item) => esc(item.views ?? 0) },
      { label: "Updated", render: (item) => `<span class="cell-nowrap">${esc(fmtDateShort(item.updated_at))}</span>` }
    ]
  });

  ROUTES.education = genericResource({
    title: "Education",
    singular: "education record",
    description: "Academic history displayed on the about page.",
    endpoint: "/admin/education",
    fields: educationFields,
    columns: [
      { label: "Qualification", render: (item) => `<div class="cell-title">${esc(item.qualification)}</div><div class="cell-sub">${esc(item.institution)}</div>` },
      { label: "Period", render: (item) => `${esc(item.start_year || "—")} – ${esc(item.end_year || "Present")}` },
      { label: "Grade", render: (item) => esc(item.grade || "—") },
      { label: "Order", render: (item) => esc(item.display_order ?? 0) },
      { label: "Visible", render: (item) => boolBadge(item.is_visible, ["Visible", "Hidden"], "success") }
    ]
  });

  ROUTES.experience = genericResource({
    title: "Experience",
    singular: "experience record",
    description: "Verified roles only. Leave empty if there is nothing to publish.",
    endpoint: "/admin/experience",
    fields: experienceFields,
    columns: [
      { label: "Role", render: (item) => `<div class="cell-title">${esc(item.role)}</div><div class="cell-sub">${esc(item.organization)}</div>` },
      { label: "Period", render: (item) => `${esc(item.start_date || "—")} – ${esc(item.is_current ? "Present" : item.end_date || "—")}` },
      { label: "Type", render: (item) => esc(item.employment_type || "—") },
      { label: "Visible", render: (item) => boolBadge(item.is_visible, ["Visible", "Hidden"], "success") }
    ]
  });

  ROUTES.skills = genericResource({
    title: "Skills",
    singular: "skill",
    description: "Skills grouped by category with optional proficiency.",
    endpoint: "/admin/skills",
    fields: skillFields,
    filters: [{ key: "visible", label: "Visibility", options: [{ value: "true", label: "Visible" }, { value: "false", label: "Hidden" }] }],
    columns: [
      { label: "Skill", render: (item) => `<div class="cell-title">${esc(item.name)}</div><div class="cell-sub">${esc(item.icon || "")}</div>` },
      { label: "Category", render: (item) => esc(item.category?.name || item.category_id || "—") },
      { label: "Proficiency", render: (item) => (item.proficiency == null ? "—" : `${esc(item.proficiency)}%`) },
      { label: "Featured", render: (item) => boolBadge(item.is_featured, ["Yes", "—"]) },
      { label: "Visible", render: (item) => boolBadge(item.is_visible, ["Visible", "Hidden"], "success") }
    ]
  });

  ROUTES["skill-categories"] = genericResource({
    title: "Skill groups",
    singular: "skill group",
    description: "Categories used to organise the skills grid.",
    endpoint: "/admin/skill-categories",
    fields: [
      { name: "name", label: "Name", full: true },
      { name: "description", label: "Description", type: "textarea", full: true, rows: 2 },
      { name: "display_order", label: "Display order", type: "number", min: 0 }
    ],
    columns: [
      { label: "Name", render: (item) => `<div class="cell-title">${esc(item.name)}</div><div class="cell-sub">${esc(item.slug)}</div>` },
      { label: "Description", render: (item) => esc(truncate(item.description || "—", 90)) },
      { label: "Order", render: (item) => esc(item.display_order ?? 0) }
    ]
  });

  ROUTES.certificates = genericResource({
    title: "Certificates",
    singular: "certificate",
    description: "Credentials with issuer verification links.",
    endpoint: "/admin/certificates",
    fields: certificateFields,
    prepareItem: (item) => ({ category_id: item.category?.id ?? null }),
    filters: [
      { key: "status", label: "Statuses", options: STATUS_OPTIONS },
      { key: "featured", label: "Featured state", options: [{ value: "true", label: "Featured" }, { value: "false", label: "Not featured" }] }
    ],
    columns: [
      { label: "Certificate", render: (item) => `<div class="cell-title">${esc(item.title)}</div><div class="cell-sub">${esc(item.issuer)}</div>` },
      { label: "Issued", render: (item) => `<span class="cell-nowrap">${esc(item.issue_date || "—")}</span>` },
      { label: "Status", render: (item) => statusBadge(item.status) },
      { label: "Featured", render: (item) => boolBadge(item.featured, ["Yes", "—"]) },
      { label: "Verify", render: (item) => (item.verification_url ? `<a class="text-link" href="${esc(item.verification_url)}" target="_blank" rel="noopener">Open ↗</a>` : "—") }
    ]
  });

  ROUTES.testimonials = genericResource({
    title: "Testimonials",
    singular: "testimonial",
    description: "Only publish approved, attributable feedback.",
    endpoint: "/admin/testimonials",
    fields: testimonialFields,
    filters: [{ key: "approved", label: "Approval", options: [{ value: "true", label: "Approved" }, { value: "false", label: "Pending" }] }],
    columns: [
      { label: "Author", render: (item) => `<div class="cell-title">${esc(item.author_name)}</div><div class="cell-sub">${esc(item.organization || item.author_role || "")}</div>` },
      { label: "Rating", render: (item) => (item.rating ? `${esc(item.rating)} / 5` : "—") },
      { label: "Approved", render: (item) => boolBadge(item.is_approved, ["Approved", "Pending"], "success") },
      { label: "Featured", render: (item) => boolBadge(item.is_featured, ["Yes", "—"]) },
      { label: "Received", render: (item) => `<span class="cell-nowrap">${esc(fmtDateShort(item.created_at))}</span>` }
    ]
  });

  ROUTES.achievements = genericResource({
    title: "Achievements",
    singular: "achievement",
    description: "Awards, recognition and milestones. Publish only verified entries.",
    endpoint: "/admin/achievements",
    fields: achievementFields,
    columns: [
      { label: "Achievement", render: (item) => `<div class="cell-title">${esc(item.title)}</div><div class="cell-sub">${esc(item.issuer || item.category || "")}</div>` },
      { label: "Date", render: (item) => esc(item.date || "—") },
      { label: "Featured", render: (item) => boolBadge(item.is_featured, ["Yes", "—"]) },
      { label: "Visible", render: (item) => boolBadge(item.is_visible, ["Visible", "Hidden"], "success") }
    ]
  });

  ROUTES.taxonomy = async function taxonomy() {
    const tabs = [
      ["blog-categories", "Blog categories", "/admin/blog-categories", "Posts can be filed under a category."],
      ["blog-tags", "Blog tags", "/admin/blog-tags", "Tags are created automatically when publishing a post."],
      ["project-categories", "Project categories", "/admin/project-categories", "Group case studies by discipline."],
      ["certificate-categories", "Certificate categories", "/admin/certificate-categories", "Group credentials by issuer type."]
    ];
    view.innerHTML = `
      <div class="view-head"><div><h1>Categories & tags</h1><p>Taxonomy shared across public content.</p></div></div>
      <div class="panel">
        <div class="filter-bar" id="taxonomy-tabs">
          ${tabs.map(([key, label], index) => `<button class="btn ${index === 0 ? "btn-primary" : "btn-ghost"} btn-sm" type="button" data-tab="${key}">${esc(label)}</button>`).join("")}
        </div>
        <div id="taxonomy-panel"></div>
      </div>`;
    const panel = $("#taxonomy-panel");
    async function loadTab(key) {
      const tab = tabs.find((entry) => entry[0] === key);
      if (!tab) return;
      $$("[data-tab]").forEach((button) => {
        const active = button.dataset.tab === key;
        button.className = `btn ${active ? "btn-primary" : "btn-ghost"} btn-sm`;
      });
      panel.innerHTML = `<div class="empty"><strong>Loading…</strong></div>`;
      try {
        const result = await api.get(tab[2] + "?per_page=100");
        const items = result.data || [];
        panel.innerHTML = `
          <div class="filter-bar"><span class="note">${esc(tab[3])}</span><span class="result-count">${items.length} records</span>${canWrite() ? `<button class="btn btn-primary btn-sm" type="button" id="taxonomy-new">+ New</button>` : ""}</div>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>Name</th><th>Slug</th><th>Description</th><th style="text-align:right">Actions</th></tr></thead>
              <tbody>
                ${
                  items.length
                    ? items
                        .map(
                          (item) => `<tr><td class="cell-title">${esc(item.name)}</td><td class="mono">${esc(item.slug)}</td><td>${esc(truncate(item.description || "—", 70))}</td>
                          <td><div class="row-actions">
                            ${canWrite() ? `<button type="button" data-edit="${item.id}">Edit</button>` : ""}
                            ${canWrite() ? `<button type="button" class="danger" data-delete="${item.id}">Delete</button>` : ""}
                          </div></td></tr>`
                        )
                        .join("")
                    : `<tr><td colspan="4"><div class="empty"><strong>No records</strong>Add the first one.</div></td></tr>`
                }
              </tbody>
            </table>
          </div>`;
        const fields = [
          { name: "name", label: "Name", full: true },
          { name: "description", label: "Description", type: "textarea", full: true, rows: 2 }
        ];
        if (key === "project-categories") fields.push({ name: "display_order", label: "Display order", type: "number", min: 0 });
        $("#taxonomy-new")?.addEventListener("click", () =>
          resourceForm({ title: "New record", endpoint: tab[2], fields, after: () => loadTab(key) })
        );
        panel.querySelectorAll("[data-edit]").forEach((button) =>
          button.addEventListener("click", () => {
            const item = items.find((entry) => String(entry.id) === button.dataset.edit);
            resourceForm({ title: "Edit record", endpoint: tab[2], fields, item, after: () => loadTab(key) });
          })
        );
        panel.querySelectorAll("[data-delete]").forEach((button) =>
          button.addEventListener("click", async () => {
            const item = items.find((entry) => String(entry.id) === button.dataset.delete);
            if (!(await confirmAction(`Delete “${item?.name || "record"}”?`))) return;
            try {
              await api.del(`${tab[2]}/${button.dataset.delete}`);
              toast("Deleted", "success");
              loadTab(key);
            } catch (error) {
              toast(error.message || "Delete failed", "error");
            }
          })
        );
      } catch (error) {
        panel.innerHTML = `<div class="empty"><strong>Could not load taxonomy</strong>${esc(error.message)}</div>`;
      }
    }
    $("#taxonomy-tabs").addEventListener("click", (event) => {
      const button = event.target.closest("[data-tab]");
      if (button) loadTab(button.dataset.tab);
    });
    loadTab("blog-categories");
  };

  /* ---------------------------------------------------------------- messages */
  ROUTES.messages = async function messages() {
    const state = { page: 1, q: "", status: "" };
    view.innerHTML = `
      <div class="view-head"><div><h1>Messages</h1><p>Contact form submissions. Reply externally, then mark the status.</p></div></div>
      <div class="panel">
        <div class="filter-bar">
          <div class="search-field">⌕ <input type="search" id="message-search" placeholder="Search name, email, subject…" /></div>
          <select class="select" id="message-status">
            <option value="">All statuses</option>
            ${["new", "read", "in_progress", "replied", "archived"].map((status) => `<option value="${status}">${status.replace("_", " ")}</option>`).join("")}
          </select>
          <span class="result-count" id="message-count"></span>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>From</th><th>Subject</th><th>Status</th><th>Received</th><th style="text-align:right">Actions</th></tr></thead>
            <tbody id="message-body"><tr><td colspan="5"><div class="empty"><strong>Loading…</strong></div></td></tr></tbody>
          </table>
        </div>
        <div class="pagination" id="message-pagination"></div>
      </div>`;
    const body = $("#message-body");
    async function load() {
      body.innerHTML = `<tr><td colspan="5"><div class="empty"><strong>Loading…</strong></div></td></tr>`;
      try {
        const result = await api.get("/admin/messages" + qs({ page: state.page, q: state.q, status: state.status }));
        const items = result.data || [];
        const meta = result.meta || {};
        $("#message-count").textContent = `${meta.total ?? items.length} messages`;
        if (!items.length) {
          body.innerHTML = `<tr><td colspan="5"><div class="empty"><strong>No messages</strong>Submissions from the public contact form appear here.</div></td></tr>`;
        } else {
          body.innerHTML = items
            .map(
              (item) => `<tr data-id="${item.id}">
                <td><div class="cell-title">${esc(item.name)}</div><div class="cell-sub">${esc(item.email)}</div></td>
                <td><div class="cell-title">${esc(item.subject)}</div><div class="cell-sub">${esc(truncate(item.message, 80))}</div></td>
                <td>${statusBadge(item.status)}</td>
                <td class="cell-nowrap">${esc(fmtDateShort(item.created_at))}</td>
                <td><div class="row-actions"><button type="button" data-action="view" data-id="${item.id}">Open</button>${canWrite() ? `<button type="button" class="danger" data-action="delete" data-id="${item.id}">Delete</button>` : ""}</div></td>
              </tr>`
            )
            .join("");
          body._items = items;
        }
        $("#message-pagination").innerHTML = meta.pages
          ? `<span>Page ${meta.page} of ${meta.pages}</span><div class="pagination-actions">
              <button class="btn btn-ghost btn-sm" type="button" data-page="${meta.page - 1}" ${meta.has_prev ? "" : "disabled"}>Previous</button>
              <button class="btn btn-ghost btn-sm" type="button" data-page="${meta.page + 1}" ${meta.has_next ? "" : "disabled"}>Next</button>
            </div>`
          : "";
      } catch (error) {
        body.innerHTML = `<tr><td colspan="5"><div class="empty"><strong>Could not load messages</strong>${esc(error.message)}</div></td></tr>`;
      }
    }
    let timer = null;
    $("#message-search").addEventListener("input", (event) => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        state.q = event.target.value.trim();
        state.page = 1;
        load();
      }, 280);
    });
    $("#message-status").addEventListener("change", (event) => {
      state.status = event.target.value;
      state.page = 1;
      load();
    });
    $("#message-pagination").addEventListener("click", (event) => {
      const button = event.target.closest("[data-page]");
      if (!button || button.disabled) return;
      state.page = Number(button.dataset.page);
      load();
    });
    body.addEventListener("click", async (event) => {
      const button = event.target.closest("[data-action]");
      if (!button) return;
      const item = (body._items || []).find((entry) => String(entry.id) === button.dataset.id);
      if (!item) return;
      if (button.dataset.action === "delete") {
        if (!(await confirmAction(`Delete the message from ${item.name}?`))) return;
        try {
          await api.del(`/admin/messages/${item.id}`);
          toast("Message deleted", "success");
          load();
        } catch (error) {
          toast(error.message || "Delete failed", "error");
        }
        return;
      }
      openModal({
        title: item.subject,
        wide: true,
        submitLabel: "Update message",
        body: `
          <dl class="kv" style="margin-bottom:1rem">
            <dt>From</dt><dd>${esc(item.name)} · <a class="text-link" href="mailto:${esc(item.email)}">${esc(item.email)}</a>${item.phone ? ` · ${esc(item.phone)}` : ""}</dd>
            <dt>Received</dt><dd>${esc(fmtDateShort(item.created_at))}</dd>
            <dt>Status</dt><dd>${statusBadge(item.status)}</dd>
          </dl>
          <div class="panel" style="margin-bottom:1rem"><div class="panel-body"><p style="white-space:pre-wrap;margin:0">${esc(item.message)}</p></div></div>
          <div class="field-grid">
            <div class="form-field"><label>Status</label><select name="status">${["new", "read", "in_progress", "replied", "archived"].map((status) => `<option value="${status}" ${status === item.status ? "selected" : ""}>${status.replace("_", " ")}</option>`).join("")}</select></div>
            <div class="form-field full"><label>Admin notes</label><textarea name="admin_notes" rows="3">${esc(item.admin_notes || "")}</textarea></div>
          </div>
          <p class="note" style="margin-top:0.7rem">Tip: open your mail client with the address above to reply, then set the status to “replied”.</p>`,
        onSubmit: async (form) => {
          await api.put(`/admin/messages/${item.id}`, {
            status: form.elements.status.value,
            admin_notes: form.elements.admin_notes.value || null
          });
          toast("Message updated", "success");
          load();
        }
      });
      const mailLink = document.createElement("a");
      mailLink.href = `mailto:${item.email}?subject=${encodeURIComponent(`Re: ${item.subject}`)}`;
      mailLink.textContent = "Reply by email";
      mailLink.className = "btn btn-ghost btn-sm";
      mailLink.style.marginRight = "auto";
      $("#modal-form .modal-foot")?.prepend(mailLink);
    });
    load();
  };

  /* ---------------------------------------------------------------- newsletter */
  ROUTES.newsletter = async function newsletter() {
    const state = { page: 1, q: "", status: "" };
    view.innerHTML = `
      <div class="view-head"><div><h1>Newsletter</h1><p>Consented subscribers. Remove addresses on request.</p></div></div>
      <div class="panel">
        <div class="filter-bar">
          <div class="search-field">⌕ <input type="search" id="newsletter-search" placeholder="Search email…" /></div>
          <select class="select" id="newsletter-status"><option value="">All statuses</option>${["confirmed", "pending", "unsubscribed"].map((status) => `<option value="${status}">${status}</option>`).join("")}</select>
          <span class="result-count" id="newsletter-count"></span>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Email</th><th>Name</th><th>Status</th><th>Source</th><th>Joined</th><th style="text-align:right">Actions</th></tr></thead>
            <tbody id="newsletter-body"><tr><td colspan="6"><div class="empty"><strong>Loading…</strong></div></td></tr></tbody>
          </table>
        </div>
        <div class="pagination" id="newsletter-pagination"></div>
      </div>`;
    const body = $("#newsletter-body");
    async function load() {
      try {
        const result = await api.get("/admin/newsletter" + qs({ page: state.page, q: state.q, status: state.status }));
        const items = result.data || [];
        const meta = result.meta || {};
        $("#newsletter-count").textContent = `${meta.total ?? items.length} subscribers`;
        if (!items.length) {
          body.innerHTML = `<tr><td colspan="6"><div class="empty"><strong>No subscribers</strong>Sign-ups appear here.</div></td></tr>`;
        } else {
          body.innerHTML = items
            .map(
              (item) => `<tr><td class="cell-title">${esc(item.email)}</td><td>${esc(item.name || "—")}</td><td>${statusBadge(item.status)}</td><td>${esc(item.source || "—")}</td><td class="cell-nowrap">${esc(fmtDateShort(item.created_at))}</td>
                <td><div class="row-actions">${canWrite() ? `<button type="button" data-action="toggle" data-id="${item.id}" data-status="${item.status === "confirmed" ? "unsubscribed" : "confirmed"}">${item.status === "confirmed" ? "Unsubscribe" : "Confirm"}</button><button type="button" class="danger" data-action="delete" data-id="${item.id}">Delete</button>` : ""}</div></td></tr>`
            )
            .join("");
          body._items = items;
        }
        $("#newsletter-pagination").innerHTML = meta.pages
          ? `<span>Page ${meta.page} of ${meta.pages}</span><div class="pagination-actions"><button class="btn btn-ghost btn-sm" type="button" data-page="${meta.page - 1}" ${meta.has_prev ? "" : "disabled"}>Previous</button><button class="btn btn-ghost btn-sm" type="button" data-page="${meta.page + 1}" ${meta.has_next ? "" : "disabled"}>Next</button></div>`
          : "";
      } catch (error) {
        body.innerHTML = `<tr><td colspan="6"><div class="empty"><strong>Could not load subscribers</strong>${esc(error.message)}</div></td></tr>`;
      }
    }
    let timer = null;
    $("#newsletter-search").addEventListener("input", (event) => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        state.q = event.target.value.trim();
        state.page = 1;
        load();
      }, 280);
    });
    $("#newsletter-status").addEventListener("change", (event) => {
      state.status = event.target.value;
      state.page = 1;
      load();
    });
    $("#newsletter-pagination").addEventListener("click", (event) => {
      const button = event.target.closest("[data-page]");
      if (!button || button.disabled) return;
      state.page = Number(button.dataset.page);
      load();
    });
    body.addEventListener("click", async (event) => {
      const button = event.target.closest("[data-action]");
      if (!button) return;
      const item = (body._items || []).find((entry) => String(entry.id) === button.dataset.id);
      if (!item) return;
      try {
        if (button.dataset.action === "toggle") {
          await api.put(`/admin/newsletter/${item.id}`, { status: button.dataset.status });
          toast("Subscriber updated", "success");
          load();
        } else if (button.dataset.action === "delete") {
          if (!(await confirmAction(`Remove ${item.email} from the newsletter?`))) return;
          await api.del(`/admin/newsletter/${item.id}`);
          toast("Subscriber removed", "success");
          load();
        }
      } catch (error) {
        toast(error.message || "Request failed", "error");
      }
    });
    load();
  };

  /* ---------------------------------------------------------------- users */
  ROUTES.users = async function users() {
    if (!canAdmin()) {
      view.innerHTML = `<div class="empty"><strong>Administrator access required</strong>Your role cannot manage admin accounts.</div>`;
      return;
    }
    view.innerHTML = `<div class="empty"><strong>Loading users…</strong></div>`;
    const result = await api.get("/admin/users");
    const items = result.data || [];
    const roleFields = [
      { name: "name", label: "Name", full: true },
      { name: "email", label: "Email", type: "email", full: true },
      { name: "role", label: "Role", type: "select", options: [{ value: "admin", label: "Admin" }, { value: "editor", label: "Editor" }, { value: "viewer", label: "Viewer" }], allowEmpty: false },
      { name: "password", label: "Password", type: "password", hint: "Minimum 8 characters. Leave blank when editing to keep the current password." },
      { name: "is_active", label: "Account active", type: "checkbox", default: true }
    ];
    view.innerHTML = `
      <div class="view-head"><div><h1>Users</h1><p>Admin, editor and viewer accounts. Roles are enforced by the API.</p></div>
        <div class="view-actions"><button class="btn btn-primary btn-sm" type="button" id="new-user">+ New user</button></div>
      </div>
      <div class="panel">
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>User</th><th>Role</th><th>Status</th><th>Last login</th><th>Created</th><th style="text-align:right">Actions</th></tr></thead>
            <tbody>
              ${items
                .map(
                  (user) => `<tr>
                    <td><div class="cell-title">${esc(user.name)}</div><div class="cell-sub">${esc(user.email)}</div></td>
                    <td>${badge(user.role, user.role === "admin" ? "info" : user.role === "editor" ? "success" : "muted")}</td>
                    <td>${boolBadge(user.is_active, ["Active", "Disabled"], "success")}</td>
                    <td class="cell-nowrap">${esc(user.last_login_at ? fmtDateShort(user.last_login_at) : "Never")}</td>
                    <td class="cell-nowrap">${esc(fmtDateShort(user.created_at))}</td>
                    <td><div class="row-actions">
                      <button type="button" data-action="edit" data-id="${user.id}">Edit</button>
                      ${user.id === currentUser.id ? "" : `<button type="button" class="danger" data-action="delete" data-id="${user.id}">Delete</button>`}
                    </div></td>
                  </tr>`
                )
                .join("")}
            </tbody>
          </table>
        </div>
      </div>`;
    $("#new-user").addEventListener("click", () =>
      resourceForm({ title: "New user", endpoint: "/admin/users", fields: roleFields, after: users })
    );
    view.querySelector("tbody").addEventListener("click", async (event) => {
      const button = event.target.closest("[data-action]");
      if (!button) return;
      const user = items.find((entry) => String(entry.id) === button.dataset.id);
      if (!user) return;
      if (button.dataset.action === "edit") {
        const fields = roleFields.map((field) => (field.name === "password" ? { ...field, hint: "Leave blank to keep the current password." } : field));
        openModal({
          title: `Edit ${user.name}`,
          body: fieldsHtml(fields, user),
          submitLabel: "Save user",
          onSubmit: async (form) => {
            const payload = collectFields(fields, form);
            if (!payload.password) delete payload.password;
            await api.put(`/admin/users/${user.id}`, payload);
            toast("User updated", "success");
            users();
          }
        });
      } else if (button.dataset.action === "delete") {
        if (!(await confirmAction(`Delete the admin account for ${user.email}?`))) return;
        try {
          await api.del(`/admin/users/${user.id}`);
          toast("User deleted", "success");
          users();
        } catch (error) {
          toast(error.message || "Delete failed", "error");
        }
      }
    });
  };

  /* ---------------------------------------------------------------- media */
  ROUTES.media = async function media() {
    const state = { page: 1, kind: "" };
    view.innerHTML = `
      <div class="view-head"><div><h1>Media library</h1><p>Images and documents stored by the platform.</p></div></div>
      <div class="split">
        <div class="panel">
          <div class="filter-bar">
            <select class="select" id="media-kind"><option value="">All files</option><option value="image">Images</option><option value="document">Documents</option></select>
            <span class="result-count" id="media-count"></span>
          </div>
          <div class="panel-body" id="media-list"><div class="empty"><strong>Loading…</strong></div></div>
          <div class="pagination" id="media-pagination"></div>
        </div>
        <div class="panel">
          <div class="panel-head"><h2>Upload</h2><span class="note">Max 25 MB</span></div>
          <div class="panel-body">
            <form id="media-form" class="inline-form">
              <div class="form-field"><label>File</label><input type="file" name="file" required /></div>
              <div class="form-field"><label>Kind</label><select name="kind"><option value="image">Image</option><option value="document">Document (PDF)</option></select></div>
              <button class="btn btn-primary btn-sm" type="submit" ${canWrite() ? "" : "disabled"}>Upload file</button>
            </form>
            <p class="note" style="margin-top:0.8rem">Uploaded files are served from the API origin. Copy the URL into profile fields, project images or certificate records.</p>
          </div>
        </div>
      </div>`;
    const list = $("#media-list");
    async function load() {
      try {
        const result = await api.get("/admin/media" + qs({ page: state.page, kind: state.kind }));
        const items = result.data || [];
        const meta = result.meta || {};
        $("#media-count").textContent = `${meta.total ?? items.length} files`;
        list.innerHTML = items.length
          ? `<div class="media-grid">${items
              .map(
                (item) => `<div class="media-card">
                  <div class="media-thumb">${item.kind === "image" ? `<img src="${esc(assetUrl(item.url))}" alt="${esc(item.original_filename)}" loading="lazy" />` : `<span>${esc((item.mime_type || "file").split("/").pop())}</span>`}</div>
                  <div class="media-info"><strong title="${esc(item.original_filename)}">${esc(item.original_filename)}</strong><span>${esc(bytes(item.size_bytes))} · ${esc(item.kind)}</span>
                    <div class="media-actions">
                      <button type="button" data-copy="${esc(assetUrl(item.url))}">Copy URL</button>
                      <a href="${esc(assetUrl(item.url))}" target="_blank" rel="noopener">Open</a>
                      ${canWrite() ? `<button type="button" data-delete="${item.id}">Delete</button>` : ""}
                    </div>
                  </div>
                </div>`
              )
              .join("")}</div>`
          : `<div class="empty"><strong>No media yet</strong>Upload images or PDFs to use across the portfolio.</div>`;
        $("#media-pagination").innerHTML = meta.pages
          ? `<span>Page ${meta.page} of ${meta.pages}</span><div class="pagination-actions"><button class="btn btn-ghost btn-sm" type="button" data-page="${meta.page - 1}" ${meta.has_prev ? "" : "disabled"}>Previous</button><button class="btn btn-ghost btn-sm" type="button" data-page="${meta.page + 1}" ${meta.has_next ? "" : "disabled"}>Next</button></div>`
          : "";
      } catch (error) {
        list.innerHTML = `<div class="empty"><strong>Could not load media</strong>${esc(error.message)}</div>`;
      }
    }
    $("#media-kind").addEventListener("change", (event) => {
      state.kind = event.target.value;
      state.page = 1;
      load();
    });
    $("#media-pagination").addEventListener("click", (event) => {
      const button = event.target.closest("[data-page]");
      if (!button || button.disabled) return;
      state.page = Number(button.dataset.page);
      load();
    });
    list.addEventListener("click", async (event) => {
      const copy = event.target.closest("[data-copy]");
      if (copy) {
        try {
          await navigator.clipboard.writeText(copy.dataset.copy);
          toast("URL copied", "success");
        } catch (_error) {
          window.prompt("Copy this URL", copy.dataset.copy);
        }
        return;
      }
      const del = event.target.closest("[data-delete]");
      if (del) {
        if (!(await confirmAction("Delete this media file? Content referencing it will break."))) return;
        try {
          await api.del(`/admin/media/${del.dataset.delete}`);
          toast("Media deleted", "success");
          load();
        } catch (error) {
          toast(error.message || "Delete failed", "error");
        }
      }
    });
    $("#media-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.target;
      const formData = new FormData(form);
      const button = form.querySelector("button[type='submit']");
      button.disabled = true;
      try {
        await api.post("/admin/media", formData, { formData: true });
        toast("File uploaded", "success");
        form.reset();
        load();
      } catch (error) {
        toast(error.message || "Upload failed", "error");
      } finally {
        button.disabled = false;
      }
    });
    load();
  };

  /* ---------------------------------------------------------------- resumes */
  ROUTES.resumes = async function resumes() {
    view.innerHTML = `<div class="empty"><strong>Loading resumes…</strong></div>`;
    const result = await api.get("/admin/resumes");
    const items = result.data || [];
    view.innerHTML = `
      <div class="view-head"><div><h1>Resumes</h1><p>Published CV versions. The default active version powers the download button.</p></div></div>
      <div class="split">
        <div class="panel">
          <div class="panel-head"><h2>Versions</h2><span class="note">${items.length} total</span></div>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>Label</th><th>Role family</th><th>Status</th><th>Downloads</th><th style="text-align:right">Actions</th></tr></thead>
              <tbody>
                ${items.length
                  ? items
                      .map(
                        (item) => `<tr><td><div class="cell-title">${esc(item.label)}</div><div class="cell-sub">${esc(bytes(item.size_bytes))} · ${esc(item.mime_type || "PDF")}</div></td>
                        <td>${esc(item.role_family || "—")}</td>
                        <td>${boolBadge(item.is_default, ["Default", "—"], "success")} ${boolBadge(item.is_active, ["Active", "Inactive"], "success")}</td>
                        <td>${esc(item.download_count ?? 0)}</td>
                        <td><div class="row-actions">
                          <a href="${esc(assetUrl(item.file_url))}" target="_blank" rel="noopener">Open</a>
                          ${canWrite() && !item.is_default ? `<button type="button" data-default="${item.id}">Make default</button>` : ""}
                          ${canWrite() ? `<button type="button" class="danger" data-delete="${item.id}">Delete</button>` : ""}
                        </div></td></tr>`
                      )
                      .join("")
                  : `<tr><td colspan="5"><div class="empty"><strong>No resumes published</strong>Upload a PDF to enable the public CV download.</div></td></tr>`}
              </tbody>
            </table>
          </div>
        </div>
        <div class="panel">
          <div class="panel-head"><h2>Upload version</h2></div>
          <div class="panel-body">
            <form id="resume-form" class="inline-form">
              <div class="form-field"><label>Label</label><input name="label" placeholder="AI/ML resume" required /></div>
              <div class="form-field"><label>Role family</label><input name="role_family" placeholder="AI/ML, Data Science…" /></div>
              <div class="form-field"><label>PDF file</label><input type="file" name="file" accept="application/pdf" required /></div>
              <div class="form-field"><label>Notes</label><textarea name="notes" rows="2"></textarea></div>
              <div class="form-field checkbox-row"><input type="checkbox" id="resume-default" name="is_default" /><label for="resume-default">Set as default</label></div>
              <div class="form-field checkbox-row"><input type="checkbox" id="resume-active" name="is_active" checked /><label for="resume-active">Active</label></div>
              <button class="btn btn-primary btn-sm" type="submit" ${canWrite() ? "" : "disabled"}>Upload resume</button>
            </form>
          </div>
        </div>
      </div>`;
    view.onclick = async (event) => {
      const makeDefault = event.target.closest("[data-default]");
      if (makeDefault) {
        try {
          await api.put(`/admin/resumes/${makeDefault.dataset.default}`, { is_default: true });
          toast("Default resume updated", "success");
          ROUTES.resumes();
        } catch (error) {
          toast(error.message || "Update failed", "error");
        }
        return;
      }
      const del = event.target.closest("[data-delete]");
      if (del) {
        if (!(await confirmAction("Delete this resume version?"))) return;
        try {
          await api.del(`/admin/resumes/${del.dataset.delete}`);
          toast("Resume deleted", "success");
          ROUTES.resumes();
        } catch (error) {
          toast(error.message || "Delete failed", "error");
        }
      }
    };
    $("#resume-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.target;
      const formData = new FormData(form);
      formData.set("is_default", form.elements.is_default.checked ? "true" : "false");
      formData.set("is_active", form.elements.is_active.checked ? "true" : "false");
      formData.delete("notes");
      if (form.elements.notes.value) formData.set("notes", form.elements.notes.value);
      try {
        await api.post("/admin/resumes", formData, { formData: true });
        toast("Resume uploaded", "success");
        ROUTES.resumes();
      } catch (error) {
        toast(error.message || "Upload failed", "error");
      }
    });
  };

  /* ---------------------------------------------------------------- analytics */
  ROUTES.analytics = async function analytics() {
    view.innerHTML = `<div class="empty"><strong>Loading analytics…</strong></div>`;
    const result = await api.get("/admin/dashboard");
    const data = result.data || {};
    const stats = data.stats || {};
    const series = data.daily_series || [];
    const max = Math.max(1, ...series.map((row) => Math.max(row.page_views || 0, row.visitors || 0)));
    const sources = data.traffic_sources || [];
    const sourceMax = Math.max(1, ...sources.map((row) => row.count || 0));
    const popular = data.popular || {};
    view.innerHTML = `
      <div class="view-head"><div><h1>Analytics</h1><p>Privacy-conscious, first-party measurement. No third-party trackers.</p></div>
        <div class="view-actions">
          <button class="btn btn-ghost btn-sm" type="button" id="export-csv">Export CSV</button>
          <a class="btn btn-ghost btn-sm" href="#/dashboard">Overview</a>
        </div>
      </div>
      <div class="stat-grid">
        ${[
          ["Unique visitors", stats.unique_visitors_30d ?? stats.total_visitors ?? 0, "Visitor records"],
          ["Page views", stats.total_page_views || 0, "Last 30 days"],
          ["CV downloads", stats.cv_downloads || 0, "Tracked events"],
          ["GitHub clicks", stats.github_clicks_30d || 0, "Last 30 days"],
          ["Messages", stats.total_contact_messages || 0, `${stats.new_contact_messages || 0} new`],
          ["Published posts", stats.published_blog_posts || 0, `${stats.total_blog_posts || 0} total`]
        ]
          .map(([label, value, meta], index) => `<div class="stat-card ${index < 2 ? "accent" : ""}"><div class="stat-card-label">${esc(label)}</div><div class="stat-card-value">${esc(value)}</div><div class="stat-card-meta">${esc(meta)}</div></div>`)
          .join("")}
      </div>
      <div class="panel" style="margin-bottom:1rem">
        <div class="panel-head"><h2>Daily traffic</h2><div class="legend"><span><i></i>Page views</span></div></div>
        <div class="panel-body">
          ${series.length
            ? `<div class="bars">${series.map((row) => `<div class="bar" style="height:${Math.max(3, Math.round(((row.page_views || 0) / max) * 130))}px" title="${esc(row.date)} · ${row.page_views} views · ${row.visitors} visitors"></div>`).join("")}</div>
               <div class="bar-label"><span>${esc(series[0].date)}</span><span>${esc(series[series.length - 1].date)}</span></div>`
            : `<div class="empty"><strong>No data collected yet</strong>Analytics events appear after visitors browse the public site. Measurement is first-party and aggregated.</div>`}
        </div>
      </div>
      <div class="split">
        <div class="panel">
          <div class="panel-head"><h2>Top content</h2><span class="note">All time, by views</span></div>
          <div class="panel-body">
            ${["projects", "blog_posts", "certificates"]
              .flatMap((key) => (popular[key] || []).map((item) => ({ ...item, type: key.replace("_", " ") })))
              .sort((a, b) => (b.views || 0) - (a.views || 0))
              .slice(0, 8)
              .map(
                (item) => `<div class="source-row"><span class="source-name"><strong>${esc(item.title)}</strong> <span class="note">${esc(item.type)}</span></span><span class="source-value">${item.views || 0} views</span></div>`
              )
              .join("") || `<div class="empty"><strong>No content views yet</strong></div>`}
          </div>
        </div>
        <div class="panel">
          <div class="panel-head"><h2>Traffic sources</h2><span class="note">Last 30 days</span></div>
          <div class="panel-body">
            ${sources.length
              ? sources.slice(0, 8).map((row) => `<div class="source-row"><span class="source-bar" style="width:${Math.max(4, Math.round((row.count / sourceMax) * 70))}px"></span><span class="source-name">${esc(row.source)}</span><span class="source-value">${row.count}</span></div>`).join("")
              : `<div class="empty"><strong>No referrers yet</strong></div>`}
          </div>
        </div>
      </div>`;
    $("#export-csv").addEventListener("click", () =>
      api.download("/analytics/export.csv", "nexus-analytics.csv").catch((error) => toast(error.message || "Export failed", "error"))
    );
  };

  /* ---------------------------------------------------------------- github */
  ROUTES.github = async function github() {
    view.innerHTML = `<div class="empty"><strong>Loading GitHub data…</strong></div>`;
    try {
      const result = await api.get("/admin/github/overview");
      const data = result.data || {};
      const profileEntry = data.profile || {};
      const repoEntry = data.repos || {};
      const profile = profileEntry.profile || {};
      const repos = (repoEntry.repos || []).slice(0, 8);
      view.innerHTML = `
        <div class="view-head"><div><h1>GitHub</h1><p>Public repository data with a short-lived cache.</p></div>
          <div class="view-actions">${canAdmin() ? `<button class="btn btn-ghost btn-sm" type="button" id="github-refresh">Refresh cache</button>` : ""}</div>
        </div>
        <div class="split">
          <div class="panel">
            <div class="panel-head"><h2>${esc(profile.name || profile.login || "GitHub profile")}</h2><span class="note">${profile.public_repos ?? repos.length} public repos</span></div>
            <div class="panel-body">
              <div class="github-head">
                ${profile.avatar_url ? `<img class="avatar-sm" src="${esc(profile.avatar_url)}" alt="" />` : `<span class="avatar-sm text-avatar">GH</span>`}
                <div><strong>@${esc(profile.login || "prabhasha-2001")}</strong><div class="note">${esc(profile.bio || "")}</div></div>
                ${profile.html_url ? `<a class="btn btn-ghost btn-sm" href="${esc(profile.html_url)}" target="_blank" rel="noopener">Open ↗</a>` : ""}
              </div>
              <div class="github-stats"><span><strong>${profile.followers ?? 0}</strong> followers</span><span><strong>${profile.following ?? 0}</strong> following</span><span><strong>${profile.public_repos ?? 0}</strong> repos</span></div>
              <p class="note">${esc(profileEntry.error || repoEntry.error || (profileEntry.cached ? "Served from a short-lived local cache." : "Live data requires GITHUB_TOKEN; cached or fallback data may be shown."))}</p>
            </div>
          </div>
          <div class="panel">
            <div class="panel-head"><h2>Repositories</h2><span class="note">Latest activity</span></div>
            <div class="panel-body">
              ${repos.length
                ? `<div class="repo-list">${repos.map((repo) => `<a class="repo" href="${esc(repo.html_url || "#")}" target="_blank" rel="noopener"><strong>${esc(repo.name)}</strong><span>${esc(repo.language || "—")} · ★ ${repo.stargazers_count ?? 0}</span></a>`).join("")}</div>`
                : `<div class="empty"><strong>No repositories available</strong>Configure GITHUB_TOKEN to fetch live data.</div>`}
            </div>
          </div>
        </div>`;
      $("#github-refresh")?.addEventListener("click", async () => {
        try {
          await api.post("/admin/github/refresh", {});
          toast("Cache cleared", "success");
          ROUTES.github();
        } catch (error) {
          toast(error.message || "Refresh failed", "error");
        }
      });
    } catch (error) {
      view.innerHTML = `<div class="empty"><strong>GitHub unavailable</strong>${esc(error.message)}</div>`;
    }
  };

  /* ---------------------------------------------------------------- AI */
  ROUTES.ai = async function aiStudio() {
    const statusResult = await api.get("/ai/status");
    const status = statusResult.data || {};
    const kinds = [
      ["project_description", "Project description"],
      ["technical_summary", "Technical summary"],
      ["blog_draft", "Blog draft"],
      ["linkedin_post", "LinkedIn post"],
      ["certificate_description", "Certificate description"],
      ["portfolio_summary", "Portfolio summary"],
      ["resume_summary", "Resume summary"]
    ];
    view.innerHTML = `
      <div class="view-head"><div><h1>AI studio</h1><p>Grounded drafting assistance. Generated text requires human review before publishing.</p></div></div>
      <div class="panel" style="margin-bottom:1rem">
        <div class="panel-head"><h2>Runtime status</h2><a class="text-link" href="#/knowledge">Knowledge base</a></div>
        <div class="panel-body">
          <div class="ai-status">
            <span>LLM: <strong>${status.llm_configured ? esc(status.llm_provider) : "template fallback"}</strong></span>
            <span>Retrieval: <strong>${esc(status.retrieval_backend || "lexical")}</strong></span>
            <span>Documents: <strong>${esc(status.knowledge_documents ?? 0)}</strong> (${esc(status.approved_documents ?? 0)} approved)</span>
            <span>Chunks: <strong>${esc(status.indexed_chunks ?? 0)}</strong></span>
          </div>
          <p class="note" style="margin-top:0.7rem">${esc(status.behavior || "")}</p>
        </div>
      </div>
      <div class="split">
        <div class="panel">
          <div class="panel-head"><h2>Generate content</h2><span class="note">Draft only</span></div>
          <div class="panel-body">
            <form id="generate-form" class="inline-form">
              <div class="form-field"><label>Kind</label><select name="kind">${kinds.map(([value, label]) => `<option value="${value}">${label}</option>`).join("")}</select></div>
              <div class="form-field"><label>Prompt</label><textarea name="prompt" rows="4" required placeholder="Describe what to draft using verified portfolio details…"></textarea></div>
              <div class="form-field"><label>Extra context (optional)</label><textarea name="context" rows="2"></textarea></div>
              <button class="btn btn-primary btn-sm" type="submit">Generate draft</button>
            </form>
            <div class="ai-output" id="generate-output" style="margin-top:0.9rem;display:none"></div>
          </div>
        </div>
        <div class="panel">
          <div class="panel-head"><h2>Resume / job match</h2><span class="note">Keyword analysis</span></div>
          <div class="panel-body">
            <form id="analyze-form" class="inline-form">
              <div class="form-field"><label>Role family</label><input name="role_family" placeholder="AI/ML Engineer" /></div>
              <div class="form-field"><label>Job description</label><textarea name="job_description" rows="5" required placeholder="Paste the job description…"></textarea></div>
              <button class="btn btn-primary btn-sm" type="submit">Analyze fit</button>
            </form>
            <div class="ai-output" id="analyze-output" style="margin-top:0.9rem;display:none"></div>
          </div>
        </div>
      </div>
      <div class="panel" style="margin-top:1rem">
        <div class="panel-head"><h2>Recent generations</h2><span class="note">Approve before reuse</span></div>
        <div class="panel-body" id="generation-list"><div class="empty"><strong>Loading…</strong></div></div>
      </div>`;

    $("#generate-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.target;
      const output = $("#generate-output");
      try {
        const result = await api.post("/admin/ai/generate", {
          kind: form.elements.kind.value,
          prompt: form.elements.prompt.value,
          context: form.elements.context.value
        });
        output.style.display = "block";
        output.textContent = result.data?.output || "No output returned.";
        toast("Draft generated", "success");
        loadGenerations();
      } catch (error) {
        toast(error.message || "Generation failed", "error");
      }
    });

    $("#analyze-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.target;
      const output = $("#analyze-output");
      try {
        const result = await api.post("/admin/ai/resume/analyze", {
          role_family: form.elements.role_family.value || null,
          job_description: form.elements.job_description.value
        });
        output.style.display = "block";
        output.textContent = result.data?.output || "No output returned.";
        toast("Analysis complete", "success");
        loadGenerations();
      } catch (error) {
        toast(error.message || "Analysis failed", "error");
      }
    });

    async function loadGenerations() {
      const panel = $("#generation-list");
      try {
        const result = await api.get("/admin/ai/generations?per_page=8");
        const items = result.data || [];
        panel.innerHTML = items.length
          ? items
              .map(
                (item) => `<div class="knowledge-row">
                  <div class="knowledge-main"><strong>${esc(item.kind.replace(/_/g, " "))}</strong><span>${esc(truncate(item.prompt, 100))} · ${esc(fmtDateShort(item.created_at))}</span></div>
                  ${statusBadge(item.status)}
                  <div class="row-actions">
                    <button type="button" data-view="${item.id}">View</button>
                    ${canWrite() && item.status === "draft" ? `<button type="button" data-review="approved" data-id="${item.id}">Approve</button><button type="button" class="danger" data-review="rejected" data-id="${item.id}">Reject</button>` : ""}
                  </div>
                </div>`
              )
              .join("")
          : `<div class="empty"><strong>No generations yet</strong>Draft content will appear here.</div>`;
        panel._items = items;
      } catch (error) {
        panel.innerHTML = `<div class="empty"><strong>Could not load generations</strong>${esc(error.message)}</div>`;
      }
    }
    view.onclick = async (event) => {
      const review = event.target.closest("[data-review]");
      if (review) {
        try {
          await api.put(`/admin/ai/generations/${review.dataset.id}/review`, { status: review.dataset.review });
          toast("Review recorded", "success");
          loadGenerations();
        } catch (error) {
          toast(error.message || "Review failed", "error");
        }
        return;
      }
      const viewButton = event.target.closest("[data-view]");
      if (viewButton) {
        const result = await api.get("/admin/ai/generations?per_page=50");
        const item = (result.data || []).find((entry) => String(entry.id) === viewButton.dataset.view);
        if (item) {
          openModal({
            title: item.kind.replace(/_/g, " "),
            wide: true,
            hideSubmit: true,
            body: `<p class="note">Prompt</p><div class="ai-output" style="max-height:120px;margin-bottom:0.8rem">${esc(item.prompt)}</div><p class="note">Output</p><div class="ai-output" style="max-height:360px">${esc(item.output)}</div>`
          });
        }
      }
    };
    loadGenerations();
  };

  ROUTES.knowledge = async function knowledge() {
    view.innerHTML = `<div class="empty"><strong>Loading knowledge base…</strong></div>`;
    const statusResult = await api.get("/ai/status");
    const status = statusResult.data || {};
    view.innerHTML = `
      <div class="view-head"><div><h1>Knowledge base</h1><p>Approved documents ground every AI answer. Upload, review, then approve.</p></div>
        <div class="view-actions">${canAdmin() ? `<button class="btn btn-ghost btn-sm" type="button" id="rebuild-index">Rebuild index</button>` : ""}</div>
      </div>
      <div class="split">
        <div class="panel">
          <div class="panel-head"><h2>Documents</h2><span class="note">${esc(status.knowledge_documents ?? 0)} total · ${esc(status.approved_documents ?? 0)} approved</span></div>
          <div class="panel-body" id="knowledge-list"><div class="empty"><strong>Loading…</strong></div></div>
        </div>
        <div class="panel">
          <div class="panel-head"><h2>Upload document</h2><span class="note">PDF, MD, TXT</span></div>
          <div class="panel-body">
            <form id="knowledge-form" class="inline-form">
              <div class="form-field"><label>Title</label><input name="title" placeholder="Research summary" /></div>
              <div class="form-field"><label>File</label><input type="file" name="file" accept=".pdf,.txt,.md,.markdown" required /></div>
              <button class="btn btn-primary btn-sm" type="submit">Upload & index</button>
            </form>
            <p class="note" style="margin-top:0.8rem">Documents remain unapproved until an administrator reviews them. Only approved content is used for answers.</p>
          </div>
        </div>
      </div>`;
    async function load() {
      const panel = $("#knowledge-list");
      try {
        const result = await api.get("/admin/ai/knowledge?per_page=50");
        const items = result.data || [];
        panel.innerHTML = items.length
          ? items
              .map(
                (item) => `<div class="knowledge-row">
                  <div class="knowledge-main"><strong>${esc(item.title)}</strong><span>${esc(bytes(item.size_bytes))} · ${esc(item.chunk_count)} chunks · ${esc(fmtDateShort(item.created_at))}</span></div>
                  ${statusBadge(item.status)}
                  ${boolBadge(item.is_approved, ["Approved", "Pending"], "success")}
                  <div class="row-actions">
                    ${canAdmin() ? `<button type="button" data-approve="${item.id}" data-value="${item.is_approved ? "false" : "true"}">${item.is_approved ? "Unapprove" : "Approve"}</button>` : ""}
                    ${canWrite() ? `<button type="button" class="danger" data-delete="${item.id}">Delete</button>` : ""}
                  </div>
                </div>`
              )
              .join("")
          : `<div class="empty"><strong>No documents</strong>Upload reference material to ground the assistant.</div>`;
      } catch (error) {
        panel.innerHTML = `<div class="empty"><strong>Could not load documents</strong>${esc(error.message)}</div>`;
      }
    }
    $("#knowledge-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.target;
      const formData = new FormData(form);
      try {
        await api.post("/admin/ai/knowledge", formData, { formData: true });
        toast("Document indexed", "success");
        form.reset();
        load();
      } catch (error) {
        toast(error.message || "Upload failed", "error");
      }
    });
    $("#rebuild-index")?.addEventListener("click", async () => {
      try {
        await api.post("/admin/ai/knowledge/rebuild", {});
        toast("Index rebuilt", "success");
        load();
      } catch (error) {
        toast(error.message || "Rebuild failed", "error");
      }
    });
    view.onclick = async (event) => {
      const approve = event.target.closest("[data-approve]");
      if (approve) {
        try {
          await api.post(`/admin/ai/knowledge/${approve.dataset.approve}/approve`, { is_approved: approve.dataset.value === "true" });
          toast("Approval updated", "success");
          load();
        } catch (error) {
          toast(error.message || "Update failed", "error");
        }
        return;
      }
      const del = event.target.closest("[data-delete]");
      if (del) {
        if (!(await confirmAction("Delete this knowledge document and its chunks?"))) return;
        try {
          await api.del(`/admin/ai/knowledge/${del.dataset.delete}`);
          toast("Document deleted", "success");
          load();
        } catch (error) {
          toast(error.message || "Delete failed", "error");
        }
      }
    };
    load();
  };

  ROUTES.conversations = async function conversations() {
    view.innerHTML = `<div class="empty"><strong>Loading conversations…</strong></div>`;
    const result = await api.get("/admin/ai/conversations?per_page=30");
    const items = result.data || [];
    view.innerHTML = `
      <div class="view-head"><div><h1>Conversations</h1><p>Public assistant sessions. Review what visitors ask and how answers were grounded.</p></div></div>
      <div class="panel">
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Session</th><th>Channel</th><th>Messages</th><th>Started</th><th>Updated</th><th style="text-align:right">Actions</th></tr></thead>
            <tbody>
              ${items.length
                ? items
                    .map(
                      (item) => `<tr><td><div class="cell-title">${esc(item.title || "Untitled conversation")}</div><div class="cell-sub mono">${esc(item.session_id)}</div></td>
                      <td>${esc(item.channel)}</td><td>${esc(item.message_count ?? 0)}</td>
                      <td class="cell-nowrap">${esc(fmtDateShort(item.created_at))}</td><td class="cell-nowrap">${esc(fmtDateShort(item.updated_at))}</td>
                      <td><div class="row-actions"><button type="button" data-open="${item.id}">Open</button></div></td></tr>`
                    )
                    .join("")
                : `<tr><td colspan="6"><div class="empty"><strong>No conversations yet</strong>Public chat sessions appear here.</div></td></tr>`}
            </tbody>
          </table>
        </div>
      </div>`;
    view.querySelector("tbody").addEventListener("click", async (event) => {
      const button = event.target.closest("[data-open]");
      if (!button) return;
      try {
        const detail = await api.get(`/admin/ai/conversations/${button.dataset.open}`);
        const data = detail.data || {};
        openModal({
          title: data.title || "Conversation",
          wide: true,
          hideSubmit: true,
          body: `<div style="display:flex;flex-direction:column;gap:0.6rem;max-height:60vh;overflow-y:auto">
            ${(data.messages || [])
              .map(
                (message) => `<div class="chat-bubble ${esc(message.role)}" style="max-width:100%">${esc(message.content)}${(message.sources || []).length ? `<div class="chat-sources">${message.sources.map((source) => `<span class="chat-source">${esc(source.title || source.source || "source")}</span>`).join("")}</div>` : ""}</div>`
              )
              .join("")}
          </div>`
        });
      } catch (error) {
        toast(error.message || "Could not load conversation", "error");
      }
    });
  };

  /* ---------------------------------------------------------------- automation */
  ROUTES.automation = async function automation() {
    view.innerHTML = `<div class="empty"><strong>Loading automation…</strong></div>`;
    const result = await api.get("/admin/automation/workflows");
    const workflows = result.data || [];
    const logsResult = await api.get("/admin/automation/logs?per_page=12");
    const logs = logsResult.data || [];
    const fields = [
      { name: "name", label: "Workflow name", full: true },
      { name: "event_key", label: "Event key", placeholder: "project.created" },
      { name: "description", label: "Description", type: "textarea", full: true, rows: 2 },
      { name: "webhook_url", label: "n8n webhook URL", type: "url", full: true },
      { name: "is_enabled", label: "Enabled", type: "checkbox" }
    ];
    view.innerHTML = `
      <div class="view-head"><div><h1>Automation</h1><p>n8n workflows triggered by platform events. Dispatch is skipped when unconfigured.</p></div>
        <div class="view-actions">${canAdmin() ? `<button class="btn btn-primary btn-sm" type="button" id="new-workflow">+ New workflow</button>` : ""}</div>
      </div>
      <div class="split">
        <div class="panel">
          <div class="panel-head"><h2>Workflows</h2><span class="note">${workflows.length} configured</span></div>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>Workflow</th><th>Event</th><th>State</th><th>Last run</th><th style="text-align:right">Actions</th></tr></thead>
              <tbody>
                ${workflows.length
                  ? workflows
                      .map(
                        (workflow) => `<tr><td><div class="cell-title">${esc(workflow.name)}</div><div class="cell-sub">${esc(workflow.description || workflow.slug)}</div></td>
                        <td class="mono">${esc(workflow.event_key)}</td>
                        <td>${boolBadge(workflow.is_enabled, ["Enabled", "Disabled"], "success")}${workflow.last_status ? ` ${statusBadge(workflow.last_status)}` : ""}</td>
                        <td class="cell-nowrap">${esc(workflow.last_run_at ? fmtDateShort(workflow.last_run_at) : "Never")}</td>
                        <td><div class="row-actions">
                          ${canAdmin() ? `<button type="button" data-test="${workflow.id}">Test</button><button type="button" data-edit="${workflow.id}">Edit</button><button type="button" class="danger" data-delete="${workflow.id}">Delete</button>` : ""}
                        </div></td></tr>`
                      )
                      .join("")
                  : `<tr><td colspan="5"><div class="empty"><strong>No workflows</strong>Create one to connect n8n.</div></td></tr>`}
              </tbody>
            </table>
          </div>
        </div>
        <div class="panel">
          <div class="panel-head"><h2>Recent runs</h2><span class="note">Last 12</span></div>
          <div class="panel-body">
            ${logs.length
              ? `<ul class="activity-list" style="margin:-1.1rem">${logs
                  .map(
                    (log) => `<li><span class="activity-dot"></span><div class="activity-main"><strong>${esc(log.event_key)}</strong><span>${esc(log.error_message || log.response_code || log.status)} · ${esc(log.duration_ms ?? 0)} ms</span></div><time>${esc(fmtDateShort(log.created_at))}</time></li>`
                  )
                  .join("")}</ul>`
              : `<div class="empty"><strong>No runs recorded</strong>Test a workflow or trigger a platform event.</div>`}
          </div>
        </div>
      </div>`;
    $("#new-workflow")?.addEventListener("click", () =>
      resourceForm({ title: "New workflow", endpoint: "/admin/automation/workflows", fields, after: automation })
    );
    view.onclick = async (event) => {
      const test = event.target.closest("[data-test]");
      if (test) {
        try {
          const result = await api.post(`/admin/automation/workflows/${test.dataset.test}/test`, {});
          const data = result.data || {};
          toast(`Test finished: ${data.status || "ok"}`, data.status === "success" ? "success" : "warning");
          ROUTES.automation();
        } catch (error) {
          toast(error.message || "Test failed", "error");
        }
        return;
      }
      const edit = event.target.closest("[data-edit]");
      if (edit) {
        const workflow = workflows.find((entry) => String(entry.id) === edit.dataset.edit);
        resourceForm({ title: "Edit workflow", endpoint: "/admin/automation/workflows", fields, item: workflow, after: automation });
        return;
      }
      const del = event.target.closest("[data-delete]");
      if (del) {
        if (!(await confirmAction("Delete this automation workflow?"))) return;
        try {
          await api.del(`/admin/automation/workflows/${del.dataset.delete}`);
          toast("Workflow deleted", "success");
          ROUTES.automation();
        } catch (error) {
          toast(error.message || "Delete failed", "error");
        }
      }
    };
  };

  /* ---------------------------------------------------------------- activity */
  ROUTES.activity = async function activity() {
    view.innerHTML = `<div class="empty"><strong>Loading activity logs…</strong></div>`;
    const result = await api.get("/admin/activity-logs?per_page=50");
    const items = result.data || [];
    const meta = result.meta || {};
    view.innerHTML = `
      <div class="view-head"><div><h1>Activity logs</h1><p>Immutable audit trail of administrative actions.</p></div></div>
      <div class="panel">
        <div class="filter-bar"><span class="note">Showing latest ${items.length} of ${meta.total ?? items.length}</span></div>
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Action</th><th>Entity</th><th>User</th><th>Metadata</th><th>When</th></tr></thead>
            <tbody>
              ${items.length
                ? items
                    .map(
                      (item) => `<tr><td class="cell-title mono">${esc(item.action)}</td><td>${esc(item.entity_type || "—")}${item.entity_id ? ` #${esc(item.entity_id)}` : ""}</td><td>${esc(item.user_name || "System")}</td><td class="mono">${esc(truncate(JSON.stringify(item.metadata || {}), 80))}</td><td class="cell-nowrap">${esc(fmtDateShort(item.created_at))}</td></tr>`
                    )
                    .join("")
                : `<tr><td colspan="5"><div class="empty"><strong>No activity yet</strong>Admin actions are recorded here.</div></td></tr>`}
            </tbody>
          </table>
        </div>
      </div>`;
  };

  /* ---------------------------------------------------------------- settings */
  ROUTES.settings = async function settings() {
    if (!canAdmin()) {
      view.innerHTML = `<div class="empty"><strong>Administrator access required</strong>Only admins can change system settings.</div>`;
      return;
    }
    view.innerHTML = `<div class="empty"><strong>Loading settings…</strong></div>`;
    const result = await api.get("/admin/settings");
    const items = result.data || [];
    view.innerHTML = `
      <div class="view-head"><div><h1>Settings</h1><p>Key/value configuration stored in the database. Values are JSON.</p></div></div>
      <div class="panel">
        <div class="panel-head"><h2>System settings</h2><span class="note">${items.length} keys</span></div>
        <div class="panel-body">
          <form id="settings-form" class="inline-form">
            <div class="form-error" id="settings-error"></div>
            ${items
              .map(
                (item, index) => `<div class="field-grid" style="align-items:start;padding-bottom:0.8rem;border-bottom:1px solid var(--line)">
                  <div class="form-field"><label>${esc(item.key)}</label><span class="hint">Category: ${esc(item.category)} · public: ${item.is_public ? "yes" : "no"}</span></div>
                  <div class="form-field"><textarea class="code" name="setting-${index}" rows="2">${esc(JSON.stringify(item.value, null, 2))}</textarea></div>
                </div>`
              )
              .join("") || `<div class="empty"><strong>No settings stored</strong>Seed the database or add keys below.</div>`}
            <div class="field-grid" style="margin-top:0.8rem">
              <div class="form-field"><label>New key</label><input name="new-key" placeholder="feature_flag" /></div>
              <div class="form-field"><label>New value (JSON)</label><input name="new-value" placeholder="true" /></div>
              <div class="form-field"><label>Category</label><input name="new-category" placeholder="general" /></div>
            </div>
            <div style="display:flex;justify-content:flex-end"><button class="btn btn-primary btn-sm" type="submit">Save settings</button></div>
          </form>
        </div>
      </div>`;
    const form = $("#settings-form");
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const errorBox = $("#settings-error");
      errorBox.classList.remove("show");
      try {
        const payload = {};
        items.forEach((item, index) => {
          const raw = form.elements[`setting-${index}`].value;
          try {
            payload[item.key] = JSON.parse(raw);
          } catch (_error) {
            throw new Error(`Setting “${item.key}” contains invalid JSON.`);
          }
        });
        const newKey = form.elements["new-key"].value.trim();
        if (newKey) {
          const rawValue = form.elements["new-value"].value.trim() || "null";
          try {
            payload[newKey] = JSON.parse(rawValue);
          } catch (_error) {
            throw new Error("New setting value is not valid JSON.");
          }
        }
        await api.put("/admin/settings", { settings: payload, category: form.elements["new-category"].value.trim() || "general" });
        toast("Settings saved", "success");
        ROUTES.settings();
      } catch (error) {
        errorBox.textContent = error.message || "Unable to save settings";
        errorBox.classList.add("show");
      }
    });
  };

  /* ---------------------------------------------------------------- backups */
  ROUTES.backups = async function backups() {
    if (!canAdmin()) {
      view.innerHTML = `<div class="empty"><strong>Administrator access required</strong>Backups are restricted to admins.</div>`;
      return;
    }
    view.innerHTML = `<div class="empty"><strong>Loading backups…</strong></div>`;
    const result = await api.get("/admin/backups");
    const items = result.data || [];
    view.innerHTML = `
      <div class="view-head"><div><h1>Backups</h1><p>Database snapshots stored on the server. Download and keep a secure copy.</p></div>
        <div class="view-actions"><button class="btn btn-primary btn-sm" type="button" id="create-backup">Create backup</button></div>
      </div>
      <div class="panel">
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Filename</th><th>Size</th><th>Created</th><th style="text-align:right">Actions</th></tr></thead>
            <tbody>
              ${items.length
                ? items
                    .map(
                      (item) => `<tr><td class="mono">${esc(item.filename)}</td><td>${esc(bytes(item.size_bytes))}</td><td class="cell-nowrap">${esc(fmtDateShort(item.created_at))}</td>
                      <td><div class="row-actions"><button type="button" data-download="${esc(item.filename)}">Download</button></div></td></tr>`
                    )
                    .join("")
                : `<tr><td colspan="4"><div class="empty"><strong>No backups yet</strong>Create the first snapshot.</div></td></tr>`}
            </tbody>
          </table>
        </div>
      </div>`;
    $("#create-backup").addEventListener("click", async () => {
      try {
        await api.post("/admin/backups", {});
        toast("Backup created", "success");
        ROUTES.backups();
      } catch (error) {
        toast(error.message || "Backup failed", "error");
      }
    });
    view.querySelector("tbody").addEventListener("click", async (event) => {
      const button = event.target.closest("[data-download]");
      if (!button) return;
      try {
        await api.download(`/admin/backups/${encodeURIComponent(button.dataset.download)}`, button.dataset.download);
      } catch (error) {
        toast(error.message || "Download failed", "error");
      }
    });
  };

  ROUTES.notfound = async function notFound() {
    view.innerHTML = `<div class="empty"><strong>View not found</strong>Use the navigation to continue.</div>`;
  };

  /* ---------------------------------------------------------------- login / boot */
  $("#login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.target;
    const button = $("#login-submit");
    const errorBox = $("#login-error");
    errorBox.hidden = true;
    button.disabled = true;
    try {
      const data = await api.login(form.elements.email.value.trim(), form.elements.password.value);
      currentUser = data.user;
      toast(`Welcome back, ${currentUser.name.split(" ")[0]}`, "success");
      await showApp();
    } catch (error) {
      errorBox.textContent = error.message || "Sign-in failed";
      errorBox.hidden = false;
      button.disabled = false;
    }
  });

  $("#sign-out").addEventListener("click", async () => {
    await api.logout();
    currentUser = null;
    showLogin();
    toast("Signed out", "success");
  });

  $("#theme-toggle").addEventListener("click", () => {
    ui.applyTheme(document.documentElement.dataset.theme === "light" ? "dark" : "light");
  });

  $("#refresh-view").addEventListener("click", () => navigate());

  $("#mobile-menu").addEventListener("click", () => {
    $("#sidebar").classList.toggle("open");
    $("#sidebar-scrim").classList.toggle("open");
  });
  $("#sidebar-scrim").addEventListener("click", () => {
    $("#sidebar").classList.remove("open");
    $("#sidebar-scrim").classList.remove("open");
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && modalRoot.classList.contains("open")) closeModal();
  });
  window.addEventListener("hashchange", () => {
    if (!$("#app-view").hidden) navigate();
  });
  window.addEventListener("nexus:unauthorized", () => {
    currentUser = null;
    showLogin();
    toast("Session expired — sign in again", "warning");
  });

  modalRoot.addEventListener("click", (event) => {
    if (event.target.classList.contains("modal-backdrop")) closeModal();
  });

  async function boot() {
    ui.initTheme();
    if (!api.token()) {
      showLogin();
      return;
    }
    try {
      const result = await api.get("/auth/me", { auth: true });
      currentUser = result.data;
      await showApp();
    } catch (_error) {
      api.clearSession();
      showLogin();
    }
  }

  boot();
})();
