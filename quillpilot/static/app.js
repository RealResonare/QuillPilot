const state = {
  writeAction: "polish",
  settings: null,
  health: null,
  importState: "state.ready",
  searchHasRun: false,
  searchResultCount: 0,
};

const ROUTES = ["home", "repository", "copilot", "settings"];

const I18N = {
  "zh-CN": {
    "app.title": "QuillPilot 控制台",
    "nav.home": "主页",
    "nav.repository": "仓库",
    "nav.copilot": "Copilot",
    "nav.settings": "设置",
    "nav.api": "API",
    "search.global": "搜索仓库",
    "home.eyebrow": "本地学术 Copilot",
    "home.title": "科研写作控制台",
    "action.refresh": "刷新",
    "action.apiDocs": "API 文档",
    "action.clearSearch": "清除搜索",
    "action.search": "搜索",
    "action.ask": "提问",
    "action.run": "运行",
    "action.insert": "插入",
    "action.save": "保存",
    "action.add": "添加",
    "metric.database": "数据库",
    "metric.papers": "已导入论文",
    "metric.bib": "BibTeX 条目",
    "metric.chunks": "已索引片段",
    "repository.eyebrow": "个人知识库",
    "repository.title": "仓库",
    "repository.importTitle": "知识库",
    "repository.pdfDir": "PDF 目录",
    "repository.bibFile": "BibTeX 文件",
    "repository.import": "导入仓库",
    "repository.searchTitle": "仓库搜索",
    "repository.searchPlaceholder": "标题、作者、BibTeX key 或论点",
    "repository.noSearch": "尚未运行仓库搜索。",
    "repository.noResults": "未找到匹配论文。",
    "repository.importInputMissing": "请输入 PDF 目录或 BibTeX 文件。",
    "repository.imported": "仓库已导入。",
    "table.paper": "论文",
    "table.key": "Key",
    "table.year": "年份",
    "table.score": "分数",
    "result.count": "{count} 条结果",
    "copilot.eyebrow": "写作工作区",
    "copilot.title": "Copilot",
    "copilot.reading": "阅读",
    "copilot.grounded": "基于文献的回答",
    "copilot.question": "问题",
    "copilot.questionPlaceholder": "这篇论文如何描述检索增强？",
    "copilot.sources": "来源数",
    "copilot.writing": "写作",
    "copilot.transform": "学术文本转换",
    "copilot.selectedText": "选中文本",
    "copilot.selectedPlaceholder": "粘贴选中的草稿文本",
    "copilot.context": "上下文",
    "copilot.contextPlaceholder": "章节目标、读者或目标论点",
    "copilot.citation": "引用",
    "copilot.verifiedKeys": "已验证 key",
    "copilot.lookup": "查找",
    "copilot.lookupPlaceholder": "论文标题、作者、论点或 BibTeX key",
    "copilot.style": "样式",
    "write.polish": "润色",
    "write.expand": "扩写",
    "write.rewrite": "重写",
    "write.challenge": "质疑",
    "state.ready": "就绪",
    "state.importing": "导入中",
    "state.failed": "失败",
    "state.loading": "加载中...",
    "state.llmReady": "LLM 就绪",
    "state.llmOffline": "LLM 离线",
    "settings.desktop": "桌面",
    "settings.general": "通用",
    "settings.hotkeys": "快捷键",
    "settings.server": "服务器",
    "settings.providers": "提供商",
    "general.language": "语言",
    "general.languageHelp": "更改 QuillPilot 的显示语言",
    "general.font": "字体",
    "general.fontHelp": "用于界面正文和控件的字体",
    "general.codeFont": "代码字体",
    "general.codeFontHelp": "用于 BibTeX key、LaTeX 引用和路径显示",
    "general.fontSize": "字号",
    "general.fontSizeHelp": "控制主界面的基础字号",
    "general.compact": "紧凑布局",
    "general.compactHelp": "在数据密集页面中减少控件间距",
    "general.progress": "显示会话进度条",
    "general.progressHelp": "智能体工作时显示状态进度",
    "language.zh": "简体中文",
    "language.en": "英文",
    "language.fr": "法语",
    "providers.title": "API 提供商",
    "providers.manage": "多 API 管理",
    "providers.help": "管理 OpenAI-compatible API 和本地 LLM 端点。",
    "providers.default": "默认: {name}",
    "providers.defaultFallback": "默认",
    "providers.empty": "尚未配置提供商。",
    "providers.new": "新提供商",
    "providers.kind.api": "API",
    "providers.kind.local": "本地 LLM",
    "providers.name": "提供商名称",
    "providers.baseUrl": "基础 URL",
    "providers.model": "模型",
    "providers.apiKey": "API key",
    "providers.enabled": "启用",
    "providers.setDefault": "设为默认",
    "providers.delete": "删除提供商",
    "hotkeys.enable": "启用全局快捷键",
    "hotkeys.enableHelp": "快捷键客户端启动时会读取这里的配置",
    "hotkeys.read": "阅读解释",
    "hotkeys.readHelp": "读取剪贴板文本并调用仓库问答",
    "hotkeys.write": "写作辅助",
    "hotkeys.writeHelp": "对剪贴板文本进行学术润色",
    "hotkeys.cite": "引用插入",
    "hotkeys.citeHelp": "查找 BibTeX key 并复制 LaTeX 引用命令",
    "toast.statusRefreshed": "状态已刷新。",
    "toast.generalSaved": "通用设置已保存。",
    "toast.providersSaved": "API 提供商已保存。",
    "toast.hotkeysSaved": "快捷键设置已保存。重启 hotkey 客户端后生效。",
    "citation.multiple": "找到多个引用候选:",
    "citation.untitled": "未命名",
  },
  "en-US": {
    "app.title": "QuillPilot Console",
    "nav.home": "Home",
    "nav.repository": "Repository",
    "nav.copilot": "Copilot",
    "nav.settings": "Settings",
    "nav.api": "API",
    "search.global": "Search repository",
    "home.eyebrow": "Local Academic Copilot",
    "home.title": "Research Writing Console",
    "action.refresh": "Refresh",
    "action.apiDocs": "API Docs",
    "action.clearSearch": "Clear search",
    "action.search": "Search",
    "action.ask": "Ask",
    "action.run": "Run",
    "action.insert": "Insert",
    "action.save": "Save",
    "action.add": "Add",
    "metric.database": "Database",
    "metric.papers": "Papers Imported",
    "metric.bib": "BibTeX Entries",
    "metric.chunks": "Chunks Indexed",
    "repository.eyebrow": "Personal Knowledge Base",
    "repository.title": "Repository",
    "repository.importTitle": "Knowledge Base",
    "repository.pdfDir": "PDF Directory",
    "repository.bibFile": "BibTeX File",
    "repository.import": "Import Repository",
    "repository.searchTitle": "Repository Search",
    "repository.searchPlaceholder": "Title, author, BibTeX key, or claim",
    "repository.noSearch": "No repository search has run.",
    "repository.noResults": "No matching papers found.",
    "repository.importInputMissing": "Enter a PDF directory or BibTeX file.",
    "repository.imported": "Repository imported.",
    "table.paper": "Paper",
    "table.key": "Key",
    "table.year": "Year",
    "table.score": "Score",
    "result.count": "{count} results",
    "copilot.eyebrow": "Writing Workspace",
    "copilot.title": "Copilot",
    "copilot.reading": "Reading",
    "copilot.grounded": "Grounded answer",
    "copilot.question": "Question",
    "copilot.questionPlaceholder": "What does this paper claim about retrieval?",
    "copilot.sources": "Sources",
    "copilot.writing": "Writing",
    "copilot.transform": "Academic transform",
    "copilot.selectedText": "Selected Text",
    "copilot.selectedPlaceholder": "Paste selected draft text",
    "copilot.context": "Context",
    "copilot.contextPlaceholder": "Section goal, audience, or target claim",
    "copilot.citation": "Citation",
    "copilot.verifiedKeys": "Verified keys",
    "copilot.lookup": "Lookup",
    "copilot.lookupPlaceholder": "Paper title, author, claim, or BibTeX key",
    "copilot.style": "Style",
    "write.polish": "Polish",
    "write.expand": "Expand",
    "write.rewrite": "Rewrite",
    "write.challenge": "Challenge",
    "state.ready": "Ready",
    "state.importing": "Importing",
    "state.failed": "Failed",
    "state.loading": "Loading...",
    "state.llmReady": "LLM Ready",
    "state.llmOffline": "LLM Offline",
    "settings.desktop": "Desktop",
    "settings.general": "General",
    "settings.hotkeys": "Hotkeys",
    "settings.server": "Server",
    "settings.providers": "Providers",
    "general.language": "Language",
    "general.languageHelp": "Change the display language.",
    "general.font": "Font",
    "general.fontHelp": "Font used for body text and controls.",
    "general.codeFont": "Code Font",
    "general.codeFontHelp": "Used for BibTeX keys, LaTeX citations, and paths.",
    "general.fontSize": "Font Size",
    "general.fontSizeHelp": "Controls the base UI font size.",
    "general.compact": "Compact Layout",
    "general.compactHelp": "Reduce spacing on data-dense pages.",
    "general.progress": "Show Progress Bar",
    "general.progressHelp": "Show progress while the agent is working.",
    "language.zh": "Simplified Chinese",
    "language.en": "English",
    "language.fr": "French",
    "providers.title": "API Providers",
    "providers.manage": "Multi-API Management",
    "providers.help": "Manage OpenAI-compatible APIs and local LLM endpoints.",
    "providers.default": "Default: {name}",
    "providers.defaultFallback": "Default",
    "providers.empty": "No providers configured.",
    "providers.new": "New Provider",
    "providers.kind.api": "API",
    "providers.kind.local": "Local LLM",
    "providers.name": "Provider name",
    "providers.baseUrl": "Base URL",
    "providers.model": "Model",
    "providers.apiKey": "API key",
    "providers.enabled": "Enabled",
    "providers.setDefault": "Set default",
    "providers.delete": "Delete provider",
    "hotkeys.enable": "Enable Global Hotkeys",
    "hotkeys.enableHelp": "The hotkey client reads this configuration on startup.",
    "hotkeys.read": "Reading Explanation",
    "hotkeys.readHelp": "Read clipboard text and ask the repository.",
    "hotkeys.write": "Writing Assist",
    "hotkeys.writeHelp": "Polish clipboard text academically.",
    "hotkeys.cite": "Citation Insert",
    "hotkeys.citeHelp": "Find a BibTeX key and copy a LaTeX citation command.",
    "toast.statusRefreshed": "Status refreshed.",
    "toast.generalSaved": "General settings saved.",
    "toast.providersSaved": "API providers saved.",
    "toast.hotkeysSaved": "Hotkey settings saved. Restart the hotkey client to apply them.",
    "citation.multiple": "Multiple citation candidates:",
    "citation.untitled": "Untitled",
  },
  "fr-FR": {
    "app.title": "Console QuillPilot",
    "nav.home": "Accueil",
    "nav.repository": "Depot",
    "nav.copilot": "Copilot",
    "nav.settings": "Parametres",
    "nav.api": "API",
    "search.global": "Rechercher dans le depot",
    "home.eyebrow": "Copilot academique local",
    "home.title": "Console de redaction scientifique",
    "action.refresh": "Actualiser",
    "action.apiDocs": "Docs API",
    "action.clearSearch": "Effacer la recherche",
    "action.search": "Rechercher",
    "action.ask": "Demander",
    "action.run": "Executer",
    "action.insert": "Inserer",
    "action.save": "Enregistrer",
    "action.add": "Ajouter",
    "metric.database": "Base de donnees",
    "metric.papers": "Articles importes",
    "metric.bib": "Entrees BibTeX",
    "metric.chunks": "Fragments indexes",
    "repository.eyebrow": "Base personnelle",
    "repository.title": "Depot",
    "repository.importTitle": "Base de connaissances",
    "repository.pdfDir": "Dossier PDF",
    "repository.bibFile": "Fichier BibTeX",
    "repository.import": "Importer le depot",
    "repository.searchTitle": "Recherche dans le depot",
    "repository.searchPlaceholder": "Titre, auteur, cle BibTeX ou argument",
    "repository.noSearch": "Aucune recherche n'a encore ete lancee.",
    "repository.noResults": "Aucun article correspondant.",
    "repository.importInputMissing": "Saisissez un dossier PDF ou un fichier BibTeX.",
    "repository.imported": "Depot importe.",
    "table.paper": "Article",
    "table.key": "Cle",
    "table.year": "Annee",
    "table.score": "Score",
    "result.count": "{count} resultats",
    "copilot.eyebrow": "Espace de redaction",
    "copilot.title": "Copilot",
    "copilot.reading": "Lecture",
    "copilot.grounded": "Reponse fondee",
    "copilot.question": "Question",
    "copilot.questionPlaceholder": "Que dit cet article sur la recherche augmentee ?",
    "copilot.sources": "Sources",
    "copilot.writing": "Redaction",
    "copilot.transform": "Transformation academique",
    "copilot.selectedText": "Texte selectionne",
    "copilot.selectedPlaceholder": "Collez le brouillon selectionne",
    "copilot.context": "Contexte",
    "copilot.contextPlaceholder": "Objectif de section, public ou these cible",
    "copilot.citation": "Citation",
    "copilot.verifiedKeys": "Cles verifiees",
    "copilot.lookup": "Recherche",
    "copilot.lookupPlaceholder": "Titre, auteur, argument ou cle BibTeX",
    "copilot.style": "Style",
    "write.polish": "Polir",
    "write.expand": "Developper",
    "write.rewrite": "Reecrire",
    "write.challenge": "Critiquer",
    "state.ready": "Pret",
    "state.importing": "Importation",
    "state.failed": "Echec",
    "state.loading": "Chargement...",
    "state.llmReady": "LLM pret",
    "state.llmOffline": "LLM hors ligne",
    "settings.desktop": "Bureau",
    "settings.general": "General",
    "settings.hotkeys": "Raccourcis",
    "settings.server": "Serveur",
    "settings.providers": "Fournisseurs",
    "general.language": "Langue",
    "general.languageHelp": "Changer la langue d'affichage.",
    "general.font": "Police",
    "general.fontHelp": "Police utilisee pour le texte et les controles.",
    "general.codeFont": "Police de code",
    "general.codeFontHelp": "Utilisee pour les cles BibTeX, citations LaTeX et chemins.",
    "general.fontSize": "Taille de police",
    "general.fontSizeHelp": "Controle la taille de base de l'interface.",
    "general.compact": "Mise en page compacte",
    "general.compactHelp": "Reduit l'espacement sur les pages denses.",
    "general.progress": "Afficher la barre de progression",
    "general.progressHelp": "Afficher la progression pendant le travail de l'agent.",
    "language.zh": "Chinois simplifie",
    "language.en": "Anglais",
    "language.fr": "Francais",
    "providers.title": "Fournisseurs API",
    "providers.manage": "Gestion multi-API",
    "providers.help": "Gerer les API compatibles OpenAI et les LLM locaux.",
    "providers.default": "Defaut: {name}",
    "providers.defaultFallback": "Defaut",
    "providers.empty": "Aucun fournisseur configure.",
    "providers.new": "Nouveau fournisseur",
    "providers.kind.api": "API",
    "providers.kind.local": "LLM local",
    "providers.name": "Nom du fournisseur",
    "providers.baseUrl": "URL de base",
    "providers.model": "Modele",
    "providers.apiKey": "Cle API",
    "providers.enabled": "Active",
    "providers.setDefault": "Definir par defaut",
    "providers.delete": "Supprimer le fournisseur",
    "hotkeys.enable": "Activer les raccourcis globaux",
    "hotkeys.enableHelp": "Le client lit cette configuration au demarrage.",
    "hotkeys.read": "Explication de lecture",
    "hotkeys.readHelp": "Lire le presse-papiers et interroger le depot.",
    "hotkeys.write": "Aide a la redaction",
    "hotkeys.writeHelp": "Polir academiquement le texte du presse-papiers.",
    "hotkeys.cite": "Insertion de citation",
    "hotkeys.citeHelp": "Trouver une cle BibTeX et copier une citation LaTeX.",
    "toast.statusRefreshed": "Statut actualise.",
    "toast.generalSaved": "Parametres generaux enregistres.",
    "toast.providersSaved": "Fournisseurs API enregistres.",
    "toast.hotkeysSaved": "Raccourcis enregistres. Redemarrez le client de raccourcis.",
    "citation.multiple": "Plusieurs citations candidates:",
    "citation.untitled": "Sans titre",
  },
};

const $ = (selector) => document.querySelector(selector);

function currentLanguage() {
  return state.settings?.general?.language || "zh-CN";
}

function t(key, params = {}) {
  const lang = currentLanguage();
  const template = I18N[lang]?.[key] || I18N["en-US"][key] || key;
  return Object.entries(params).reduce((value, [name, replacement]) => value.replaceAll(`{${name}}`, replacement), template);
}

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 2600);
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `Request failed: ${response.status}`);
  }
  return payload;
}

function applyI18n() {
  document.title = t("app.title");
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    node.placeholder = t(node.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-i18n-title]").forEach((node) => {
    const label = t(node.dataset.i18nTitle);
    node.title = label;
    node.setAttribute("aria-label", label);
  });
  updateSearchCount();
  updateHealthChip();
  updateImportChip();
  renderProviders(state.settings?.providers || [], state.settings?.default_provider_id);
}

function setChip(element, label, variant = "neutral") {
  element.textContent = label;
  element.className = `status-chip ${variant}`;
}

function updateHealthChip() {
  if (!state.health) return;
  setChip($("#llm-status"), state.health.llm_configured ? t("state.llmReady") : t("state.llmOffline"), state.health.llm_configured ? "" : "warning");
}

function updateImportChip() {
  const variant = state.importState === "state.failed" ? "error" : state.importState === "state.importing" ? "warning" : "";
  setChip($("#import-state"), t(state.importState), variant);
}

async function loadHealth() {
  state.health = await request("/health");
  $("#database-path").textContent = state.health.database || "-";
  updateHealthChip();
}

function updateSearchCount() {
  $("#search-count").textContent = t("result.count", { count: String(state.searchResultCount) });
}

function renderEmptySearch(key) {
  $("#results-body").innerHTML = `<tr><td colspan="4" class="empty-row">${escapeHtml(t(key))}</td></tr>`;
}

function renderResults(results) {
  const body = $("#results-body");
  state.searchHasRun = true;
  state.searchResultCount = results.length;
  updateSearchCount();
  if (!results.length) {
    renderEmptySearch("repository.noResults");
    return;
  }
  body.innerHTML = results
    .map(
      (item) => `
        <tr>
          <td>
            <span class="paper-title">${escapeHtml(item.title)}</span>
            <span class="paper-snippet">${escapeHtml(item.snippet || "")}</span>
          </td>
          <td><code>${escapeHtml(item.bibtex_key || "-")}</code></td>
          <td>${escapeHtml(item.year || "-")}</td>
          <td class="number">${Number(item.score || 0).toFixed(2)}</td>
        </tr>
      `,
    )
    .join("");
}

async function runSearch(query) {
  const trimmed = query.trim();
  if (!trimmed) {
    state.searchHasRun = false;
    state.searchResultCount = 0;
    updateSearchCount();
    renderEmptySearch("repository.noSearch");
    return;
  }
  const payload = await request(`/library/search?q=${encodeURIComponent(trimmed)}&limit=12`);
  renderResults(payload.results || []);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function applyGeneralSettings(general) {
  if (!general) return;
  document.documentElement.style.setProperty("--app-font-size", `${general.font_size || 14}px`);
  document.body.style.fontFamily = `"${general.font_family || "Nunito Sans"}", Arial, sans-serif`;
  document.documentElement.lang = general.language || "zh-CN";
  applyI18n();
}

async function loadSettings() {
  const payload = await request("/settings");
  state.settings = payload;
  fillGeneralSettings(payload.general);
  renderProviders(payload.providers || [], payload.default_provider_id);
  fillHotkeySettings(payload.hotkeys);
  applyGeneralSettings(payload.general);
}

async function saveSettings(nextSettings) {
  const payload = await request("/settings", {
    method: "PUT",
    body: JSON.stringify(nextSettings),
  });
  state.settings = payload;
  fillGeneralSettings(payload.general);
  renderProviders(payload.providers || [], payload.default_provider_id);
  fillHotkeySettings(payload.hotkeys);
  applyGeneralSettings(payload.general);
  await loadHealth().catch(() => undefined);
  return payload;
}

function fillGeneralSettings(general = {}) {
  $("#setting-language").value = general.language || "zh-CN";
  $("#setting-font-family").value = general.font_family || "Nunito Sans";
  $("#setting-code-font-family").value = general.code_font_family || "Source Code Pro";
  $("#setting-font-size").value = general.font_size || 14;
  $("#setting-compact-mode").checked = Boolean(general.compact_mode);
  $("#setting-show-progress").checked = Boolean(general.show_progress);
}

function collectGeneralSettings() {
  return {
    language: $("#setting-language").value,
    font_family: $("#setting-font-family").value,
    code_font_family: $("#setting-code-font-family").value,
    font_size: Number($("#setting-font-size").value || 14),
    compact_mode: $("#setting-compact-mode").checked,
    show_progress: $("#setting-show-progress").checked,
  };
}

function fillHotkeySettings(hotkeys = {}) {
  $("#hotkey-enabled").checked = Boolean(hotkeys.enabled ?? true);
  $("#hotkey-read").value = hotkeys.read || "ctrl+alt+r";
  $("#hotkey-write").value = hotkeys.write || "ctrl+alt+w";
  $("#hotkey-cite").value = hotkeys.cite || "ctrl+alt+c";
}

function collectHotkeySettings() {
  return {
    enabled: $("#hotkey-enabled").checked,
    read: $("#hotkey-read").value.trim() || "ctrl+alt+r",
    write: $("#hotkey-write").value.trim() || "ctrl+alt+w",
    cite: $("#hotkey-cite").value.trim() || "ctrl+alt+c",
  };
}

function renderProviders(providers, defaultProviderId) {
  const list = $("#provider-list");
  if (!list) return;
  const defaultProvider = providers.find((item) => item.id === defaultProviderId);
  $("#default-provider-label").textContent = defaultProvider ? t("providers.default", { name: defaultProvider.name }) : t("providers.defaultFallback");
  if (!providers.length) {
    list.innerHTML = `<div class="empty-row">${escapeHtml(t("providers.empty"))}</div>`;
    return;
  }
  list.innerHTML = providers
    .map(
      (provider) => `
        <div class="provider-item" data-provider-id="${escapeHtml(provider.id)}">
          <input class="provider-name" type="text" value="${escapeHtml(provider.name)}" aria-label="${escapeHtml(t("providers.name"))}" />
          <select class="provider-kind" aria-label="${escapeHtml(t("providers.kind.api"))}">
            <option value="api" ${provider.kind === "api" ? "selected" : ""}>${escapeHtml(t("providers.kind.api"))}</option>
            <option value="local" ${provider.kind === "local" ? "selected" : ""}>${escapeHtml(t("providers.kind.local"))}</option>
          </select>
          <input class="provider-base-url" type="text" value="${escapeHtml(provider.base_url)}" aria-label="${escapeHtml(t("providers.baseUrl"))}" />
          <input class="provider-model" type="text" value="${escapeHtml(provider.model)}" aria-label="${escapeHtml(t("providers.model"))}" />
          <input class="provider-api-key" type="password" value="${escapeHtml(provider.api_key || "")}" placeholder="${escapeHtml(t("providers.apiKey"))}" aria-label="${escapeHtml(t("providers.apiKey"))}" />
          <div class="provider-actions">
            <label class="switch" title="${escapeHtml(t("providers.enabled"))}">
              <input class="provider-enabled" type="checkbox" ${provider.enabled ? "checked" : ""} />
              <span></span>
            </label>
            <button class="icon-button provider-default" type="button" title="${escapeHtml(t("providers.setDefault"))}" aria-label="${escapeHtml(t("providers.setDefault"))}">
              <i data-lucide="${provider.id === defaultProviderId ? "star" : "star-off"}"></i>
            </button>
            <button class="icon-button provider-delete" type="button" title="${escapeHtml(t("providers.delete"))}" aria-label="${escapeHtml(t("providers.delete"))}">
              <i data-lucide="trash-2"></i>
            </button>
          </div>
        </div>
      `,
    )
    .join("");
  list.querySelectorAll(".provider-default").forEach((button) => {
    button.addEventListener("click", () => {
      state.settings.default_provider_id = button.closest(".provider-item").dataset.providerId;
      renderProviders(collectProviders(), state.settings.default_provider_id);
    });
  });
  list.querySelectorAll(".provider-delete").forEach((button) => {
    button.addEventListener("click", () => {
      const item = button.closest(".provider-item");
      item.remove();
      const providers = collectProviders();
      if (!providers.some((provider) => provider.id === state.settings.default_provider_id)) {
        state.settings.default_provider_id = providers[0]?.id || null;
      }
      renderProviders(providers, state.settings.default_provider_id);
    });
  });
  window.lucide?.createIcons();
}

function collectProviders() {
  return Array.from(document.querySelectorAll(".provider-item")).map((item) => ({
    id: item.dataset.providerId,
    name: item.querySelector(".provider-name").value.trim() || t("providers.new"),
    kind: item.querySelector(".provider-kind").value,
    base_url: item.querySelector(".provider-base-url").value.trim(),
    model: item.querySelector(".provider-model").value.trim(),
    api_key: item.querySelector(".provider-api-key").value,
    enabled: item.querySelector(".provider-enabled").checked,
  }));
}

function nextSettingsPatch(section) {
  const current = state.settings || {};
  return {
    general: section === "general" ? collectGeneralSettings() : current.general,
    providers: section === "providers" ? collectProviders() : current.providers || [],
    default_provider_id: current.default_provider_id || collectProviders()[0]?.id || null,
    hotkeys: section === "hotkeys" ? collectHotkeySettings() : current.hotkeys,
  };
}

function bindSettings() {
  document.querySelectorAll(".settings-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const page = tab.dataset.settingsPage;
      document.querySelectorAll(".settings-tab").forEach((item) => item.classList.toggle("active", item === tab));
      document.querySelectorAll(".settings-page").forEach((panel) => {
        panel.classList.toggle("active", panel.dataset.settingsPagePanel === page);
      });
    });
  });

  $("#setting-language").addEventListener("change", () => {
    const next = collectGeneralSettings();
    state.settings = state.settings || {};
    state.settings.general = next;
    applyGeneralSettings(next);
  });

  $("#save-general").addEventListener("click", async () => {
    try {
      await saveSettings(nextSettingsPatch("general"));
      showToast(t("toast.generalSaved"));
    } catch (error) {
      showToast(error.message);
    }
  });

  $("#add-provider").addEventListener("click", () => {
    const providers = collectProviders();
    const id = `provider-${Date.now().toString(36)}`;
    providers.push({
      id,
      name: t("providers.new"),
      kind: "api",
      base_url: "https://api.openai.com/v1",
      model: "gpt-4o-mini",
      api_key: "",
      enabled: true,
    });
    if (!state.settings.default_provider_id) {
      state.settings.default_provider_id = id;
    }
    renderProviders(providers, state.settings.default_provider_id);
  });

  $("#save-providers").addEventListener("click", async () => {
    try {
      await saveSettings(nextSettingsPatch("providers"));
      showToast(t("toast.providersSaved"));
    } catch (error) {
      showToast(error.message);
    }
  });

  $("#save-hotkeys").addEventListener("click", async () => {
    try {
      await saveSettings(nextSettingsPatch("hotkeys"));
      showToast(t("toast.hotkeysSaved"));
    } catch (error) {
      showToast(error.message);
    }
  });

  window.addEventListener("hashchange", syncRouteFromHash);
  syncRouteFromHash();
}

function syncRouteFromHash() {
  const route = (window.location.hash || "#home").replace("#", "");
  const activeRoute = ROUTES.includes(route) ? route : "home";
  if (route !== activeRoute) {
    window.location.hash = `#${activeRoute}`;
    return;
  }
  document.querySelectorAll(".app-view").forEach((view) => {
    view.classList.toggle("active", view.id === activeRoute);
  });
  document.querySelectorAll(".nav-item").forEach((item) => {
    if (item.getAttribute("href")?.startsWith("#")) {
      item.classList.toggle("active", item.getAttribute("href") === `#${activeRoute}`);
    }
  });
}

function bindForms() {
  $("#refresh-health").addEventListener("click", () => loadHealth().then(() => showToast(t("toast.statusRefreshed"))).catch((error) => showToast(error.message)));

  $("#global-search").addEventListener("submit", (event) => {
    event.preventDefault();
    const query = $("#global-query").value;
    $("#search-query").value = query;
    location.hash = "#repository";
    runSearch(query).catch((error) => showToast(error.message));
  });

  $("#library-search").addEventListener("submit", (event) => {
    event.preventDefault();
    runSearch($("#search-query").value).catch((error) => showToast(error.message));
  });

  $("#clear-search").addEventListener("click", () => {
    $("#search-query").value = "";
    $("#global-query").value = "";
    state.searchHasRun = false;
    state.searchResultCount = 0;
    updateSearchCount();
    renderEmptySearch("repository.noSearch");
  });

  $("#import-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const pdfDir = $("#pdf-dir").value.trim();
    const bibFile = $("#bib-file").value.trim();
    if (!pdfDir && !bibFile) {
      showToast(t("repository.importInputMissing"));
      return;
    }
    state.importState = "state.importing";
    updateImportChip();
    try {
      const payload = await request("/library/import", {
        method: "POST",
        body: JSON.stringify({ pdf_dir: pdfDir || null, bib_file: bibFile || null }),
      });
      $("#papers-imported").textContent = payload.papers_imported;
      $("#bib-imported").textContent = payload.bib_entries_imported;
      $("#chunks-indexed").textContent = payload.chunks_indexed;
      state.importState = "state.ready";
      updateImportChip();
      showToast(payload.warnings?.length ? payload.warnings[0] : t("repository.imported"));
    } catch (error) {
      state.importState = "state.failed";
      updateImportChip();
      showToast(error.message);
    }
  });

  $("#read-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = $("#read-question").value.trim();
    if (!question) return;
    $("#read-output").textContent = t("state.loading");
    try {
      const payload = await request("/read/ask", {
        method: "POST",
        body: JSON.stringify({ question, top_k: Number($("#read-top-k").value || 6) }),
      });
      $("#read-output").textContent = payload.answer || "-";
    } catch (error) {
      $("#read-output").textContent = error.message;
    }
  });

  document.querySelectorAll(".segment").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".segment").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      state.writeAction = button.dataset.action;
    });
  });

  $("#write-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = $("#write-text").value.trim();
    if (!text) return;
    $("#write-output").textContent = t("state.loading");
    try {
      const payload = await request("/write/assist", {
        method: "POST",
        body: JSON.stringify({
          text,
          action: state.writeAction,
          context: $("#write-context").value.trim() || null,
          top_k: 4,
        }),
      });
      $("#write-output").textContent = payload.result || "-";
    } catch (error) {
      $("#write-output").textContent = error.message;
    }
  });

  $("#cite-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = $("#cite-query").value.trim();
    if (!query) return;
    $("#cite-output").textContent = t("state.loading");
    try {
      const payload = await request("/cite/insert", {
        method: "POST",
        body: JSON.stringify({ query, style: $("#cite-style").value, top_k: 5 }),
      });
      if (payload.citation) {
        $("#cite-output").textContent = payload.citation;
        await navigator.clipboard?.writeText(payload.citation).catch(() => undefined);
      } else {
        $("#cite-output").textContent = [
          payload.message || t("citation.multiple"),
          ...(payload.candidates || []).map((item) => `${item.bibtex_key} - ${item.title || t("citation.untitled")}`),
        ].join("\n");
      }
    } catch (error) {
      $("#cite-output").textContent = error.message;
    }
  });
}

window.addEventListener("DOMContentLoaded", () => {
  bindForms();
  bindSettings();
  renderEmptySearch("repository.noSearch");
  applyI18n();
  loadHealth().catch((error) => showToast(error.message));
  loadSettings().catch((error) => showToast(error.message));
  window.setTimeout(() => window.lucide?.createIcons(), 0);
});
