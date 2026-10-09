// 4.0 页面没有旧的插槽。首页小组件把脚本留下来，再把按钮插回下载页和添加 RSS。

const tmdb = { id: "", mediaType: "tv" };

async function call(method, url, body) {
  const response = await fetch(url, {
    method,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.msg_zh || data.detail || data.msg_en || "请求失败";
    throw new Error(typeof message === "string" ? message : "请求失败");
  }
  return data;
}

function hideSlot(element) {
  const body = element.getRootNode()?.host;
  const slot = body?.closest?.(".plugin-slot");
  if (!slot) return;
  slot.style.display = "none";
  const wrap = slot.closest(".plugin-widgets");
  if (
    wrap &&
    [...wrap.querySelectorAll(".plugin-slot")].every(
      (node) => node.style.display === "none"
    )
  ) {
    wrap.style.display = "none";
  }
}

function rewriteAnalysis(url, body) {
  if (!String(url).includes("api/v1/rss/analysis") || !tmdb.id.trim()) return null;
  let data;
  try {
    data = JSON.parse(body);
  } catch {
    return null;
  }
  if (!data || data.aggregate || data.parser !== "tmdb") return null;
  return {
    url: String(url).replace(
      "api/v1/rss/analysis",
      "api/v1/extensions/hfzy/rss-analysis"
    ),
    body: JSON.stringify({
      url: data.url || "",
      name: data.name || "",
      aggregate: false,
      parser: data.parser || "tmdb",
      tmdb_media_type: tmdb.mediaType,
      tmdb_id: tmdb.id.trim(),
    }),
  };
}

function patchAnalysis() {
  if (window.__hfzyAnalysis) return;
  window.__hfzyAnalysis = true;
  const originalFetch = window.fetch;
  window.fetch = (input, init = {}) => {
    const url = typeof input === "string" ? input : input?.url;
    const next = rewriteAnalysis(url, init.body);
    if (!next) return originalFetch(input, init);
    return originalFetch(next.url, { ...init, body: next.body });
  };
  const proto = XMLHttpRequest.prototype;
  const originalOpen = proto.open;
  const originalSend = proto.send;
  proto.open = function open(method, url, ...rest) {
    this.__hfzyUrl = url;
    this.__hfzyMethod = method;
    return originalOpen.call(this, method, url, ...rest);
  };
  proto.send = function send(body) {
    const next = rewriteAnalysis(this.__hfzyUrl, body);
    if (!next) return originalSend.call(this, body);
    originalOpen.call(this, this.__hfzyMethod || "POST", next.url, true);
    return originalSend.call(this, next.body);
  };
}

function parserName(anchor) {
  const select = anchor.querySelector(".parser-select");
  if (!select) return "";
  const label =
    select.querySelector(
      ".n-base-selection-input__content, .n-base-selection-overlay__wrapper"
    ) || select.querySelector(".n-base-selection");
  const text = (label?.textContent || "").replace(/\s+/g, " ").trim().toLowerCase();
  return text.split(" ")[0] || "";
}

function aggregateOn(anchor) {
  const scope = anchor.parentElement || anchor;
  const toggles = scope.querySelectorAll("[role='switch']");
  for (const toggle of toggles) {
    if (toggle.getAttribute("aria-checked") === "true") return true;
    if (String(toggle.className).includes("--active")) return true;
  }
  return false;
}

function tmdbAllowed(anchor) {
  return parserName(anchor) === "tmdb" && !aggregateOn(anchor);
}

const TMDB_TYPES = [
  ["tv", "剧集"],
  ["movie", "电影"],
];

function tmdbTypeLabel() {
  return TMDB_TYPES.find(([value]) => value === tmdb.mediaType)?.[1] || "剧集";
}

function closeTmdbMenu() {
  document.querySelector("[data-hfzy-tmdb-menu]")?.remove();
}

function paintLikeSelection(target, selection) {
  const style = selection ? getComputedStyle(selection) : null;
  const height = selection?.offsetHeight ? `${selection.offsetHeight}px` : "34px";
  target.style.boxSizing = "border-box";
  target.style.height = height;
  target.style.margin = "0";
  target.style.padding = "0 12px";
  target.style.border = "1px solid transparent";
  target.style.borderRadius = style?.borderRadius || "var(--radius-md, 8px)";
  target.style.backgroundColor = style?.backgroundColor || "var(--color-surface-hover)";
  target.style.color = style?.color || "var(--color-text)";
  target.style.font = "inherit";
  target.style.fontSize = style?.fontSize || "14px";
  target.style.boxShadow = style?.boxShadow && style.boxShadow !== "none" ? style.boxShadow : "none";
  target.style.outline = "none";
}

function openTmdbMenu(trigger) {
  closeTmdbMenu();
  const menu = document.createElement("div");
  menu.dataset.hfzyTmdbMenu = "1";
  menu.setAttribute("role", "listbox");
  const box = trigger.getBoundingClientRect();
  menu.style.cssText = `position:fixed;z-index:4002;top:${Math.round(box.bottom + 4)}px;left:${Math.round(box.left)}px;min-width:${Math.round(Math.max(box.width, 140))}px;padding:4px;background:var(--color-surface);border-radius:var(--radius-md, 8px);box-shadow:0 6px 16px rgba(15,23,42,.12);`;
  TMDB_TYPES.forEach(([value, label]) => {
    const item = document.createElement("button");
    item.type = "button";
    item.setAttribute("role", "option");
    const selected = tmdb.mediaType === value;
    item.style.cssText = `display:flex;align-items:center;justify-content:space-between;gap:12px;width:100%;height:34px;padding:0 12px;border:0;border-radius:6px;background:${selected ? "var(--color-surface-hover)" : "transparent"};color:var(--color-text);font:inherit;font-size:14px;cursor:pointer;text-align:left;`;
    const text = document.createElement("span");
    text.textContent = label;
    item.appendChild(text);
    if (selected) {
      const mark = document.createElement("span");
      mark.textContent = "✓";
      mark.style.color = "var(--color-primary)";
      item.appendChild(mark);
    }
    item.addEventListener("mouseenter", () => {
      item.style.background = "var(--color-surface-hover)";
    });
    item.addEventListener("mouseleave", () => {
      item.style.background = tmdb.mediaType === value ? "var(--color-surface-hover)" : "transparent";
    });
    item.addEventListener("click", (event) => {
      event.stopPropagation();
      tmdb.mediaType = value;
      const labelNode = trigger.querySelector("[data-hfzy-type-label]");
      if (labelNode) labelNode.textContent = label;
      closeTmdbMenu();
    });
    menu.appendChild(item);
  });
  document.body.appendChild(menu);
}

let showTmdb = true;
let showFilter = true;
let showPlay = true;
let showEtaLine = true;

function ensureTmdbRow() {
  const anchor = document.querySelector(".options-row:not([data-hfzy-tmdb])");
  if (!anchor) return;
  if (!showTmdb) {
    const hidden = anchor.parentElement?.querySelector("[data-hfzy-tmdb]");
    if (hidden) hidden.style.display = "none";
    return;
  }
  let row = anchor.parentElement?.querySelector("[data-hfzy-tmdb]");
  if (row?.querySelector("select")) {
    row.remove();
    row = null;
  }
  if (!tmdbAllowed(anchor)) {
    tmdb.id = "";
    if (row) {
      row.style.display = "none";
      const input = row.querySelector("input");
      if (input) input.value = "";
    }
    return;
  }
  if (!row) {
    row = document.createElement("div");
    row.dataset.hfzyTmdb = "1";
    row.innerHTML = `
      <div data-hfzy-type style="display:flex;align-items:center;gap:12px;flex:0 0 auto;">
        <label>TMDB 信息</label>
        <button type="button" data-hfzy-type-trigger aria-haspopup="listbox" aria-label="TMDB 类型">
          <span data-hfzy-type-label>${tmdbTypeLabel()}</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>
        </button>
      </div>
      <input type="text" inputmode="numeric" placeholder="TMDB 编号" aria-label="TMDB 编号">
    `;
    anchor.insertAdjacentElement("afterend", row);
    const trigger = row.querySelector("[data-hfzy-type-trigger]");
    const input = row.querySelector("input");
    input.value = tmdb.id;
    trigger.addEventListener("click", (event) => {
      event.stopPropagation();
      if (document.querySelector("[data-hfzy-tmdb-menu]")) closeTmdbMenu();
      else openTmdbMenu(trigger);
    });
    input.addEventListener("input", () => {
      tmdb.id = input.value;
    });
  }
  const selection = anchor.querySelector(".parser-select .n-base-selection");
  const anchorStyle = getComputedStyle(anchor);
  row.style.display = "flex";
  row.style.flexWrap = "wrap";
  row.style.alignItems = "center";
  row.style.gap = "16px";
  row.style.margin = "0";
  row.style.boxSizing = "border-box";
  row.style.padding = anchorStyle.padding;
  row.style.background = anchorStyle.backgroundColor;
  row.style.borderRadius = anchorStyle.borderRadius;
  const label = anchor.querySelector(".option-label");
  const ownLabel = row.querySelector("label");
  if (label && ownLabel) {
    const labelStyle = getComputedStyle(label);
    ownLabel.style.fontSize = labelStyle.fontSize;
    ownLabel.style.fontWeight = labelStyle.fontWeight;
    ownLabel.style.color = labelStyle.color;
    ownLabel.style.whiteSpace = "nowrap";
  }
  const trigger = row.querySelector("[data-hfzy-type-trigger]");
  const input = row.querySelector("input");
  paintLikeSelection(trigger, selection);
  paintLikeSelection(input, selection);
  trigger.style.display = "inline-flex";
  trigger.style.alignItems = "center";
  trigger.style.justifyContent = "space-between";
  trigger.style.gap = "8px";
  trigger.style.width = "140px";
  trigger.style.flex = "0 0 140px";
  trigger.style.cursor = "pointer";
  input.style.flex = "1 1 160px";
  input.style.minWidth = "160px";
  input.style.backgroundColor = "var(--color-surface)";
  input.style.border = "1px solid var(--color-border)";
}

let filterRoot = null;
let filterMenu = null;
let filterMode = "all";

const FILTERS = [
  ["all", "全部"],
  ["done", "已完成"],
  ["pending", "未完成"],
];

function downloaderTitle() {
  return [...document.querySelectorAll(".page-title")].find(
    (node) => node.getClientRects().length && /downloader/i.test(node.textContent || "")
  );
}

function closeFilterMenu() {
  filterMenu?.remove();
  filterMenu = null;
}

function openFilterMenu() {
  closeFilterMenu();
  const box = filterRoot.getBoundingClientRect();
  filterMenu = document.createElement("div");
  filterMenu.dataset.hfzyFilterMenu = "1";
  filterMenu.style.cssText =
    "position:fixed;z-index:4001;min-width:128px;padding:4px;background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-md, 8px);box-shadow:0 8px 24px rgba(15,23,42,.12);";
  filterMenu.style.top = `${box.bottom + 6}px`;
  filterMenu.style.left = `${Math.max(8, box.right - 128)}px`;
  FILTERS.forEach(([key, label]) => {
    const item = document.createElement("button");
    item.type = "button";
    item.textContent = filterMode === key ? `✓ ${label}` : label;
    item.style.cssText =
      "display:block;width:100%;height:32px;padding:0 10px;border:0;border-radius:6px;background:transparent;color:var(--color-text);font:inherit;font-size:13px;text-align:left;cursor:pointer;";
    item.addEventListener("click", (event) => {
      event.stopPropagation();
      filterMode = key;
      const trigger = filterRoot.querySelector("span");
      if (trigger) trigger.textContent = label;
      closeFilterMenu();
      applyFilter(filterMode);
    });
    filterMenu.appendChild(item);
  });
  document.body.appendChild(filterMenu);
}

function placeFilter() {
  if (!filterRoot) return;
  const title = downloaderTitle();
  const main = document.querySelector("#main-content");
  if (!title || !main) {
    filterRoot.style.visibility = "hidden";
    closeFilterMenu();
    return;
  }
  const titleBox = title.getBoundingClientRect();
  const mainBox = main.getBoundingClientRect();
  const width = filterRoot.offsetWidth || 84;
  const height = filterRoot.offsetHeight || 28;
  const top = Math.max(8, titleBox.top + (titleBox.height - height) / 2);
  const left = Math.max(
    8,
    Math.min(mainBox.right, window.innerWidth) - width - 8
  );
  filterRoot.style.visibility = "visible";
  filterRoot.style.top = `${Math.round(top)}px`;
  filterRoot.style.left = `${Math.round(left)}px`;
}

function ensureFilter() {
  if (!showFilter || !downloaderTitle()) {
    filterRoot?.remove();
    filterRoot = null;
    closeFilterMenu();
    return;
  }
  if (!filterRoot?.isConnected) {
    filterRoot = document.createElement("button");
    filterRoot.type = "button";
    filterRoot.dataset.hfzyFilter = "1";
    filterRoot.setAttribute("aria-label", "下载列表筛选");
    filterRoot.style.cssText =
      "position:fixed;z-index:4000;display:inline-flex;align-items:center;gap:4px;height:28px;padding:0 10px;border:1px solid transparent;border-radius:var(--radius-sm, 4px);background:transparent;color:var(--color-text);font:inherit;font-size:13px;font-weight:500;cursor:pointer;";
    filterRoot.innerHTML = `<span>${
      FILTERS.find(([key]) => key === filterMode)?.[1] || "全部"
    }</span><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>`;
    filterRoot.addEventListener("click", (event) => {
      event.stopPropagation();
      if (filterMenu) closeFilterMenu();
      else openFilterMenu();
    });
    document.body.appendChild(filterRoot);
  }
  placeFilter();
}

function rowDone(row) {
  const cell = row.querySelector('[data-col-key="progress"]');
  const matched = cell?.textContent.match(/(\d+(?:\.\d+)?)%/);
  return Boolean(matched) && Number(matched[1]) >= 100;
}

function applyFilter(mode) {
  if (!downloaderTitle()) return;
  document.querySelectorAll(".fold-panel").forEach((panel) => {
    const rows = [...panel.querySelectorAll("tbody tr")].filter((row) =>
      row.querySelector('[data-col-key="progress"]')
    );
    rows.forEach((row) => {
      row.style.display = "";
    });
    if (mode === "all" || rows.length === 0) {
      panel.style.display = "";
      return;
    }
    const allDone = rows.every(rowDone);
    const hide = mode === "pending" ? allDone : !allDone;
    panel.style.display = hide ? "none" : "";
  });
}

async function openPlayer(host, name, button) {
  button.disabled = true;
  try {
    const torrents = await call("GET", "/api/v1/downloader/torrents");
    const list = Array.isArray(torrents) ? torrents : [];
    const found = list.find((item) => String(item.name || "").trim() === name);
    if (!found?.hash) {
      host?.toast?.("没有找到这个任务", "error");
      return;
    }
    const media = await call(
      "GET",
      `/api/v1/extensions/player/torrents/${found.hash}/media`
    );
    const file = media.files?.[0];
    if (!file?.url) {
      host?.toast?.("未找到可播放媒体文件", "info");
      return;
    }
    const url = /^https?:\/\//i.test(file.url)
      ? file.url
      : new URL(file.url, location.origin).toString();
    window.open(url, "_blank", "noopener,noreferrer");
  } catch (error) {
    host?.toast?.(error.message || "获取播放地址失败", "error");
  } finally {
    button.disabled = false;
  }
}

function ensurePlay(host) {
  if (!showPlay || !downloaderTitle()) {
    document.querySelectorAll("[data-hfzy-play]").forEach((node) => node.remove());
    return;
  }
  document.querySelectorAll(".fold-panel tbody [data-col-key='name']").forEach((cell) => {
    const existing = cell.querySelector("[data-hfzy-play]");
    const holder =
      cell.firstElementChild && cell.firstElementChild !== existing
        ? cell.firstElementChild
        : cell;
    holder.style.display = "flex";
    holder.style.flexDirection = "row";
    holder.style.alignItems = "center";
    holder.style.flexWrap = "nowrap";
    holder.style.gap = "6px";
    holder.style.minWidth = "0";
    if (existing) {
      if (existing.parentElement !== holder) holder.prepend(existing);
      return;
    }
    const name = cell.textContent.trim();
    if (!name) return;
    const button = document.createElement("button");
    button.dataset.hfzyPlay = "1";
    button.type = "button";
    button.title = "网页播放";
    button.setAttribute("aria-label", "网页播放");
    button.innerHTML =
      '<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path d="M8 5v14l11-7L8 5z" fill="currentColor"/></svg>';
    button.style.cssText =
      "display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;margin:0;padding:0;flex:0 0 22px;color:var(--color-primary);background:var(--color-surface-2);border:1px solid var(--color-border);border-radius:var(--radius-sm, 4px);cursor:pointer;";
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      openPlayer(host, name, button);
    });
    holder.prepend(button);
  });
}

function watchFilterPlace() {
  if (window.__hfzyFilterPlace) return;
  window.__hfzyFilterPlace = true;
  window.addEventListener("resize", placeFilter);
  window.addEventListener("scroll", placeFilter, true);
  document.addEventListener("click", (event) => {
    const tmdbMenu = document.querySelector("[data-hfzy-tmdb-menu]");
    if (
      tmdbMenu &&
      !tmdbMenu.contains(event.target) &&
      !event.target?.closest?.("[data-hfzy-type-trigger]")
    ) {
      closeTmdbMenu();
    }
    if (!filterMenu) return;
    if (filterRoot?.contains(event.target) || filterMenu.contains(event.target)) return;
    closeFilterMenu();
  });
}

let filterHits = [];
let countKey = "";
let countTimer = 0;
let settingsCache = null;
let settingsAt = 0;

function tagLabel(element) {
  return (element.querySelector(".n-tag__content")?.textContent || element.textContent || "").trim();
}

function textWidth(font, text) {
  const canvas = textWidth.canvas || (textWidth.canvas = document.createElement("canvas"));
  const context = canvas.getContext("2d");
  if (!context) return text.length * 8;
  context.font = font;
  return context.measureText(text).width;
}

function applyEtaLine() {
  document.querySelectorAll(".fold-panel table").forEach((table) => {
    const header = table.querySelector('thead [data-col-key="eta"]');
    if (!header) return;
    const cells = [...table.querySelectorAll('[data-col-key="eta"]')];
    const col = table.querySelectorAll("colgroup col")[header.cellIndex];
    const targets = col ? [col, ...cells] : cells;
    if (!showEtaLine) {
      targets.forEach((node) => {
        if (!node.dataset.hfzyEta) return;
        node.style.width = "";
        node.style.minWidth = "";
        node.style.maxWidth = "";
        node.style.whiteSpace = "";
        delete node.dataset.hfzyEta;
      });
      return;
    }
    const sample = table.querySelector('tbody [data-col-key="eta"]') || header;
    const sampleStyle = getComputedStyle(sample);
    let measured = 0;
    cells.forEach((cell) => {
      const text = (cell.textContent || "").trim() || "ETA";
      measured = Math.max(measured, textWidth(sampleStyle.font, text));
    });
    const pad =
      (parseFloat(sampleStyle.paddingLeft) || 0) +
      (parseFloat(sampleStyle.paddingRight) || 0);
    const width = `${Math.max(80, Math.ceil(measured + pad + 4))}px`;
    targets.forEach((node) => {
      if (node.dataset.hfzyEta === width) return;
      node.dataset.hfzyEta = width;
      node.style.whiteSpace = "nowrap";
      node.style.width = width;
      node.style.minWidth = width;
      node.style.maxWidth = width;
    });
  });
}

function ensureHitStyle() {
  if (document.getElementById("hfzy-filter-hit-style")) return;
  const style = document.createElement("style");
  style.id = "hfzy-filter-hit-style";
  style.textContent = `
    .filter-tags .n-tag.hfzy-filter-hit {
      border-color: var(--color-warning) !important;
      box-shadow: inset 0 0 0 1px var(--color-warning);
    }
  `;
  document.head.appendChild(style);
}

function applyHits() {
  document.querySelectorAll(".filter-tags .n-tag").forEach((element) => {
    element.classList.toggle("hfzy-filter-hit", filterHits.includes(tagLabel(element)));
  });
}

function dialogSignature() {
  const season = document.querySelector(".season-input");
  if (!season) return "";
  const link = document.querySelector(".info-value--link")?.textContent?.trim() || "";
  const tags = [...document.querySelectorAll(".filter-tags .n-tag")].map(tagLabel).join("\n");
  return `${link}|${season.value}|${tags}`;
}

async function hfzySettings() {
  if (settingsCache && Date.now() - settingsAt < 15000) return settingsCache;
  try {
    settingsCache = await call("GET", "/api/v1/extensions/hfzy/config");
    showTmdb = settingsCache.tmdb_info !== false;
    showFilter = settingsCache.downloader_filter !== false;
    showPlay = settingsCache.player_enable !== false;
    showEtaLine = settingsCache.downloader_eta_single_line !== false;
  } catch {
    settingsCache = {};
  }
  settingsAt = Date.now();
  return settingsCache;
}

function scheduleCount() {
  const key = dialogSignature();
  if (!key) {
    filterHits = [];
    applyHits();
    return;
  }
  if (key === countKey && document.querySelector("[data-hfzy-count]")) {
    applyHits();
    return;
  }
  clearTimeout(countTimer);
  countTimer = setTimeout(() => {
    refreshCount(key);
  }, 400);
}

async function refreshCount(key) {
  const seasonInput = document.querySelector(".season-input");
  const row = seasonInput?.closest(".meta-row");
  if (!seasonInput || !row) return;
  const link = document.querySelector(".info-value--link")?.textContent?.trim() || "";
  const tags = [...document.querySelectorAll(".filter-tags .n-tag")].map(tagLabel).filter(Boolean);
  const cfg = await hfzySettings();
  const showCount = cfg.rss_episode_count !== false && Boolean(link);
  const showHits = cfg.rss_filter_hit !== false && Boolean(link);
  if (!showCount && !showHits) {
    row.querySelector("[data-hfzy-count]")?.remove();
    filterHits = [];
    applyHits();
    countKey = key;
    return;
  }
  try {
    const data = await call("POST", "/api/v1/extensions/hfzy/rss-episode-count", {
      rss_link: link,
      filter: tags,
      season: Number(seasonInput.value) || 1,
      episode_type: "episode",
    });
    if (dialogSignature() !== key) return;
    countKey = key;
    filterHits = showHits ? data.hits || [] : [];
    applyHits();
    let label = row.querySelector("[data-hfzy-count]");
    if (!showCount) {
      label?.remove();
      return;
    }
    if (!label) {
      label = document.createElement("span");
      label.dataset.hfzyCount = "1";
      label.style.cssText =
        "margin-left:6px;font-size:13px;color:var(--color-text-secondary);white-space:nowrap;";
      seasonInput.insertAdjacentElement("afterend", label);
    }
    const videos = data.videos ?? 0;
    label.textContent = `· 共 ${data.versions ?? 0} 版 ${videos} 个视频`;
    label.title = "版是过滤后剩下的发布版本，视频是剩下的条目";
    label.style.color = videos === 0 ? "var(--color-warning)" : "var(--color-text-secondary)";
  } catch {
    if (dialogSignature() !== key) return;
    countKey = key;
  }
}

let activeHost = { toast() {} };
let copyFix = true;

function copyWithSelection(text) {
  const area = document.createElement("textarea");
  area.value = text;
  area.setAttribute("readonly", "");
  area.style.cssText = "position:fixed;top:0;left:0;opacity:0;pointer-events:none;";
  const parent = document.activeElement?.closest?.("[role='dialog']") || document.body;
  parent.appendChild(area);
  area.focus();
  area.select();
  area.setSelectionRange(0, area.value.length);
  let ok = false;
  try {
    ok = document.execCommand("copy");
  } catch {
    ok = false;
  }
  area.remove();
  return ok;
}

function installCopyFix() {
  if (window.__hfzyCopyClick) return;
  window.__hfzyCopyClick = true;
  const writeText = (text) => {
    if (!copyFix) {
      const original = window.__hfzyCopyOriginal;
      if (original) return original(text);
      return Promise.reject(new Error("copy failed"));
    }
    return copyWithSelection(String(text ?? ""))
      ? Promise.resolve()
      : Promise.reject(new Error("copy failed"));
  };
  const existing = navigator.clipboard;
  if (existing?.writeText) {
    window.__hfzyCopyOriginal = existing.writeText.bind(existing);
    const wrapped = (text) => {
      if (!copyFix) return window.__hfzyCopyOriginal(text);
      if (window.isSecureContext) {
        return window.__hfzyCopyOriginal(text).catch(() => writeText(text));
      }
      return writeText(text);
    };
    try {
      existing.writeText = wrapped;
    } catch {
      Object.defineProperty(existing, "writeText", {
        configurable: true,
        writable: true,
        value: wrapped,
      });
    }
    return;
  }
  const clipboard = { writeText };
  try {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      get: () => clipboard,
    });
  } catch {
    try {
      navigator.clipboard = clipboard;
    } catch {
      /* 页面不允许替换剪贴板对象时，复制按钮仍走原来的调用。 */
    }
  }
}

function installHfzy(host) {
  if (host) activeHost = host;
  if (window.__hfzyUi) return;
  window.__hfzyUi = true;
  hfzySettings().then((cfg) => {
    copyFix = cfg?.rss_copy_fix !== false;
  });
  installCopyFix();
  patchAnalysis();
  ensureHitStyle();
  watchFilterPlace();
  const tick = () => {
    ensureTmdbRow();
    ensureFilter();
    applyFilter(filterMode);
    ensurePlay(activeHost);
    applyEtaLine();
    scheduleCount();
  };
  tick();
  new MutationObserver(tick).observe(document.body, {
    childList: true,
    subtree: true,
  });
}

class HfzyBoot extends HTMLElement {
  connectedCallback() {
    hideSlot(this);
    installHfzy(this.host);
  }
}

if (!customElements.get("ab-plugin-hfzy-boot")) {
  customElements.define("ab-plugin-hfzy-boot", HfzyBoot);
}

installHfzy(activeHost);
