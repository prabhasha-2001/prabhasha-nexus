(function () {
  const api = window.nexusApi;
  const ui = window.nexusUI;
  const { $, escapeHtml, formatDate, markdown, emptyState, errorState, tagList, truncate } = ui;

  const query = new URLSearchParams(window.location.search);

  function projectCard(project, featured = false) {
    return `
      <article class="card project-card ${featured ? "featured" : ""}">
        <a class="card-cover" href="project.html?slug=${encodeURIComponent(project.slug)}" aria-label="${escapeHtml(project.title)}">
          ${project.thumbnail_url ? `<img src="${escapeHtml(project.thumbnail_url)}" alt="" loading="lazy" />` : `<span class="cover-glyph">${escapeHtml(ui.initials(project.title))}</span>`}
          <span class="card-badge">${escapeHtml(project.project_type || project.category?.name || "Project")}</span>
        </a>
        <div class="card-body">
          <h3><a href="project.html?slug=${encodeURIComponent(project.slug)}">${escapeHtml(project.title)}</a></h3>
          <p class="muted">${escapeHtml(truncate(project.short_description, 150))}</p>
          <div class="tag-row">${tagList((project.technologies || []).slice(0, 5))}</div>
          <div class="card-foot">
            <span class="muted small">${project.metrics?.length ? escapeHtml(`${project.metrics.length} measured metric${project.metrics.length > 1 ? "s" : ""}`) : "Case study"}</span>
            <a class="text-link" href="project.html?slug=${encodeURIComponent(project.slug)}">Read case study →</a>
          </div>
        </div>
      </article>`;
  }

  function metricGrid(metrics) {
    if (!metrics || !metrics.length) return "";
    return `<div class="metric-grid">${metrics
      .map(
        (metric) => `<div class="metric-card"><span class="metric-value">${escapeHtml(metric.value)}${metric.unit ? `<small>${escapeHtml(metric.unit)}</small>` : ""}</span><span class="metric-name">${escapeHtml(metric.name)}</span>${metric.evaluation_run ? `<span class="metric-meta">run: ${escapeHtml(metric.evaluation_run)}</span>` : ""}</div>`
      )
      .join("")}</div>`;
  }

  function skillGroups(categories) {
    const groups = (categories || [])
      .map((category) => ({ ...category, skills: (category.skills || []).filter((skill) => skill.is_visible) }))
      .filter((category) => category.skills.length);
    if (!groups.length) return emptyState("Skills are being curated", "Verified skills will appear once published.");
    return `<div class="skill-groups">${groups
      .map(
        (category) => `<div class="skill-group"><h3>${escapeHtml(category.name)}</h3><div class="chip-row">${category.skills
          .map((skill) => `<span class="chip ${skill.is_featured ? "chip-accent" : ""}">${escapeHtml(skill.name)}</span>`)
          .join("")}</div></div>`
      )
      .join("")}</div>`;
  }

  async function safeGet(path) {
    try {
      const result = await api.get(path);
      return result.data;
    } catch (_error) {
      return null;
    }
  }

  async function renderHome(profile) {
    const [projects, research, skills, education, certificates] = await Promise.all([
      safeGet("/projects?per_page=100"),
      safeGet("/research?per_page=50"),
      safeGet("/skills"),
      safeGet("/education"),
      safeGet("/certificates?per_page=10")
    ]);
    const name = profile?.full_name || "Prabhasha Dilshani";
    const featured = (projects || []).filter((project) => project.featured).slice(0, 3);
    const list = featured.length ? featured : (projects || []).slice(0, 3);
    const skillCount = (skills || []).reduce(
      (total, category) => total + (category.skills || []).filter((skill) => skill.is_visible).length,
      0
    );

    $("#hero-name").textContent = name;
    $("#hero-title").textContent = profile?.professional_title || "AI/ML · Data Science · Software Engineering";
    $("#hero-summary").textContent = profile?.summary || "";
    $("#hero-location").textContent = profile?.location || "Sri Lanka";
    $("#hero-avatar").textContent = ui.initials(name);
    $("#stat-projects").textContent = String((projects || []).length).padStart(2, "0");
    $("#stat-research").textContent = String((research || []).length).padStart(2, "0");
    $("#stat-skills").textContent = String(skillCount).padStart(2, "0");
    $("#stat-education").textContent = String((education || []).length).padStart(2, "0");

    const featuredContainer = $("#featured-projects");
    featuredContainer.innerHTML = list.length ? list.map((project) => projectCard(project, true)).join("") : emptyState("Projects are on the way", "Published case studies will appear here.");

    const researchContainer = $("#research-spotlight");
    const spotlight = (research || [])[0];
    researchContainer.innerHTML = spotlight
      ? `<article class="spotlight-card">
          <span class="eyebrow">Research spotlight</span>
          <h3>${escapeHtml(spotlight.title)}</h3>
          <p class="muted">${escapeHtml(truncate(spotlight.abstract, 280))}</p>
          <div class="spotlight-meta">
            ${spotlight.sample_size ? `<span><strong>${escapeHtml(spotlight.sample_size)}</strong> respondents</span>` : ""}
            ${spotlight.institutions_count ? `<span><strong>${escapeHtml(spotlight.institutions_count)}</strong> institutions</span>` : ""}
            ${spotlight.publication_status ? `<span>${escapeHtml(spotlight.publication_status)}</span>` : ""}
          </div>
          <a class="text-link" href="research.html?slug=${encodeURIComponent(spotlight.slug)}">Explore the study →</a>
        </article>`
      : emptyState("Research updates soon", "Academic work will be published here once available.");

    $("#home-skills").innerHTML = skillGroups(skills);
    $("#home-certificates").innerHTML = (certificates || []).length
      ? `<div class="chip-row">${(certificates || []).slice(0, 8).map((item) => `<span class="chip">${escapeHtml(item.title)}</span>`).join("")}</div>`
      : `<p class="muted">No certificates have been published yet. Credentials are added only after verification.</p>`;
  }

  async function renderAbout(profile) {
    $("#about-intro").textContent = profile?.about || profile?.summary || "";
    $("#about-goals").textContent = profile?.career_goals || "";
    $("#about-avatar").textContent = ui.initials(profile?.full_name);
    $("#about-name").textContent = profile?.full_name || "";
    $("#about-title").textContent = profile?.professional_title || "";
    $("#about-location").textContent = profile?.location || "";
    $("#about-email").href = `mailto:${profile?.email || ""}`;
    $("#about-email").textContent = profile?.email || "";
    $("#about-phone").href = `tel:${profile?.phone || ""}`;
    $("#about-phone").textContent = profile?.phone || "";
    $("#about-github").href = profile?.github_url || "#";
    $("#about-linkedin").href = profile?.linkedin_url || "#";
    $("#about-interests").innerHTML = (profile?.interests || []).map((item) => `<span class="chip chip-accent">${escapeHtml(item)}</span>`).join("");
    $("#about-languages").innerHTML = (profile?.languages || []).map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join("");

    const [education, experience, achievements, skills] = await Promise.all([
      safeGet("/education"),
      safeGet("/experience"),
      safeGet("/achievements"),
      safeGet("/skills")
    ]);

    $("#education-timeline").innerHTML = (education || []).length
      ? `<div class="timeline">${education
          .map(
            (item) => `<div class="timeline-item">
              <span class="timeline-dot"></span>
              <div class="timeline-head"><strong>${escapeHtml(item.qualification)}</strong><span>${escapeHtml([item.start_year, item.end_year].filter(Boolean).join(" – "))}</span></div>
              <p>${escapeHtml(item.institution)}${item.grade ? ` · ${escapeHtml(item.grade)}` : ""}</p>
              ${item.description ? `<p class="muted">${escapeHtml(item.description)}</p>` : ""}
            </div>`
          )
          .join("")}</div>`
      : emptyState("Education details coming soon", "Verified qualifications will be listed here.");

    $("#experience-list").innerHTML = (experience || []).length
      ? (experience || [])
          .map(
            (item) => `<article class="card compact"><h3>${escapeHtml(item.role)}</h3><p class="muted">${escapeHtml(item.organization)} · ${escapeHtml([item.start_date, item.end_date].filter(Boolean).join(" – ") || "Dates pending")}</p><p>${escapeHtml(item.description || "")}</p></article>`
          )
          .join("")
      : `<p class="muted">No professional experience entries have been published yet. This section is reserved for verified roles only.</p>`;

    $("#achievements-list").innerHTML = (achievements || []).length
      ? (achievements || [])
          .map(
            (item) => `<article class="card compact"><h3>${escapeHtml(item.title)}</h3><p class="muted">${escapeHtml([item.issuer, formatDate(item.date)].filter(Boolean).join(" · "))}</p><p>${escapeHtml(item.description || "")}</p></article>`
          )
          .join("")
      : `<p class="muted">No achievements have been published yet. Only verified items will be added.</p>`;

    $("#about-skills").innerHTML = skillGroups(skills);
    loadGithub();
  }

  async function loadGithub() {
    const container = $("#github-panel");
    if (!container) return;
    container.innerHTML = `<div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line"></div>`;
    try {
      const [profile, repos] = await Promise.all([safeGet("/github/profile"), safeGet("/github/repos")]);
      if (!profile?.profile) {
        container.innerHTML = `<p class="muted">GitHub data is temporarily unavailable. Visit <a href="https://github.com/prabhasha-2001" target="_blank" rel="noopener">github.com/prabhasha-2001</a>.</p>`;
        return;
      }
      const user = profile.profile;
      const repoList = (repos?.repos || []).slice(0, 4);
      container.innerHTML = `
        <div class="github-head">
          ${user.avatar_url ? `<img class="avatar-sm" src="${escapeHtml(user.avatar_url)}" alt="" />` : `<span class="avatar-sm text-avatar">${escapeHtml(ui.initials(user.login))}</span>`}
          <div><strong>${escapeHtml(user.name || user.login || "GitHub")}</strong><p class="muted small">@${escapeHtml(user.login || "prabhasha-2001")}</p></div>
          <a class="btn btn-ghost btn-sm" href="${escapeHtml(user.html_url || "https://github.com/prabhasha-2001")}" target="_blank" rel="noopener">Follow ↗</a>
        </div>
        ${user.bio ? `<p class="muted">${escapeHtml(user.bio)}</p>` : ""}
        <div class="github-stats">
          <span><strong>${escapeHtml(user.public_repos ?? "—")}</strong> repositories</span>
          <span><strong>${escapeHtml(user.followers ?? "—")}</strong> followers</span>
          <span><strong>${escapeHtml(user.following ?? "—")}</strong> following</span>
        </div>
        ${repoList.length ? `<div class="repo-list">${repoList.map((repo) => `<a class="repo" href="${escapeHtml(repo.html_url)}" target="_blank" rel="noopener"><strong>${escapeHtml(repo.name)}</strong><span>${escapeHtml(repo.language || "Code")} · ★ ${escapeHtml(repo.stargazers_count ?? 0)}</span></a>`).join("")}</div>` : ""}`;
    } catch (_error) {
      container.innerHTML = `<p class="muted">GitHub is unavailable right now.</p>`;
    }
  }

  async function renderProjects() {
    const grid = $("#projects-grid");
    grid.innerHTML = ui.skeletonCards(4);
    const [projects, categories] = await Promise.all([
      safeGet("/projects?per_page=100"),
      safeGet("/projects/categories")
    ]);
    const all = projects || [];
    const filter = $("#project-filter");
    const search = $("#project-search");
    filter.innerHTML = `<option value="">All categories</option>${(categories || [])
      .map((category) => `<option value="${escapeHtml(category.slug)}">${escapeHtml(category.name)}</option>`)
      .join("")}`;
    const paint = () => {
      const term = search.value.trim().toLowerCase();
      const category = filter.value;
      const filtered = all.filter((project) => {
        const matchesCategory = !category || project.category?.slug === category;
        const haystack = `${project.title} ${project.short_description} ${(project.technologies || []).join(" ")}`.toLowerCase();
        return matchesCategory && (!term || haystack.includes(term));
      });
      $("#projects-count").textContent = `${filtered.length} project${filtered.length === 1 ? "" : "s"}`;
      grid.innerHTML = filtered.length
        ? filtered.map((project) => projectCard(project)).join("")
        : emptyState("No matching projects", "Try a different search term or category.");
    };
    search.addEventListener("input", paint);
    filter.addEventListener("change", paint);
    paint();
  }

  async function renderProjectDetail() {
    const slug = query.get("slug");
    const root = $("#project-root");
    if (!slug) {
      errorState(root, "No project was selected.", () => (window.location.href = "projects.html"));
      return;
    }
    try {
      const project = (await api.get(`/projects/${encodeURIComponent(slug)}`)).data;
      const related = (await safeGet("/projects?per_page=100")) || [];
      const sections = [
        ["Problem", project.problem_statement],
        ["Solution", project.solution],
        ["Architecture", project.architecture],
        ["Implementation", project.implementation],
        ["Challenges", project.challenges],
        ["Future improvements", project.future_improvements],
        ["Dataset", project.dataset_info]
      ].filter(([, value]) => value);
      document.title = `${project.title} · Prabhasha Nexus`;
      root.innerHTML = `
        <a class="back-link" href="projects.html">← All projects</a>
        <header class="detail-head">
          <span class="eyebrow">${escapeHtml(project.project_type || project.category?.name || "Case study")}</span>
          <h1>${escapeHtml(project.title)}</h1>
          <p class="lead">${escapeHtml(project.short_description)}</p>
          <div class="tag-row">${tagList(project.technologies, "chip")}</div>
          <div class="detail-actions">
            ${project.github_url ? `<a class="btn btn-primary" href="${escapeHtml(project.github_url)}" target="_blank" rel="noopener">View code ↗</a>` : ""}
            ${project.live_url ? `<a class="btn btn-ghost" href="${escapeHtml(project.live_url)}" target="_blank" rel="noopener">Live demo ↗</a>` : ""}
            ${project.docs_url ? `<a class="btn btn-ghost" href="${escapeHtml(project.docs_url)}" target="_blank" rel="noopener">Documentation ↗</a>` : ""}
            <span class="muted small">${project.views || 0} views · published ${formatDate(project.published_at)}</span>
          </div>
        </header>
        ${metricGrid(project.metrics)}
        ${project.description ? `<section class="prose card"><h2>Overview</h2>${markdown(project.description)}</section>` : ""}
        ${sections.length ? `<div class="detail-grid">${sections.map(([title, value]) => `<section class="card prose"><h2>${escapeHtml(title)}</h2>${markdown(value)}</section>`).join("")}</div>` : ""}
        ${(project.images || []).length ? `<section class="gallery">${project.images.map((image) => `<figure><img src="${escapeHtml(image.url)}" alt="${escapeHtml(image.caption || project.title)}" loading="lazy" /><figcaption>${escapeHtml(image.caption || "")}</figcaption></figure>`).join("")}</section>` : ""}
        <section class="related">
          <div class="section-head"><h2>More case studies</h2><a class="text-link" href="projects.html">Browse all →</a></div>
          <div class="grid grid-3">${related.filter((item) => item.slug !== project.slug).slice(0, 3).map((item) => projectCard(item)).join("")}</div>
        </section>`;
      ui.trackEvent("project_view", { content_type: "project", content_id: project.id, page_type: "project" });
    } catch (error) {
      errorState(root, error.message || "This project could not be loaded.", () => window.location.reload());
    }
  }

  function researchCard(item) {
    return `<article class="card research-card">
      <span class="eyebrow">${escapeHtml(item.publication_status || "Research")}</span>
      <h3><a href="research.html?slug=${encodeURIComponent(item.slug)}">${escapeHtml(item.title)}</a></h3>
      <p class="muted">${escapeHtml(truncate(item.abstract, 220))}</p>
      <div class="card-foot">
        <span class="muted small">${[item.sample_size && `${item.sample_size} respondents`, item.institutions_count && `${item.institutions_count} institutions`].filter(Boolean).map(escapeHtml).join(" · ") || "Academic study"}</span>
        <a class="text-link" href="research.html?slug=${encodeURIComponent(item.slug)}">Read study →</a>
      </div>
    </article>`;
  }

  function groupedMetrics(metrics) {
    if (!metrics?.length) return "";
    const order = ["distribution", "model", "baseline", "other"];
    const groups = {};
    metrics.forEach((metric) => {
      const key = metric.metric_type || "other";
      (groups[key] = groups[key] || []).push(metric);
    });
    return order
      .filter((key) => groups[key])
      .map(
        (key) => `<section class="card prose"><h2>${escapeHtml(key === "other" ? "Additional measurements" : `${key[0].toUpperCase()}${key.slice(1)} metrics`)}</h2>${metricGrid(groups[key])}${groups[key].some((metric) => metric.notes) ? `<ul>${groups[key].filter((metric) => metric.notes).map((metric) => `<li><strong>${escapeHtml(metric.name)}:</strong> ${escapeHtml(metric.notes)}</li>`).join("")}</ul>` : ""}</section>`
      )
      .join("");
  }

  async function renderResearch() {
    const root = $("#research-root");
    const slug = query.get("slug");
    if (slug) {
      try {
        const item = (await api.get(`/research/${encodeURIComponent(slug)}`)).data;
        document.title = `${item.title} · Research`;
        root.innerHTML = `
          <a class="back-link" href="research.html">← All research</a>
          <header class="detail-head">
            <span class="eyebrow">${escapeHtml(item.publication_status || "Academic research")}</span>
            <h1>${escapeHtml(item.title)}</h1>
            <div class="chip-row">
              ${item.sample_size ? `<span class="chip">Sample: ${escapeHtml(item.sample_size)}</span>` : ""}
              ${item.institutions_count ? `<span class="chip">Institutions: ${escapeHtml(item.institutions_count)}</span>` : ""}
              <span class="chip">${escapeHtml(item.status)}</span>
            </div>
            <div class="detail-actions">
              ${item.paper_url ? `<a class="btn btn-primary" href="${escapeHtml(item.paper_url)}" target="_blank" rel="noopener">Read paper ↗</a>` : ""}
              ${item.dataset_url ? `<a class="btn btn-ghost" href="${escapeHtml(item.dataset_url)}" target="_blank" rel="noopener">Dataset ↗</a>` : ""}
            </div>
          </header>
          <section class="card prose"><h2>Abstract</h2>${markdown(item.abstract || "Abstract not published yet.")}</section>
          <div class="detail-grid">
            ${item.methodology ? `<section class="card prose"><h2>Methodology</h2>${markdown(item.methodology)}</section>` : ""}
            ${groupedMetrics(item.metrics)}
          </div>
          ${item.notes ? `<section class="card prose"><h2>Notes</h2>${markdown(item.notes)}</section>` : ""}`;
      } catch (error) {
        errorState(root, error.message || "Research record not found.", () => (window.location.href = "research.html"));
      }
      return;
    }
    root.innerHTML = ui.skeletonCards(3);
    try {
      const items = (await api.get("/research?per_page=50")).data || [];
      root.innerHTML = items.length
        ? `<div class="grid grid-3">${items.map(researchCard).join("")}</div>`
        : emptyState("No published research yet", "Academic studies will appear here once published.");
    } catch (error) {
      errorState(root, error.message, () => renderResearch());
    }
  }

  async function renderCertificates() {
    const root = $("#certificates-root");
    root.innerHTML = ui.skeletonCards(3);
    try {
      const items = (await api.get("/certificates?per_page=100")).data || [];
      root.innerHTML = items.length
        ? `<div class="grid grid-3">${items
            .map(
              (item) => `<article class="card cert-card">
                <div class="cert-mark">${escapeHtml(ui.initials(item.issuer))}</div>
                <span class="eyebrow">${escapeHtml(item.category?.name || "Credential")}</span>
                <h3>${escapeHtml(item.title)}</h3>
                <p class="muted">${escapeHtml(item.issuer)}${item.issue_date ? ` · ${formatDate(item.issue_date)}` : ""}</p>
                ${item.description ? `<p>${escapeHtml(item.description)}</p>` : ""}
                <div class="card-foot">
                  ${item.verification_url ? `<a class="text-link" href="${escapeHtml(item.verification_url)}" target="_blank" rel="noopener">Verify ↗</a>` : `<span class="muted small">Verified credential</span>`}
                  ${item.file_url ? `<a class="text-link" href="${escapeHtml(item.file_url)}" target="_blank" rel="noopener">View file ↗</a>` : ""}
                </div>
              </article>`
            )
            .join("")}</div>`
        : emptyState("Credentials coming soon", "Certificates are published only after verification. None are listed yet.");
    } catch (error) {
      errorState(root, error.message, () => renderCertificates());
    }
  }

  async function renderBlog() {
    const root = $("#blog-root");
    const slug = query.get("slug");
    if (slug) {
      try {
        const post = (await api.get(`/blogs/${encodeURIComponent(slug)}`)).data;
        document.title = `${post.title} · Writing`;
        root.innerHTML = `
          <a class="back-link" href="blog.html">← All writing</a>
          <article class="article">
            <header class="detail-head">
              <span class="eyebrow">${escapeHtml(post.category?.name || "Writing")} · ${escapeHtml(String(post.reading_minutes))} min read</span>
              <h1>${escapeHtml(post.title)}</h1>
              <div class="tag-row">${tagList(post.tags, "chip")}</div>
              <span class="muted small">Published ${formatDate(post.published_at)} · ${post.views || 0} views</span>
            </header>
            ${post.cover_image_url ? `<img class="article-cover" src="${escapeHtml(post.cover_image_url)}" alt="" />` : ""}
            <div class="prose">${markdown(post.content)}</div>
          </article>`;
        ui.trackEvent("blog_view", { content_type: "blog", content_id: post.id, page_type: "blog" });
      } catch (error) {
        errorState(root, error.message || "Post not found.", () => (window.location.href = "blog.html"));
      }
      return;
    }
    root.innerHTML = ui.skeletonCards(3);
    try {
      const posts = (await api.get("/blogs?per_page=100")).data || [];
      root.innerHTML = posts.length
        ? `<div class="grid grid-3">${posts
            .map(
              (post) => `<article class="card post-card">
                <span class="eyebrow">${escapeHtml(post.category?.name || "Writing")} · ${escapeHtml(String(post.reading_minutes))} min</span>
                <h3><a href="blog.html?slug=${encodeURIComponent(post.slug)}">${escapeHtml(post.title)}</a></h3>
                <p class="muted">${escapeHtml(truncate(post.excerpt || post.content, 190))}</p>
                <div class="tag-row">${tagList((post.tags || []).slice(0, 4), "chip")}</div>
                <div class="card-foot"><span class="muted small">${formatDate(post.published_at)}</span><a class="text-link" href="blog.html?slug=${encodeURIComponent(post.slug)}">Read →</a></div>
              </article>`
            )
            .join("")}</div>`
        : emptyState("Writing is on the way", "Articles will be published here. No drafts are exposed publicly.");
    } catch (error) {
      errorState(root, error.message, () => renderBlog());
    }
  }

  async function renderContact(profile) {
    const email = profile?.email || "mtprabhashadilshani2001@gmail.com";
    $("#contact-email").href = `mailto:${email}`;
    $("#contact-email").textContent = email;
    $("#contact-phone").textContent = profile?.phone || "Available on request";
    $("#contact-location").textContent = profile?.location || "Sri Lanka";
    $("#contact-linkedin").href = profile?.linkedin_url || "#";
    $("#contact-github").href = profile?.github_url || "#";

    const form = $("#contact-form");
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = $("button[type=submit]", form);
      const status = $("#contact-status");
      button.disabled = true;
      status.className = "form-note";
      status.textContent = "Sending…";
      const data = Object.fromEntries(new FormData(form).entries());
      try {
        const result = await api.post("/contact", {
          name: data.name,
          email: data.email,
          phone: data.phone || null,
          subject: data.subject,
          message: data.message,
          website: data.website || ""
        });
        status.className = "form-note success";
        status.textContent = result.data?.message || "Message sent.";
        form.reset();
        ui.toast("Message sent successfully", "success");
      } catch (error) {
        status.className = "form-note error";
        status.textContent = error.message || "Unable to send message.";
      } finally {
        button.disabled = false;
      }
    });

    const newsletter = $("#newsletter-form");
    newsletter.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = $("button[type=submit]", newsletter);
      const status = $("#newsletter-status");
      const data = Object.fromEntries(new FormData(newsletter).entries());
      button.disabled = true;
      try {
        const result = await api.post("/newsletter", {
          email: data.email,
          consent: data.consent === "on",
          source: "website-contact"
        });
        status.className = "form-note success";
        status.textContent = result.data?.message || "Subscribed.";
        newsletter.reset();
      } catch (error) {
        status.className = "form-note error";
        status.textContent = error.message || "Unable to subscribe.";
      } finally {
        button.disabled = false;
      }
    });
  }

  const renderers = {
    home: renderHome,
    about: renderAbout,
    projects: renderProjects,
    project: renderProjectDetail,
    research: renderResearch,
    certificates: renderCertificates,
    blog: renderBlog,
    contact: renderContact
  };

  document.addEventListener("DOMContentLoaded", async () => {
    const progress = $("#scroll-progress");
    if (progress) {
      window.addEventListener("scroll", () => {
        const height = document.documentElement.scrollHeight - window.innerHeight;
        progress.style.transform = `scaleX(${height > 0 ? window.scrollY / height : 0})`;
      }, { passive: true });
    }
    const profile = await ui.initChrome();
    const page = document.body.dataset.page || "home";
    if (renderers[page]) await renderers[page](profile);
  });
})();
