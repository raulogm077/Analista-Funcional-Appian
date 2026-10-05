/* ==========================================================================
   Appian Kit runtime — renderiza un app spec (JSON con componentes SAIL reales)
   como prototipo navegable. Sin dependencias. Lo inyecta build.py.
   ========================================================================== */
(function () {
  "use strict";
  const $json = (id) => { const el = document.getElementById(id); return el ? JSON.parse(el.textContent) : null; };
  const SPEC = $json("px-spec");
  const BRAND = $json("px-brand") || {};
  const ICONS = $json("px-icons") || {};
  const LOGO = (document.getElementById("px-logo") || {}).innerHTML || "";
  const LANG = (SPEC.app && SPEC.app.language) || "es";
  const T = {
    es: { next: "Siguiente", prev: "Anterior", req: "Se requiere un valor", search: "Buscar", export: "Exportar a Excel", of: "de", empty: "No hay elementos disponibles", cancel: "Cancelar", upload: "Subir archivos", drop: "o arrastre los archivos aquí", select: "Seleccione un valor", yes: "Sí", no: "No", step: "Paso", filters: "Filtros", clear: "Borrar filtro", add: "Añadir", confirm: "Confirmar", noValue: "–", results: "resultados" },
    en: { next: "Next", prev: "Back", req: "A value is required", search: "Search", export: "Export to Excel", of: "of", empty: "No items available", cancel: "Cancel", upload: "Upload", drop: "or drop files here", select: "Select a value", yes: "Yes", no: "No", step: "Step", filters: "Filters", clear: "Clear filter", add: "Add", confirm: "Confirm", noValue: "–", results: "results" }
  }[LANG] || {};

  /* ---------------- state ---------------- */
  const S = {};                 // local!/ri!/pv! variables
  const UI = {};                // estado de UI: pestañas, páginas de grid, secciones, pasos de wizard
  let route = null;             // { screen, params, view }
  const hist = [];
  let dialogs = [];             // [{ screen, params }]
  let confirmBox = null;        // { header, message, onOk, color }
  const invalid = {};           // screenId -> true cuando se ha intentado enviar con errores
  let REQ = [];                 // registro de campos requeridos del render actual
  let VALS = [];                // validaciones ($validations) activas en el render actual
  const NODES = {};             // path -> node (inspector)
  let inspector = false, capture = false, panel = null;

  const screens = SPEC.screens || [];
  const byId = Object.fromEntries(screens.map((s) => [s.id, s]));
  const datasets = SPEC.data || {};

  function initState(obj) { if (obj) for (const k in obj) S[k] = clone(obj[k]); }
  function clone(v) { return v == null ? v : JSON.parse(JSON.stringify(v)); }
  initState(SPEC.state);

  /* ---------------- helpers ---------------- */
  function h(tag, attrs, ...kids) {
    const el = document.createElement(tag);
    if (attrs) for (const k in attrs) {
      const v = attrs[k];
      if (v == null || v === false) continue;
      if (k === "class") el.className = v;
      else if (k === "style" && typeof v === "object") { for (const sk in v) { const sv = v[sk]; if (sv == null || sv === "") continue; if (sk.startsWith("--")) el.style.setProperty(sk, sv); else el.style[sk] = sv; } }
      else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
      else if (k === "html") el.innerHTML = v;
      else el.setAttribute(k, v === true ? "" : v);
    }
    add(el, kids);
    return el;
  }
  function add(el, kids) {
    for (const c of kids.flat(Infinity)) {
      if (c == null || c === false || c === "") continue;
      el.appendChild(c instanceof Node ? c : document.createTextNode(String(c)));
    }
    return el;
  }
  function icon(name, cls) {
    const d = ICONS[name];
    const span = document.createElement("span");
    span.style.display = "inline-flex";
    if (cls) span.className = cls;
    span.innerHTML = d
      ? `<svg class="ic" viewBox="${d[0]}" aria-hidden="true"><path d="${d[1]}"/></svg>`
      : `<svg class="ic" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6"/></svg>`;
    return span;
  }
  const arr = (v) => (v == null ? [] : Array.isArray(v) ? v : [v]);
  const isEmpty = (v) => v == null || v === "" || (Array.isArray(v) && v.length === 0);
  const up = (s) => (s || "").toString().toUpperCase();

  // colores con nombre de gráficos y líneas de referencia (Appian no publica los hex: aproximaciones)
  const NAMED = { BLUEGRAY: "#5b6f82", GREEN: "#2e8540", GOLD: "#c19a1e", ORANGE: "#e8772e", PURPLE: "#7a5cc2", RED: "#d0342c", SKYBLUE: "#3e9bd6", LIMEGREEN: "#7cb82f", YELLOW: "#e8c21c", AMBER: "#f0a202", PINK: "#e0609a", VIOLETRED: "#b8246d" };
  const SEM = Object.assign({ ACCENT: "var(--accent)", POSITIVE: "var(--positive)", NEGATIVE: "var(--negative)", WARN: "var(--warn)", INFO: "var(--info)", SECONDARY: "var(--text-2)", STANDARD: "inherit", TRANSPARENT: "transparent" }, NAMED);
  const SEMBG = { ACCENT: "var(--accent-tint)", POSITIVE: "var(--bg-positive)", NEGATIVE: "var(--bg-negative)", SUCCESS: "var(--bg-positive)", ERROR: "var(--bg-negative)", WARN: "var(--bg-warn)", INFO: "var(--bg-info)", SECONDARY: "#eceef0", STANDARD: "var(--std-bg)", TRANSPARENT: "transparent" };
  // hex reales para calcular el contraste del texto sobre colores semánticos sólidos
  // (colores estándar de Appian; start() los sustituye por los del perfil CSS de la marca, que build.py pone en :root)
  const SEMHEX = { POSITIVE: "#117c00", NEGATIVE: "#b2002c", WARN: "#d97706", INFO: "#115ebb", SECONDARY: "#666666" };
  function color(v, fallback) { if (!v) return fallback; const u = String(v); if (u.startsWith("#")) return u; return SEM[up(u)] || fallback; }
  function hexOf(c) { if (!c) return null; const u = String(c); if (u.startsWith("#")) return u; if (up(u) === "ACCENT") return (BRAND.site && BRAND.site.accentColor) || "#1d659c"; return SEMHEX[up(u)] || NAMED[up(u)] || null; }
  function solidFg(c) {
    let hex = c;
    if (!hex || !hex.startsWith("#")) {
      const map = { "var(--accent)": BRAND.site && BRAND.site.accentColor, "var(--negative)": SEMHEX.NEGATIVE, "var(--positive)": SEMHEX.POSITIVE, "var(--warn)": SEMHEX.WARN, "var(--info)": SEMHEX.INFO, "var(--text-2)": "#666666" };
      hex = map[c] || "#1d659c";
    }
    hex = hex.replace("#", "");
    if (hex.length === 3) hex = hex.split("").map((x) => x + x).join("");
    // #RRGGBBAA (tinte con transparencia): se compone sobre blanco antes de elegir
    const al = hex.length === 8 ? parseInt(hex.slice(6), 16) / 255 : 1;
    hex = hex.slice(0, 6);
    const [r, g, b] = [0, 2, 4].map((i) => (parseInt(hex.substr(i, 2), 16) * al + 255 * (1 - al)) / 255).map((x) => (x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4)));
    const L = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    // el que más contraste da (blanco frente a casi negro #1a1a1a, L = 0,0103): el cruce está en L ≈ 0,19
    return (L + 0.05) / (0.0103 + 0.05) > 1.05 / (L + 0.05) ? "#1a1a1a" : "#ffffff";
  }

  // contraste WCAG 2.x (fórmula de luminancia relativa): texto normal 4,5:1, texto grande y controles 3:1
  const rgbOf = (hex) => { let x = String(hex || "").replace("#", "").slice(0, 6); if (x.length === 3) x = x.split("").map((c) => c + c).join(""); return /^[0-9a-f]{6}$/i.test(x) ? [0, 2, 4].map((i) => parseInt(x.substr(i, 2), 16)) : null; };
  const lumOf = (hex) => { const c = rgbOf(hex); if (!c) return null; const [r, g, b] = c.map((v) => v / 255).map((v) => (v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4))); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const contrastOf = (a, b) => { const la = lumOf(a), lb = lumOf(b); return la == null || lb == null ? null : (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05); };
  const mixHex = (a, b, t) => { const x = rgbOf(a), y = rgbOf(b); return "#" + x.map((v, i) => Math.round(v * (1 - t) + y[i] * t).toString(16).padStart(2, "0")).join(""); };
  const SCHEME_HEX = { CHARCOAL_SCHEME: "#2e2e35", NAVY_SCHEME: "#0f203a", PLUM_SCHEME: "#3c2a4d" };
  // 26.9 (Improved link visibility): los enlaces ajustan su color al fondo. Candidatos: el color de resaltado del site y el de acento
  // aclarado u oscurecido lo justo para llegar a 4,5:1 sobre el fondo.
  function readableOn(bg, cands, need) {
    need = need || 4.5;
    if (!rgbOf(bg)) return null;
    for (const c of cands.filter(rgbOf)) if (contrastOf(c, bg) >= need) return c;
    const base = cands.find(rgbOf) || "#1d659c", to = lumOf(bg) < 0.18 ? "#ffffff" : "#000000";
    for (let k = 1; k <= 10; k++) { const c = mixHex(base, to, k / 10); if (contrastOf(c, bg) >= need) return c; }
    return to;
  }
  const accentHex = () => (BRAND.site && BRAND.site.accentColor) || "#1d659c";
  const linkOn = (bg) => readableOn(bg, [accentHex(), (BRAND.site || {}).selectedPageHighlightColor]);
  // contenedor con fondo oscuro (hex o esquema): marca .ondark y fija el color de enlace legible sobre ese fondo
  function darkProps(bg) {
    const hex = SCHEME_HEX[up(bg)] || (String(bg || "").startsWith("#") ? String(bg).slice(0, 7) : null);
    if (!hex || !rgbOf(hex) || solidFg(hex) !== "#ffffff") return null;
    return { cls: " ondark", vars: { "--lnk": linkOn(hex) } };
  }

  /* ---------------- expressions ---------------- */
  const FN = {
    _if: (c, a, b) => (truthy(c) ? a : b),
    _and: (...a) => a.every(truthy), _or: (...a) => a.some(truthy), _not: (a) => !truthy(a),
    _isnull: (a) => isEmpty(a), _notnull: (a) => !isEmpty(a),
    _contains: (a, v) => arr(a).map(String).includes(String(v)),
    _len: (a) => (a == null ? 0 : a.length), _count: (a) => arr(a).length,
    _sum: (...a) => a.flat().reduce((x, y) => x + (Number(y) || 0), 0),
    _upper: (s) => up(s), _lower: (s) => (s || "").toString().toLowerCase(),
    _today: () => (SPEC.app && SPEC.app.today) || new Date().toISOString().slice(0, 10),
    _now: () => (SPEC.app && SPEC.app.today ? SPEC.app.today + "T09:00:00" : new Date().toISOString()),
    // fechas como número de días (permite restar fechas: todate(b) - todate(a) > 90)
    _todate: (v) => { if (v == null || v === "") return null; const m = String(v).match(/^(\d{4})-(\d{2})-(\d{2})/); return m ? Math.round(Date.UTC(+m[1], +m[2] - 1, +m[3]) / 86400000) : null; },
    _tointeger: (v) => (v == null || v === "" ? null : Math.trunc(Number(v))),
    _text: (v) => (v == null ? "" : String(v)),
    _index: (a, i, d) => { const x = arr(a)[Number(i) - 1]; return x === undefined ? d : x; },
    _where: (a) => arr(a).map((x, i) => (truthy(x) ? i + 1 : null)).filter((x) => x != null),
    _displayvalue: (v, from, to, d) => { const i = arr(from).map(String).indexOf(String(v)); return i >= 0 ? arr(to)[i] : d; },
    _rows: (name, filter) => rowsOf(name).filter((r) => !filter || truthy(evalExpr(filter, { row: r }))),
    // listas (patrones de lista doble, entradas dinámicas…)
    _append: (a, ...b) => arr(a).concat(...b.map((x) => arr(x))),
    _difference: (a, b) => { const bs = arr(b).map(String); return arr(a).filter((x) => !bs.includes(String(x))); },
    _union: (a, b) => { const out = []; for (const x of arr(a).concat(arr(b))) if (!out.map(String).includes(String(x))) out.push(x); return out; },
    _remove: (a, i) => { const is = arr(i).map(Number); return arr(a).filter((x, k) => !is.includes(k + 1)); },
    _wherecontains: (v, a) => { const vs = arr(v).map(String); return arr(a).map((x, k) => (vs.includes(String(x)) ? k + 1 : null)).filter((x) => x != null); },
    _joinarray: (a, sep) => arr(a).join(sep == null ? "" : sep),
    _left: (t, n) => String(t == null ? "" : t).slice(0, Number(n) || 0),
    _search: (f, w) => String(w == null ? "" : w).toLowerCase().indexOf(String(f == null ? "" : f).toLowerCase()) + 1,
    _defaultvalue: (v, d) => (isEmpty(v) ? d : v),
  };
  function truthy(v) { return Array.isArray(v) ? v.length > 0 : !!v; }
  const exprCache = {};
  // campo de un registro o de una lista de registros (como en SAIL: lista.campo devuelve lista)
  FN._p = (o, f) => (Array.isArray(o) ? o.map((x) => (x == null ? null : x[f])) : o == null ? undefined : o[f]);
  const chain = (base, rest) => (rest || "").split(".").filter(Boolean).reduce((acc, f) => `_p(${acc},"${f}")`, base);
  function compile(src) {
    if (exprCache[src]) return exprCache[src];
    const parts = src.split(/("(?:[^"\\]|\\.)*")/);
    const out = parts.map((p, i) => {
      if (i % 2) return p;
      return p
        // referencias a campos de registro: fv!row[recordType!X.fields.campo] → fv!row.campo; puntuación de búsqueda inteligente → .similarityScore
        .replace(/\[\s*recordType![\w ]+?\.searchResults\.\w+\.similarityScore\s*\]/g, ".similarityScore")
        .replace(/\[\s*recordType![\w ]+?\.fields\.(\w+)\s*\]/g, ".$1")
        .replace(/\b(local|ri|pv)!([A-Za-z_][\w]*)((?:\.[A-Za-z_]\w*)*)/g, (m, ns, n, rest) => chain(`_v("${ns}!${n}")`, rest))
        .replace(/\bfv!(row|item|index|value|isFirst|isLast|data|percentage|identifier|selection|nodeValue)((?:\.[A-Za-z_]\w*)*)/g, (m, n, rest) => chain(`_fv("${n}")`, rest))
        .replace(/\brv!record((?:\.[A-Za-z_]\w*)*)/g, (m, rest) => chain("_rec()", rest))
        .replace(/\bdata!([A-Za-z_]\w*)/g, '_rows("$1")')
        .replace(/\ba!isNullOrEmpty\(/g, "_isnull(").replace(/\ba!isNotNullOrEmpty\(/g, "_notnull(").replace(/\ba!defaultValue\(/g, "_defaultvalue(")
        .replace(/\b(if|and|or|not|isnull|contains|len|length|count|sum|upper|lower|today|now|todate|tointeger|text|index|where|displayvalue|rows|append|difference|union|remove|wherecontains|joinarray|left|search)\(/gi, (m, f) => `_${f.toLowerCase() === "length" ? "len" : f.toLowerCase()}(`)
        .replace(/<>/g, "!=").replace(/([^<>!=])=(?!=)/g, "$1==").replace(/&/g, "+")
        .replace(/\bnull\b/g, "null").replace(/\btrue\b/gi, "true").replace(/\bfalse\b/gi, "false")
        .replace(/\{/g, "[").replace(/\}/g, "]"); // listas SAIL {a, b} → arrays
    }).join("");
    let fn;
    try { fn = new Function("_v", "_fv", "_rec", "F", `with(F){ return (${out}); }`); }
    catch (e) { console.warn("Expresión no válida:", src, "→", out); fn = () => undefined; }
    return (exprCache[src] = fn);
  }
  function evalExpr(src, ctx) {
    ctx = ctx || {};
    try {
      return compile(src)((k) => (ctx.locals && k in ctx.locals ? ctx.locals[k] : S[k]), (k) => (ctx.fv || {})[k] ?? (k === "row" ? ctx.row : k === "item" || k === "data" ? ctx.item : k === "index" ? ctx.index : undefined), () => ctx.record, FN);
    } catch (e) { return undefined; }
  }
  const FILTERS = {
    date: (v) => { if (!v) return ""; const m = String(v).match(/^(\d{4})-(\d{2})-(\d{2})/); return m ? `${m[3]}/${m[2]}/${m[1]}` : v; },
    datetime: (v) => { if (!v) return ""; const m = String(v).match(/^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}))?/); return m ? `${m[3]}/${m[2]}/${m[1]}${m[4] ? " " + m[4] + ":" + m[5] : ""}` : v; },
    // separador de miles también con 4 cifras (6.000,00 €), como Appian: de-DE usa los mismos separadores que es-ES y siempre agrupa
    eur: (v) => (v == null || v === "" ? "" : Number(v).toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €"),
    num: (v) => (v == null || v === "" ? "" : Number(v).toLocaleString(LANG === "es" ? "de-DE" : "en-GB", { maximumFractionDigits: 2 })),
    pct: (v) => (v == null ? "" : `${v} %`),
    upper: (v) => up(v),
    initials: (v) => (v || "").split(/\s+/).filter(Boolean).slice(0, 2).map((x) => x[0]).join("").toUpperCase(),
    dash: (v) => (v == null || v === "" || (Array.isArray(v) && !v.length) ? "–" : v),
    // fechas en texto (calendarios, comentarios): «lunes, 5 de octubre», «octubre de 2026», «lunes», «5 oct», «09:30»
    longdate: (v) => fmtDate(v, "long"), monthyear: (v) => fmtDate(v, "month"), dayname: (v) => fmtDate(v, "day"), daymonth: (v) => fmtDate(v, "short"),
    time: (v) => { const m = String(v || "").match(/T(\d{2}):(\d{2})/); return m ? `${m[1]}:${m[2]}` : ""; },
  };
  function fmtDate(v, kind) {
    const m = String(v || "").match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (!m) return v || "";
    const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
    const es = LANG === "es";
    const DN = es ? ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"] : ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    const MN = es ? ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"] : ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const day = DN[d.getUTCDay()], mon = MN[+m[2] - 1], dd = +m[3];
    const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
    if (kind === "long") return es ? cap(`${day}, ${dd} de ${mon}`) : `${day}, ${mon} ${dd}`;
    if (kind === "month") return es ? cap(`${mon} de ${m[1]}`) : `${mon} ${m[1]}`;
    if (kind === "day") return cap(day);
    return es ? `${dd} ${mon.slice(0, 3)}` : `${mon.slice(0, 3)} ${dd}`;
  }
  function interp(str, ctx) {
    if (typeof str !== "string") return str;
    const whole = str.match(/^\{([^{}]+)\}$/);
    if (whole) return token(whole[1], ctx);
    if (/^(local|ri|pv)![A-Za-z_]\w*(\.\w+)*$/.test(str) || /^fv!(row|item|index|data)(\.\w+)*$/.test(str) || /^rv!record(\.\w+)*$/.test(str)) return evalExpr(str, ctx);
    if (str.indexOf("{") < 0) return str;
    return str.replace(/\{([^{}]+)\}/g, (m, t) => { const v = token(t, ctx); return v == null ? "" : Array.isArray(v) ? v.join(", ") : v; });
  }
  function token(t, ctx) {
    const [e, ...fs] = t.split("|").map((x) => x.trim());
    let v = evalExpr(e, ctx);
    for (const f of fs) {
      const [fname, arg] = f.split(":");
      if (fname === "map") { const m = (SPEC.maps || {})[arg] || {}; v = m[v] !== undefined ? m[v] : m["*"]; }
      else if (FILTERS[fname]) v = FILTERS[fname](v);
    }
    return v;
  }
  const BOOL_PARAMS = new Set(["showWhen", "disabled", "required", "readOnly", "isCollapsible", "isInitiallyCollapsed", "disableNextButton", "selectionDisabled", "isThumbnail"]);
  function P(node, key, ctx, dflt) {
    let v = node[key];
    if (v === undefined) return dflt;
    if (typeof v === "string") {
      if (BOOL_PARAMS.has(key)) return truthy(evalExpr(v.replace(/^[{=]|\}$/g, ""), ctx));
      v = interp(v, ctx);
    }
    return v === undefined ? dflt : v;
  }
  const visible = (node, ctx) => node && (node.showWhen === undefined || P(node, "showWhen", ctx, true));

  /* ---------------- data ---------------- */
  function dsByRecordType(rt) {
    const name = String(rt || "").replace(/^recordType!/, "").split(".")[0];
    for (const k in datasets) if (datasets[k].recordType === name) return k;
    return null;
  }
  function rowsOf(ref) {
    if (Array.isArray(ref)) return ref;
    if (ref == null) return [];
    let k = String(ref);
    if (k.startsWith("data!")) k = k.slice(5);
    else if (k.startsWith("recordType!")) k = dsByRecordType(k);
    else if (/^(local|ri|pv)!/.test(k)) return arr(S[k]);
    const d = datasets[k];
    return d ? (Array.isArray(d) ? d : d.rows || []) : [];
  }
  const fieldOf = (s) => String(s || "").split(".").pop().replace(/[\]'"]/g, "");

  /* ---------------- bindings ---------------- */
  function refOf(node, key, ctx) {
    const r = node[key];
    if (typeof r !== "string") return null;
    const m = r.match(/^fv!(item|row)((?:\.\w+)*)$/);
    if (m && ctx.itemRef) return { path: ctx.itemRef, index: ctx.srcIndex != null ? ctx.srcIndex : ctx.index - 1, fields: m[2] ? m[2].slice(1).split(".") : [] }; // fv!item solo: listas de valores simples; con $filter, la posición en la lista original
    const v = r.match(/^((?:local|ri|pv)![A-Za-z_]\w*)((?:\.\w+)*)$/);
    if (v) return { path: v[1], fields: v[2] ? v[2].slice(1).split(".") : [] };
    return null;
  }
  function readRef(r) {
    let cur = S[r.path];
    if (r.index != null) cur = arr(cur)[r.index];
    for (const f of r.fields || []) cur = cur == null ? undefined : cur[f];
    return cur;
  }
  function getVal(node, ctx) {
    const r = refOf(node, "value", ctx);
    if (r) return readRef(r);
    return P(node, "value", ctx);
  }
  function setIn(obj, fields, v) {
    if (!fields.length) return v;
    const [f, ...rest] = fields;
    const base = obj && typeof obj === "object" ? (Array.isArray(obj) ? obj.slice() : Object.assign({}, obj)) : {};
    base[f] = setIn(base[f], rest, v);
    return base;
  }
  function writeRef(r, v) {
    if (!r) return;
    if (r.index != null) { const a = arr(S[r.path]).slice(); a[r.index] = setIn(a[r.index], r.fields || [], v); S[r.path] = a; }
    else S[r.path] = setIn(S[r.path], r.fields || [], v);
  }
  function saveInto(node, v, ctx, key) {
    key = key || "saveInto";
    const targets = arr(node[key]);
    for (const t of targets) {
      if (typeof t === "string") { const r = refOf({ x: t }, "x", ctx); writeRef(r, v); }
      else if (t && t.type === "a!save") {
        const r = refOf({ x: t.target }, "x", ctx);
        let val = t.value;
        if (val === "save!value") val = v;
        else if (typeof val === "string" && val.startsWith("save!value.")) val = val.slice(11).split(".").reduce((o, f) => (o == null ? o : o[f]), v); // p. ej. outputsSaveInto: save!value.decision
        else if (typeof val === "string") val = interp(val, ctx);
        writeRef(r, clone(val));
      }
    }
  }

  /* ---------------- actions ---------------- */
  function findScreenForRecord(rt) {
    const name = String(rt || "").replace(/^recordType!/, "").split(".")[0];
    return screens.find((s) => s.type === "record" && s.recordType === name);
  }
  function deepInterp(v, ctx) {
    if (typeof v === "string") return v.includes("{") ? interp(v, ctx) : v;
    if (Array.isArray(v)) return v.map((x) => deepInterp(x, ctx));
    if (v && typeof v === "object") return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, deepInterp(x, ctx)]));
    return v;
  }
  function runAction(act, ctx, srcNode) {
    for (const a of arr(act)) {
      if (!a) continue;
      const params = {};
      if (a.params) for (const k in a.params) params[k] = interp(a.params[k], ctx);
      // cambios de variables en el orden en que se escriben (como la lista de a!save de un saveInto); append y prepend
      // evalúan las {expresiones} del elemento que añaden (p. ej. el texto de un comentario nuevo antes de vaciar el campo)
      for (const op of Object.keys(a)) {
        if (op === "set") for (const k in a.set) { const v = a.set[k]; S[k] = typeof v === "string" ? interp(v, ctx) : clone(v); }
        else if (op === "append") for (const k in a.append) S[k] = arr(S[k]).concat([deepInterp(clone(a.append[k]), ctx)]);
        else if (op === "prepend") for (const k in a.prepend) S[k] = [deepInterp(clone(a.prepend[k]), ctx)].concat(arr(S[k]));
        else if (op === "remove") for (const k in a.remove) { const i = Number(interp(a.remove[k], ctx)) - 1; S[k] = arr(S[k]).filter((x, j) => j !== i); }
      }
      if (a.close) closeDialog();
      if (a.closeAll) dialogs = [];
      if (a.back) back();
      if (a.goto) go(interp(a.goto, ctx), params, { view: a.view });
      if (a.dialog) openDialog(interp(a.dialog, ctx), params);
      if (a.step) wizardStep(a.step, ctx);
      if (a.url) window.open(a.url, "_blank", "noopener");
    }
    rerender();
  }
  // $action.step: salta al paso N (1 = primero) del asistente de la pantalla (enlaces «Editar» del paso de revisión)
  function wizardStep(step, ctx) { const base = String(ctx.scope || "").split(":")[0]; UI["wiz:" + base] = Math.max(0, Number(interp(step, ctx)) - 1); }
  function clickable(node, ctx) {
    // a!dynamicLink, a!recordLink, a!startProcessLink, a!safeLink, buttons...
    return (ev) => {
      if (inspector) return;
      if (ev) ev.preventDefault();
      if (node.saveInto) saveInto(node, P(node, "value", ctx), ctx);
      if (node.type === "a!recordLink") {
        const scr = findScreenForRecord(node.recordType);
        if (scr) return runAction(Object.assign({ goto: scr.id, params: { id: node.identifier }, view: node.dashboard }, node.$action || {}), ctx);
      }
      if (node.type === "a!safeLink" && node.uri && !node.$action) { window.open(interp(node.uri, ctx), "_blank", "noopener"); return; }
      if (node.type === "a!pageLink" && !node.$action) {
        const pg = String(interp(node.page || "", ctx)).split(/[.!]/).pop().toLowerCase();
        const sp = arr(SPEC.site && SPEC.site.pages).find((x) => [x.id, x.screen, x.label, x.name].filter(Boolean).map((v) => String(v).toLowerCase()).includes(pg));
        const target = sp ? sp.screen : (screens.find((x) => x.id.toLowerCase() === pg) || {}).id;
        if (target) return runAction({ goto: target, params: node.urlParameters || {} }, ctx);
      }
      runAction(node.$action, ctx, node);
    };
  }
  function go(screenId, params, opt) {
    if (!byId[screenId]) { console.warn("Pantalla no encontrada:", screenId); return; }
    if (route) hist.push(route);
    route = { screen: screenId, params: params || {}, view: (opt && opt.view) || null };
    // entrar en una pantalla la carga de nuevo, como en Appian: secciones plegables, pestañas y grids vuelven a su estado inicial
    for (const k in UI) if (!k.startsWith("view:")) delete UI[k];
    UI["view:" + screenId] = (opt && opt.view) || null;
    dialogs = [];
    enterScreen(byId[screenId], route.params);
    window.scrollTo(0, 0);
  }
  function enterScreen(scr, params) {
    for (const k in S) if (k.startsWith("ri!")) delete S[k];
    if (params) for (const k in params) S["ri!" + k] = params[k];
    const lctx = screenCtx(scr, params);
    // los textos con {expresión} se evalúan también dentro de mapas y listas (p. ej. local!correo.asunto = "Estudio {rv!record.codigo}")
    const init = (v) => (typeof v === "string" ? (v.includes("{") ? interp(v, lctx) : v) : Array.isArray(v) ? v.map(init) : v && typeof v === "object" ? Object.fromEntries(Object.entries(v).map(([a, b]) => [a, init(b)])) : v);
    if (scr.local) for (const k in scr.local) S[k] = init(clone(scr.local[k]));
    delete invalid[scr.id];
    delete UI["wiz:" + scr.id];
  }
  function back() { if (hist.length) { route = hist.pop(); dialogs = []; } }
  function openDialog(id, params) {
    if (!byId[id]) { console.warn("Diálogo no encontrado:", id); return; }
    dialogs.push({ screen: id, params: params || {} });
    enterScreen(byId[id], params);
  }
  function closeDialog() { dialogs.pop(); }

  /* ---------------- validation ---------------- */
  function checkRequired(scope) {
    const miss = REQ.filter((r) => r.scope === scope && isEmpty(r.get()));
    const bad = VALS.filter((v) => v.scope === scope);
    return miss.length === 0 && bad.length === 0;
  }

  /* ---------------- component renderers ---------------- */
  const R = {};
  let pathSeq = 0;
  function render(node, ctx, key) {
    if (node == null) return null;
    if (typeof node === "string") return h("div", { class: "rt" }, interp(node, ctx));
    if (Array.isArray(node)) return node.map((n, i) => render(n, ctx, (key || "") + "." + i));
    if (!visible(node, ctx)) return null;
    const fn = R[node.type];
    const k = key || "n" + pathSeq++;
    const c = Object.assign({}, ctx, { key: k });
    let el;
    if (!fn) el = h("div", { class: "banner", style: { "--mbg": "#fff4e0", "--mhl": "#ff9f2f" } }, h("div", null, h("div", { class: "pt" }, `Componente no soportado en el prototipo: ${node.type}`)));
    else el = fn(node, c);
    if (el && el.nodeType === 1) {
      el.setAttribute("data-sail", node.type);
      el.setAttribute("data-k", k);
      if (node.$assumption) el.setAttribute("data-assume", "");
      NODES[k] = node;
    }
    return el;
  }
  const SPACE = { NONE: 0, EVEN_LESS: 4, LESS: 8, STANDARD: 16, MORE: 24, EVEN_MORE: 36 };
  const LAYOUT_NO_MARGIN = new Set(["a!columnsLayout", "a!sideBySideLayout", "a!cardLayout", "a!sectionLayout", "a!boxLayout", "a!cardGroupLayout", "a!billboardLayout", "a!tabLayout", "a!buttonArrayLayout", "a!headingField", "a!messageBanner", "a!horizontalLine"]);
  function stack(list, ctx, key) {
    const wrap = h("div", { class: "stack" });
    let prevBelow = null;
    const items = [];
    // como en SAIL, las listas anidadas ({a, {b, c}}) y las expresiones de a!forEach que devuelven listas se aplanan
    const pushItem = (n, c, k) => {
      if (Array.isArray(n)) n.forEach((x, j) => pushItem(x, c, `${k}.${j}`));
      else if (n && n.type === "a!forEach") forEachItems(n, c).forEach((it, j) => pushItem(it.node, it.ctx, `${k}.${j}`));
      else items.push({ node: n, ctx: c, key: k });
    };
    arr(list).forEach((n, i) => pushItem(n, ctx, `${key}.${i}`));
    for (const it of items) {
      const el = render(it.node, it.ctx, it.key);
      if (!el) continue;
      const n = it.node || {};
      const dfltBelow = typeof n === "object" && n.type === "a!headingField" ? "STANDARD" : "STANDARD";
      const above = SPACE[P(n, "marginAbove", it.ctx, "NONE")] || 0;
      if (prevBelow != null) el.style.marginTop = prevBelow + above + "px";
      else if (above) el.style.marginTop = above + "px";
      prevBelow = SPACE[P(n, "marginBelow", it.ctx, dfltBelow)];
      if (prevBelow == null) prevBelow = 16;
      wrap.appendChild(el);
    }
    return wrap;
  }
  function forEachItems(n, ctx) {
    const src = n.items;
    let items; let itemRef = null;
    if (typeof src === "string" && /^(local|ri|pv)!\w+$/.test(src) && !(ctx.locals && src in ctx.locals)) { items = arr(S[src]); itemRef = src; }
    else if (typeof src === "string" && /^(local|ri|pv|fv|rv)!\w+(\.\w+)*$/.test(src)) items = arr(evalExpr(src, ctx)); // fv!item.respuestas, local!x.adjuntos
    else if (typeof src === "string") items = arr(src.startsWith("{") || src.includes("(") ? evalExpr(src.replace(/^\{|\}$/g, ""), ctx) : rowsOf(src));
    else items = arr(src);
    // $local: variables de cada vuelta, como a!localVariables dentro de la expresión ({"local!comentario": "fv!item"})
    const withLocals = (c, it, i) => { if (!n.$local) return c; const loc = Object.assign({}, ctx.locals); const cc = Object.assign({}, c, { locals: loc }); for (const k in n.$local) loc[k] = typeof n.$local[k] === "string" ? interp(n.$local[k], cc) : clone(n.$local[k]); return cc; };
    let list = items.map((it, i) => ({ it, src: i }));
    if (n.$filter) list = list.filter((x, i) => truthy(evalExpr(n.$filter, withLocals(Object.assign({}, ctx, { item: x.it, row: x.it, index: i + 1 }), x.it, i))));
    if (n.$limit) list = list.slice(0, n.$limit);
    return list.map((x, i) => ({ node: n.expression, ctx: withLocals(Object.assign({}, ctx, { item: x.it, row: typeof x.it === "object" ? x.it : ctx.row, index: i + 1, srcIndex: x.src, itemRef }), x.it, i) }));
  }
  R["a!forEach"] = (n, ctx) => stack([n], ctx, ctx.key);

  /* ---- field wrapper ---- */
  function field(n, ctx, control, opt) {
    opt = opt || {};
    const lp = up(P(n, "labelPosition", ctx, ctx.labelPosition || "ABOVE"));
    const label = P(n, "label", ctx);
    const req = !!P(n, "required", ctx, false);
    const el = h("div", { class: `fld lp-${lp}` + (control && control.classList && control.classList.contains("ro-val") || /^a!(richTextDisplayField|tagField|linkField|stampField)$/.test(n.type) ? " ro" : "") });
    if (label && lp !== "COLLAPSED") {
      const help = P(n, "helpTooltip", ctx);
      el.appendChild(h("div", { class: "lbl" }, label, req ? h("span", { class: "req", "aria-hidden": "true" }, "*") : null, help ? h("span", { class: "help", title: help }, icon("question-circle")) : null));
    }
    const body = h("div", { class: "fbody" }, control);
    const instr = P(n, "instructions", ctx);
    if (instr) body.appendChild(h("div", { class: "instr" }, instr));
    const errs = [];
    if (opt.getValue && req && !P(n, "readOnly", ctx, false) && !P(n, "disabled", ctx, false)) {
      REQ.push({ scope: ctx.scope, get: opt.getValue });
      if (invalid[ctx.scope] && isEmpty(opt.getValue())) errs.push(P(n, "requiredMessage", ctx) || T.req);
    }
    if (invalid[ctx.scope]) for (const v of arr(n.validations)) if (v) errs.push(valMsg(v, ctx));
    for (const v of arr(n.$validations)) if (v && truthy(evalExpr(v.when, ctx))) { errs.push(interp(v.message, ctx)); VALS.push({ scope: ctx.scope }); }
    if (errs.length) { el.classList.add("err"); errs.forEach((e) => body.appendChild(h("div", { class: "ferr" }, icon("exclamation-circle"), e))); }
    el.appendChild(body);
    return el;
  }
  function readOnlyVal(v) { return h("div", { class: "ro-val" + (isEmpty(v) ? " empty" : "") }, isEmpty(v) ? T.noValue : Array.isArray(v) ? v.join(", ") : String(v)); }
  function schedule() { clearTimeout(schedule.t); schedule.t = setTimeout(rerender, 0); }

  /* ---- inputs ---- */
  function textLike(type, n, ctx, extra) {
    const ref = refOf(n, "saveInto", ctx) || refOf(n, "value", ctx);
    let v = getVal(n, ctx);
    const fmt = n.$format && FILTERS[n.$format];
    if (P(n, "readOnly", ctx, false)) return field(n, ctx, readOnlyVal(fmt ? fmt(v) : v));
    const disabled = P(n, "disabled", ctx, false);
    const al = { RIGHT: "right", CENTER: "center" }[up(P(n, "align", ctx))];
    const attrs = { class: "inp", id: "f-" + ctx.key, type, value: v == null ? "" : v, placeholder: P(n, "placeholder", ctx), disabled, "aria-label": P(n, "label", ctx), style: al ? `text-align:${al}` : null };
    if (extra) Object.assign(attrs, extra);
    const commit = (e) => { let val = e.target.value; if (type === "number") val = val === "" ? null : Number(val); if (val === "") val = null; saveInto(n, val, ctx); if (ref && !n.saveInto) writeRef(ref, val); schedule(); };
    let ctl;
    if (type === "textarea") { ctl = h("textarea", Object.assign(attrs, { rows: n.height === "TALL" ? 8 : n.height === "SHORT" ? 3 : 5, onchange: commit })); ctl.value = v == null ? "" : v; }
    else ctl = h("input", Object.assign(attrs, { onchange: commit }));
    let control = ctl;
    const limit = P(n, "characterLimit", ctx);
    if (limit || P(n, "showCharacterCount", ctx, false)) {
      const cc = h("div", { class: "charcount" }, `${(v || "").length}${limit ? " / " + limit : ""}`);
      ctl.addEventListener("input", (e) => (cc.textContent = `${e.target.value.length}${limit ? " / " + limit : ""}`));
      if (limit) ctl.setAttribute("maxlength", limit);
      control = h("div", { class: "fbody" }, ctl, cc);
    }
    return field(n, ctx, control, { getValue: () => getVal(n, ctx) });
  }
  R["a!textField"] = (n, ctx) => textLike("text", n, ctx);
  R["a!encryptedTextField"] = (n, ctx) => textLike("password", n, ctx);
  R["a!integerField"] = (n, ctx) => textLike("number", n, ctx, { step: 1 });
  R["a!floatingPointField"] = (n, ctx) => textLike("number", n, ctx, { step: "any" });
  R["a!paragraphField"] = (n, ctx) => textLike("textarea", n, ctx);
  function dateInput(n, ctx, withTime) {
    const v = getVal(n, ctx);
    if (P(n, "readOnly", ctx)) return field(n, ctx, readOnlyVal(withTime ? FILTERS.datetime(v) : FILTERS.date(v)));
    const es = LANG === "es";
    const show = (iso) => { if (!iso) return ""; const [d, t] = String(iso).split("T"); const [y, m, dd] = d.split("-"); return `${dd}/${m}/${y}${withTime && t ? " " + t.slice(0, 5) : ""}`; };
    const parse = (txt) => { const m = String(txt).trim().match(/^(\d{1,2})[\/.-](\d{1,2})[\/.-](\d{4})(?:\s+(\d{1,2}):(\d{2}))?$/); if (!m) return txt.trim() ? txt : null; const iso = `${m[3]}-${m[2].padStart(2, "0")}-${m[1].padStart(2, "0")}`; return withTime ? `${iso}T${(m[4] || "00").padStart(2, "0")}:${m[5] || "00"}` : iso; };
    const save = (val) => { saveInto(n, val, ctx); const r = refOf(n, "value", ctx); if (r && !n.saveInto) writeRef(r, val); schedule(); };
    const txt = h("input", { class: "inp", id: "f-" + ctx.key, value: show(v), placeholder: withTime ? (es ? "dd/mm/aaaa hh:mm" : "dd/mm/yyyy hh:mm") : es ? "dd/mm/aaaa" : "dd/mm/yyyy", disabled: P(n, "disabled", ctx, false), "aria-label": P(n, "label", ctx), onchange: (e) => save(parse(e.target.value)) });
    const nat = h("input", { type: withTime ? "datetime-local" : "date", tabindex: "-1", "aria-hidden": "true", value: v || "", style: { position: "absolute", right: "0", bottom: "0", width: "1px", height: "1px", opacity: "0", pointerEvents: "none" }, onchange: (e) => save(e.target.value || null) });
    const btn = h("button", { type: "button", class: "ic-r", "aria-label": es ? "Abrir calendario" : "Open calendar", style: { pointerEvents: "auto", border: "0", background: "none", cursor: "pointer", padding: "4px", right: "4px" }, onclick: () => { try { nat.showPicker(); } catch (e) { nat.focus(); } } }, icon("calendar"));
    return field(n, ctx, h("div", { class: "inp-wrap" }, txt, btn, nat), { getValue: () => getVal(n, ctx) });
  }
  R["a!dateField"] = (n, ctx) => dateInput(n, ctx, false);
  R["a!dateTimeField"] = (n, ctx) => dateInput(n, ctx, true);

  function choices(n, ctx) {
    let labels = P(n, "choiceLabels", ctx, []); let values = P(n, "choiceValues", ctx);
    if (typeof n.choiceLabels === "string" && !Array.isArray(labels)) labels = arr(labels);
    if (n.$options) { const o = typeof n.$options === "string" ? rowsOf(n.$options) : n.$options; labels = o.map((x) => (typeof x === "object" ? x.label : x)); values = o.map((x) => (typeof x === "object" ? x.value : x)); }
    labels = arr(labels); values = values === undefined ? labels.slice() : arr(values);
    if (/ByIndex$/.test(n.type)) values = labels.map((x, i) => i + 1);
    return labels.map((l, i) => ({ label: l, value: values[i] }));
  }
  function choiceSingle(n, ctx) {
    const opts = choices(n, ctx);
    const v = getVal(n, ctx);
    if (P(n, "readOnly", ctx)) return field(n, ctx, readOnlyVal((opts.find((o) => String(o.value) === String(v)) || {}).label));
    const empty = isEmpty(v) || !opts.some((o) => String(o.value) === String(v));
    const sel = h("select", { class: "inp" + (empty ? " ph" : ""), id: "f-" + ctx.key, disabled: P(n, "disabled", ctx, false), "aria-label": P(n, "label", ctx), onchange: (e) => { const o = opts[e.target.selectedIndex - 1]; saveInto(n, o ? o.value : null, ctx); schedule(); } },
      h("option", { value: "" }, P(n, "placeholder", ctx) || (n.placeholder === undefined ? T.select : "")),
      opts.map((o) => h("option", { value: String(o.value), selected: String(o.value) === String(v) }, o.label)));
    return field(n, ctx, h("div", { class: "inp-wrap" }, sel, icon("angle-down", "ic-r")), { getValue: () => getVal(n, ctx) });
  }
  R["a!dropdownField"] = choiceSingle; R["a!dropdownFieldByIndex"] = choiceSingle;
  function choiceMulti(n, ctx) {
    const opts = choices(n, ctx);
    const v = arr(getVal(n, ctx));
    const has = (x) => v.map(String).includes(String(x));
    if (P(n, "readOnly", ctx)) return field(n, ctx, readOnlyVal(opts.filter((o) => has(o.value)).map((o) => o.label)));
    const box = h("div", { class: "inp multi" });
    opts.filter((o) => has(o.value)).forEach((o) => box.appendChild(h("span", { class: "token" }, o.label, h("button", { class: "x", type: "button", "aria-label": "Quitar", onclick: () => { saveInto(n, v.filter((x) => String(x) !== String(o.value)), ctx); schedule(); } }, "×"))));
    const sel = h("select", { class: "inp", style: { border: 0, minHeight: "26px", flex: 1, padding: "0 4px" }, "aria-label": P(n, "label", ctx), onchange: (e) => { const o = opts.find((x) => String(x.value) === e.target.value); if (o) saveInto(n, v.concat([o.value]), ctx); schedule(); } },
      h("option", { value: "" }, v.length ? "" : P(n, "placeholder", ctx) || T.select), opts.filter((o) => !has(o.value)).map((o) => h("option", { value: String(o.value) }, o.label)));
    box.appendChild(sel);
    return field(n, ctx, box, { getValue: () => getVal(n, ctx) });
  }
  R["a!multipleDropdownField"] = choiceMulti; R["a!multipleDropdownFieldByIndex"] = choiceMulti;
  function checkGroup(n, ctx, multi) {
    const opts = choices(n, ctx);
    const v = getVal(n, ctx);
    const vs = arr(v).map(String);
    if (P(n, "readOnly", ctx)) return field(n, ctx, readOnlyVal(opts.filter((o) => vs.includes(String(o.value))).map((o) => o.label)));
    const g = h("div", { class: `chk-group cl-${up(P(n, "choiceLayout", ctx, "STACKED"))} cs-${up(P(n, "choiceStyle", ctx, "STANDARD"))}`, role: multi ? "group" : "radiogroup" });
    opts.forEach((o, i) => {
      const on = vs.includes(String(o.value));
      g.appendChild(h("label", { class: "chk" + (on ? " on" : "") },
        h("input", { type: multi ? "checkbox" : "radio", name: "r-" + ctx.key, id: `f-${ctx.key}-${i}`, checked: on, disabled: P(n, "disabled", ctx, false), onchange: () => {
          if (multi) saveInto(n, on ? arr(v).filter((x) => String(x) !== String(o.value)) : arr(v).concat([o.value]), ctx);
          else saveInto(n, o.value, ctx);
          schedule();
        } }), h("span", null, o.label)));
    });
    return field(n, ctx, g, { getValue: () => getVal(n, ctx) });
  }
  R["a!radioButtonField"] = (n, ctx) => checkGroup(n, ctx, false); R["a!radioButtonFieldByIndex"] = R["a!radioButtonField"];
  R["a!checkboxField"] = (n, ctx) => checkGroup(n, ctx, true); R["a!checkboxFieldByIndex"] = R["a!checkboxField"];
  R["a!booleanCheckboxField"] = (n, ctx) => {
    const v = !!getVal(n, ctx);
    return field(n, ctx, h("label", { class: "chk" }, h("input", { type: "checkbox", id: "f-" + ctx.key, checked: v, disabled: P(n, "disabled", ctx, false), onchange: () => { saveInto(n, !v, ctx); schedule(); } }), h("span", null, P(n, "choiceLabel", ctx, ""))), { getValue: () => (getVal(n, ctx) ? true : null) });
  };
  R["a!toggleField"] = (n, ctx) => {
    const v = !!getVal(n, ctx);
    return field(n, ctx, h("button", { type: "button", class: "toggle" + (v ? " on" : ""), role: "switch", "aria-checked": String(v), style: { background: "none", border: 0, padding: 0 }, disabled: P(n, "disabled", ctx, false), onclick: () => { saveInto(n, !v, ctx); schedule(); } }, h("span", { class: "sw" }), h("span", null, P(n, "choiceLabel", ctx, ""))));
  };
  function picker(n, ctx, kind) {
    const pool = n.$options ? (typeof n.$options === "string" ? rowsOf(n.$options) : n.$options) : kind === "user" ? SPEC.users || [] : kind === "record" ? rowsOf(n.recordType) : /^(doc|folder|docfolder)$/.test(kind) ? docPool(kind, n, ctx) : SPEC.groups || [];
    const icOf = (p) => (kind === "record" ? "file-text-o" : kind === "folder" || (kind === "docfolder" && p && p.folder) ? "folder" : kind === "doc" || kind === "docfolder" ? fileIcon(String(labelOf(p))) : kind === "custom" ? "search" : "users");
    const labelOf = (x) => (typeof x === "object" ? x.label || x.name || x.nombre || x.titulo || x.codigo || x.id : x);
    const idOf = (x) => (typeof x === "object" ? x.id ?? x.value ?? labelOf(x) : x);
    const v = arr(getVal(n, ctx));
    const sel = v.map((id) => pool.find((p) => String(idOf(p)) === String(id)) || id);
    if (P(n, "readOnly", ctx)) return field(n, ctx, readOnlyVal(sel.map(labelOf)));
    const max = P(n, "maxSelections", ctx);
    const box = h("div", { class: "inp multi", style: { position: "relative" } });
    sel.forEach((s) => box.appendChild(h("span", { class: "token" }, kind === "user" ? h("span", { class: "av" }, FILTERS.initials(labelOf(s))) : /doc|folder/.test(kind) ? icon(icOf(s)) : null, labelOf(s), h("button", { class: "x", type: "button", "aria-label": "Quitar", onclick: () => { saveInto(n, v.filter((x) => String(x) !== String(idOf(s))), ctx); schedule(); } }, "×"))));
    if (!max || v.length < max) {
      const inp = h("input", { id: "f-" + ctx.key, placeholder: v.length ? "" : P(n, "placeholder", ctx) || "", "aria-label": P(n, "label", ctx) });
      const pop = h("div", { class: "pop", hidden: true, style: { top: "100%", left: 0 } });
      const fill = () => {
        const q = inp.value.toLowerCase();
        pop.innerHTML = "";
        pool.filter((p) => !v.map(String).includes(String(idOf(p))) && String(labelOf(p)).toLowerCase().includes(q)).slice(0, 8)
          .forEach((p) => pop.appendChild(h("button", { type: "button", onmousedown: (e) => { e.preventDefault(); saveInto(n, max === 1 ? [idOf(p)] : v.concat([idOf(p)]), ctx); schedule(); } }, kind === "user" ? h("span", { class: "token", style: { padding: "0" } }, h("span", { class: "av", style: { margin: 0 } }, FILTERS.initials(labelOf(p)))) : icon(icOf(p)), labelOf(p))));
        pop.hidden = !pop.childNodes.length;
      };
      inp.addEventListener("input", fill); inp.addEventListener("focus", fill); inp.addEventListener("blur", () => setTimeout(() => (pop.hidden = true), 150));
      box.appendChild(inp); box.appendChild(pop);
    }
    return field(n, ctx, box, { getValue: () => getVal(n, ctx) });
  }
  R["a!pickerFieldUsers"] = (n, ctx) => picker(n, ctx, "user");
  R["a!pickerFieldGroups"] = (n, ctx) => picker(n, ctx, "group");
  R["a!pickerFieldUsersAndGroups"] = (n, ctx) => picker(n, ctx, "user");
  R["a!pickerFieldRecords"] = (n, ctx) => picker(n, ctx, "record");
  R["a!pickerFieldCustom"] = (n, ctx) => picker(n, ctx, "custom");
  R["a!pickerFieldDocuments"] = (n, ctx) => picker(n, ctx, "doc");
  R["a!pickerFieldFolders"] = (n, ctx) => picker(n, ctx, "folder");
  R["a!fileUploadField"] = (n, ctx) => {
    const v = arr(getVal(n, ctx));
    const files = v.map((f) => (typeof f === "object" ? f : { name: f }));
    const list = h("div", { class: "files" }, files.map((f, i) => h("div", { class: "file" }, icon(/\.pdf$/i.test(f.name) ? "file-pdf-o" : /\.xlsx?$/i.test(f.name) ? "file-excel-o" : "file-o"), f.name, h("span", { class: "sz" }, f.size || ""),
      P(n, "readOnly", ctx) ? null : h("button", { class: "x", type: "button", style: { border: 0, background: "none", cursor: "pointer" }, "aria-label": "Quitar", onclick: () => { saveInto(n, v.filter((x, j) => j !== i), ctx); schedule(); } }, "×"))));
    if (P(n, "readOnly", ctx)) return field(n, ctx, files.length ? list : readOnlyVal(null));
    const inp = h("input", { type: "file", hidden: true, multiple: (P(n, "maxSelections", ctx) || 2) > 1, onchange: (e) => { const nf = Array.from(e.target.files).map((f) => ({ name: f.name, size: Math.max(1, Math.round(f.size / 1024)) + " KB" })); saveInto(n, v.concat(nf), ctx); schedule(); } });
    const disp = up(P(n, "buttonDisplay", ctx, "LABEL_AND_ICON"));
    const exp = up(P(n, "dropZoneStyle", ctx, "COMPACT")) === "EXPANDED";
    const btn = h("button", { type: "button", class: uploadBtnCls(n, ctx), style: uploadBtnStyle(n, ctx), "aria-label": T.upload, onclick: () => inp.click() }, disp !== "LABEL" ? icon("upload") : null, disp !== "ICON" ? T.upload : null);
    const box = h("div", { class: "upload" + (exp ? " exp" : "") + (P(n, "showBorder", ctx, true) ? "" : " nob") }, exp ? h("span", { class: "upi", "aria-hidden": "true" }, icon("cloud-upload")) : null, btn, h("span", { class: "instr" }, T.drop), inp, files.length ? list : null);
    box.addEventListener("dragover", (e) => e.preventDefault());
    box.addEventListener("drop", (e) => { e.preventDefault(); const nf = Array.from(e.dataTransfer.files).map((f) => ({ name: f.name, size: Math.max(1, Math.round(f.size / 1024)) + " KB" })); saveInto(n, v.concat(nf), ctx); schedule(); });
    return field(n, ctx, box, { getValue: () => getVal(n, ctx) });
  };
  R["a!styledTextEditorField"] = (n, ctx) => {
    const v = getVal(n, ctx);
    if (P(n, "readOnly", ctx)) return field(n, ctx, h("div", { class: "ro-val", html: v || "" }));
    const ed = h("div", { class: "ed", contenteditable: "true", id: "f-" + ctx.key, role: "textbox", "aria-multiline": "true", html: v || "", onblur: (e) => { saveInto(n, e.target.innerHTML || null, ctx); schedule(); } });
    const tb = h("div", { class: "tb" }, ["bold", "italic", "underline", "list-ul", "list-ol", "link"].map((i) => h("span", null, icon(i))));
    return field(n, ctx, h("div", { class: "rte" }, tb, ed), { getValue: () => getVal(n, ctx) });
  };
  R["a!cardChoiceField"] = (n, ctx) => {
    const data = typeof n.data === "string" ? rowsOf(n.data) : arr(n.data);
    const ct = n.cardTemplate && typeof n.cardTemplate === "object" ? n.cardTemplate : null;
    const tpl = ct ? { idField: null, icon: ct.icon, primaryText: ct.primaryText, secondaryText: ct.secondaryText, iconColor: ct.iconColor, tooltip: ct.tooltip } : n.$template || {};
    const kind = ct ? (ct.type === "a!cardTemplateTile" ? "tile" : ct.type === "a!cardTemplateBarTextStacked" ? "stacked" : "bar") : "bar";
    const v = arr(getVal(n, ctx)).map(String);
    const max = P(n, "maxSelections", ctx, 1);
    const ro = P(n, "disabled", ctx, false);
    const g = h("div", { class: `cardchoice k-${kind} sp-${up(P(n, "spacing", ctx, "STANDARD"))} al-${up(P(n, "align", ctx, "START"))}` + (P(n, "showShadow", ctx, false) ? " sh" : ""), role: max === 1 ? "radiogroup" : "group" });
    data.forEach((d) => {
      const c = { ...ctx, row: d, item: d };
      const rawId = ct ? P(ct, "id", c) : d[tpl.idField || "id"] ?? d.value;
      const id = String(rawId);
      const on = v.includes(id);
      if (ct && ct.showWhen !== undefined && !P(ct, "showWhen", c, true)) return;
      const ic = tpl.icon ? interp(tpl.icon, c) : null;
      const icCol = tpl.iconColor ? color(interp(tpl.iconColor, c), "var(--accent)") : "var(--accent)";
      const onClick = () => { if (ro) return; saveInto(n, max === 1 ? (on ? null : rawId) : on ? v.filter((x) => x !== id) : v.concat([rawId]), ctx); schedule(); };
      g.appendChild(h("button", { type: "button", class: "cc" + (on ? " on" : ""), "aria-pressed": String(on), disabled: ro, title: tpl.tooltip ? interp(tpl.tooltip, c) : null, onclick: onClick },
        ic ? h("span", { class: "ci", style: { color: icCol } }, icon(ic)) : null,
        h("span", { class: "ct" }, h("span", { class: "p" }, interp(tpl.primaryText || "{fv!item.label}", c)), tpl.secondaryText ? h("span", { class: "s" }, interp(tpl.secondaryText, c)) : null),
        kind !== "tile" ? h("span", { class: "ck", "aria-hidden": "true" }, on ? icon("check-circle") : null) : null));
    });
    return field(n, ctx, g, { getValue: () => getVal(n, ctx) });
  };
  // estilos del botón de subida y de firma: valores anteriores (PRIMARY, SECONDARY, NORMAL, STANDARD, LINK) y los de 26.8 (SOLID, OUTLINE, GHOST, LINK) con buttonColor
  function uploadBtnCls(n, ctx) {
    const bs = { PRIMARY: "SOLID", SOLID: "SOLID", GHOST: "GHOST", LINK: "LINK" }[up(P(n, "buttonStyle", ctx, "SECONDARY"))] || "OUTLINE";
    return `btn s-${bs} z-${up(P(n, "buttonSize", ctx, "SMALL"))}`;
  }
  function uploadBtnStyle(n, ctx) { const c = P(n, "buttonColor", ctx, "ACCENT"); const bc = color(c, "var(--accent)"); return { "--bc": bc, "--bfg": solidFg(hexOf(c) || bc) }; }

  /* ---- display ---- */
  function rtItem(it, ctx) {
    if (it == null) return null;
    if (typeof it === "string" || typeof it === "number") { const v = interp(String(it), ctx); return document.createTextNode(Array.isArray(v) ? v.join(", ") : String(v ?? "")); }
    if (Array.isArray(it)) return it.map((x) => rtItem(x, ctx));
    if (!visible(it, ctx)) return null;
    const t = it.type;
    if (t === "a!richTextItem") {
      const styles = arr(P(it, "style", ctx)).map(up);
      const cls = [...styles, it.size ? "z-" + up(it.size) : ""].join(" ");
      const col = color(P(it, "color", ctx));
      const inner = [].concat(arr(it.text).map((x) => rtItem(x, ctx)));
      const link = it.link;
      const sp = link ? h("a", { class: cls + " " + up(P(it, "linkStyle", ctx, "INLINE")), href: "#", style: col ? { color: col } : null, onclick: clickable(link, ctx) }, inner) : h("span", { class: cls, style: col ? { color: col } : null }, inner);
      return sp;
    }
    if (t === "a!richTextIcon") {
      const ic = h("span", { class: it.size ? "z-" + up(it.size) : "", style: { color: color(P(it, "color", ctx)) || null }, title: P(it, "caption", ctx) }, icon(P(it, "icon", ctx)));
      return it.link ? h("a", { href: "#", class: "STANDALONE", "aria-label": P(it, "altText", ctx) || P(it, "caption", ctx) || P(it, "icon", ctx), onclick: clickable(it.link, ctx) }, ic) : ic;
    }
    // elementos de lista con subnivel (a!richTextListItem.nestedList)
    const li = (x) => (x && x.type === "a!richTextListItem" && !visible(x, ctx) ? null : h("li", null, rtItem(x && x.type === "a!richTextListItem" ? x.text : x, ctx), x && x.nestedList ? rtItem(x.nestedList, ctx) : null));
    if (t === "a!richTextBulletedList") return h("ul", null, arr(it.items).map(li));
    if (t === "a!richTextNumberedList") return h("ol", null, arr(it.items).map(li));
    if (t === "a!richTextListItem") return rtItem(it.text, ctx);
    if (t === "a!richTextImage") return inlineImg(it.image, ctx);
    if (/Link$/.test(t)) return h("a", { href: "#", onclick: clickable(it, ctx) }, interp(it.label || "", ctx));
    return document.createTextNode("");
  }
  R["a!richTextDisplayField"] = (n, ctx) => {
    const al = up(P(n, "align", ctx, "LEFT"));
    const body = h("div", { class: `rt al-${al}`, style: n.preventWrapping ? { whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" } : null }, rtItem(n.value, ctx));
    return n.label ? field(n, ctx, body) : body;
  };
  R["a!headingField"] = (n, ctx) => {
    const tag = (P(n, "headingTag", ctx) || "H2").toLowerCase();
    const size = up(P(n, "size", ctx, "MEDIUM_PLUS"));
    const col = P(n, "color", ctx, "STANDARD");
    const txt = interp(n.text, ctx);
    const inner = n.link ? h("a", { href: "#", class: "lnk", onclick: clickable(n.link, ctx) }, txt) : txt;
    return h(tag, { class: `heading fs-${size} fw-${up(P(n, "fontWeight", ctx, "SEMI_BOLD"))} al-${up(P(n, "align", ctx, "START"))}`, style: { color: color(col, "inherit") } }, inner);
  };
  R["a!stampField"] = (n, ctx) => {
    const bg = P(n, "backgroundColor", ctx, "ACCENT"), fg = P(n, "contentColor", ctx);
    const bgc = color(bg, "var(--accent)");
    const st = h("span", { class: `stamp z-${up(P(n, "size", ctx, "MEDIUM"))} shape-${up(P(n, "shape", ctx, "ROUNDED"))}`, style: { "--sbg": bgc, "--sfg": fg ? color(fg) : up(bg) === "TRANSPARENT" ? "var(--accent)" : solidFg(hexOf(bg) || bgc) }, title: P(n, "tooltip", ctx), role: n.accessibilityText ? "img" : null, "aria-label": P(n, "accessibilityText", ctx) }, n.icon ? icon(P(n, "icon", ctx)) : P(n, "text", ctx));
    const al = up(P(n, "align", ctx, "CENTER"));
    const wrap = h("div", { style: { display: "flex", justifyContent: al === "CENTER" ? "center" : al === "END" ? "flex-end" : "flex-start" } }, n.link ? h("a", { href: "#", onclick: clickable(n.link, ctx) }, st) : st);
    return n.label ? field(n, ctx, wrap) : wrap;
  };
  R["a!tagField"] = (n, ctx) => {
    const tags = h("div", { class: `tags z-${up(P(n, "size", ctx, "STANDARD"))}`, style: { justifyContent: up(n.align) === "CENTER" ? "center" : up(n.align) === "END" ? "flex-end" : null } },
      arr(n.tags).filter((t) => visible(t, ctx)).map((t) => {
        const bg = P(t, "backgroundColor", ctx, "ACCENT") || "ACCENT";
        const B = up(bg);
        const bgc = B === "SECONDARY" ? "#e4e7ea" : color(bg, "var(--accent)");
        const tc = P(t, "textColor", ctx);
        const fg = tc && up(tc) !== "STANDARD" ? color(tc) : B === "SECONDARY" ? "var(--text)" : solidFg(hexOf(bg) || "#e4e7ea");
        const tagEl = h("span", { class: "tag", style: { "--tbg": bgc, "--tfg": fg }, title: P(t, "tooltip", ctx) }, P(t, "text", ctx));
        return t.link ? h("a", { href: "#", onclick: clickable(t.link, ctx), style: { textDecoration: "none" } }, tagEl) : tagEl;
      }));
    return n.label ? field(n, ctx, tags) : tags;
  };
  R["a!linkField"] = (n, ctx) => {
    const links = h("div", { class: "links", style: { justifyContent: up(n.align) === "CENTER" ? "center" : up(n.align) === "RIGHT" ? "flex-end" : null } }, arr(n.links).filter((l) => visible(l, ctx)).map((l) => h("a", { href: "#", onclick: clickable(l, ctx) }, interp(l.label || "", ctx))));
    return field(n, ctx, links);
  };
  R["a!progressBarField"] = (n, ctx) => {
    const p = Math.max(0, Math.min(100, Number(P(n, "percentage", ctx, 0)) || 0));
    const pb = h("div", { class: "pbar " + up(P(n, "style", ctx, "THIN")), style: { "--pc": color(P(n, "color", ctx, "ACCENT")) } }, h("div", { class: "trk" }, h("div", { class: "v", style: { width: p + "%" } })), P(n, "showPercentage", ctx, true) ? h("div", { class: "pct" }, p + "%") : null);
    return field(n, ctx, pb);
  };
  R["a!gaugeField"] = (n, ctx) => {
    const p = Math.max(0, Math.min(100, Number(P(n, "percentage", ctx, 0)) || 0));
    const sz = { SMALL: 96, MEDIUM: 136, LARGE: 184 }[up(P(n, "size", ctx, "MEDIUM"))] || 136;
    const gctx = Object.assign({}, ctx, { fv: Object.assign({}, ctx.fv, { percentage: p }) }); // fv!percentage en color o textos
    const colv = P(n, "color", gctx, "ACCENT");
    const col = hexOf(colv) || color(colv, "var(--accent)");
    const r = 44, c = 2 * Math.PI * r;
    const pt = n.primaryText;
    let inner;
    if (pt && typeof pt === "object" && pt.type === "a!gaugeIcon") inner = h("span", { class: "gi", style: { color: pt.color ? color(P(pt, "color", gctx)) : null }, role: "img", "aria-label": P(pt, "altText", gctx) }, icon(P(pt, "icon", gctx)));
    else if (pt && typeof pt === "object" && pt.type === "a!gaugeFraction") { const d = Number(P(pt, "denominator", gctx, 100)) || 100; inner = h("span", { class: "gp" }, `${FILTERS.num(Math.round((p * d) / 100))} ${T.of} ${FILTERS.num(d)}`); }
    else if (pt && typeof pt === "object" && pt.type === "a!gaugePercentage") inner = h("span", { class: "gp" }, FILTERS.num(Math.round(p)) + (LANG === "es" ? " %" : "%"));
    else inner = h("span", { class: "gp" }, pt == null ? FILTERS.num(Math.round(p)) + "%" : P(n, "primaryText", gctx));
    const g = h("div", { class: "gauge", style: { width: sz + "px", height: sz + "px", "--gsz": sz + "px" }, title: P(n, "tooltip", gctx), role: "img", "aria-label": P(n, "accessibilityText", gctx) || `${Math.round(p)}%` });
    g.innerHTML = `<svg width="${sz}" height="${sz}" viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="${r}" fill="none" stroke="#e3e6e8" stroke-width="7"/><circle cx="50" cy="50" r="${r}" fill="none" stroke="${col.startsWith("var") ? "currentColor" : col}" style="color:${col}" stroke-width="7" stroke-linecap="round" stroke-dasharray="${(c * p) / 100} ${c}" transform="rotate(-90 50 50)"/></svg>`;
    g.appendChild(h("div", { class: "gtxt" }, inner, n.secondaryText ? h("span", { class: "gs" }, P(n, "secondaryText", gctx)) : null));
    const al = up(P(n, "align", ctx, "CENTER"));
    return field(n, ctx, h("div", { style: { display: "flex", justifyContent: al === "START" ? "flex-start" : al === "END" ? "flex-end" : "center" } }, g));
  };
  R["a!milestoneField"] = (n, ctx) => {
    const steps = arr(P(n, "steps", ctx));
    const links = arr(n.links);
    let active = P(n, "active", ctx, null);
    active = active == null || active === "" ? 0 : Number(active);
    const allDone = active === -1;
    const ori = up(P(n, "orientation", ctx, "HORIZONTAL"));
    const st = up(P(n, "stepStyle", ctx, "LINE"));
    const ms = h("div", { class: `ms ${ori} ${st}`, style: { "--mc": color(P(n, "color", ctx, "ACCENT")) }, role: "list", "aria-label": P(n, "accessibilityText", ctx) || P(n, "label", ctx) || null },
      steps.map((s, i) => {
        const done = allDone || i + 1 < active, cur = !allDone && i + 1 === active;
        const lab = links[i] ? h("a", { href: "#", onclick: clickable(links[i], ctx) }, s) : h("span", null, s);
        return h("div", { class: "st" + (done ? " done" : cur ? " cur" : ""), role: "listitem", "aria-current": cur ? "step" : null }, h("span", { class: "dot" }, done && st !== "LINE" ? icon("check") : ""), h("span", { class: "sl" }, lab));
      }));
    return field(n, ctx, ms);
  };
  R["a!messageBanner"] = (n, ctx) => {
    const bg = up(P(n, "backgroundColor", ctx, "INFO"));
    const hl = up(P(n, "highlightColor", ctx, { INFO: "INFO", SUCCESS: "POSITIVE", WARN: "WARN", ERROR: "NEGATIVE" }[bg] || "INFO"));
    const ic = P(n, "icon", ctx, { INFO: "info-circle", SUCCESS: "check-circle", WARN: "exclamation-triangle", ERROR: "exclamation-circle" }[bg]);
    const bgMap = { INFO: "var(--bg-info)", SUCCESS: "var(--bg-positive)", WARN: "var(--bg-warn)", ERROR: "var(--bg-negative)" };
    return h("div", { class: `banner shape-${up(P(n, "shape", ctx, "SQUARED"))}` + (P(n, "showDecorativeBar", ctx, true) ? "" : " nobar"), role: "status", style: { "--mbg": String(bg).startsWith("#") ? bg : bgMap[bg] || bgMap.INFO, "--mhl": color(hl, "var(--info)") } },
      h("span", { class: "bi" }, icon(ic)), h("div", null, n.primaryText ? h("div", { class: "pt" }, rtItem(n.primaryText, ctx)) : null, n.secondaryText ? h("div", { class: "stxt" }, rtItem(n.secondaryText, ctx)) : null));
  };
  R["a!kpiField"] = (n, ctx) => {
    const tpl = up(P(n, "template", ctx, "COMPACT"));
    const fmt = (x) => (x == null ? "—" : n.$format && FILTERS[n.$format] ? FILTERS[n.$format](x) : FILTERS.num(Math.round(x * 100) / 100));
    let raw = null, val = P(n, "$value", ctx);
    if (val == null && n.data && n.primaryMeasure) { raw = measureOf(n.primaryMeasure, dataRows(n, ctx), ctx); val = fmt(raw); }
    if (val == null) val = "—";
    // medida secundaria: a!measure (con $filter) o $secondaryValue → tendencia como en Appian (AUTO = diferencia y %)
    let sec = n.$secondaryValue != null ? Number(P(n, "$secondaryValue", ctx)) : null;
    if (sec == null && n.data && n.secondaryMeasure) sec = measureOf(n.secondaryMeasure, dataRows(n, ctx), ctx);
    if (raw == null && n.$value != null) raw = parseFloat(String(P(n, "$value", ctx)).replace(/\./g, "").replace(",", "."));
    let tr = n.$trend != null ? String(P(n, "$trend", ctx)) : null, trNum = tr != null ? parseFloat(tr.replace(",", ".")) : null;
    const tmode = up(P(n, "trend", ctx, "AUTO"));
    if (tr == null && sec != null && raw != null && !isNaN(raw) && tmode !== "NONE") {
      const diff = raw - sec, pct = sec ? (diff / Math.abs(sec)) * 100 : null;
      const sgn = (x) => (x > 0 ? "+" : x < 0 ? "−" : "");
      const fmtT = n.$format === "eur" ? FILTERS.eur : FILTERS.num;
      const d = sgn(diff) + fmtT(Math.abs(Math.round(diff * 100) / 100)), pc = pct == null ? "" : sgn(pct) + FILTERS.num(Math.abs(Math.round(pct * 10) / 10)) + " %";
      tr = tmode === "DIFFERENCE" ? d : tmode === "PERCENTAGE" ? pc : `${d}${pc ? " (" + pc + ")" : ""}`;
      trNum = diff;
    }
    const trCol = up(P(n, "trendColor", ctx, "AUTO"));
    const tcol = trNum === 0 ? "var(--text-2)" : trCol === "AUTO" ? (trNum < 0 ? "var(--negative)" : "var(--positive)") : trCol === "REVERSE" ? (trNum < 0 ? "var(--positive)" : "var(--negative)") : color(trCol, "var(--text-2)");
    const trIcon = n.trendIcon ? P(n, "trendIcon", ctx) : trNum > 0 ? "arrow-up" : trNum < 0 ? "arrow-down" : "minus";
    const icCol = color(P(n, "iconColor", ctx, "STANDARD"), "inherit");
    const stampi = up(P(n, "iconStyle", ctx, "ICON")) === "STAMP";
    const icEl = n.icon ? h("span", { class: "ki" + (stampi ? " stampi" : ""), style: { color: icCol === "inherit" ? null : icCol } }, icon(P(n, "icon", ctx))) : null;
    const pst = up(P(n, "primaryTextStyle", ctx, "PLAIN"));
    const kt = n.primaryText ? h("div", { class: "kt" + (pst === "STRONG" ? " strong" : pst === "EMPHASIS" ? " em" : ""), style: { color: n.primaryTextColor ? color(P(n, "primaryTextColor", ctx)) : null } }, P(n, "primaryText", ctx)) : null;
    const kv = h("div", { class: "kvrow" }, h("span", { class: "kv", style: { color: n.primaryMeasureColor ? color(P(n, "primaryMeasureColor", ctx)) : null } }, val));
    const trEl = tr != null ? h("span", { class: "tr", style: { color: tcol } }, icon(trIcon), tr) : null;
    const ks = n.secondaryText ? h("span", { class: "ks", style: { color: n.secondaryTextColor ? color(P(n, "secondaryTextColor", ctx)) : null } }, P(n, "secondaryText", ctx)) : null;
    const foot = trEl || ks ? h("div", { class: "kfoot" }, trEl, ks) : null;
    let body;
    if (tpl === "COMPACT") body = [h("div", { class: "khead" }, icEl, kt), kv, foot];
    else body = [icEl, h("div", { class: "kbody" }, kt, kv, foot)];
    return h("div", { class: `kpi t-${tpl} z-${up(P(n, "size", ctx, "STANDARD"))} al-${up(P(n, "align", ctx, "START"))}`, title: P(n, "tooltip", ctx) }, body);
  };
  R["a!horizontalLine"] = (n, ctx) => h("hr", { class: `hr w-${up(P(n, "weight", ctx, "THIN"))} s-${up(P(n, "style", ctx, "SOLID"))} c-${up(P(n, "color", ctx, "SECONDARY"))}` });
  R["a!imageField"] = (n, ctx) => {
    const sz = { ICON: 20, ICON_PLUS: 28, TINY: 40, EXTRA_SMALL: 60, SMALL: 80, SMALL_PLUS: 110, MEDIUM: 150, MEDIUM_PLUS: 200, LARGE: 260, LARGE_PLUS: 340, EXTRA_LARGE: 440, FIT: null, GALLERY: 120 }[up(P(n, "size", ctx, "MEDIUM"))];
    const avatar = up(n.style) === "AVATAR";
    const imgs = arr(n.images).map((im) => {
      const src = im && im.type === "a!webImage" ? interp(im.source, ctx) : null;
      const alt = im && (im.altText || im.caption) ? interp(im.altText || im.caption, ctx) : "Imagen";
      if (src && src.startsWith("data:")) return h("img", { src, alt, style: { width: sz ? sz + "px" : "100%", borderRadius: up(n.style) === "AVATAR" ? "50%" : "4px" } });
      if (im && im.type === "a!userImage") {
        // sin foto, Appian pinta las iniciales sobre un color fijo por usuario (el mismo en toda la aplicación)
        const px = sz || 40; const u = String(interp(im.user || "", ctx) || ""), nm = (usrOf(u) || {}).name || u;
        const bgv = P(im, "backgroundColor", ctx, null), bgh = bgv ? hexOf(bgv) || "#527500" : avatarBg(nm), bgc = bgv ? color(bgv, "var(--accent)") : bgh;
        return h("span", { class: "stamp", role: "img", "aria-label": nm, style: { "--sbg": bgc, "--sfg": solidFg(bgh), width: px + "px", height: px + "px", fontSize: Math.round(px * 0.4) + "px", borderRadius: "50%" }, title: nm }, FILTERS.initials(nm)); }
      return h("div", { class: "imgph img-doc", role: "img", "aria-label": alt, style: { width: sz ? sz + "px" : "100%", height: sz ? sz * 0.7 + "px" : "160px", borderRadius: up(n.style) === "AVATAR" ? "50%" : null } }, h("span", { class: "img-i" }, icon(im && im.type === "a!documentImage" ? "file-image-o" : "picture-o")), h("span", null, alt));
    });
    const al = up(P(n, "align", ctx, "START"));
    return field(n, ctx, h("div", { style: { display: "flex", gap: "10px", flexWrap: "wrap", justifyContent: al === "CENTER" ? "center" : al === "END" ? "flex-end" : null } }, imgs));
  };
  // Visor de documentos: barra (nombre, página actual, zoom, descarga), página inicial (initialPageDisplay) y resaltado de la primera
  // coincidencia de highlightedText. Solo de prototipo: $fileName, $pages (nº de páginas; 4 por defecto) y $content (texto de cada
  // página: un texto o una lista de párrafos por página). Sin documento (document vacío) muestra «Documento no disponible», como Appian.
  R["a!documentViewerField"] = (n, ctx) => {
    const doc = P(n, "document", ctx);
    const hgt = { SHORT: 320, MEDIUM: 520, TALL: 760 }[up(P(n, "height", ctx, "MEDIUM"))] || 520;
    if (n.document !== undefined && isEmpty(doc)) return field(n, ctx, h("div", { class: "docv2 na", style: { height: Math.min(hgt, 220) + "px" } }, icon("file-o"), LANG === "es" ? "Documento no disponible" : "Document not available"));
    const content = arr(n.$content).map((pg) => arr(pg).map((x) => interp(String(x), ctx)));
    const pages = Math.max(1, Number(P(n, "$pages", ctx, content.length || 4)) || 4);
    const init = Math.min(pages, Math.max(1, Number(P(n, "initialPageDisplay", ctx, 1)) || 1));
    const k = "docv:" + ctx.key;
    if (!UI[k] || UI[k].init !== init) UI[k] = { init, page: init, zoom: 100 }; // al cambiar initialPageDisplay (p. ej. al pulsar una cita) vuelve a esa página
    const st = UI[k];
    const name = interp(n.$fileName || "", ctx) || (typeof doc === "string" && /\.\w{2,4}$/.test(doc) ? doc : "Documento.pdf");
    const hl = String(P(n, "highlightedText", ctx) || "").trim();
    // la primera coincidencia del documento (sin distinguir mayúsculas); sin $content, el texto resaltado aparece en la página inicial
    const low = hl.toLowerCase();
    let hlPage = null;
    if (hl) { const i = content.findIndex((pg) => pg.some((t) => t.toLowerCase().includes(low))); hlPage = i >= 0 ? i + 1 : content.length ? null : init; }
    const mark = (t, on) => { if (!on) return t; const i = t.toLowerCase().indexOf(low); return i < 0 ? t : [t.slice(0, i), h("mark", null, t.slice(i, i + hl.length)), t.slice(i + hl.length)]; };
    const pg = st.page;
    let paras = content[pg - 1];
    let first = true;
    const body = paras && paras.length
      ? paras.map((t) => { const on = hlPage === pg && first && t.toLowerCase().includes(low); if (on) first = false; return h("p", null, mark(t, on)); })
      : [Array.from({ length: 5 }, (x, i) => h("i", { style: { width: 58 + ((i * 37 + pg * 11) % 40) + "%" } })),
         hlPage === pg ? h("p", { class: "hlp" }, "… ", h("mark", null, hl), " …") : null,
         Array.from({ length: 8 }, (x, i) => h("i", { style: { width: 50 + ((i * 29 + pg * 7) % 48) + "%" } }))];
    const nav = (d) => () => { if (inspector) return; st.page = Math.min(pages, Math.max(1, st.page + d)); rerender(); };
    const zoom = (d) => () => { if (inspector) return; st.zoom = Math.min(200, Math.max(50, st.zoom + d)); rerender(); };
    const ib = (ic, label, fn, dis) => h("button", { type: "button", class: "ib", title: label, "aria-label": label, disabled: dis, onclick: fn }, icon(ic));
    const es = LANG === "es";
    const viewer = h("div", { class: "docv2" + (P(n, "disabled", ctx, false) ? " dis" : ""), style: { height: hgt + "px" }, role: "document", "aria-label": P(n, "accessibilityText", ctx) || P(n, "altText", ctx) || name },
      h("div", { class: "dv-tb" }, icon(/\.docx?$/i.test(name) ? "file-word-o" : /\.xlsx?$/i.test(name) ? "file-excel-o" : "file-pdf-o"), h("span", { class: "dv-n", title: name }, name), h("span", { class: "sp" }),
        ib("angle-left", es ? "Página anterior" : "Previous page", nav(-1), pg <= 1), h("span", { class: "dv-p" }, `${pg} / ${pages}`), ib("angle-right", es ? "Página siguiente" : "Next page", nav(1), pg >= pages),
        h("span", { class: "dv-sep" }), ib("search-minus", es ? "Reducir" : "Zoom out", zoom(-25), st.zoom <= 50), h("span", { class: "dv-p" }, st.zoom + " %"), ib("search-plus", es ? "Ampliar" : "Zoom in", zoom(25), st.zoom >= 200),
        h("span", { class: "dv-sep" }), ib("download", es ? "Descargar" : "Download")),
      h("div", { class: "dv-body" }, h("div", { class: "page", style: { width: `min(${Math.round(5.2 * st.zoom)}px, calc(100% - 8px))` } },
        pg === 1 ? h("div", { class: "dv-title" }, name.replace(/\.\w{2,4}$/, "")) : null, body, h("div", { class: "dv-foot" }, `${es ? "Página" : "Page"} ${pg}`))));
    return field(n, ctx, viewer);
  };
  R["a!timeDisplayField"] = (n, ctx) => field(n, ctx, readOnlyVal(P(n, "value", ctx)));
  R["a!eventHistoryListField"] = (n, ctx) => {
    let evs = typeof n.$events === "string" ? rowsOf(n.$events) : arr(n.$events);
    if (n.$filter) evs = evs.filter((r) => truthy(evalExpr(n.$filter, Object.assign({}, ctx, { row: r }))));
    const es = up(P(n, "eventStyle", ctx, "FULL_LIST"));
    if (es === "PREVIEW_LIST") evs = evs.slice(0, Number(P(n, "previewListPageSize", ctx, 3)) || 3);
    const cardCmt = up(P(n, "commentLayout", ctx, "LIST")) === "CARD";
    const cmtBg = n.commentCardColor ? color(P(n, "commentCardColor", ctx)) : null;
    const showUser = up(P(n, "displayUser", ctx, "NAME_AND_AVATAR"));
    const av = (e) => (showUser === "NONE" ? null : h("span", { class: "av" }, FILTERS.initials(e.user)));
    const meta = (e) => h("div", { class: "meta" }, [showUser !== "NONE" ? e.user : null, FILTERS.datetime(e.timestamp)].filter(Boolean).join(" · "));
    let list;
    if (!evs.length) list = h("div", { class: "gempty" }, P(n, "emptyListMessage", ctx, T.empty));
    else if (es === "TIMELINE") {
      list = h("ol", { class: "events timeline" }, evs.map((e) => h("li", { class: "tl" }, h("span", { class: "tl-dot", style: e.color ? { "--dc": color(e.color) } : null }, e.icon ? icon(e.icon) : null),
        h("div", { class: "tl-b" }, h("div", { class: "ttl" }, e.event), meta(e), e.details ? h("div", { class: "det" }, e.details) : null, e.comment ? h("div", { class: "cmt" + (cardCmt ? " card-c" : ""), style: cmtBg ? { background: cmtBg } : null }, e.comment) : null))));
    } else {
      const withC = es === "LIST_WITH_COMMENTS";
      list = h("div", { class: "events" + (withC ? " with-c" : "") }, evs.map((e) => h("div", { class: "ev" }, av(e), h("div", { style: { flex: 1, minWidth: 0 } }, h("div", { class: "ttl" }, e.event), meta(e), e.details ? h("div", { class: "det" }, e.details) : null,
        e.comment ? h("div", { class: "cmt" + (cardCmt || withC ? " card-c" : ""), style: cmtBg ? { background: cmtBg } : null }, e.comment) : null))));
    }
    return field(n, ctx, list);
  };
  /* ---- navegadores, organigrama y multimedia: catálogo completo de Appian 26.9 ----
     Datos del prototipo (validate.py no los comprueba; el resto de parámetros son los de Appian):
       app.json users     [{ id, name, title, supervisor, groups: [id de grupo] }]  → navegadores de usuarios y grupos, organigrama
       app.json groups    [{ id, name, parent, description }]  (parent = id del grupo padre)
       app.json documents [{ id, name, folder, type: "folder" | "document", size, modified }]  → navegadores y selectores de documentos y carpetas
       $tree  (cualquier navegador) jerarquía propia: [{ id, label, description, details, icon, user, type, count, children: [...] }]
     Como en Appian, la ruta se guarda en pathValue/pathSaveInto (documentos y carpetas: navigationValue/navigationSaveInto)
     y la selección en selectionValue/selectionSaveInto; sin variable, el prototipo la recuerda mientras se está en la pantalla. */
  const same = (a, b) => a != null && b != null && String(a).toLowerCase() === String(b).toLowerCase();
  const KEY = (v) => (v != null && typeof v === "object" ? JSON.stringify(v) : String(v));
  const grpOf = (id) => arr(SPEC.groups).find((g) => same(g.id, id) || same(g.name, id));
  const usrOf = (id) => arr(SPEC.users).find((u) => same(u.id, id) || same(u.name, id));
  const isFolder = (d) => /^folder$/i.test((d && d.type) || "");
  const fileIcon = (name) => (/\.pdf$/i.test(name) ? "file-pdf-o" : /\.docx?$/i.test(name) ? "file-word-o" : /\.(xlsx?|csv)$/i.test(name) ? "file-excel-o" : /\.(png|jpe?g|gif|svg)$/i.test(name) ? "file-image-o" : "file-o");
  const AVATAR_BG = ["#1A2732", "#527500", "#525C65", "#3D6B8C"];
  const avatarBg = (name) => AVATAR_BG[Array.from(String(name || "")).reduce((a, c) => a + c.charCodeAt(0), 0) % AVATAR_BG.length];
  function bind(n, ctx, valKey, saveKey, dflt) {
    const r = refOf(n, valKey, ctx);
    const uk = "bind:" + ctx.key + ":" + valKey;
    return {
      get: () => (r ? readRef(r) : UI[uk] !== undefined ? UI[uk] : P(n, valKey, ctx, dflt)),
      set: (v) => { if (n[saveKey]) saveInto(n, v, ctx, saveKey); else if (r) writeRef(r, v); if (!r) UI[uk] = v; schedule(); },
    };
  }
  function listOf(v, ctx) {
    if (typeof v === "string" && /^(data|recordType|local|ri|pv)!/.test(v)) return rowsOf(v);
    return arr(typeof v === "string" ? interp(v, ctx) : v);
  }
  // usuarios y grupos: miembros directos (grupos y después usuarios) de un grupo
  function ugKids(gid, opt) {
    const g = grpOf(gid), ids = g ? [g.id, g.name] : [gid];
    const inG = (x) => ids.some((i) => same(x, i));
    const es = LANG === "es";
    const groups = arr(SPEC.groups).filter((x) => (gid == null ? x.parent == null : inG(x.parent))).map((x) => {
      const ng = arr(SPEC.groups).filter((y) => same(y.parent, x.id)).length, nu = arr(SPEC.users).filter((u) => arr(u.groups).some((y) => same(y, x.id) || same(y, x.name))).length;
      return { val: x.id, label: x.name, desc: x.description, kind: "group", icon: "users", drill: ng + (opt.hideUsers ? 0 : nu) > 0, select: !!opt.groups, kids: () => ugKids(x.id, opt),
        tip: es ? `Grupos miembro: ${ng} · Usuarios miembro: ${nu}` : `Member group count: ${ng}, Member user count: ${nu}` };
    });
    const users = opt.hideUsers || gid == null ? [] : arr(SPEC.users).filter((u) => arr(u.groups).some(inG))
      .map((u) => ({ val: u.id, label: u.name, desc: u.title, kind: "user", user: u.name, drill: false, select: !!opt.users }));
    return groups.concat(users);
  }
  // documentos y carpetas: contenido de una carpeta (carpetas primero)
  function docKids(fid, opt) {
    const f = arr(SPEC.documents).find((d) => same(d.id, fid) || same(d.name, fid)), ids = f ? [f.id, f.name] : [fid];
    return arr(SPEC.documents).filter((d) => (fid == null ? d.folder == null : ids.some((i) => same(d.folder, i))) && (!opt.onlyFolders || isFolder(d)))
      .sort((a, b) => Number(isFolder(b)) - Number(isFolder(a)))
      .map((d) => (isFolder(d)
        ? { val: d.id ?? d.name, label: d.name, kind: "folder", icon: "folder", drill: true, select: !!opt.folders, kids: () => docKids(d.id ?? d.name, opt) }
        : { val: d.id ?? d.name, label: d.name, kind: "doc", icon: fileIcon(d.name), desc: [d.size, FILTERS.date(d.modified)].filter(Boolean).join(" · "), drill: false, select: !!opt.docs }));
  }
  // $tree del prototipo
  function treeNodes(list, ctx, opt) {
    return arr(list).map((x) => {
      if (x == null || typeof x !== "object") x = { label: x };
      const kids = x.children || x.nodes;
      const kind = /^(user|group|folder|document|doc)$/i.test(x.type || "") ? up(x.type).toLowerCase().replace("document", "doc") : x.user ? "user" : "node";
      const label = interp(String(x.label ?? x.name ?? x.id ?? ""), ctx);
      const dsel = kind === "user" ? opt.users : kind === "group" ? opt.groups : kind === "folder" ? opt.folders : kind === "doc" ? opt.docs : opt.nodes;
      return { val: x.id ?? label, label, desc: x.description != null ? interp(String(x.description), ctx) : null, details: x.details != null ? interp(String(x.details), ctx) : null,
        kind, icon: x.icon || (kind === "group" ? "users" : kind === "folder" ? "folder" : kind === "doc" ? fileIcon(label) : null), user: kind === "user" ? interp(String(x.user === true || !x.user ? label : x.user), ctx) : null,
        count: x.count, drill: x.drillable ?? x.isDrillable ?? !!arr(kids).length, select: x.selectable ?? x.isSelectable ?? (dsel === undefined ? true : !!dsel), kids: kids ? () => treeNodes(kids, ctx, opt) : null };
    });
  }
  // a!hierarchyBrowserField*: valores reales de SAIL con nodeConfigs (fv!nodeValue) y nextColumnValues / nextLevelValues
  function sailNodes(values, n, ctx, nextKey, countKey) {
    const cfg = n.nodeConfigs && typeof n.nodeConfigs === "object" ? n.nodeConfigs : {};
    return arr(values).map((v) => {
      const c = Object.assign({}, ctx, { fv: Object.assign({}, ctx.fv, { nodeValue: v }) });
      if (cfg.showWhen !== undefined && !P(cfg, "showWhen", c, true)) return null;
      const dflt = v != null && typeof v === "object" ? v.label ?? v.name ?? v.nombre ?? v.titulo ?? v.id : v;
      const im = cfg.image && typeof cfg.image === "object" ? cfg.image : null;
      const user = im && im.type === "a!userImage" ? String(interp(im.user || "", c) || "") : null;
      const src = im && im.type === "a!webImage" ? String(interp(im.source || "", c) || "") : null;
      const kids = n[nextKey] !== undefined ? () => sailNodes(listOf(P(n, nextKey, c), c), n, ctx, nextKey, countKey) : null;
      return { val: v, label: String(P(cfg, "label", c) ?? dflt ?? ""), desc: P(cfg, "description", c), details: P(cfg, "details", c), kind: user ? "user" : "node",
        user: user ? (usrOf(user) || {}).name || user : null, src: src && src.startsWith("data:") ? src : null, icon: cfg.$icon ? P(cfg, "$icon", c) : im && im.type === "a!documentImage" ? "file-image-o" : null,
        count: P(cfg, countKey, c), drill: P(cfg, "isDrillable", c, true) && !!kids, select: P(cfg, "isSelectable", c, true), kids };
    }).filter(Boolean);
  }
  function findPath(nodes, target, depth) {
    if (target == null || (depth || 0) > 8) return null;
    for (const nd of nodes) {
      if (KEY(nd.val) === KEY(target)) return [nd.val];
      if (nd.drill && nd.kids) { const p = findPath(nd.kids(), target, (depth || 0) + 1); if (p) return [nd.val].concat(p); }
    }
    return null;
  }
  function nodeImg(nd, px) {
    if (nd.src) return h("img", { class: "nv-img", src: nd.src, alt: "", style: { width: px + "px", height: px + "px" } });
    if (nd.user) return h("span", { class: "nv-av", "aria-hidden": "true", style: { width: px + "px", height: px + "px", fontSize: Math.round(px * 0.4) + "px", background: avatarBg(nd.user) } }, FILTERS.initials(nd.user));
    return h("span", { class: "nv-ic k-" + (nd.kind || "node"), "aria-hidden": "true", style: { fontSize: Math.round(px * 0.8) + "px" } }, icon(nd.icon || (nd.drill ? "sitemap" : "circle")));
  }
  const NAV_H = { SHORT: 200, MEDIUM: 320, TALL: 480 };
  /* Navegador en columnas (usuarios, grupos, documentos, carpetas y a!hierarchyBrowserFieldColumns): cada pulsación en un nodo que se
     puede desplegar abre la columna siguiente; el nodo seleccionado se resalta con el color de acento y una marca. */
  function colBrowser(n, ctx, first, o) {
    const es = LANG === "es";
    const ro = P(n, "readOnly", ctx, false);
    const ss = bind(n, ctx, "selectionValue", "selectionSaveInto", null);
    const sel = ss.get();
    let path, setPath;
    if (o.nav) { // documentos y carpetas: navigationValue es la carpeta abierta (la ruta se deduce)
      const nb = bind(n, ctx, "navigationValue", "navigationSaveInto", null);
      path = findPath(first, nb.get()) || [];
      setPath = (p) => nb.set(p.length ? p[p.length - 1] : null);
    } else { const pb = bind(n, ctx, "pathValue", "pathSaveInto", []); path = arr(pb.get()); setPath = (p) => pb.set(p); }
    const cols = [first], onPath = [];
    for (const p of path) {
      const nd = cols[cols.length - 1].find((x) => KEY(x.val) === KEY(p));
      if (!nd) break;
      onPath.push(nd);
      if (nd.drill && nd.kids) cols.push(nd.kids()); else break;
    }
    const act = (ci, nd) => () => {
      if (inspector) return;
      const canSel = nd.select && !ro;
      if (!nd.drill && !canSel) return;
      const pre = onPath.slice(0, ci).map((x) => x.val);
      if (nd.drill || !o.nav) setPath(pre.concat([nd.val]));
      else if (onPath.length > ci) setPath(pre); // documento en otra columna: la navegación vuelve a su carpeta
      if (canSel) ss.set(nd.val);
    };
    const colEls = cols.map((list, ci) => h("div", { class: "cb-col", role: "listbox", "aria-label": ci === 0 ? P(n, "label", ctx) || (es ? "Primera columna" : "First column") : onPath[ci - 1] ? onPath[ci - 1].label : null },
      list.length ? list.map((nd) => {
        const inPath = !!onPath[ci] && KEY(onPath[ci].val) === KEY(nd.val);
        const isSel = sel != null && KEY(sel) === KEY(nd.val) && (inPath || (o.nav && ci === cols.length - 1));
        const live = nd.drill || (nd.select && !ro);
        return h("button", { type: "button", role: "option", class: "cb-n" + (inPath ? " path" : "") + (isSel ? " sel" : "") + (live ? "" : " inert") + (nd.select && !nd.drill ? " leaf" : ""), "aria-selected": isSel ? "true" : "false", title: nd.tip || null, onclick: act(ci, nd) },
          nodeImg(nd, 20), h("span", { class: "cb-l" }, h("span", { class: "cb-t" }, nd.label), nd.desc ? h("span", { class: "cb-d" }, nd.desc) : null),
          isSel ? h("span", { class: "cb-i" }, icon("check")) : nd.drill ? h("span", { class: "cb-i" }, icon("angle-right")) : null);
      }) : h("div", { class: "cb-empty" }, T.empty)));
    while (colEls.length < 3) colEls.push(h("div", { class: "cb-col", "aria-hidden": "true" }));
    const box = h("div", { class: "cbr", style: { height: (NAV_H[up(P(n, "height", ctx, "MEDIUM"))] || 320) + "px" }, role: "group", "aria-label": P(n, "accessibilityText", ctx) || P(n, "label", ctx) || null }, colEls);
    box.__layout = () => { box.scrollLeft = box.scrollWidth; };
    return field(n, ctx, box);
  }
  const UG = (n, ctx, opt) => (n.$tree ? treeNodes(n.$tree, ctx, opt) : ugKids(P(n, "rootGroup", ctx), opt));
  const DOCS = (n, ctx, opt) => (n.$tree ? treeNodes(n.$tree, ctx, opt) : docKids(P(n, "rootFolder", ctx), opt));
  const PATHB = { nav: false }, NAVB = { nav: true };
  R["a!userBrowserFieldColumns"] = (n, ctx) => colBrowser(n, ctx, UG(n, ctx, { users: true, groups: false }), PATHB);
  R["a!groupBrowserFieldColumns"] = (n, ctx) => colBrowser(n, ctx, UG(n, ctx, { users: false, groups: true, hideUsers: P(n, "hideUsers", ctx, false) }), PATHB);
  R["a!userAndGroupBrowserFieldColumns"] = (n, ctx) => colBrowser(n, ctx, UG(n, ctx, { users: true, groups: true }), PATHB);
  R["a!documentBrowserFieldColumns"] = (n, ctx) => colBrowser(n, ctx, DOCS(n, ctx, { docs: true, folders: false }), NAVB);
  R["a!folderBrowserFieldColumns"] = (n, ctx) => colBrowser(n, ctx, DOCS(n, ctx, { docs: false, folders: true, onlyFolders: true }).filter((x) => x.kind !== "doc"), NAVB);
  R["a!documentAndFolderBrowserFieldColumns"] = (n, ctx) => colBrowser(n, ctx, DOCS(n, ctx, { docs: true, folders: true }), NAVB);
  R["a!hierarchyBrowserFieldColumns"] = (n, ctx) => colBrowser(n, ctx, n.$tree ? treeNodes(n.$tree, ctx, {}) : sailNodes(listOf(n.firstColumnValues, ctx), n, ctx, "nextColumnValues", "nextColumnCount"), PATHB);
  /* Árbol vertical (a!hierarchyBrowserFieldTree y a!orgChartField): una fila por nivel, conectores desde el nodo activo y
     contador de hijos bajo cada tarjeta (relleno en los nodos de la ruta). */
  function treeView(n, ctx, rows, card) {
    const wrap = h("div", { class: "hb", role: "tree", "aria-label": P(n, "accessibilityText", ctx) || P(n, "label", ctx) || null });
    rows.forEach((row, ri) => {
      const r = h("div", { class: "hb-row" + (ri ? " kids" : ""), role: "group" }, row.items.map((it) => card(it, ri, row)));
      if (ri) wrap.appendChild(h("div", { class: "hb-link", "aria-hidden": "true" }));
      wrap.appendChild(r);
    });
    // conectores: línea vertical desde el centro del nodo activo de cada fila hasta el corchete de la fila siguiente
    wrap.__layout = () => {
      const links = wrap.querySelectorAll(":scope > .hb-link");
      const rowsEl = wrap.querySelectorAll(":scope > .hb-row");
      links.forEach((ln, i) => {
        const act = rowsEl[i] && rowsEl[i].querySelector(".cur, .path");
        const nx = rowsEl[i + 1];
        if (!act || !nx) return;
        const wb = wrap.getBoundingClientRect(), ab = act.getBoundingClientRect();
        ln.style.left = ab.left - wb.left + ab.width / 2 + wrap.scrollLeft + "px";
        const kids = nx.children; if (!kids.length) return;
        // el corchete va del primer al último hijo y llega siempre hasta la vertical del nodo activo
        const nb = nx.getBoundingClientRect(), f = kids[0].getBoundingClientRect(), l = kids[kids.length - 1].getBoundingClientRect();
        const pc = ab.left + ab.width / 2 - nb.left;
        const left = Math.min(f.left - nb.left + f.width / 2, pc), right = Math.max(l.left - nb.left + l.width / 2, pc);
        nx.style.setProperty("--bl", left + "px");
        nx.style.setProperty("--br", nb.width - right + "px");
      });
    };
    return field(n, ctx, wrap);
  }
  function hbCard(nd, opts) {
    const cnt = nd.count != null ? nd.count : nd.drill && nd.kids ? nd.kids().length : null;
    return h("button", { type: "button", role: "treeitem", class: "hb-c" + (opts.path ? " path" : "") + (opts.cur ? " cur" : ""), "aria-selected": opts.cur ? "true" : "false", onclick: opts.onclick },
      nodeImg(nd, opts.img || 40), h("span", { class: "hb-t" + (opts.link ? " lnkc" : "") }, nd.label), nd.desc ? h("span", { class: "hb-d" }, nd.desc) : null, nd.details ? h("span", { class: "hb-x" }, nd.details) : null,
      cnt ? h("span", { class: "hb-k" + (opts.path || opts.cur ? " on" : "") }, String(cnt)) : null);
  }
  R["a!hierarchyBrowserFieldTree"] = (n, ctx) => {
    const pb = bind(n, ctx, "pathValue", "pathSaveInto", []);
    let path = arr(pb.get());
    const tree = n.$tree ? treeNodes(n.$tree, ctx, {}) : null;
    let rootNd = tree ? (path.length ? tree.find((x) => KEY(x.val) === KEY(path[0])) : null) || tree[0] : path.length ? sailNodes([path[0]], n, ctx, "nextLevelValues", "nextLevelCount")[0] : null;
    if (!rootNd) return field(n, ctx, h("div", { class: "gempty" }, T.empty));
    if (!path.length || KEY(path[0]) !== KEY(rootNd.val)) path = [rootNd.val];
    const rows = [{ items: [rootNd], active: rootNd }];
    for (let i = 1; ; i++) {
      const par = rows[rows.length - 1].active;
      if (!par || !par.drill || !par.kids) break;
      const kids = par.kids(); if (!kids.length) break;
      const a = i < path.length ? kids.find((k) => KEY(k.val) === KEY(path[i])) || null : null;
      rows.push({ items: kids, active: a });
      if (!a) break;
    }
    const last = rows.reduce((acc, r) => (r.active ? r.active : acc), null);
    return treeView(n, ctx, rows, (nd, ri, row) => hbCard(nd, { path: row.active === nd && nd !== last, cur: nd === last,
      onclick: () => { if (inspector) return; pb.set(rows.slice(0, ri).map((r) => r.active.val).concat([nd.val])); } }));
  };
  R["a!orgChartField"] = (n, ctx) => {
    const vb = bind(n, ctx, "value", "saveInto", null);
    const users = arr(SPEC.users);
    const focus = usrOf(vb.get()) || users.find((u) => !u.supervisor) || users[0];
    if (!focus) return field(n, ctx, h("div", { class: "gempty" }, T.empty));
    const reportsOf = (u) => users.filter((x) => x !== u && (same(x.supervisor, u.id) || same(x.supervisor, u.name)));
    const total = (u, seen) => reportsOf(u).reduce((a, x) => (seen.has(x.id) ? a : (seen.add(x.id), a + 1 + total(x, seen))), 0);
    const cnt = (u) => (P(n, "showTotalCounts", ctx, false) ? total(u, new Set([u.id])) : reportsOf(u).length);
    const supOf = (u) => (u.supervisor ? usrOf(u.supervisor) : null);
    const anc = [];
    for (let s = supOf(focus); s && !anc.includes(s) && s !== focus; s = supOf(s)) { anc.unshift(s); if (!P(n, "showAllAncestors", ctx, false)) break; }
    const asNode = (u) => ({ val: u.id, label: u.name, desc: [u.title, u.location].filter(Boolean).join(" · "), user: u.name, kind: "user", count: cnt(u) || null, drill: true });
    const rows = anc.map((a) => ({ items: [a], active: a })).concat([{ items: anc.length ? reportsOf(anc[anc.length - 1]) : [focus], active: focus }]);
    const reps = reportsOf(focus); if (reps.length) rows.push({ items: reps, active: null });
    return treeView(n, ctx, rows, (u, ri, row) => hbCard(asNode(u), { img: 48, link: true, path: row.active === u && u !== focus, cur: u === focus,
      onclick: () => { if (inspector) return; vb.set(u.id); } }));
  };
  // selector de documentos y carpetas (y el de documentos o carpetas): sugerencias de app.json documents o de $options
  function docPool(kind, n, ctx) {
    let all = arr(SPEC.documents);
    const ff = P(n, "folderFilter", ctx);
    if (ff != null && ff !== "") { const ids = new Set(); const walk = (fid) => arr(SPEC.documents).filter((d) => same(d.folder, fid)).forEach((d) => { ids.add(d); if (isFolder(d)) { walk(d.id); walk(d.name); } }); walk(ff); all = all.filter((d) => ids.has(d)); }
    return all.filter((d) => (kind === "folder" ? isFolder(d) : kind === "doc" ? !isFolder(d) : true)).map((d) => ({ id: d.id ?? d.name, label: d.name, folder: isFolder(d) }));
  }
  R["a!pickerFieldDocumentsAndFolders"] = (n, ctx) => picker(n, ctx, "docfolder");
  /* Vídeo (a!videoField + a!webVideo): reproductor 16:9 con controles. Solo de prototipo: $duration en a!webVideo ("2:30"). */
  R["a!videoField"] = (n, ctx) => {
    const es = LANG === "es";
    const vids = arr(n.videos).filter((v) => v && visible(v, ctx));
    const player = (v, i) => {
      const src = String(P(v, "source", ctx) || ""), host = (src.match(/^https?:\/\/(?:www\.)?([^/?#]+)/) || [])[1] || "";
      const k = "vid:" + ctx.key + ":" + i, on = !!UI[k], dur = interp(v.$duration || "", ctx) || "–:–";
      const toggle = () => { if (inspector) return; UI[k] = !on; rerender(); };
      const tip = P(v, "tooltip", ctx);
      return h("div", { class: "vid" + (on ? " on" : ""), title: tip || null, role: "region", "aria-label": tip || (es ? "Vídeo" : "Video") },
        h("div", { class: "vid-s" }, tip ? h("div", { class: "vid-t" }, tip) : null, h("button", { type: "button", class: "vid-play", "aria-label": on ? (es ? "Pausar" : "Pause") : (es ? "Reproducir" : "Play"), onclick: toggle }, icon(on ? "pause" : "play")),
          host ? h("span", { class: "vid-src" }, host) : null),
        h("div", { class: "vid-c" }, h("button", { type: "button", class: "vid-b", "aria-label": on ? (es ? "Pausar" : "Pause") : (es ? "Reproducir" : "Play"), onclick: toggle }, icon(on ? "pause" : "play")),
          h("span", { class: "vid-tm" }, `${on ? "0:08" : "0:00"} / ${dur}`), h("span", { class: "vid-bar" }, h("i", { style: { width: on ? "6%" : "0" } })),
          h("span", { class: "vid-b" }, icon("volume-up")), h("span", { class: "vid-b" }, icon("cc")), h("span", { class: "vid-b" }, icon("expand"))));
    };
    return field(n, ctx, vids.length ? h("div", { class: "vids" + (vids.length > 1 ? " multi" : "") }, vids.map(player)) : h("div", { class: "gempty" }, T.empty));
  };
  /* Contenido web (a!webContentField): marco con la página externa. El prototipo no carga la web: muestra su dominio y un esqueleto.
     Solo de prototipo: $title (qué muestra la página). 26.9: puede pedir cámara y micrófono (videollamadas, verificación de identidad). */
  R["a!webContentField"] = (n, ctx) => {
    const es = LANG === "es";
    const src = String(P(n, "source", ctx) || ""), host = (src.match(/^https?:\/\/(?:www\.)?([^/?#]+)/) || [])[1] || src || (es ? "sin origen" : "no source");
    const hgt = { SHORT: 240, MEDIUM: 400, TALL: 600 }[up(P(n, "height", ctx, "MEDIUM"))] || 400;
    const ttl = interp(n.$title || "", ctx);
    const sk = (w) => h("i", { style: { width: w + "%" } });
    return field(n, ctx, h("div", { class: "wc" + (P(n, "showBorder", ctx, true) ? " b" : "") + (P(n, "disabled", ctx, false) ? " dis" : ""), style: { height: hgt + "px" }, role: "document", "aria-label": P(n, "altText", ctx) || P(n, "accessibilityText", ctx) || host },
      h("div", { class: "wc-top" }, h("span", { class: "wc-dot" }), sk(18), h("span", { class: "sp" }), sk(8), sk(8), sk(8)),
      h("div", { class: "wc-body" }, h("div", { class: "wc-hero" }, h("span", { class: "wc-ic" }, icon("globe")), h("div", null, h("div", { class: "wc-h" }, ttl || (es ? "Contenido web externo" : "External web content")), h("div", { class: "wc-u" }, icon("lock"), " ", host))),
        h("div", { class: "wc-sk" }, [72, 90, 64, 84, 40].map(sk)), h("div", { class: "wc-cards" }, [0, 1, 2].map(() => h("div", { class: "wc-card" }, sk(60), sk(85), sk(40)))))));
  };
  /* Firma (a!signatureField, estilo de 26.8): botón «Dibujar firma» → cuadro para firmar con línea discontinua; al guardar, la firma
     queda como imagen con opción de quitarla. El valor es el documento de la firma: { name, src } (o un texto con el nombre del fichero). */
  function sigImg(v) {
    const src = v && typeof v === "object" ? v.src : null;
    const name = v && typeof v === "object" ? v.name : String(v || "");
    return h("div", { class: "sig-img" }, src ? h("img", { class: "sig-draw", src, alt: LANG === "es" ? "Firma" : "Signature" }) : h("span", { class: "sig-draw", html: '<svg viewBox="0 0 240 70" width="240" height="70" aria-hidden="true"><path d="M12 48c14-30 26-40 30-30s-12 38-4 40 20-34 30-30-6 26 4 26 16-22 26-20 2 18 12 18 18-16 30-14 10 10 22 8 30-10 60-12" fill="none" stroke="#1a2732" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>' }),
      h("span", { class: "sig-n" }, icon("file-image-o"), " ", name || "firma.png"));
  }
  R["a!signatureField"] = (n, ctx) => {
    const es = LANG === "es";
    const v = getVal(n, ctx);
    const ro = P(n, "readOnly", ctx, false), dis = P(n, "disabled", ctx, false);
    const k = "sig:" + ctx.key;
    const setV = (x) => { const r = refOf(n, "value", ctx); saveInto(n, x, ctx); if (r && !n.saveInto) writeRef(r, x); schedule(); };
    let body;
    if (!isEmpty(v)) body = h("div", { class: "sig-v" }, sigImg(v), ro || dis ? null : h("button", { type: "button", class: "btn s-LINK z-SMALL", style: { "--bc": "var(--accent)" }, onclick: () => { if (!inspector) setV(null); } }, icon("times"), es ? "Quitar firma" : "Remove signature"));
    else if (ro) body = readOnlyVal(null);
    else body = h("div", { class: "sig-btn" }, h("button", { type: "button", class: uploadBtnCls(n, ctx), style: uploadBtnStyle(n, ctx), disabled: dis, onclick: () => { if (inspector) return; UI[k] = true; rerender(); } }, icon("signature"), es ? "Dibujar firma" : "Draw signature"));
    const el = field(n, ctx, body, { getValue: () => getVal(n, ctx) });
    if (UI[k]) {
      const cv = h("canvas", { width: 560, height: 200, class: "sig-cv", "aria-label": es ? "Zona de firma" : "Signature area" });
      let drawing = false, dirty = false;
      const g = cv.getContext && cv.getContext("2d");
      const pt = (e) => { const b = cv.getBoundingClientRect(); return [(e.clientX - b.left) * (cv.width / b.width), (e.clientY - b.top) * (cv.height / b.height)]; };
      if (g) { g.lineWidth = 3; g.lineCap = "round"; g.lineJoin = "round"; g.strokeStyle = "#1a2732"; }
      const save = h("button", { type: "button", class: "btn s-SOLID", style: { "--bc": "var(--accent)", "--bfg": solidFg(accentHex()) }, disabled: true }, es ? "Guardar" : "Save");
      cv.addEventListener("pointerdown", (e) => { if (!g) return; drawing = true; const [x, y] = pt(e); g.beginPath(); g.moveTo(x, y); cv.setPointerCapture && cv.setPointerCapture(e.pointerId); });
      cv.addEventListener("pointermove", (e) => { if (!drawing) return; const [x, y] = pt(e); g.lineTo(x, y); g.stroke(); if (!dirty) { dirty = true; save.disabled = false; } });
      cv.addEventListener("pointerup", () => (drawing = false));
      const close = () => { delete UI[k]; rerender(); };
      save.addEventListener("click", () => { const name = P(n, "fileName", ctx) || (es ? "firma" : "signature"); delete UI[k]; setV({ name: /\.\w+$/.test(name) ? name : name + ".png", src: cv.toDataURL("image/png") }); });
      el.appendChild(h("div", { class: "dlg-bg sig-bg", role: "dialog", "aria-modal": "true", "aria-label": es ? "Firmar" : "Sign" },
        h("div", { class: "dlg w-NARROW" }, h("div", { class: "dlg-h" }, h("h2", null, P(n, "label", ctx) || (es ? "Firma" : "Signature")), h("button", { type: "button", class: "x", "aria-label": T.cancel, onclick: close }, "×")),
          h("div", { class: "dlg-c" }, h("div", { class: "sig-pad" }, cv, h("span", { class: "sig-x", "aria-hidden": "true" }, "×"), h("span", { class: "sig-line", "aria-hidden": "true" })), h("div", { class: "instr" }, es ? "Firme dentro del recuadro con el ratón, el dedo o un lápiz." : "Sign inside the box with your mouse, finger or stylus.")),
          h("div", { class: "dlg-f" }, h("div", { class: "grp" }, h("button", { type: "button", class: "btn s-OUTLINE", style: { "--bc": "var(--text-2)" }, onclick: close }, T.cancel), h("button", { type: "button", class: "btn s-GHOST", style: { "--bc": "var(--accent)" }, onclick: () => { if (g) g.clearRect(0, 0, cv.width, cv.height); dirty = false; save.disabled = true; } }, icon("eraser"), es ? "Borrar" : "Clear")),
            h("div", { class: "grp pri" }, save)))));
    }
    return el;
  };
  // Código de barras: en web es un campo de texto (el escaneo con cámara es de Appian Mobile); masked oculta el valor.
  R["a!barcodeField"] = (n, ctx) => textLike(P(n, "masked", ctx, false) ? "password" : "text", n, ctx, { style: `text-align:${{ CENTER: "center", RIGHT: "right" }[up(P(n, "align", ctx, "LEFT"))] || "left"}` });
  // imagen dentro de texto enriquecido (a!richTextImage): a la altura de la línea
  function inlineImg(im, ctx) {
    if (!im || typeof im !== "object") return null;
    const alt = interp(im.altText || im.caption || "", ctx);
    if (im.type === "a!userImage") { const u = interp(im.user || "", ctx); const nm = (usrOf(u) || {}).name || u; return h("span", { class: "nv-av rti", title: nm, style: { background: avatarBg(nm) } }, FILTERS.initials(nm)); }
    const src = im.type === "a!webImage" ? String(interp(im.source || "", ctx) || "") : "";
    if (src.startsWith("data:")) return h("img", { class: "rti", src, alt });
    return h("span", { class: "rti ph", title: alt || null, role: alt ? "img" : null, "aria-label": alt || null }, icon("picture-o"));
  }
  /* ---- IA: componentes de chat ----
     a!agentChatField (26.6), a!chatField + a!chatMessage, a!dataFabricChatField + a!suggestedQuestion, a!recordsChatField, a!documentsChatField.
     La conversación del prototipo vive en UI["chat:<key>"]. Claves solo de prototipo (validate.py no las comprueba):
       $messages  conversación ya empezada: [{ role: USER|ASSISTANT|TOOL|THOUGHT|BLOCKED, text, tool, input, output }]
       $replies   respuestas simuladas, por turnos (texto o { text, content (componente), tools: [{ tool, text, input, output }],
                  thoughts: [texto], outputs: {…} para outputsSaveInto, blocked: true (bloqueo de guardrail), $action })
       $sessions  (agente) conversaciones anteriores del selector: texto o { name, messages }
       $state     estado fijo para capturas: RUNNING (respondiendo, botón Detener) | UNAVAILABLE (función de IA no habilitada) */
  const AI = LANG === "es"
    ? { send: "Enviar", stop: "Detener respuesta", newChat: "Nueva conversación", recent: "Conversaciones anteriores", ph: "Escriba un mensaje", dfTitle: "Data Fabric Chatbot", dfPh: "Haga una pregunta sobre sus datos", recInit: "¡Hola! Soy un chatbot con IA que puede darle más información sobre este registro. ¿En qué puedo ayudarle?", recSug: "¿Qué preguntas puede responder?", stopped: "Respuesta detenida por el usuario", tool: "Herramienta", input: "Entrada", output: "Salida", thoughts: "Razonamiento del modelo", unavailable: "Esta función no está disponible en este momento. Póngase en contacto con el administrador.", noReply: "(Respuesta simulada: defina $replies en el componente.)" }
    : { send: "Send", stop: "Stop response", newChat: "New conversation", recent: "Previous conversations", ph: "Type a message", dfTitle: "Data Fabric Chatbot", dfPh: "Ask a question about your data.", recInit: "Hi! I'm an AI-powered chatbot who can give you more information on this record. What would you like help with?", recSug: "What questions can you answer?", stopped: "Response stopped by user", tool: "Tool", input: "Input", output: "Output", thoughts: "Model reasoning", unavailable: "This function is currently unavailable. Contact your administrator.", noReply: "(Simulated reply: define $replies on the component.)" };
  const CHAT_H = { EXTRA_SHORT: 180, SHORT: 260, SHORT_PLUS: 320, MEDIUM: 400, MEDIUM_PLUS: 480, TALL: 560, TALL_PLUS: 640, EXTRA_TALL: 740 };
  const trunc = (s, n) => { s = String(s == null ? "" : s); return s.length > n ? s.slice(0, n - 1) + "…" : s; };
  const fmtJson = (v) => (typeof v === "string" ? v : JSON.stringify(v, null, 2));
  function normMsg(m, ctx) {
    if (typeof m === "string") return { role: "ASSISTANT", text: interp(m, ctx) };
    return Object.assign({}, m, { role: up(m.role || "ASSISTANT"), text: m.text != null ? interp(String(m.text), ctx) : null });
  }
  function chatState(n, ctx) {
    const k = "chat:" + ctx.key;
    if (!UI[k]) UI[k] = { msgs: arr(n.$messages).map((m) => normMsg(m, ctx)), busy: false, turn: 0, sess: null };
    return UI[k];
  }
  // texto de respuesta con un Markdown mínimo (párrafos, listas y **negrita**), como las respuestas de los agentes
  function mdLite(text) {
    const inline = (s) => s.split(/(\*\*[^*]+\*\*)/).map((p) => (/^\*\*[^*]+\*\*$/.test(p) ? h("strong", null, p.slice(2, -2)) : p));
    return h("div", { class: "md" }, String(text == null ? "" : text).split(/\n{2,}/).map((b) => {
      const lines = b.split("\n");
      if (lines.every((l) => /^\s*[-•]\s+/.test(l))) return h("ul", null, lines.map((l) => h("li", null, inline(l.replace(/^\s*[-•]\s+/, "")))));
      if (lines.every((l) => /^\s*\d+[.)]\s+/.test(l))) return h("ol", null, lines.map((l) => h("li", null, inline(l.replace(/^\s*\d+[.)]\s+/, "")))));
      return h("p", null, lines.map((l, i) => [i ? h("br") : null, inline(l)]));
    }));
  }
  function chatMsgEl(m, opt, ctx, key) {
    const av = opt.avatar ? h("span", { class: "av", "aria-hidden": "true" }, icon(opt.avatar)) : null;
    const body = (bubble) => (m.content ? h("div", { class: "cmc" }, render(m.content, m.ctx || ctx, key)) : bubble ? h("div", { class: "bub" }, mdLite(m.text)) : h("div", { class: "txt" }, mdLite(m.text)));
    if (m.role === "USER") return h("div", { class: "cm u" }, m.content ? body(false) : h("div", { class: "bub" }, m.text));
    if (m.role === "TOOL") {
      const head = [icon("wrench"), h("span", { class: "tl" }, h("span", { class: "tn" }, m.tool || AI.tool), m.text ? " · " + interp(m.text, ctx) : null), icon("check", "ok")];
      if (opt.debug && (m.input != null || m.output != null))
        return h("details", { class: "cm tool" }, h("summary", null, head, icon("angle-down", "chev")),
          m.input != null ? h("div", { class: "io" }, h("div", { class: "k" }, AI.input), h("pre", null, fmtJson(m.input))) : null,
          m.output != null ? h("div", { class: "io" }, h("div", { class: "k" }, AI.output), h("pre", null, fmtJson(m.output))) : null);
      return h("div", { class: "cm tool" }, head);
    }
    if (m.role === "THOUGHT") return h("details", { class: "cm tool" }, h("summary", null, icon("lightbulb-o"), h("span", { class: "tl" }, AI.thoughts), icon("angle-down", "chev")), h("div", { class: "io" }, mdLite(m.text)));
    if (m.role === "STOPPED") return h("div", { class: "cm note" }, icon("stop-circle"), AI.stopped);
    if (m.role === "BLOCKED") return h("div", { class: "cm a blk" }, av, h("div", { class: "bub" }, icon("exclamation-triangle"), h("span", null, m.text)));
    return h("div", { class: "cm a" + (m.content ? " wide" : "") }, av, body(opt.bubble));
  }
  function chatSend(n, ctx, st, text, kind) {
    text = String(text == null ? "" : text).trim();
    if (!text || st.busy || inspector) return;
    st.msgs.push({ role: "USER", text });
    if (kind === "chat" && n.saveInto) saveInto(n, text, ctx); // a!chatField: saveInto recibe el texto enviado (save!value)
    const replies = arr(n.$replies);
    const r = replies.length ? replies[st.turn % replies.length] : null;
    st.turn++;
    const rep = r == null ? { text: AI.noReply } : typeof r === "string" ? { text: r } : r;
    const debug = kind === "agent" || kind === "df" ? P(n, "debugMode", ctx, false) : false;
    const steps = [];
    if (debug) arr(rep.thoughts).forEach((t) => steps.push({ role: "THOUGHT", text: interp(String(t), ctx) }));
    if (kind === "agent") arr(rep.tools).forEach((t) => steps.push(Object.assign({ role: "TOOL" }, typeof t === "string" ? { tool: t } : t)));
    st.busy = true;
    rerender();
    let i = 0;
    const tick = () => {
      if (!st.busy) return; // detenida con el botón Detener
      if (i < steps.length) { st.msgs.push(steps[i++]); rerender(); st.timer = setTimeout(tick, 600); return; }
      st.msgs.push(rep.content ? { role: "ASSISTANT", content: rep.content } : { role: rep.blocked ? "BLOCKED" : "ASSISTANT", text: interp(String(rep.text || ""), ctx) });
      st.busy = false;
      if (rep.outputs && n.outputsSaveInto) saveInto(n, clone(rep.outputs), ctx, "outputsSaveInto");
      if (rep.$action) runAction(rep.$action, ctx); else rerender();
    };
    st.timer = setTimeout(tick, 750);
  }
  function chatStop(st) { if (!st.busy) return; clearTimeout(st.timer); st.busy = false; st.msgs.push({ role: "STOPPED" }); rerender(); }
  const chatRunning = (n, st) => st.busy || up(n.$state) === "RUNNING";
  function chatMsgs(n, ctx, st, opt, intro, extra) {
    const typing = chatRunning(n, st) ? h("div", { class: "cm a" }, opt.avatar ? h("span", { class: "av", "aria-hidden": "true" }, icon(opt.avatar)) : null, h("div", { class: "typing", role: "status", "aria-label": LANG === "es" ? "Respondiendo" : "Responding" }, h("i"), h("i"), h("i"))) : null;
    const err = up(n.$state) === "UNAVAILABLE" ? h("div", { class: "aic-err", role: "alert" }, icon("exclamation-circle"), AI.unavailable) : null;
    const all = (extra || []).concat(st.msgs);
    const box = h("div", { class: "aic-msgs", role: "log", "aria-live": "polite" }, err || [intro, all.map((m, i) => chatMsgEl(m, opt, ctx, `${ctx.key}.m${i}`)), typing]);
    requestAnimationFrame(() => { if (box.isConnected && all.length) box.scrollTop = box.scrollHeight; });
    return box;
  }
  function chatInput(n, ctx, st, kind, opt) {
    const running = chatRunning(n, st);
    const off = up(n.$state) === "UNAVAILABLE";
    const inp = h("input", { class: "inp", id: "f-" + ctx.key + "-msg", placeholder: opt.ph, "aria-label": opt.aria || opt.ph, disabled: off });
    const send = () => chatSend(n, ctx, st, inp.value, kind);
    inp.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); send(); } });
    let btn;
    if (running && kind === "agent") btn = h("button", { type: "button", class: "cbtn stop", "aria-label": AI.stop, title: AI.stop, onclick: () => chatStop(st) }, icon("stop"));
    else if (opt.buttonStyle) {
      const bs = up(opt.buttonStyle);
      btn = h("button", { type: "button", class: "btn z-SMALL " + (bs === "PRIMARY" ? "s-SOLID" : bs === "LINK" ? "s-LINK" : "s-OUTLINE"), style: { "--bc": "var(--accent)", "--bfg": solidFg(hexOf("ACCENT")) }, disabled: running || off, onclick: send }, AI.send);
    } else btn = h("button", { type: "button", class: "cbtn", "aria-label": AI.send, title: AI.send, disabled: running || off, onclick: send }, icon("paper-plane"));
    return h("div", { class: "aic-in" }, inp, btn);
  }
  const chatHeight = (n, ctx, dflt) => { const hk = up(P(n, "height", ctx, dflt)); return { cls: "h-" + hk, style: CHAT_H[hk] ? { height: CHAT_H[hk] + "px" } : null }; };
  const helpIcon = (n, ctx) => (n.helpTooltip ? h("span", { class: "help", title: P(n, "helpTooltip", ctx) }, icon("question-circle")) : null);

  // Agent Chat: barra de título con selector de conversaciones, bienvenida, streaming, llamadas a herramientas (entradas y salidas solo en debugMode) y botón Detener
  R["a!agentChatField"] = (n, ctx) => {
    const st = chatState(n, ctx);
    const opt = { avatar: "magic", debug: P(n, "debugMode", ctx, false) };
    let picker = null;
    if (P(n, "showSessionPicker", ctx, true)) {
      const sessions = arr(n.$sessions).map((s) => (typeof s === "string" ? { name: interp(s, ctx) } : Object.assign({}, s, { name: interp(s.name || "", ctx) })));
      const cur = st.sess || (st.msgs.find((m) => m.role === "USER") || {}).text || AI.newChat;
      const pop = h("div", { class: "pop", hidden: true, role: "menu", style: { right: 0, top: "calc(100% + 4px)", minWidth: "260px" } },
        h("button", { type: "button", role: "menuitem", onclick: () => { clearTimeout(st.timer); Object.assign(st, { msgs: [], sess: null, busy: false }); rerender(); } }, icon("plus"), AI.newChat),
        sessions.length ? h("div", { class: "pop-h" }, AI.recent) : null,
        sessions.map((s) => h("button", { type: "button", role: "menuitem", onclick: () => { clearTimeout(st.timer); Object.assign(st, { msgs: arr(s.messages).map((m) => normMsg(m, ctx)), sess: s.name, busy: false }); rerender(); } }, icon("comment-o"), trunc(s.name, 42))));
      picker = h("div", { class: "sess" }, h("button", { type: "button", class: "sess-b", "aria-haspopup": "menu", title: cur, onclick: (e) => { e.stopPropagation(); pop.hidden = !pop.hidden; } }, h("span", { class: "sn" }, trunc(cur, 34)), icon("angle-down")), pop);
      document.addEventListener("click", () => (pop.hidden = true), { once: true });
    }
    const welcome = P(n, "welcomeMessage", ctx);
    const intro = welcome && !st.msgs.some((m) => m.role === "USER") ? h("div", { class: "aic-welcome" }, h("span", { class: "wi", "aria-hidden": "true" }, icon("magic")), mdLite(welcome)) : null;
    const hh = chatHeight(n, ctx, "FILL");
    return h("div", { class: `aic agent ${hh.cls} shape-${up(P(n, "shape", ctx, "SQUARED"))}` + (P(n, "showBorder", ctx, false) ? " b" : ""), style: hh.style },
      h("div", { class: "aic-h" }, h("span", { class: "t" }, P(n, "title", ctx, "Agent Chat")), picker),
      chatMsgs(n, ctx, st, opt, intro),
      chatInput(n, ctx, st, "agent", { ph: P(n, "placeholder", ctx) || AI.ph, aria: P(n, "title", ctx, "Agent Chat") }));
  };

  // Chat personalizado: título (texto o componentes), mensajes a!chatMessage (texto con estilo por defecto o componentes), saveInto al enviar
  R["a!chatField"] = (n, ctx) => {
    const st = chatState(n, ctx);
    const specMsgs = [];
    const pushMsg = (m, c) => {
      if (m == null || !visible(m, c)) return;
      if (typeof m === "string") return specMsgs.push({ role: "ASSISTANT", text: interp(m, c) });
      if (m.type !== "a!chatMessage") return specMsgs.push({ role: "ASSISTANT", content: m, ctx: c });
      const role = up(P(m, "role", c, "ASSISTANT"));
      const mc = m.messageContent;
      specMsgs.push(mc && typeof mc === "object" ? { role, content: mc, ctx: c } : { role, text: interp(String(mc == null ? "" : mc), c) });
    };
    arr(n.messages).forEach((m) => { if (m && m.type === "a!forEach") forEachItems(m, ctx).forEach((it) => pushMsg(it.node, it.ctx)); else pushMsg(m, ctx); });
    const bg = String(P(n, "backgroundColor", ctx, "WHITE"));
    const hex = bg.startsWith("#");
    const dark = hex ? solidFg(bg) === "#ffffff" : /_SCHEME$/.test(up(bg));
    const tt = n.title;
    const titleEl = tt == null ? null : typeof tt === "string" ? h("div", { class: "aic-t" }, interp(tt, ctx), helpIcon(n, ctx)) : h("div", { class: "aic-t comp" }, render(tt, ctx, ctx.key + ".title"));
    const hh = chatHeight(n, ctx, "AUTO");
    return h("div", { class: `aic chat ${hh.cls} shape-${up(P(n, "shape", ctx, "SQUARED"))} ${hex ? "" : "bg-" + up(bg)}` + (dark ? " dark" : "") + (P(n, "showBorder", ctx, false) ? " b" : ""), style: Object.assign({ background: hex ? bg : null }, hh.style) },
      titleEl,
      chatMsgs(n, ctx, st, { bubble: true }, null, specMsgs),
      chatInput(n, ctx, st, "chat", { ph: P(n, "placeholder", ctx) || AI.ph, aria: typeof tt === "string" ? interp(tt, ctx) : AI.ph }));
  };

  // Data Fabric Chatbot: barra de título, hasta 3 preguntas sugeridas con icono (clicables) al empezar; recomendado dentro de un a!pane mostrable/ocultable
  R["a!dataFabricChatField"] = (n, ctx) => {
    const st = chatState(n, ctx);
    const qs = arr(n.suggestedQuestions).filter((q) => q != null && (typeof q === "string" || visible(q, ctx))).slice(0, 3);
    const intro = qs.length && !st.msgs.some((m) => m.role === "USER") ? h("div", { class: "aic-sugg" }, qs.map((q) => {
      const text = typeof q === "string" ? interp(q, ctx) : P(q, "question", ctx, "");
      const ic = typeof q === "string" ? null : P(q, "iconName", ctx);
      return h("button", { type: "button", class: "sq", onclick: () => chatSend(n, ctx, st, text, "df") }, ic ? h("span", { class: "sqi", style: { color: color(P(q, "iconColor", ctx, "STANDARD"), "inherit") } }, icon(ic)) : null, h("span", null, text));
    })) : null;
    return h("div", { class: "aic df h-FILL" },
      h("div", { class: "aic-h" }, h("span", { class: "t" }, P(n, "title", ctx, AI.dfTitle)), helpIcon(n, ctx)),
      chatMsgs(n, ctx, st, { avatar: "magic", debug: P(n, "debugMode", ctx, false) }, intro),
      chatInput(n, ctx, st, "df", { ph: P(n, "placeholder", ctx) || AI.dfPh }));
  };

  // Records Chatbot: campo con etiqueta; primer mensaje del bot, hasta 3 preguntas sugeridas (texto) y botón Enviar con buttonStyle (PRIMARY por defecto)
  R["a!recordsChatField"] = (n, ctx) => {
    const st = chatState(n, ctx);
    const first = { role: "ASSISTANT", text: P(n, "initialMessage", ctx) || AI.recInit };
    let qs = n.suggestedQuestions == null ? [AI.recSug] : arr(P(n, "suggestedQuestions", ctx));
    qs = qs.filter((q) => !isEmpty(q)).slice(0, 3);
    const opt = { avatar: "magic", bubble: true };
    const sugg = qs.length && !st.msgs.some((m) => m.role === "USER") ? h("div", { class: "aic-sugg chips" }, qs.map((q) => h("button", { type: "button", class: "sq", onclick: () => chatSend(n, ctx, st, q, "rec") }, q))) : null;
    const hh = chatHeight(n, ctx, "AUTO");
    const box = h("div", { class: `aic rec b ${hh.cls}`, style: hh.style },
      chatMsgs(n, ctx, st, opt, [chatMsgEl(first, opt, ctx, ctx.key + ".m0"), sugg]),
      chatInput(n, ctx, st, "rec", { ph: AI.ph, aria: P(n, "label", ctx) || AI.ph, buttonStyle: P(n, "buttonStyle", ctx, "PRIMARY") }));
    return field(n, ctx, box);
  };

  // Documents Chatbot: campo con etiqueta y chat sin mensaje inicial ni preguntas sugeridas
  R["a!documentsChatField"] = (n, ctx) => {
    const st = chatState(n, ctx);
    const hh = chatHeight(n, ctx, "AUTO");
    const nd = arr(P(n, "documents", ctx)).length;
    // sin conversación: estado inicial que dice sobre qué se puede preguntar (Appian no pone mensaje de bienvenida)
    const hint = st.msgs.length ? null : h("div", { class: "aic-welcome" }, h("span", { class: "wi" }, icon("file-text-o")),
      h("div", null, LANG === "es" ? `Pregunte por el contenido ${nd === 1 ? "del documento" : `de ${nd || "los"} documentos`}` : "Ask about the documents"));
    const box = h("div", { class: `aic rec b ${hh.cls}`, style: hh.style },
      chatMsgs(n, ctx, st, { avatar: "magic", bubble: true }, hint),
      chatInput(n, ctx, st, "doc", { ph: AI.ph, aria: P(n, "label", ctx) || AI.ph }));
    return field(n, ctx, box);
  };
  // a!recordKnowledgeGraph (26.8): registro base en el centro y registros relacionados alrededor (hasta relationshipLevel niveles),
  // con etiqueta de tipo de registro y nombre, minimapa (showMiniMap) y controles de zoom. Solo de prototipo:
  //   $root  { recordType, name, icon }   registro base (por defecto, el título del registro de la pantalla)
  //   $nodes [{ recordType, name, icon, parent }]   relacionados; parent = name de otro nodo (sin parent: primer nivel)
  R["a!recordKnowledgeGraph"] = (n, ctx) => {
    const hk = up(P(n, "height", ctx, "AUTO"));
    const H = { SHORT: 280, MEDIUM: 420, TALL: 560 }[hk] || 420;
    const lvl = Math.max(1, Math.min(10, Number(P(n, "relationshipLevel", ctx, 3)) || 3));
    const rootN = n.$root || {};
    const root = { recordType: interp(rootN.recordType || String(n.recordType || "").replace(/^recordType!/, ""), ctx), name: interp(rootN.name || (ctx.record && (ctx.record.titulo || ctx.record.nombre || ctx.record.codigo)) || "Registro", ctx), icon: rootN.icon || "file-text-o" };
    const all = arr(n.$nodes).map((x) => ({ recordType: interp(x.recordType || "", ctx), name: interp(String(x.name || ""), ctx), icon: x.icon || "file-o", parent: x.parent != null ? interp(String(x.parent), ctx) : null }));
    const byName = {}; all.forEach((x) => (byName[x.name] = x));
    const depth = (x, d) => (!x.parent || !byName[x.parent] || d > 10 ? 1 : 1 + depth(byName[x.parent], d + 1));
    const nodes = all.filter((x) => depth(x, 0) <= lvl);
    // árbol radial: cada nodo recibe un sector proporcional a sus hojas; el nivel k va en la elipse k (el último, junto al borde)
    const kidsOf = (par) => nodes.filter((x) => (par ? x.parent === par.name && byName[x.parent] === par : !x.parent || !byName[x.parent]));
    const leaves = (x, d) => { const k = d > 10 ? [] : kidsOf(x); return k.length ? k.reduce((t, c) => t + leaves(c, d + 1), 0) : 1; };
    const maxD = Math.max(1, ...nodes.map((x) => depth(x, 0)));
    const pos = new Map();
    const lay = (par, a0, a1, d) => {
      const kids = kidsOf(par);
      const tot = kids.reduce((t, c) => t + leaves(c, 0), 0) || 1;
      let a = a0;
      kids.forEach((c) => {
        const span = ((a1 - a0) * leaves(c, 0)) / tot, mid = a + span / 2;
        pos.set(c, { x: 50 + ((41 * d) / maxD) * Math.cos(mid), y: 50 + ((40 * d) / maxD) * Math.sin(mid) });
        if (d < 10) lay(c, a, a + span, d + 1);
        a += span;
      });
    };
    const first = kidsOf(null);
    const off = first.length ? (Math.PI * leaves(first[0], 0)) / Math.max(1, first.reduce((t, c) => t + leaves(c, 0), 0)) : 0;
    lay(null, -Math.PI / 2 - off, (3 * Math.PI) / 2 - off, 1);
    const placed = nodes.filter((x) => pos.has(x));
    const edges = placed.map((x) => { const a = pos.get(x); const b = x.parent && byName[x.parent] && pos.get(byName[x.parent]) || { x: 50, y: 50 }; return `<line x1="${b.x}" y1="${b.y}" x2="${a.x}" y2="${a.y}" vector-effect="non-scaling-stroke"/>`; }).join("");
    const svg = h("div", { class: "kg-edges", html: `<svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">${edges}</svg>` });
    const nodeEl = (x, p, main) => h("div", { class: "kg-n" + (main ? " main" : ""), style: { left: p.x + "%", top: p.y + "%" }, title: `${x.recordType}: ${x.name}`, tabindex: "0" }, h("span", { class: "kg-i" }, icon(x.icon)), h("span", { class: "kg-t" }, h("span", { class: "kg-rt" }, x.recordType), h("span", { class: "kg-nm" }, x.name)));
    const es = LANG === "es";
    const ib = (ic, label) => h("button", { type: "button", class: "ib", title: label, "aria-label": label }, icon(ic));
    const mini = P(n, "showMiniMap", ctx, true) ? h("div", { class: "kg-mini", "aria-hidden": "true", html: `<svg viewBox="0 0 100 100" preserveAspectRatio="none"><rect x="3" y="3" width="94" height="94" class="vp"/>${placed.map((x) => { const q = pos.get(x); return `<rect x="${q.x - 5}" y="${q.y - 3}" width="10" height="6" rx="2"/>`; }).join("")}<rect x="43" y="46" width="14" height="8" rx="2" class="c"/></svg>` }) : null;
    const el = h("div", { class: "kg", style: { height: H + "px" }, role: "img", "aria-label": P(n, "accessibilityText", ctx) || P(n, "label", ctx) || root.name },
      svg, placed.map((x) => nodeEl(x, pos.get(x), false)), nodeEl(root, { x: 50, y: 50 }, true),
      h("div", { class: "kg-tb" }, ib("search-plus", es ? "Ampliar" : "Zoom in"), ib("search-minus", es ? "Reducir" : "Zoom out"), ib("expand", es ? "Pantalla completa" : "Full screen")), mini);
    return field(n, ctx, el);
  };
  R["a!recordActionField"] = (n, ctx) => {
    const st = up(P(n, "style", ctx, "TOOLBAR"));
    const disp = up(P(n, "display", ctx, "LABEL_AND_ICON"));
    const acts = arr(n.actions).filter((a) => visible(a, ctx));
    const lab = (a) => interp(a.$label || fieldOf(a.action), ctx);
    const ico = (a) => (a.$icon && disp !== "LABEL" ? icon(interp(a.$icon, ctx)) : null);
    const txt = (a) => (disp === "ICON" ? null : lab(a));
    if (st === "LINKS") return h("div", { class: "ra st-LINKS" }, acts.map((a) => h("a", { href: "#", onclick: clickable(a, ctx) }, ico(a), txt(a))));
    if (st === "CARDS") return h("div", { class: "ra st-CARDS" }, acts.map((a) => h("button", { type: "button", onclick: clickable(a, ctx) }, a.$icon ? h("span", { style: { fontSize: "22px" } }, icon(a.$icon)) : null, lab(a))));
    if (st === "MENU" || st === "MENU_ICON") {
      const pop = h("div", { class: "pop", hidden: true, style: { right: 0, top: "100%" } }, acts.map((a) => h("button", { type: "button", onclick: clickable(a, ctx) }, ico(a), lab(a))));
      const b = h("button", { type: "button", class: "btn s-OUTLINE", style: { "--bc": "var(--accent)" }, "aria-haspopup": "menu", onclick: (e) => { e.stopPropagation(); pop.hidden = !pop.hidden; } }, st === "MENU_ICON" ? icon("ellipsis-v") : [T.filters === "Filtros" ? "Acciones" : "Actions", icon("angle-down")]);
      document.addEventListener("click", () => (pop.hidden = true), { once: true });
      return h("div", { class: "ra menu-btn", style: { position: "relative", display: "inline-flex" } }, b, pop);
    }
    const primary = st === "CALL_TO_ACTION" || st === "TOOLBAR_PRIMARY" || st === "SIDEBAR_PRIMARY";
    const al = up(P(n, "align", ctx, "START"));
    return h("div", { class: `ra st-${st}`, style: { justifyContent: al === "END" ? "flex-end" : al === "CENTER" ? "center" : null } }, acts.map((a, i) => {
      const solid = primary && i === 0;
      const bc = solid ? brandPrimary() : "var(--accent)";
      return h("button", { type: "button", class: `btn ${solid ? "s-SOLID" : "s-OUTLINE"}`, style: { "--bc": bc, "--bfg": solidFg(bc) }, onclick: clickable(a, ctx) }, ico(a), txt(a));
    }));
  };
  function brandPrimary() { return (BRAND.components && BRAND.components.primaryButton && BRAND.components.primaryButton.color) || "var(--accent)"; }

  /* ---- buttons ---- */
  R["a!buttonWidget"] = (n, ctx) => {
    const st = up(P(n, "style", ctx, "OUTLINE"));
    const bc = color(P(n, "color", ctx, "ACCENT"), "var(--accent)");
    const ic = P(n, "icon", ctx);
    const pos = up(P(n, "iconPosition", ctx, "START"));
    const b = h("button", { type: "button", class: `btn s-${st} z-${up(P(n, "size", ctx, "STANDARD"))}` + (up(n.width) === "FILL" ? " fill" : ""), style: { "--bc": bc, "--bfg": solidFg(bc) }, disabled: P(n, "disabled", ctx, false), title: P(n, "tooltip", ctx), "aria-label": P(n, "accessibilityText", ctx) || (n.label ? null : P(n, "tooltip", ctx)) },
      ic && pos === "START" ? icon(ic) : null, P(n, "label", ctx), ic && pos === "END" ? icon(ic) : null);
    b.addEventListener("click", (e) => {
      if (inspector) return;
      const doIt = () => {
        const validate = P(n, "validate", ctx, !!P(n, "submit", ctx, false));
        if (validate && !checkRequired(ctx.scope)) { invalid[ctx.scope] = true; rerender(); return; }
        if (n.saveInto) saveInto(n, P(n, "value", ctx), ctx);
        runAction(n.$action, ctx, n);
      };
      // como en Appian: si el botón valida, los errores se muestran antes y la confirmación no llega a abrirse
      if ((n.confirmMessage || n.confirmHeader) && P(n, "validate", ctx, !!P(n, "submit", ctx, false)) && !checkRequired(ctx.scope)) { invalid[ctx.scope] = true; rerender(); return; }
      if (n.confirmMessage || n.confirmHeader) { confirmBox = { header: P(n, "confirmHeader", ctx), message: P(n, "confirmMessage", ctx), ok: P(n, "confirmButtonLabel", ctx) || P(n, "label", ctx), cancel: P(n, "cancelButtonLabel", ctx) || T.cancel, color: bc, onOk: doIt }; rerender(); }
      else doIt();
    });
    return b;
  };
  R["a!buttonArrayLayout"] = (n, ctx) => h("div", { class: `btns al-${up(P(n, "align", ctx, "START"))}` }, arr(n.buttons).map((b, i) => render(b, ctx, ctx.key + ".b" + i)));
  R["a!buttonLayout"] = (n, ctx) => h("div", { class: "form-btns" }, h("div", { class: "grp" }, arr(n.secondaryButtons).map((b, i) => render(b, ctx, ctx.key + ".s" + i))), h("div", { class: "grp pri" }, arr(n.primaryButtons).map((b, i) => render(b, ctx, ctx.key + ".p" + i))));

  /* ---- layouts ---- */
  const padCls = (v, d) => "pd-" + up(v || d || "STANDARD");
  R["a!cardLayout"] = (n, ctx) => {
    const sv = String(P(n, "style", ctx, "NONE") || "NONE"), st = up(sv);
    const hex = sv.startsWith("#"); // también cuando el color sale de una expresión ({…|map:…}, if(…))
    const cls = ["card", "st-" + (hex ? "HEX" : st), "shape-" + up(P(n, "shape", ctx, "SQUARED")), padCls(P(n, "padding", ctx), "LESS"), n.height && up(n.height) !== "AUTO" ? "h-" + up(n.height) + " hfix" : ""];
    if (P(n, "showBorder", ctx, true)) cls.push("b");
    if (P(n, "showShadow", ctx, false)) cls.push("sh");
    if (n.link) cls.push("link");
    const bc = n.borderColor ? color(P(n, "borderColor", ctx) === "STANDARD" ? null : P(n, "borderColor", ctx)) : null;
    const bw = { MEDIUM: 2, THICK: 4 }[up(P(n, "borderWeight", ctx, "THIN"))]; // 26.7
    const dk = darkProps(hex ? sv : st);
    const el = h("div", { class: cls.join(" ") + (dk ? dk.cls : ""), style: Object.assign({ background: hex ? sv : null, color: hex ? solidFg(sv) : null, borderColor: bc || null, borderWidth: bw && cls.includes("b") ? bw + "px" : null }, dk ? dk.vars : null), title: P(n, "tooltip", ctx), role: n.link ? "link" : null, tabindex: n.link ? "0" : null, "aria-label": n.link ? P(n, "accessibilityText", ctx) : null });
    const bar = up(P(n, "decorativeBarPosition", ctx, "NONE"));
    if (bar !== "NONE") el.appendChild(h("span", { class: "dbar " + bar, style: { "--bar": color(P(n, "decorativeBarColor", ctx, "ACCENT"), "var(--accent)").replace("var(--text-2)", "var(--accent)") } }));
    el.appendChild(stack(n.contents, ctx, ctx.key + ".c"));
    if (n.link) el.addEventListener("click", clickable(n.link, ctx));
    return el;
  };
  R["a!cardGroupLayout"] = (n, ctx) => {
    const cw = { EXTRA_NARROW: 140, NARROW: 180, NARROW_PLUS: 220, MEDIUM: 260, MEDIUM_PLUS: 300, WIDE: 360, WIDE_PLUS: 420, EXTRA_WIDE: 520 }[up(P(n, "cardWidth", ctx, "MEDIUM"))];
    const cards = [];
    arr(n.cards).forEach((c, i) => { if (c && c.type === "a!forEach") forEachItems(c, ctx).forEach((it, j) => cards.push(render(it.node, it.ctx, `${ctx.key}.${i}.${j}`))); else cards.push(render(c, ctx, `${ctx.key}.${i}`)); });
    const g = h("div", { class: `cgl sp-${up(P(n, "spacing", ctx, "STANDARD"))}`, style: { "--cw": cw + "px" } }, cards);
    if (n.cardHeight) Array.from(g.children).forEach((c) => c.classList.add("h-" + up(n.cardHeight)));
    return n.label ? field(n, ctx, g) : g;
  };
  R["a!sectionLayout"] = (n, ctx) => {
    const coll = P(n, "isCollapsible", ctx, false);
    const k = "sec:" + ctx.key;
    if (UI[k] === undefined) UI[k] = coll && P(n, "isInitiallyCollapsed", ctx, false);
    const size = up(P(n, "labelSize", ctx, "MEDIUM"));
    const tag = (P(n, "labelHeadingTag", ctx) || ({ LARGE_PLUS: "H1", LARGE: "H1", MEDIUM_PLUS: "H2", MEDIUM: "H2", SMALL: "H3", EXTRA_SMALL: "H4" }[size] || "H2")).toLowerCase();
    const label = P(n, "label", ctx);
    const el = h("section", { class: "sec" + (UI[k] ? " closed" : "") });
    if (label) {
      const dcol = n.dividerColor ? color(P(n, "dividerColor", ctx), "var(--border)").replace("inherit", "#9aa1a8") : null;
      const hd = h(tag, { class: `sec-h fs-${size} dv-${up(P(n, "divider", ctx, "NONE"))} dw-${up(P(n, "dividerWeight", ctx, "THIN"))}` + (coll ? " coll" : "") + (n.labelFontWeight ? " lfw-" + up(P(n, "labelFontWeight", ctx)) : ""), style: { color: color(P(n, "labelColor", ctx, "ACCENT"), "inherit"), "--dvc": dcol } },
        coll ? icon("angle-down", "chev") : null, n.labelIcon ? icon(P(n, "labelIcon", ctx)) : null, label);
      if (coll) { hd.setAttribute("role", "button"); hd.setAttribute("tabindex", "0"); hd.addEventListener("click", () => { UI[k] = !UI[k]; rerender(); }); }
      el.appendChild(hd);
    }
    el.appendChild(h("div", { class: "sec-c" }, stack(n.contents, ctx, ctx.key + ".c"), vmsgs(n.validations, ctx, { marginTop: "8px" })));
    return el;
  };
  R["a!boxLayout"] = (n, ctx) => {
    const coll = P(n, "isCollapsible", ctx, false);
    const k = "box:" + ctx.key;
    if (UI[k] === undefined) UI[k] = coll && P(n, "isInitiallyCollapsed", ctx, false);
    const bst = String(P(n, "style", ctx, "STANDARD"));
    const bhex = bst.startsWith("#");
    const bxc = n.borderColor ? String(P(n, "borderColor", ctx)) : null; // 26.7: borderColor, borderWeight, labelFontWeight
    const bxw = { MEDIUM: 2, THICK: 4 }[up(P(n, "borderWeight", ctx, "THIN"))];
    const el = h("div", { class: `box st-${bhex ? "HEX" : up(bst)} shape-${up(P(n, "shape", ctx, "SQUARED"))}`, style: { boxShadow: P(n, "showShadow", ctx, false) ? "0 2px 8px rgba(0,0,0,.1)" : null, border: P(n, "showBorder", ctx, true) ? null : "0", borderColor: bxc && up(bxc) !== "STANDARD" ? color(bxc) : null, borderWidth: bxw && P(n, "showBorder", ctx, true) ? bxw + "px" : null } });
    const hd = h((P(n, "labelHeadingTag", ctx) || "div").toLowerCase(), { class: `box-h fs-${up(P(n, "labelSize", ctx, "EXTRA_SMALL"))}` + (n.labelFontWeight ? " lfw-" + up(P(n, "labelFontWeight", ctx)) : ""), style: { cursor: coll ? "pointer" : null, background: bhex ? bst : null, color: bhex ? solidFg(bst) : null } }, coll ? icon(UI[k] ? "angle-right" : "angle-down") : null, P(n, "label", ctx));
    if (coll) hd.addEventListener("click", () => { UI[k] = !UI[k]; rerender(); });
    el.appendChild(hd);
    if (!UI[k]) el.appendChild(h("div", { class: padCls(P(n, "padding", ctx), "LESS") }, stack(n.contents, ctx, ctx.key + ".c")));
    return el;
  };
  R["a!columnsLayout"] = (n, ctx) => {
    const cols = arr(n.columns).filter((c) => visible(c, ctx));
    const el = h("div", { class: `cols sp-${up(P(n, "spacing", ctx, "STANDARD"))} av-${up(P(n, "alignVertical", ctx, "TOP"))}` + (P(n, "showDividers", ctx, false) ? " dividers" : "") + (up(n.stackWhen) === "NEVER" || arr(n.stackWhen).map(up).includes("NEVER") ? " nostack" : "") });
    cols.forEach((c, i) => {
      const w = up(P(c, "width", ctx, "AUTO"));
      const m = w.match(/^(\d+)X$/);
      const col = h("div", { class: "col w-" + w, style: m ? { flex: `${m[1]} 1 0` } : null, "data-sail": "a!columnLayout", "data-k": `${ctx.key}.${i}` }, stack(c.contents, ctx, `${ctx.key}.${i}.c`));
      NODES[`${ctx.key}.${i}`] = c;
      el.appendChild(col);
    });
    return el;
  };
  R["a!sideBySideLayout"] = (n, ctx) => {
    const el = h("div", { class: `sbs sp-${up(P(n, "spacing", ctx, "STANDARD"))} av-${up(P(n, "alignVertical", ctx, "TOP"))} stack-${arr(n.stackWhen || "PHONE").map(up).join(" stack-")}` });
    arr(n.items).filter((it) => visible(it, ctx)).forEach((it, i) => {
      const w = up(P(it, "width", ctx, "AUTO"));
      const m = w.match(/^(\d+)X$/);
      const cell = h("div", { class: "sbi w-" + w, style: m ? { flex: `${m[1]} 1 0` } : null, "data-sail": "a!sideBySideItem", "data-k": `${ctx.key}.${i}` }, render(it.item, ctx, `${ctx.key}.${i}.i`));
      NODES[`${ctx.key}.${i}`] = it;
      el.appendChild(cell);
    });
    return el;
  };
  R["a!tabLayout"] = (n, ctx) => {
    const tabs = arr(n.tabs).filter((t) => visible(t, ctx));
    const k = "tab:" + ctx.key;
    const keyOf = (t, i) => (t.id != null ? P(t, "id", ctx) : i + 1);
    let sel = UI[k];
    if (sel === undefined && n.selectedTab != null) { const want = P(n, "selectedTab", ctx); const j = tabs.findIndex((t, i) => String(keyOf(t, i)) === String(want)); sel = j >= 0 ? j : 0; }
    sel = Math.min(sel || 0, Math.max(0, tabs.length - 1));
    const hl = color(P(n, "highlightColor", ctx, "ACCENT"), "var(--accent)");
    // 26.7: orientación vertical (pestañas a la izquierda en una columna estrecha), ancho de pestaña y divisor; por defecto el divisor
    // y el relleno dependen de la orientación (horizontal: divisor y STANDARD; vertical: sin divisor y NONE)
    const vert = up(P(n, "orientation", ctx, "HORIZONTAL")) === "VERTICAL";
    const divider = P(n, "showDivider", ctx, !vert);
    const dc = String(P(n, "dividerColor", ctx, "SECONDARY"));
    const dcol = dc.startsWith("#") ? dc : up(dc) === "STANDARD" ? "#8a9097" : "var(--border)";
    const bar = h("div", { class: "tabs" + (vert ? " vert" : "") + (divider ? "" : " nodiv") + (up(P(n, "tabWidth", ctx, "MINIMIZE")) === "FILL" ? " fill" : ""), role: "tablist", "aria-orientation": vert ? "vertical" : null, style: { "--thl": hl, "--tdc": dcol } }, tabs.map((t, i) => h("button", { type: "button", role: "tab", "aria-selected": String(i === sel), class: i === sel ? "sel" : "", onclick: () => { if (inspector) return; UI[k] = i; if (n.selectedTabSaveInto) saveInto({ saveInto: n.selectedTabSaveInto }, keyOf(t, i), ctx); rerender(); } }, t.icon ? icon(P(t, "icon", ctx)) : null, h("span", { class: "tlab" }, P(t, "label", ctx)))));
    const pad = up(P(n, "contentsPadding", ctx, vert ? "NONE" : "STANDARD"));
    const body = tabs[sel] ? h("div", { class: "tab-c", role: "tabpanel", style: vert ? { paddingLeft: (SPACE[pad] ?? 0) + "px" } : { paddingTop: (SPACE[pad] ?? 16) + "px" } }, stack(tabs[sel].contents, ctx, `${ctx.key}.t${sel}`)) : null;
    if (tabs[sel]) { body.setAttribute("data-sail", "a!tabItem"); body.setAttribute("data-k", `${ctx.key}.t${sel}`); NODES[`${ctx.key}.t${sel}`] = tabs[sel]; }
    return h("div", { class: "tabl" + (vert ? " vert" : "") }, bar, body);
  };
  R["a!paneLayout"] = (n, ctx) => h("div", { class: "pane-layout" + (P(n, "showPaneDividers", ctx, true) ? " div" : "") }, arr(n.panes).filter((p) => visible(p, ctx)).map((p, i) => {
    const bg = P(p, "backgroundColor", ctx, "WHITE");
    const el = h("div", { class: `pane w-${up(P(p, "width", ctx, "AUTO"))} ${String(bg).startsWith("#") ? "" : "bg-" + up(bg)} ${padCls(P(p, "padding", ctx), "STANDARD")}`, style: String(bg).startsWith("#") ? { background: bg } : null, "data-sail": "a!pane", "data-k": `${ctx.key}.${i}` }, stack(p.contents, ctx, `${ctx.key}.${i}.c`));
    NODES[`${ctx.key}.${i}`] = p;
    return el;
  }));
  R["a!billboardLayout"] = (n, ctx) => {
    const bg = P(n, "backgroundColor", ctx, "#f0f0f0");
    const hgt = { EXTRA_SHORT: 100, SHORT: 160, SHORT_PLUS: 200, MEDIUM: 260, MEDIUM_PLUS: 320, TALL: 380, TALL_PLUS: 440, EXTRA_TALL: 520 }[up(P(n, "height", ctx, "MEDIUM"))];
    // fondo: imagen web (data: o http[s]) si la hay; un a!documentImage o a!webVideo se representa con un marcador sobre backgroundColor
    const med = n.backgroundMedia && typeof n.backgroundMedia === "object" ? n.backgroundMedia : null;
    const src = med && med.type === "a!webImage" ? interp(med.source || "", ctx) : null;
    const pos = `${{ LEFT: "left", RIGHT: "right" }[up(P(n, "backgroundMediaPositionHorizontal", ctx, "CENTER"))] || "center"} ${{ TOP: "top", BOTTOM: "bottom" }[up(P(n, "backgroundMediaPositionVertical", ctx, "MIDDLE"))] || "center"}`;
    const bbk = darkProps(String(bg).startsWith("#") ? bg : "#f0f0f0");
    const el = h("div", { class: "billboard" + (bbk ? bbk.cls : "") + (med && !src ? " ph" : "") + (solidFg(String(bg).startsWith("#") ? bg : "#f0f0f0") === "#1a1a1a" && !src && !med ? " light" : ""), role: n.accessibilityText ? "img" : null, "aria-label": P(n, "accessibilityText", ctx), style: { "--lnk": bbk ? bbk.vars["--lnk"] : null, "--bb": bg, minHeight: up(n.height) === "AUTO" ? null : (hgt || 260) + "px", backgroundImage: src && /^(data:|https?:)/.test(src) ? `url("${src}")` : null, backgroundPosition: pos } });
    if (med && !src) el.appendChild(h("span", { class: "bb-ph", "aria-hidden": "true" }, icon(med.type === "a!webVideo" ? "play-circle" : "picture-o")));
    const ov = n.overlay;
    if (ov && visible(ov, ctx)) {
      const t = ov.type;
      const cls = t === "a!barOverlay" ? `ov bar ${up(P(ov, "position", ctx, "BOTTOM"))}` : t === "a!columnOverlay" ? `ov col ${up(P(ov, "position", ctx, "START"))}` : "ov full";
      const o = h("div", { class: `${cls} st-${up(P(ov, "style", ctx, "DARK"))} ${padCls(P(ov, "padding", ctx), "STANDARD")}`, "data-sail": t, "data-k": ctx.key + ".o" }, stack(ov.contents, ctx, ctx.key + ".o.c"));
      NODES[ctx.key + ".o"] = ov;
      el.appendChild(o);
    }
    return el;
  };
  function imgOf(im, ctx, px) {
    if (!im) return null;
    if (im.type === "a!userImage") { const u = String(interp(im.user || "", ctx) || ""); return h("span", { class: "stamp", style: { "--sbg": "var(--accent)", "--sfg": "var(--accent-fg, #fff)", width: px + "px", height: px + "px", fontSize: Math.round(px * 0.38) + "px" } }, FILTERS.initials((usrOf(u) || {}).name || u)); }
    const src = im.type === "a!webImage" ? interp(im.source || "", ctx) : null;
    if (src && src.startsWith("data:")) return h("img", { src, alt: interp(im.altText || "", ctx), style: { width: px + "px", height: px + "px", objectFit: "cover", borderRadius: "8px" } });
    return h("span", { class: "imgph", style: { width: px + "px", height: px + "px" } }, icon("picture-o"));
  }
  function headerTemplate(tb, ctx, big) {
    if (!tb) return null;
    if (typeof tb === "string") return h("div", { class: "form-title" }, h("h1", null, interp(tb, ctx)));
    if (Array.isArray(tb)) return h("div", null, tb.map((x, i) => render(x, ctx, ctx.key + ".tb" + i)));
    if (tb.type === "a!cardLayout" || tb.type === "a!billboardLayout") return render(tb, ctx, ctx.key + ".tb");
    const full = tb.type === "a!headerTemplateFull" || tb.type === "a!headerTemplateImage";
    const bgv = full ? P(tb, "backgroundColor", ctx, "ACCENT") : null;
    const bg = bgv ? (up(bgv) === "WHITE" ? "#ffffff" : /_SCHEME$/.test(up(bgv)) ? { CHARCOAL_SCHEME: "var(--charcoal)", NAVY_SCHEME: "var(--navy)", PLUM_SCHEME: "var(--plum)" }[up(bgv)] : color(bgv, "var(--accent)")) : null;
    const fg = bg ? solidFg(hexOf(bgv) || (up(bgv) === "WHITE" ? "#ffffff" : "#1a2732")) : null;
    const sc = P(tb, "stampColor", ctx, "ACCENT");
    const stamp = tb.stampIcon ? h("span", { class: "hdr-stamp", style: { background: color(sc, "var(--accent)"), color: up(sc) === "TRANSPARENT" ? fg || "var(--accent)" : solidFg(hexOf(sc) || "#527500") } }, icon(P(tb, "stampIcon", ctx))) : null;
    const img = tb.type === "a!headerTemplateImage" && tb.image ? h("span", { class: "hdr-img" }, imgOf(tb.image, ctx, { SMALL: 48, MEDIUM: 72, LARGE: 96 }[up(P(tb, "imageSize", ctx, "MEDIUM"))] || 72)) : null;
    const el = h("div", { class: "hdrtpl" + (full ? " full" : " simple") + (up(bgv) === "WHITE" ? " white" : ""), "data-sail": tb.type, "data-k": ctx.key + ".tb", style: { background: bg, color: fg } },
      h("div", { class: "hdr-in" }, img, stamp,
        h("div", null, h("h1", { class: "t", style: { color: tb.titleColor ? color(P(tb, "titleColor", ctx)) : null } }, P(tb, "title", ctx)), tb.secondaryText ? h("div", { class: "s", style: { color: tb.secondaryTextColor ? color(P(tb, "secondaryTextColor", ctx)) : bg ? "inherit" : null, opacity: bg && !tb.secondaryTextColor && up(bgv) !== "WHITE" ? 0.85 : null } }, P(tb, "secondaryText", ctx)) : null)));
    NODES[ctx.key + ".tb"] = tb;
    return el;
  }
  // a!sidebarTemplate: barra lateral del formulario o asistente (título, texto, imagen y contenido adicional); en asistentes verticales lleva el hito
  function sidebar(tb, ctx, extra) {
    const bgv = P(tb, "backgroundColor", ctx, "ACCENT");
    const bg = up(bgv) === "WHITE" ? "#ffffff" : /_SCHEME$/.test(up(bgv)) ? { CHARCOAL_SCHEME: "var(--charcoal)", NAVY_SCHEME: "var(--navy)", PLUM_SCHEME: "var(--plum)" }[up(bgv)] : color(bgv, "var(--accent)");
    const dark = up(bgv) !== "WHITE" && solidFg(hexOf(bgv) || (/_SCHEME$/.test(up(bgv)) ? "#1a2732" : "#ffffff")) === "#ffffff";
    const w = { NARROW_PLUS: 260, MEDIUM: 320, MEDIUM_PLUS: 380 }[up(P(tb, "width", ctx, "MEDIUM"))] || 320;
    const el = h("aside", { class: "sidebar" + (dark ? " dark" : ""), "data-sail": "a!sidebarTemplate", "data-k": ctx.key + ".tb", style: { background: bg, "--sbbg": bg, flex: `0 0 ${w}px` } },
      tb.image ? h("div", { class: "sb-img" }, imgOf(tb.image, ctx, { SMALL_PLUS: 64, MEDIUM: 88, MEDIUM_PLUS: 112 }[up(P(tb, "imageSize", ctx, "MEDIUM"))] || 88)) : null,
      h("h1", { class: "t", style: { color: tb.titleColor ? color(P(tb, "titleColor", ctx)) : null } }, P(tb, "title", ctx)),
      tb.secondaryText ? h("div", { class: "s", style: { color: tb.secondaryTextColor ? color(P(tb, "secondaryTextColor", ctx)) : null } }, P(tb, "secondaryText", ctx)) : null,
      extra || null,
      tb.additionalContents ? h("div", { class: "sb-more" }, stack(tb.additionalContents, ctx, ctx.key + ".tb.ac")) : null);
    NODES[ctx.key + ".tb"] = tb;
    return el;
  }
  function titleText(tb, ctx) { return !tb ? "" : typeof tb === "string" ? interp(tb, ctx) : P(tb, "title", ctx, ""); }
  R["a!formLayout"] = (n, ctx) => {
    const w = up(P(n, "contentsWidth", ctx, "NARROW"));
    const bg = P(n, "backgroundColor", ctx, "WHITE");
    if (ctx.inDialog) return stack(n.contents, ctx, ctx.key + ".c");
    const btns = n.buttons ? render(n.buttons, ctx, ctx.key + ".btn") : null;
    if (btns && P(n, "showButtonDivider", ctx, false)) btns.classList.add("divider");
    if (btns && P(n, "isButtonFooterFixed", ctx, false)) btns.classList.add("fixed");
    const formVal = vmsgs(n.validations, ctx);
    const tb = n.titleBar;
    const bgStyle = { class: String(bg).startsWith("#") ? "" : "bg-" + up(bg), style: { background: String(bg).startsWith("#") ? bg : null, minHeight: "100%" } };
    if (tb && typeof tb === "object" && tb.type === "a!sidebarTemplate") {
      return h("div", Object.assign({}, bgStyle, { class: bgStyle.class + " with-sb" }), sidebar(tb, ctx), h("div", { class: "sb-main" }, h("div", { class: `form w-${w}` }, stack(n.contents, ctx, ctx.key + ".c"), formVal, btns)));
    }
    const tbFull = tb && typeof tb === "object" && /Full|Image/.test(tb.type);
    const tbEl = headerTemplate(tb, ctx);
    if (tbEl && P(n, "isTitleBarFixed", ctx, false)) tbEl.classList.add("fixed");
    if (tbEl && P(n, "showTitleBarDivider", ctx, false)) tbEl.classList.add("divider");
    return h("div", bgStyle,
      tbFull ? tbEl : null,
      h("div", { class: "page-pad" }, h("div", { class: `form w-${w}` }, tbFull ? null : tbEl, stack(n.contents, ctx, ctx.key + ".c"), formVal, btns)));
  };
  function valMsg(v, ctx) { return v && typeof v === "object" ? interp(v.message || "", ctx) : interp(v, ctx); }
  // validaciones de formulario, sección o asistente: tras pulsar un botón que valida o, con a!validationMessage(validateAfter: "REFRESH"), en cuanto se cumplen.
  // Como en Appian, una validación activa impide enviar (aunque todavía no se vea).
  function vmsgs(list, ctx, style) {
    const on = arr(list).filter((v) => v && visible(v, ctx) && String(valMsg(v, ctx)).trim() !== "");
    on.forEach(() => VALS.push({ scope: ctx.scope }));
    return on.filter((v) => invalid[ctx.scope] || (typeof v === "object" && up(P(v, "validateAfter", ctx, "SUBMIT")) === "REFRESH"))
      .map((v) => h("div", { class: "ferr", style }, icon("exclamation-circle"), valMsg(v, ctx)));
  }
  R["a!headerContentLayout"] = (n, ctx) => {
    const bg = P(n, "backgroundColor", ctx, "WHITE");
    const dk = darkProps(bg);
    return h("div", { class: "hcl " + (String(bg).startsWith("#") ? "" : "bg-" + up(bg)) + (dk ? dk.cls : ""), style: Object.assign({ background: String(bg).startsWith("#") ? bg : null, color: dk ? "#fff" : null }, dk ? dk.vars : null) },
      n.header ? h("div", { class: "hcl-header" }, arr(n.header).map((x, i) => render(x, ctx, ctx.key + ".h" + i))) : null,
      h("div", { class: "hcl-contents" }, h("div", { class: "page-pad", style: { padding: { NONE: "0", EVEN_LESS: "4px", LESS: "8px 12px", MORE: "28px 32px 44px", EVEN_MORE: "40px 48px 56px" }[up(n.contentsPadding)] || null } }, stack(n.contents, ctx, ctx.key + ".c"))));
  };
  R["a!wizardLayout"] = (n, ctx) => {
    const steps = arr(n.steps).filter((s) => visible(s, ctx));
    const k = "wiz:" + ctx.scope;
    const cur = Math.min(UI[k] || 0, steps.length - 1);
    const style = up(P(n, "style", ctx, "DOT_VERTICAL"));
    const vert = /VERTICAL/.test(style);
    const stepStyle = style.startsWith("CHEVRON") ? "CHEVRON" : style.startsWith("LINE") ? "LINE" : "DOT";
    const msNode = { type: "a!milestoneField", steps: steps.map((s) => P(s, "label", ctx)), active: cur + 1, orientation: vert ? "VERTICAL" : "HORIZONTAL", stepStyle, labelPosition: "COLLAPSED", color: tbColorFor(n, ctx) };
    const stepEl = style === "MINIMAL" ? h("div", { class: "wiz-min" }, `${T.step} ${cur + 1} ${T.of} ${steps.length}`) : R["a!milestoneField"](msNode, ctx);
    const s = steps[cur];
    const sctx = Object.assign({}, ctx, { scope: ctx.scope + ":s" + cur });
    const body = h("div", { class: "wiz-body" },
      P(n, "showStepHeadings", ctx, true) && s ? h("h2", null, P(s, "label", ctx)) : null,
      s && s.instructions ? h("div", { class: "wi" }, P(s, "instructions", ctx)) : null,
      s ? stack(s.contents, sctx, `${ctx.key}.s${cur}`) : null,
      s ? vmsgs(s.validations, sctx) : null);
    if (s) { body.setAttribute("data-sail", "a!wizardStep"); body.setAttribute("data-k", `${ctx.key}.s${cur}`); NODES[`${ctx.key}.s${cur}`] = s; }
    const last = cur === steps.length - 1;
    const prevB = cur > 0 ? h("button", { type: "button", class: "btn s-OUTLINE", style: { "--bc": "var(--accent)" }, onclick: () => { if (!inspector) { UI[k] = cur - 1; rerender(); } } }, T.prev) : null;
    const nextB = !last ? h("button", { type: "button", class: "btn s-SOLID", style: { "--bc": brandPrimary(), "--bfg": solidFg(brandPrimary()) }, disabled: s && P(s, "disableNextButton", ctx, false), onclick: () => { if (inspector) return; if (!checkRequired(sctx.scope)) { invalid[sctx.scope] = true; rerender(); return; } delete invalid[sctx.scope]; UI[k] = cur + 1; rerender(); } }, T.next) : null;
    const lastCtx = Object.assign({}, ctx, { scope: sctx.scope });
    const footer = h("div", { class: "form-btns" + (P(n, "showButtonDivider", ctx, false) || ctx.inDialog ? " divider" : "") + (P(n, "isButtonFooterFixed", ctx, false) ? " fixed" : "") },
      h("div", { class: "grp" }, arr(n.secondaryButtons).map((b, i) => render(b, lastCtx, ctx.key + ".sb" + i)), prevB),
      h("div", { class: "grp pri" }, nextB, last ? arr(n.primaryButtons).map((b, i) => render(b, lastCtx, ctx.key + ".pb" + i)) : null));
    ctx.__wizFooter = footer;
    const tb = n.titleBar;
    const sb = tb && typeof tb === "object" && tb.type === "a!sidebarTemplate";
    // con sidebar y estilo vertical, el hito va en la barra lateral (como en Appian)
    const wrap = h("div", { class: "wiz-wrap" + (vert && !sb ? " vert" : "") }, sb && vert ? null : stepEl, body);
    if (ctx.inDialog) { ctx.dialogFooter && ctx.dialogFooter(footer); return wrap; }
    const w = up(P(n, "contentsWidth", ctx, "FULL"));
    const bg = P(n, "backgroundColor", ctx, "WHITE");
    const bgA = { class: String(bg).startsWith("#") ? "" : "bg-" + up(bg), style: { background: String(bg).startsWith("#") ? bg : null, minHeight: "100%" } };
    if (sb) return h("div", Object.assign({}, bgA, { class: bgA.class + " with-sb" }), sidebar(tb, ctx, vert ? stepEl : null), h("div", { class: "sb-main" }, h("div", { class: `form w-${w}` }, wrap, footer)));
    const tbFull = tb && typeof tb === "object" && /Full|Image/.test(tb.type);
    const tbEl = headerTemplate(tb, ctx);
    if (tbEl && P(n, "showTitleBarDivider", ctx, false)) tbEl.classList.add("divider");
    return h("div", bgA, tbFull ? tbEl : null, h("div", { class: "page-pad" }, h("div", { class: `form w-${w}` }, tbFull ? null : tbEl, wrap, footer)));
  };
  function tbColorFor(n, ctx) { const tb = n.titleBar; if (tb && typeof tb === "object" && tb.type === "a!sidebarTemplate") { const b = up(P(tb, "backgroundColor", ctx, "ACCENT")); return b === "WHITE" ? "ACCENT" : (BRAND.site && BRAND.site.selectedPageHighlightColor) || "#ffffff"; } return "ACCENT"; }
  R["a!gridRowLayout"] = (n, ctx) => h("tr", null, arr(n.contents).map((c, i) => h("td", null, render(Object.assign({ labelPosition: "COLLAPSED" }, c), ctx, ctx.key + "." + i))));

  /* ---- grids ---- */
  R["a!gridField"] = (n, ctx) => {
    const k = "grid:" + ctx.key;
    const st = UI[k] || (UI[k] = { page: 0, q: "", sort: null, desc: false, filters: {} });
    if (st.sort == null && n.initialSorts) { const s0 = arr(n.initialSorts)[0]; if (s0) { st.sort = fieldOf(s0.field); st.desc = s0.ascending === false; } }
    let rows = n.$chart ? chartRows(n.$chart, ctx) : n.$rows ? rowsOf(n.$rows) : typeof n.data === "string" ? rowsOf(n.data) : arr(n.data);
    if (n.$filter) rows = rows.filter((r) => truthy(evalExpr(n.$filter, Object.assign({}, ctx, { row: r }))));
    const ufs = arr(n.userFilters).map((u) => (typeof u === "string" ? { field: fieldOf(u), label: fieldOf(u).replace(/([a-z])([A-Z])/g, "$1 $2").toLowerCase().replace(/^./, (c) => c.toUpperCase()) } : u));
    for (const f in st.filters) if (st.filters[f] != null) rows = rows.filter((r) => String(r[f]) === String(st.filters[f]));
    if (st.q) rows = searchRows(n, ctx, rows, st);
    if (st.sort) rows = rows.slice().sort((a, b) => { const x = a[st.sort], y = b[st.sort]; const c = x == null ? -1 : y == null ? 1 : typeof x === "number" ? x - y : String(x).localeCompare(String(y), "es"); return st.desc ? -c : c; });
    const cols = arr(n.columns).filter((c) => visible(c, ctx));
    const ps = Number(P(n, "pageSize", ctx, 10));
    const total = rows.length;
    const pages = Math.max(1, Math.ceil(total / ps));
    if (st.page >= pages) st.page = pages - 1;
    const pageRows = rows.slice(st.page * ps, st.page * ps + ps);
    const selectable = P(n, "selectable", ctx, false);
    const selStyle = up(P(n, "selectionStyle", ctx, "CHECKBOX"));
    const rowSel = selectable && /HIGHLIGHT$/.test(selStyle) && selStyle !== "CHECKBOX_SUBTLE_HIGHLIGHT";
    const withChk = selectable && !rowSel;
    const maxSel = P(n, "maxSelections", ctx, null);
    const selRef = n.selectionSaveInto || n.selectionValue;
    const selVal = arr(typeof n.selectionValue === "string" ? S[n.selectionValue] : n.selectionValue).map(String);
    const setSel = (id, on) => { let nv = on ? selVal.filter((x) => x !== id) : maxSel === 1 ? [id] : selVal.concat([id]); if (maxSel && nv.length > maxSel) nv = nv.slice(-maxSel); const raw = nv.map((x) => (isNaN(Number(x)) ? x : Number(x))); if (typeof n.selectionSaveInto === "string") S[n.selectionSaveInto] = raw; else if (n.selectionSaveInto) saveInto({ saveInto: n.selectionSaveInto }, raw, ctx); else if (typeof selRef === "string") S[selRef] = raw; schedule(); };

    const tb = h("div", { class: "grid-tb" });
    if (P(n, "showSearchBox", ctx, false)) {
      const inp = h("input", { class: "inp", id: "f-" + ctx.key + "-q", placeholder: T.search, "aria-label": T.search, value: st.q, onchange: (e) => { st.q = e.target.value; st.page = 0; schedule(); } });
      tb.appendChild(h("div", { class: "search" }, icon("search"), inp));
    }
    const allRows = n.$chart ? chartRows(n.$chart, ctx) : n.$rows ? rowsOf(n.$rows) : typeof n.data === "string" ? rowsOf(n.data) : arr(n.data);
    const ufTxt = (v) => (v === true ? "Sí" : v === false ? "No" : String(v));
    ufs.forEach((f) => {
      const vals = [...new Set(allRows.map((r) => r[f.field]).filter((v) => v != null))].sort();
      const on = st.filters[f.field] != null;
      const pop = h("div", { class: "pop", hidden: true, style: { top: "calc(100% + 4px)", left: 0 } }, on ? h("button", { type: "button", onclick: () => { st.filters[f.field] = null; st.page = 0; rerender(); } }, icon("times"), T.clear) : null, vals.map((v) => h("button", { type: "button", onclick: () => { st.filters[f.field] = v; st.page = 0; rerender(); } }, ufTxt(v))));
      const b = h("button", { type: "button", class: "uf" + (on ? " on" : ""), "aria-haspopup": "listbox", onclick: (e) => { e.stopPropagation(); const was = pop.hidden; document.querySelectorAll(".grid-tb .pop").forEach((p) => (p.hidden = true)); pop.hidden = !was; } }, on ? `${f.label}: ${ufTxt(st.filters[f.field])}` : f.label, icon("angle-down"), pop);
      tb.appendChild(b);
    });
    const hasTb = tb.childNodes.length || P(n, "showExportButton", ctx, false) || P(n, "showRefreshButton", ctx, false) || n.recordActions;
    if (hasTb) {
      tb.appendChild(h("span", { class: "sp" }));
      if (n.recordActions) tb.appendChild(render({ type: "a!recordActionField", actions: arr(n.recordActions), style: up(n.actionsStyle || "TOOLBAR") === "TOOLBAR_PRIMARY" ? "TOOLBAR_PRIMARY" : "TOOLBAR", display: n.actionsDisplay }, ctx, ctx.key + ".ra"));
      if (P(n, "showRefreshButton", ctx, false)) tb.appendChild(h("button", { type: "button", class: "ib", title: "Actualizar", "aria-label": "Actualizar" }, icon("refresh")));
      if (P(n, "showExportButton", ctx, false)) tb.appendChild(h("button", { type: "button", class: "ib", title: T.export, "aria-label": T.export }, icon("file-excel-o")));
    }
    // anchos relativos 1X–10X: porcentaje del total (las columnas AUTO cuentan como 1X)
    const relW = (c) => { const m = String(c.width || "").match(/^(\d+)X$/i); return m ? Number(m[1]) : null; };
    const relTot = cols.some((c) => relW(c)) ? cols.reduce((a, c) => a + (relW(c) || (!c.width || up(c.width) === "AUTO" ? 1 : 0)), 0) : 0;
    const thead = h("tr", null, withChk ? h("th", { class: "selc" }) : null, cols.map((c) => {
      const sf = c.sortField ? fieldOf(c.sortField) : null;
      const arrow = sf && st.sort === sf ? icon(st.desc ? "caret-down" : "caret-up") : null;
      return h("th", { style: relW(c) ? { width: (100 * relW(c)) / relTot + "%" } : null, class: `${sf ? "sortable" : ""} al-${up(P(c, "align", ctx, "START"))} ${c.width && !relW(c) ? "gw-" + up(c.width) : ""}`, onclick: sf ? () => { if (st.sort === sf) st.desc = !st.desc; else { st.sort = sf; st.desc = false; } rerender(); } : null, "aria-sort": sf && st.sort === sf ? (st.desc ? "descending" : "ascending") : null }, P(c, "label", ctx), c.helpTooltip ? h("span", { class: "help", title: P(c, "helpTooltip", ctx) }, " ", icon("question-circle")) : null, arrow ? " " : null, arrow);
    }));
    const tbody = h("tbody");
    pageRows.forEach((r, ri) => {
      const rctx = Object.assign({}, ctx, { row: r, fv: { row: r, identifier: r.id, index: ri + 1 } });
      const id = String(r.id ?? ri);
      const on = selVal.includes(id);
      const selOff = selectable && n.disableRowSelectionWhen != null && truthy(evalExpr(n.disableRowSelectionWhen, rctx));
      tbody.appendChild(h("tr", { "aria-selected": selectable ? String(on) : null, class: (on && /HIGHLIGHT/.test(selStyle) ? "rsel " + (selStyle.includes("SUBTLE") ? "subtle" : "strong") : "") + (rowSel && !selOff ? " rowsel" : ""), onclick: rowSel && !selOff ? (e) => { if (inspector || e.target.closest("a,button,input")) return; setSel(id, on); } : null },
        withChk ? h("td", { class: "selc" }, h("input", { type: "checkbox", "aria-label": "Seleccionar fila", checked: on, disabled: selOff, onchange: () => setSel(id, on) })) : null,
        cols.map((c, ci) => {
          let cell;
          if (c.value && typeof c.value === "object") cell = render(Object.assign({ labelPosition: "COLLAPSED" }, c.value), rctx, `${ctx.key}.r${ri}.${ci}`);
          else { const v = c.value == null ? "" : interp(String(c.value), rctx); cell = document.createTextNode(v == null ? "" : String(v)); }
          const bg = c.backgroundColor ? P(c, "backgroundColor", rctx) : null;
          return h("td", { class: `al-${up(P(c, "align", ctx, "START"))}`, style: bg ? { background: SEMBG[up(bg)] || bg } : null, title: bg && c.accessibilityText ? P(c, "accessibilityText", rctx) : null }, cell);
        })));
    });
    if (!pageRows.length) tbody.appendChild(h("tr", null, h("td", { colspan: cols.length + (withChk ? 1 : 0), class: "gempty" }, P(n, "emptyGridMessage", ctx, T.empty))));
    const table = h("table", { class: "g" }, h("thead", null, thead), tbody);
    const pager = total > ps || n.$alwaysPage ? h("div", { class: "gpage" },
      h("button", { type: "button", "aria-label": "Primera página", disabled: st.page === 0, onclick: () => { st.page = 0; rerender(); } }, icon("angle-double-left")),
      h("button", { type: "button", "aria-label": "Página anterior", disabled: st.page === 0, onclick: () => { st.page--; rerender(); } }, icon("angle-left")),
      h("span", null, h("strong", null, `${total ? st.page * ps + 1 : 0} - ${Math.min(total, st.page * ps + ps)}`), ` ${T.of} ${total}`),
      h("button", { type: "button", "aria-label": "Página siguiente", disabled: st.page >= pages - 1, onclick: () => { st.page++; rerender(); } }, icon("angle-right")),
      h("button", { type: "button", "aria-label": "Última página", disabled: st.page >= pages - 1, onclick: () => { st.page = pages - 1; rerender(); } }, icon("angle-double-right"))) : null;
    const GH = { EXTRA_SHORT: 120, SHORT: 200, SHORT_PLUS: 260, MEDIUM: 340, MEDIUM_PLUS: 420, TALL: 520, TALL_PLUS: 620, EXTRA_TALL: 760 }[up(P(n, "height", ctx, "AUTO"))];
    const g = h("div", { class: `grid sp-${up(P(n, "spacing", ctx, "STANDARD"))} bs-${up(P(n, "borderStyle", ctx, "LIGHT"))}` + (P(n, "shadeAlternateRows", ctx, false) ? " shade" : "") }, hasTb ? tb : null, h("div", { class: "gwrap" + (GH ? " fixh" : ""), style: GH ? { maxHeight: GH + "px" } : null }, table), pager);
    return n.label ? field(n, ctx, g) : g;
  };
  // Búsqueda del grid. Palabra clave: contiene el texto (similarityScore 1). Búsqueda inteligente (26.6, smartSearchType +
  // similarityScoreThreshold, que por defecto vale 1 = solo palabra clave): SEMANTIC añade coincidencias por términos (sin acentos,
  // por raíz) con puntuación < 1 si alcanzan el umbral; LEXICAL, coincidencias por términos con puntuación > 1. Cada fila lleva
  // similarityScore (en SAIL: fv!row[recordType!X.searchResults.allSearchFields.similarityScore]) y, sin orden elegido por el
  // usuario, los resultados se ordenan por relevancia.
  function searchRows(n, ctx, rows, st) {
    const norm = (x) => String(x == null ? "" : x).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    const q = norm(st.q).trim();
    const type = n.smartSearchType ? up(P(n, "smartSearchType", ctx)) : null;
    const thrRaw = n.similarityScoreThreshold === undefined ? 1 : P(n, "similarityScoreThreshold", ctx);
    const thr = thrRaw == null || thrRaw === "" ? 0 : Number(thrRaw);
    const semantic = type === "SEMANTIC" || (!type && thr < 1);
    const terms = q.split(/[^a-z0-9ñ]+/).filter((w) => w.length > 2).map((w) => w.slice(0, Math.max(4, w.length - 2)));
    const out = [];
    for (const r of rows) {
      const txt = norm(Object.values(r).filter((v) => v == null || typeof v !== "object").join(" · "));
      const hits = terms.filter((w) => txt.includes(w)).length;
      let score = null;
      if (txt.includes(q)) score = 1;
      if (type === "LEXICAL" && hits) score = 1 + hits;
      else if (score == null && semantic && hits && terms.length) { const sc = Math.round((0.35 + 0.55 * (hits / terms.length)) * 100) / 100; if (sc >= thr) score = sc; }
      if (score != null) out.push(Object.assign({}, r, { similarityScore: score }));
    }
    if ((type || semantic) && !st.sort) out.sort((a, b) => b.similarityScore - a.similarityScore);
    return out;
  }
  R["a!gridLayout"] = (n, ctx) => {
    const heads = arr(n.headerCells).filter((c) => visible(c, ctx));
    const confs = arr(n.columnConfigs);
    const rows = [];
    arr(n.rows).forEach((r, i) => { if (r && r.type === "a!forEach") forEachItems(r, ctx).forEach((it, j) => rows.push(render(it.node, it.ctx, `${ctx.key}.r${i}.${j}`))); else rows.push(render(r, ctx, `${ctx.key}.r${i}`)); });
    // anchos como en Appian: con table-layout fixed, las columnas de ancho fijo se respetan y las DISTRIBUTE (en %) se reparten el resto según su weight
    const GLW = { ICON: 44, ICON_PLUS: 64, NARROW: 110, NARROW_PLUS: 150, MEDIUM: 210, MEDIUM_PLUS: 270, WIDE: 350 };
    const dist = (c) => !c.width || !GLW[up(c.width)];
    const tw = confs.filter(dist).reduce((a, c) => a + (Number(c.weight) || 1), 0);
    const table = h("table", { class: "g", style: confs.length && confs.length === heads.length ? { tableLayout: "fixed" } : null }, h("colgroup", null, confs.map((c) => h("col", { style: dist(c) ? (tw ? { width: ((Number(c.weight) || 1) / tw) * 100 + "%" } : null) : { width: GLW[up(c.width)] + "px" } }))),
      h("thead", null, h("tr", null, heads.map((c) => h("th", { class: "al-" + up(P(c, "align", ctx, "START")) }, P(c, "label", ctx))))), h("tbody", null, rows.length ? rows : h("tr", null, h("td", { colspan: heads.length, class: "gempty" }, P(n, "emptyGridMessage", ctx, T.empty)))));
    const addL = n.addRowLink ? h("a", { href: "#", class: "gl-add", onclick: clickable(n.addRowLink, ctx) }, icon("plus"), interp(n.addRowLink.label || T.add, ctx)) : null;
    return field(n, ctx, h("div", { class: `grid ed sp-${up(P(n, "spacing", ctx, "STANDARD"))} bs-${up(P(n, "borderStyle", ctx, "LIGHT"))}` + (P(n, "shadeAlternateRows", ctx, true) ? " shade" : "") }, h("div", { class: "gwrap" }, table, addL)));
  };

  /* ---- charts ---- */
  function palette(n, ctx) {
    const cs = n.colorScheme;
    if (cs && typeof cs === "object" && cs.colors) return cs.colors;
    const named = { CLASSIC: ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"], MIDNIGHT: ["#1b2a49", "#465881", "#00909e", "#c9d1d3", "#8e7dbe", "#5c5470"], OCEAN: ["#006d77", "#83c5be", "#264653", "#2a9d8f", "#90e0ef", "#023e8a"], MOSS: ["#606c38", "#283618", "#a3b18a", "#dda15e", "#bc6c25", "#588157"], BERRY: ["#6a0572", "#ab83a1", "#c3423f", "#ff6f59", "#9b5de5", "#5f0f40"], PARACHUTE: ["#ff595e", "#ffca3a", "#8ac926", "#1982c4", "#6a4c93", "#f08080"], RAINFOREST: ["#2d6a4f", "#40916c", "#52b788", "#74c69d", "#1b4332", "#95d5b2"], SUNSET: ["#f94144", "#f3722c", "#f8961e", "#f9c74f", "#90be6d", "#43aa8b"] };
    return named[up(cs)] || (BRAND.components && BRAND.components.chartColorScheme) || named.CLASSIC;
  }
  function dataRows(n, ctx) {
    let rows = rowsOf(n.data);
    if (n.$filter) rows = rows.filter((r) => truthy(evalExpr(n.$filter, Object.assign({}, ctx, { row: r }))));
    return rows;
  }
  function measureOf(m, rows, ctx) {
    if (m && m.$filter) rows = rows.filter((r) => truthy(evalExpr(m.$filter, Object.assign({}, ctx || {}, { row: r }))));
    const f = up((m && m.function) || "COUNT"), fld = fieldOf(m && m.field);
    const vals = rows.map((r) => Number(r[fld]) || 0);
    if (f === "SUM") return vals.reduce((a, b) => a + b, 0);
    if (f === "AVG") return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
    if (f === "MIN") return vals.length ? Math.min(...vals) : 0;
    if (f === "MAX") return vals.length ? Math.max(...vals) : 0;
    if (f === "DISTINCT_COUNT") return new Set(rows.map((r) => r[fld])).size;
    return rows.length;
  }
  function aggregate(n, ctx) {
    const cfg = n.config || {};
    const rows = dataRows(n, ctx);
    const g1 = fieldOf(cfg.primaryGrouping && cfg.primaryGrouping.field);
    const g2 = cfg.secondaryGrouping ? fieldOf(cfg.secondaryGrouping.field) : null;
    const ms = arr(cfg.measures);
    let cats = [...new Set(rows.map((r) => r[g1]))].filter((x) => x != null);
    if (n.$categories) cats = n.$categories;
    else if (/fecha|date|mes|month/i.test(g1)) {
      // nombres de mes (ene, febrero, Apr…): orden del calendario; fechas ISO: orden cronológico
      const MI = (c) => ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"].indexOf(String(c).slice(0, 3).toLowerCase()) + 1 || ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"].indexOf(String(c).slice(0, 3).toLowerCase()) + 1;
      if (cats.every((c) => MI(c))) cats.sort((a, b) => MI(a) - MI(b)); else cats.sort();
    } else cats.sort((a, b) => String(a).localeCompare(String(b), "es"));
    // intervalos de fecha de a!grouping (MONTH_SHORT_TEXT…): etiquetas como en Appian, el orden sigue siendo cronológico
    const iv = up(cfg.primaryGrouping && cfg.primaryGrouping.interval);
    const MES = LANG === "es" ? ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"] : ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const catLabel = (c) => { const m = String(c).match(/^(\d{4})-(\d{2})/); if (!m || !iv.startsWith("MONTH")) return c; return iv === "MONTH_SHORT_TEXT" ? `${MES[+m[2] - 1]} ${m[1].slice(2)}` : iv === "MONTH_TEXT" ? `${MES[+m[2] - 1]} ${m[1]}` : `${m[2]}/${m[1]}`; };
    // agrupación secundaria = la primaria (una serie por categoría, para dar a cada barra su color): series en el orden de las categorías
    // $series (solo de prototipo): orden fijo de los valores de la agrupación secundaria, para que cada serie lleve su color
    const sv2 = g2 === g1 ? cats.slice() : g2 ? (n.$series ? arr(n.$series) : [...new Set(rows.map((r) => r[g2]))].filter((x) => x != null)) : [];
    const series = g2
      ? sv2.map((sv) => ({ label: sv, data: cats.map((c) => measureOf(ms[0], rows.filter((r) => r[g1] === c && r[g2] === sv))), color: null }))
      : ms.map((m) => ({ label: m.label || (up(m.function) === "COUNT" ? "Total" : fieldOf(m.field)), data: cats.map((c) => measureOf(m, rows.filter((r) => r[g1] === c))), color: null }));
    return { cats: cats.map(catLabel), raw: cats, g1, series };
  }
  // filas de la tabla alternativa de un gráfico ($chart en a!gridField, helper chart_table): una por categoría, con la categoría
  // y una columna por serie (s1, s2…); con la agrupación secundaria igual a la principal (colores por estado), una sola columna
  function chartRows(c, ctx) {
    let cats, series;
    if (c.data && c.config) {
      const a = aggregate(c, ctx);
      const g2 = c.config.secondaryGrouping ? fieldOf(c.config.secondaryGrouping.field) : null;
      cats = a.cats;
      series = g2 && g2 === a.g1 ? [{ data: cats.map((x, i) => a.series.reduce((t, s) => t + (Number(s.data[i]) || 0), 0)) }] : a.series;
    } else if (c.type === "a!pieChartField") {
      const ss = arr(c.series).filter((s) => visible(s, ctx));
      cats = ss.map((s) => P(s, "label", ctx, ""));
      series = [{ data: ss.map((s) => Number(P(s, "data", ctx, 0)) || 0) }];
    } else {
      cats = arr(P(c, "categories", ctx, []));
      series = chartSeries(c, ctx);
    }
    return cats.map((cat, i) => { const r = { id: i + 1, categoria: cat }; series.forEach((s, j) => { r["s" + (j + 1)] = arr(s.data)[i]; }); return r; });
  }
  function chartSeries(n, ctx) { if (n.data && n.config) return aggregate(n, ctx).series; return arr(n.series).filter((s) => visible(s, ctx)).map((s) => ({ label: P(s, "label", ctx, ""), data: arr(P(s, "data", ctx, [])).map(Number), color: s.color ? hexOf(P(s, "color", ctx)) || color(P(s, "color", ctx)) : null, links: arr(s.links) })); }
  const nice = (m) => { if (m <= 0) return 1; const p = Math.pow(10, Math.floor(Math.log10(m))); const f = m / p; return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * p; };
  const esc = (t) => String(t == null ? "" : t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
  function refLines(n, ctx) {
    // la etiqueta usa el color de la línea oscurecido lo justo para leerse (4,5:1) sobre el fondo blanco del gráfico
    return arr(n.referenceLines).filter((r) => r && visible(r, ctx)).map((r) => ({ label: P(r, "label", ctx, ""), value: Number(P(r, "value", ctx, 0)),
      color: readableOn("#ffffff", [hexOf(P(r, "color", ctx, "ACCENT")) || "#666666"], 3) || color(P(r, "color", ctx, "ACCENT"), "#666"), // la línea, con 3:1 como mínimo (WCAG 1.4.11)
      text: readableOn("#ffffff", [hexOf(P(r, "color", ctx, "ACCENT")) || "#666666"]) || "#666666", dash: { SOLID: "", DOT: "2 4", DASH: "7 5", DASHDOT: "8 4 2 4", SHORTDASH: "4 3" }[up(P(r, "style", ctx, "DASH"))] ?? "7 5" }));
  }
  function legendEl(list, filt, hid, cls, val) {
    return h("div", { class: "legend" + cls + (filt ? " filt" : "") }, list.map((s, i) => {
      const kids = [h("i", { style: { background: s.color } }), h("span", { class: "ll" }, s.label), val ? h("b", null, val(s, i)) : null];
      if (!filt) return h("span", null, kids);
      return h("button", { type: "button", class: hid[i] ? "off" : "", "aria-pressed": String(!hid[i]), title: LANG === "es" ? "Mostrar u ocultar" : "Show or hide", onclick: () => { if (inspector) return; hid[i] = !hid[i]; if (list.every((x, j) => hid[j])) hid[i] = false; rerender(); } }, kids);
    }));
  }
  function xyChart(n, ctx, kind) {
    const agg = n.data && n.config ? aggregate(n, ctx) : null;
    const cats = agg ? agg.cats : arr(P(n, "categories", ctx, []));
    let ser = agg ? agg.series : chartSeries(n, ctx);
    const pal = palette(n, ctx);
    // 26.8 allowLegendFiltering: al pulsar un elemento de la leyenda se oculta o muestra esa serie (el color de cada serie no cambia)
    ser = ser.map((s, si) => ({ ...s, color: s.color || pal[si % pal.length] }));
    const allSer = ser;
    const lgf = P(n, "allowLegendFiltering", ctx, false) && ser.length > 1;
    const hid = UI["lg:" + ctx.key] || (UI["lg:" + ctx.key] = {});
    if (lgf) ser = ser.filter((s, si) => !hid[si]);
    const stk = up(n.stacking || "NONE");
    const pctStack = stk === "PERCENT_TO_TOTAL";
    const stacked = stk === "NORMAL" || pctStack;
    if (pctStack) { const tot = cats.map((c, i) => ser.reduce((a, s) => a + (s.data[i] || 0), 0) || 1); ser = ser.map((s) => ({ ...s, data: s.data.map((v, i) => (100 * (v || 0)) / tot[i]) })); }
    const hk = up(P(n, "height", ctx, "MEDIUM"));
    const H = hk === "AUTO" && kind === "bar" ? Math.max(120, 44 + cats.length * 34) : { MICRO: 70, SHORT: 180, MEDIUM: 270, TALL: 390 }[hk] || 270;
    const micro = hk === "MICRO";
    const horizPre = kind === "bar";
    const maxLab = Math.max(0, ...cats.map((c) => Math.min(24, String(c).length)));
    const refs = refLines(n, ctx);
    const showLabels = P(n, "showDataLabels", ctx, false);
    const xT = P(n, "xAxisTitle", ctx), yT = P(n, "yAxisTitle", ctx);
    const xNone = up(P(n, "xAxisStyle", ctx, "STANDARD")) === "NONE", yNone = up(P(n, "yAxisStyle", ctx, "STANDARD")) === "NONE" || micro;
    const el = h("div", { class: "chart" + (micro ? " micro" : "") });
    // profundizar: a!xxxChartConfig.link (con fv!selection = valor de la agrupación) o links de cada a!chartSeries
    const cfgLink = n.config && n.config.link;
    const linked = (si, i) => !!(cfgLink || (ser[si] && ser[si].links && ser[si].links[i]));
    el.addEventListener("click", (e) => {
      const t = e.target.closest && e.target.closest("[data-ci]");
      if (!t || inspector) return;
      const i = Number(t.getAttribute("data-ci")), si = Number(t.getAttribute("data-si"));
      if (cfgLink) { const sel = {}; sel[agg.g1] = agg.raw[i]; clickable(cfgLink, Object.assign({}, ctx, { fv: Object.assign({}, ctx.fv, { selection: sel }) }))(e); }
      else clickable(ser[si].links[i], ctx)(e);
    });
    el.__draw = (Wd) => {
      const W = Math.max(micro ? 120 : 260, Math.round(Wd || 640));
      const L = micro ? 2 : horizPre ? Math.min(180, 14 + maxLab * 6.6) + (yT ? 18 : 0) : 54 + (yT ? 18 : 0), B = micro ? 4 : 34 + (xT ? 18 : 0), Tp = micro ? 4 : 14, Rr = micro ? 2 : 18;
      const iw = W - L - Rr, ih = H - B - Tp;
      const vals = stacked ? cats.map((c, i) => ser.reduce((a, s) => a + (s.data[i] || 0), 0)) : ser.flatMap((s) => s.data);
      const rawMax = Math.max(1, ...vals, ...refs.map((r) => r.value));
      const allInt = ser.every((s) => s.data.every((v) => Number.isInteger(v)));
      let maxV = pctStack ? 100 : allInt && rawMax <= 4 ? rawMax + 1 : allInt && rawMax <= 40 ? Math.ceil(rawMax / 4) * 4 : nice(rawMax);
      const yMax = P(n, "yAxisMax", ctx), yMin = P(n, "yAxisMin", ctx);
      if (yMax != null && yMax !== "") maxV = Number(yMax);
      const minV = yMin != null && yMin !== "" ? Number(yMin) : 0;
      const span = maxV - minV || 1;
      const horiz = kind === "bar";
      const pos = (v) => (horiz ? L + (iw * (v - minV)) / span : Tp + ih - (ih * (v - minV)) / span);
      const fmtAx = (v) => (pctStack ? Math.round(v) + " %" : FILTERS.num(Math.round(v * 100) / 100));
      let g = "";
      const nt = allInt && !pctStack && span <= 5 && Number.isInteger(span) ? span : 4; // marcas enteras con pocos valores
      if (!yNone) for (let t = 0; t <= nt; t++) {
        const v = minV + (span * t) / nt;
        if (horiz) { const x = pos(v); g += `<line class="gl" x1="${x}" x2="${x}" y1="${Tp}" y2="${Tp + ih}"/><text class="ax" x="${x}" y="${H - 16 - (xT ? 18 : 0)}" text-anchor="middle">${fmtAx(v)}</text>`; }
        else { const y = pos(v); g += `<line class="gl" x1="${L}" x2="${L + iw}" y1="${y}" y2="${y}"/><text class="ax" x="${L - 6}" y="${y + 4}" text-anchor="end">${fmtAx(v)}</text>`; }
      }
      const band = (horiz ? ih : iw) / Math.max(1, cats.length);
      if (!xNone && !micro) cats.forEach((c, i) => {
        const room = horizPre ? 24 : Math.max(4, Math.floor(band / 7));
        const lab = String(c).length > room ? String(c).slice(0, room - 1) + "…" : c;
        if (horiz) g += `<text class="ax" x="${L - 8}" y="${Tp + band * i + band / 2 + 4}" text-anchor="end"><title>${esc(c)}</title>${esc(lab)}</text>`;
        else g += `<text class="ax" x="${L + band * i + band / 2}" y="${H - 16 - (xT ? 18 : 0)}" text-anchor="middle"><title>${esc(c)}</title>${esc(lab)}</text>`;
      });
      const lab = (x, y, v, anchor) => (showLabels ? `<text class="dl" x="${x}" y="${y}" text-anchor="${anchor || "middle"}">${pctStack ? Math.round(v) + " %" : FILTERS.num(Math.round(v * 100) / 100)}</text>` : "");
      // 26.8 (smart contrast): la etiqueta dentro de un segmento apilado toma blanco o negro según el color del segmento
      const labIn = (x, y, v, col, room) => (showLabels && v && room >= 16 ? `<text class="dl in" x="${x}" y="${y}" text-anchor="middle" dominant-baseline="central" style="fill:${solidFg(rgbOf(col) ? col : hexOf(col) || "#527500")}">${pctStack ? Math.round(v) + " %" : FILTERS.num(Math.round(v * 100) / 100)}</text>` : "");
      if (kind === "column" || kind === "bar") {
        const inner = band * (micro ? 0.8 : 0.66), bw = stacked ? inner : inner / Math.max(1, ser.length);
        cats.forEach((c, i) => {
          let acc = 0;
          ser.forEach((s, si) => {
            const v = s.data[i] || 0;
            const col = s.color || pal[si % pal.length];
            const off = band * i + (band - inner) / 2 + (stacked ? 0 : bw * si);
            const a0 = stacked ? acc : 0, a1 = a0 + v;
            const dk = linked(si, i) ? ` data-ci="${i}" data-si="${si}" class="lk"` : "";
            if (horiz) { const x0 = pos(Math.max(minV, a0)), x1 = pos(a1); g += `<rect${dk} x="${x0}" y="${Tp + off}" width="${Math.max(0, x1 - x0)}" height="${Math.max(1, bw - 2)}" fill="${col}"><title>${esc(s.label)} · ${esc(c)}: ${fmtAx(v)}</title></rect>` + (!stacked ? lab(x1 + 6, Tp + off + bw / 2 + 3, v, "start") : labIn((x0 + x1) / 2, Tp + off + bw / 2, v, col, x1 - x0 >= 30 && bw >= 14 ? 16 : 0)); }
            else { const y1 = pos(a1), y0 = pos(Math.max(minV, a0)); g += `<rect${dk} x="${L + off}" y="${y1}" width="${Math.max(1, bw - 2)}" height="${Math.max(0, y0 - y1)}" fill="${col}"><title>${esc(s.label)} · ${esc(c)}: ${fmtAx(v)}</title></rect>` + (!stacked ? lab(L + off + (bw - 2) / 2, y1 - 5, v) : labIn(L + off + (bw - 2) / 2, (y0 + y1) / 2, v, col, bw >= 24 ? y0 - y1 : 0)); }
            acc += v;
          });
        });
      } else {
        const base = cats.map(() => 0); // áreas apiladas: cada serie se dibuja sobre la suma de las anteriores
        ser.forEach((s, si) => {
          const col = s.color || pal[si % pal.length];
          const stk = kind === "area" && stacked;
          const top = s.data.map((v, i) => (stk ? base[i] + (v || 0) : v || 0));
          const pts = top.map((v, i) => [L + band * i + band / 2, pos(v)]);
          if (!pts.length) return;
          if (stk) { const bot = base.map((v, i) => [L + band * i + band / 2, pos(v)]).reverse(); g += `<path d="M${pts.map((p) => p.join(",")).join(" L")} L${bot.map((p) => p.join(",")).join(" L")} Z" fill="${col}" fill-opacity=".55"/>`; top.forEach((v, i) => (base[i] = v)); }
          else if (kind === "area") g += `<path d="M${pts[0][0]},${Tp + ih} L${pts.map((p) => p.join(",")).join(" L")} L${pts[pts.length - 1][0]},${Tp + ih} Z" fill="${col}" fill-opacity=".18"/>`;
          g += `<polyline points="${pts.map((p) => p.join(",")).join(" ")}" fill="none" stroke="${col}" stroke-width="${micro ? 2 : 2.5}"/>`;
          if (!micro) pts.forEach((p, i) => (g += `<circle${linked(si, i) ? ` data-ci="${i}" data-si="${si}" class="lk"` : ""} cx="${p[0]}" cy="${p[1]}" r="3.5" fill="${col}"><title>${esc(s.label)} · ${esc(cats[i])}: ${fmtAx(s.data[i])}</title></circle>` + lab(p[0], p[1] - 8, s.data[i])));
        });
      }
      refs.forEach((r) => {
        if (r.value < minV || r.value > maxV) return;
        if (horiz) { const x = pos(r.value); g += `<line x1="${x}" x2="${x}" y1="${Tp}" y2="${Tp + ih}" stroke="${r.color}" stroke-width="2" stroke-dasharray="${r.dash}"/>` + (r.label ? `<text class="rl" stroke="#fff" stroke-width="4" stroke-linejoin="round" paint-order="stroke" x="${x + 4}" y="${Tp + 10}" fill="${r.text}">${esc(r.label)}</text>` : ""); }
        else { const y = pos(r.value); g += `<line x1="${L}" x2="${L + iw}" y1="${y}" y2="${y}" stroke="${r.color}" stroke-width="2" stroke-dasharray="${r.dash}"/>` + (r.label ? `<text class="rl" stroke="#fff" stroke-width="4" stroke-linejoin="round" paint-order="stroke" x="${L + iw}" y="${y - 5}" text-anchor="end" fill="${r.text}">${esc(r.label)}</text>` : ""); }
      });
      if (!micro) g += `<line x1="${L}" x2="${horiz ? L : L + iw}" y1="${Tp + ih}" y2="${Tp + ih}" stroke="#999"/>`;
      if (xT) g += `<text class="axt" x="${L + iw / 2}" y="${H - 4}" text-anchor="middle">${esc(xT)}</text>`;
      if (yT) g += `<text class="axt" transform="translate(12 ${Tp + ih / 2}) rotate(-90)" text-anchor="middle">${esc(yT)}</text>`;
      const svgHtml = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="${esc(P(n, "accessibilityText", ctx) || P(n, "label", ctx) || "Gráfico")}">${g}</svg>`;
      const old = el.querySelector("svg"); if (old) old.outerHTML = svgHtml; else el.insertAdjacentHTML("afterbegin", svgHtml);
    };
    el.__draw(640);
    if (!micro && P(n, "showLegend", ctx, allSer.length > 1) && allSer.length) el.appendChild(legendEl(allSer, lgf, hid, ""));
    return field(n, ctx, el);
  }
  R["a!columnChartField"] = (n, ctx) => xyChart(n, ctx, "column");
  R["a!barChartField"] = (n, ctx) => xyChart(n, ctx, "bar");
  R["a!lineChartField"] = (n, ctx) => xyChart(n, ctx, "line");
  R["a!areaChartField"] = (n, ctx) => xyChart(n, ctx, "area");
  R["a!pieChartField"] = (n, ctx) => {
    const agg = n.data && n.config ? aggregate(n, ctx) : null;
    const pal = palette(n, ctx);
    const allSer = (agg ? agg.cats.map((c, i) => ({ label: c, v: agg.series[0].data[i], color: null })) : arr(n.series).map((s) => ({ label: P(s, "label", ctx, ""), v: Number(P(s, "data", ctx, 0)) || 0, color: s.color ? hexOf(P(s, "color", ctx)) || color(P(s, "color", ctx)) : null }))).map((s, i) => ({ ...s, color: s.color || pal[i % pal.length] }));
    const lgf = P(n, "allowLegendFiltering", ctx, false) && allSer.length > 1;
    const hid = UI["lg:" + ctx.key] || (UI["lg:" + ctx.key] = {});
    const ser = lgf ? allSer.filter((s, i) => !hid[i]) : allSer;
    const tot = ser.reduce((a, s) => a + s.v, 0) || 1;
    const donut = up(n.style) === "DONUT";
    const pct = P(n, "showAsPercentage", ctx, false);
    const lstyle = up(P(n, "seriesLabelStyle", ctx, "LEGEND"));
    const txt = (s) => (pct ? Math.round((100 * s.v) / tot) + " %" : FILTERS.num(s.v));
    let a0 = -Math.PI / 2, g = "";
    ser.forEach((s, i) => {
      const a1 = a0 + (2 * Math.PI * s.v) / tot, large = a1 - a0 > Math.PI ? 1 : 0;
      const p = (a, r) => [100 + r * Math.cos(a), 100 + r * Math.sin(a)];
      const [x0, y0] = p(a0, 90), [x1, y1] = p(a1, 90);
      const col = s.color || pal[i % pal.length];
      g += ser.length === 1 ? `<circle cx="100" cy="100" r="90" fill="${col}"/>` : `<path d="M100,100 L${x0},${y0} A90,90 0 ${large} 1 ${x1},${y1} Z" fill="${col}" stroke="#fff" stroke-width="1.5"><title>${esc(s.label)}: ${txt(s)}</title></path>`;
      if ((lstyle === "ON_CHART" || P(n, "showDataLabels", ctx, false)) && s.v / tot > 0.06) { const [lx, ly] = p((a0 + a1) / 2, donut ? 72 : 60); g += `<text class="pl" x="${lx}" y="${ly}" text-anchor="middle" dominant-baseline="central" fill="${solidFg(col)}">${txt(s)}</text>`; }
      a0 = a1;
    });
    if (donut) g += `<circle cx="100" cy="100" r="52" fill="#fff"/><text x="100" y="100" text-anchor="middle" dominant-baseline="central" font-size="22" font-weight="700" fill="#222">${FILTERS.num(tot)}</text>`;
    const px = { SHORT: 200, MEDIUM: 280, TALL: 360 }[up(P(n, "height", ctx, "MEDIUM"))] || 280;
    const el = h("div", { class: "chart pie" });
    el.innerHTML = `<svg viewBox="0 0 200 200" style="width:${px}px;max-width:100%" role="img" aria-label="${esc(P(n, "accessibilityText", ctx) || P(n, "label", ctx) || "Gráfico")}">${g}</svg>`;
    if (lstyle !== "NONE") el.appendChild(legendEl(allSer, lgf, hid, " v", lstyle === "ON_CHART" ? null : (s, i) => (lgf && hid[i] ? "–" : txt(s))));
    return field(n, ctx, el);
  };
  // a!scatterChartField: un punto por grupo (primaryGrouping) con xAxisMeasure / yAxisMeasure; secondaryGrouping = series
  R["a!scatterChartField"] = (n, ctx) => {
    const rows = dataRows(n, ctx);
    const g1 = fieldOf(n.primaryGrouping && n.primaryGrouping.field), g2 = n.secondaryGrouping ? fieldOf(n.secondaryGrouping.field) : null;
    const groups = [...new Set(rows.map((r) => r[g1]))].filter((x) => x != null);
    const pts = groups.map((gv) => { const rr = rows.filter((r) => r[g1] === gv); return { label: gv, x: measureOf(n.xAxisMeasure, rr, ctx), y: measureOf(n.yAxisMeasure, rr, ctx), s: g2 ? rr[0][g2] : "" }; });
    const series = [...new Set(pts.map((p) => p.s))];
    const pal = palette(n, ctx), refs = refLines(n, ctx);
    const H = { MICRO: 90, SHORT: 200, MEDIUM: 290, TALL: 400 }[up(P(n, "height", ctx, "MEDIUM"))] || 290;
    const xT = P(n, "xAxisTitle", ctx), yT = P(n, "yAxisTitle", ctx);
    const el = h("div", { class: "chart" });
    el.__draw = (Wd) => {
      const W = Math.max(260, Math.round(Wd || 640)), L = 58 + (yT ? 18 : 0), B = 34 + (xT ? 18 : 0), Tp = 14, Rr = 18, iw = W - L - Rr, ih = H - B - Tp;
      const mx = n.xAxisMax != null ? Number(P(n, "xAxisMax", ctx)) : nice(Math.max(1, ...pts.map((p) => p.x))), my = n.yAxisMax != null ? Number(P(n, "yAxisMax", ctx)) : nice(Math.max(1, ...pts.map((p) => p.y), ...refs.map((r) => r.value)));
      const X = (v) => L + (iw * v) / mx, Y = (v) => Tp + ih - (ih * v) / my;
      let g = "";
      for (let t = 0; t <= 4; t++) { const y = Y((my * t) / 4), x = X((mx * t) / 4); g += `<line class="gl" x1="${L}" x2="${L + iw}" y1="${y}" y2="${y}"/><text class="ax" x="${L - 6}" y="${y + 4}" text-anchor="end">${FILTERS.num((my * t) / 4)}</text><text class="ax" x="${x}" y="${H - 16 - (xT ? 18 : 0)}" text-anchor="middle">${FILTERS.num((mx * t) / 4)}</text>`; }
      refs.forEach((r) => { const y = Y(r.value); g += `<line x1="${L}" x2="${L + iw}" y1="${y}" y2="${y}" stroke="${r.color}" stroke-width="2" stroke-dasharray="${r.dash}"/>` + (r.label ? `<text class="rl" stroke="#fff" stroke-width="4" stroke-linejoin="round" paint-order="stroke" x="${L + iw}" y="${y - 5}" text-anchor="end" fill="${r.text}">${esc(r.label)}</text>` : ""); });
      pts.forEach((p) => { const col = pal[series.indexOf(p.s) % pal.length]; g += `<circle cx="${X(p.x)}" cy="${Y(p.y)}" r="6" fill="${col}" fill-opacity=".85" stroke="#fff"><title>${esc(p.label)}: ${FILTERS.num(p.x)} · ${FILTERS.num(p.y)}</title></circle>`; });
      g += `<line x1="${L}" x2="${L + iw}" y1="${Tp + ih}" y2="${Tp + ih}" stroke="#999"/>`;
      if (xT) g += `<text class="axt" x="${L + iw / 2}" y="${H - 4}" text-anchor="middle">${esc(xT)}</text>`;
      if (yT) g += `<text class="axt" transform="translate(12 ${Tp + ih / 2}) rotate(-90)" text-anchor="middle">${esc(yT)}</text>`;
      const svgHtml = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="${esc(P(n, "label", ctx) || "Gráfico de dispersión")}">${g}</svg>`;
      const old = el.querySelector("svg"); if (old) old.outerHTML = svgHtml; else el.insertAdjacentHTML("afterbegin", svgHtml);
    };
    el.__draw(640);
    if (series.length > 1 && P(n, "showLegend", ctx, true)) el.appendChild(h("div", { class: "legend" }, series.map((sv, i) => h("span", null, h("i", { style: { background: pal[i % pal.length] } }), sv))));
    return field(n, ctx, el);
  };

  /* ---------------- screens ---------------- */
  function recordOf(scr, params) {
    const rows = rowsOf(scr.dataset ? "data!" + scr.dataset : "recordType!" + scr.recordType);
    const id = params && params.id;
    if (id == null || id === "") return scr.type === "record" ? rows[0] || {} : {}; // sin id: la ficha enseña el primero (índice de pantallas); un alta o una tarea, nada
    return rows.find((r) => String(r.id) === String(id)) || {};
  }
  function screenCtx(scr, params, extra) {
    const ctx = Object.assign({ scope: scr.id, screen: scr.id }, extra || {});
    if (scr.type === "record" || scr.recordType) ctx.record = recordOf(scr, params);
    else if (params && params.id && scr.dataset) ctx.record = recordOf(scr, params);
    return ctx;
  }
  function renderRecord(scr, params, view) {
    const ctx = screenCtx(scr, params);
    const views = arr(scr.views);
    const k = "view:" + scr.id;
    let vi = views.findIndex((v) => v.id === UI[k]);
    if (vi < 0) vi = 0;
    UI[k] = views[vi] && views[vi].id;
    const title = interp(scr.title || "{rv!record.id}", ctx);
    const crumbs = scr.breadcrumb ? h("div", { class: "crumbs" }, h("a", { href: "#", onclick: (e) => { e.preventDefault(); if (!inspector) runAction({ goto: scr.breadcrumb.goto }, ctx); } }, interp(scr.breadcrumb.label, ctx)), icon("angle-right"), h("span", null, title)) : null;
    const actions = scr.recordActions ? render({ type: "a!recordActionField", actions: scr.recordActions, style: scr.recordActionsStyle || "TOOLBAR_PRIMARY" }, ctx, scr.id + ".ra") : null;
    const hbg = scr.headerBackgroundColor ? interp(scr.headerBackgroundColor, ctx) : null;
    const hdark = hbg && solidFg(hexOf(hbg) || "#ffffff") === "#ffffff";
    const hdr = h("div", { class: "rec-hdr" + (hbg ? " bgc" : "") + (hdark ? " dark" : ""), style: hbg ? { background: color(hbg) } : null, "data-sail": "Record View · header", "data-k": scr.id + ".hdr" },
      h("div", { class: "in" }, crumbs, h("div", { class: "rec-top" }, h("h1", null, title), scr.headerStamp ? render(scr.headerStamp, ctx, scr.id + ".hs") : null, actions),
        views.length > 1 ? h("div", { class: "tabs", role: "tablist" }, views.map((v, i) => h("button", { type: "button", role: "tab", "aria-selected": String(i === vi), class: i === vi ? "sel" : "", onclick: () => { if (!inspector) { UI[k] = v.id; rerender(); } } }, v.label))) : null));
    NODES[scr.id + ".hdr"] = { type: "Record View header", recordType: scr.recordType, headerBackgroundColor: scr.headerBackgroundColor, recordActionsStyle: scr.recordActionsStyle, $note: "Cabecera de la vista de registro: título, fondo (Record header background: Color) y atajos de acciones se configuran en el Record Type." };
    const body = views[vi] ? render(views[vi].interface, ctx, `${scr.id}.v${vi}`) : null;
    return h("div", null, hdr, body);
  }
  function renderScreen(scr, params, view) {
    if (!scr) return h("div", { class: "page-pad" }, "Pantalla no encontrada");
    if (scr.type === "record") return renderRecord(scr, params, view);
    return render(scr.interface, screenCtx(scr, params), scr.id);
  }
  function renderDialog(d, idx) {
    const scr = byId[d.screen];
    const ifc = scr.interface || {};
    let footer = null;
    const ctx = screenCtx(scr, d.params, { inDialog: true, dialogFooter: (f) => (footer = f) });
    // ancho del cuadro: el de la acción de registro (Dialog Width, $dialogWidth); el formulario va a FULL dentro
    const cw = up(ifc.contentsWidth || "");
    const w = up(scr.$dialogWidth || (cw && cw !== "FULL" ? cw : ifc.type === "a!wizardLayout" ? "MEDIUM" : "NARROW"));
    const body = render(ifc, ctx, scr.id);
    if (!footer && ifc.buttons) {
      const b = render(ifc.buttons, ctx, scr.id + ".btn");
      footer = b; if (footer) footer.className = "dlg-f";
    } else if (footer) footer.className = "dlg-f";
    const formVal = vmsgs(ifc.validations, ctx, { marginTop: "12px" });
    const tb = ifc.titleBar;
    const closeBtn = h("button", { type: "button", class: "x", "aria-label": T.cancel, onclick: () => { if (!inspector) { closeDialog(); rerender(); } } }, icon("times"));
    // barra de título con plantilla (a!headerTemplateFull, a!headerTemplateImage, a!headerTemplateSimple): cabecera del diálogo a todo el ancho
    const tpl = tb && typeof tb === "object" && /^a!headerTemplate(Full|Image|Simple)$/.test(tb.type) ? headerTemplate(tb, Object.assign({}, ctx, { key: scr.id }), true) : null;
    if (tpl && tpl.style.color) closeBtn.style.color = tpl.style.color;
    const head = tpl ? h("div", { class: "dlg-tpl" }, tpl, closeBtn) : h("div", { class: "dlg-h" }, h("h2", null, titleText(tb, ctx) || scr.title), closeBtn);
    const dlg = h("div", { class: `dlg w-${w}`, role: "dialog", "aria-modal": "true", "aria-label": titleText(tb, ctx) || scr.title }, head,
      h("div", { class: "dlg-c" }, !tpl && tb && typeof tb === "object" && tb.secondaryText ? h("div", { class: "instr", style: { marginBottom: "12px" } }, P(tb, "secondaryText", ctx)) : null, body, formVal), footer);
    return h("div", { class: "dlg-bg", style: { zIndex: 80 + idx } }, dlg);
  }
  function renderConfirm() {
    const c = confirmBox;
    const close = () => { confirmBox = null; rerender(); };
    return h("div", { class: "dlg-bg", style: { zIndex: 150 } }, h("div", { class: "dlg w-EXTRA_NARROW confirm", role: "alertdialog", "aria-modal": "true" },
      c.header ? h("div", { class: "dlg-h" }, h("h2", null, c.header)) : null,
      h("div", { class: "dlg-c" }, c.message),
      h("div", { class: "dlg-f" }, h("div", { class: "grp" }, h("button", { type: "button", class: "btn s-OUTLINE", style: { "--bc": "var(--text-2)" }, onclick: close }, c.cancel)),
        h("div", { class: "grp pri" }, h("button", { type: "button", class: "btn s-SOLID", style: { "--bc": c.color, "--bfg": solidFg(c.color) }, onclick: () => { const f = c.onOk; confirmBox = null; f(); } }, c.ok)))));
  }

  /* ---------------- site shell ---------------- */
  function siteShell(content) {
    const site = SPEC.site || {};
    const pages = arr(site.pages);
    const curScr = byId[route.screen] || {};
    const curPage = pages.find((p) => p.screen === route.screen || (p.pages || []).some((x) => x.screen === route.screen)) || pages.find((p) => arr(p.includes).includes(route.screen) || arr(p.includes).includes(curScr.recordType));
    // estilo de la barra (ux-site-branding.html#style-header-bar-only): Helium pinta el icono encima del nombre; Mercury y Oxygen no pintan
    // iconos en web y solo pintan los nombres si hay más de una página; la barra lateral (SIDEBAR) siempre lleva icono
    const bs = BRAND.site || {}, lay = up(bs.navigationLayout || "HEADER_BAR"), hstyle = up(bs.headerBarStyle || "MERCURY");
    const withIcons = site.showPageIcons !== false && (lay === "SIDEBAR" || hstyle === "HELIUM");
    const withNames = lay === "SIDEBAR" || hstyle === "HELIUM" || pages.length > 1;
    const nav = h("nav", { class: "site-nav" + (hstyle === "HELIUM" && lay !== "SIDEBAR" ? " helium" : ""), "aria-label": "Páginas del site" }, withNames ? pages.map((p) => h("button", { type: "button", class: p === curPage ? "sel" : "", "aria-current": p === curPage ? "page" : null, onclick: () => { if (!inspector) { hist.length = 0; route = null; go(p.screen || (p.pages && p.pages[0].screen)); rerender(); } } }, withIcons && p.icon ? icon(p.icon) : null, p.title)) : []);
    const user = site.user || { name: "Usuario" };
    const hdr = h("header", { class: "site-hdr", "data-sail": "Site · header bar", "data-k": "site" },
      h("div", { class: "site-brand" }, h("span", { html: LOGO, style: { display: "inline-flex" } }), site.displayName ? h("span", { class: "dn" }, site.displayName) : null),
      nav, h("div", { class: "site-user" }, h("span", { class: "uname" }, user.name), h("span", { class: "avatar", title: user.name }, FILTERS.initials(user.name))));
    NODES.site = { type: "Site", navigationLayout: (BRAND.site || {}).navigationLayout, headerBarStyle: (BRAND.site || {}).headerBarStyle, backgroundColor: (BRAND.site || {}).backgroundColor, selectedPageHighlightColor: (BRAND.site || {}).selectedPageHighlightColor, accentColor: (BRAND.site || {}).accentColor, pages: pages.map((p) => p.title), $note: "Configuración del objeto Site (ver brand-*.json)" };
    const svg = hdr.querySelector(".site-brand svg"); if (svg) svg.classList.add("logo");
    return h("div", { class: "site" + ((BRAND.site || {}).useUppercase ? " upper" : "") }, hdr, h("main", { class: "site-body" }, content));
  }

  /* ---------------- prototype chrome ---------------- */
  // nombre legible de una pantalla fuera de su contexto (índice, trazabilidad): sin plantillas {…}
  function screenLabel(sc) {
    if (!sc) return "";
    const t = sc.title || sc.id;
    if (t.indexOf("{") < 0) return t;
    if (sc.ref) return sc.ref; // el nombre que da el análisis
    return sc.type === "record" && sc.recordType ? `Ficha de ${sc.recordType}` : t.replace(/\{[^}]*\}/g, "…");
  }
  function chrome() {
    const frag = document.createDocumentFragment();
    const cur = byId[route.screen] || {};
    const bar = h("div", { class: "px-bar", role: "toolbar", "aria-label": "Herramientas del prototipo" },
      h("button", { type: "button", class: panel === "screens" ? "on" : "", onclick: () => { panel = panel === "screens" ? null : "screens"; rerender(); }, title: "Índice de pantallas" }, icon("bars"), "Pantallas"),
      h("button", { type: "button", class: panel === "trace" ? "on" : "", onclick: () => { panel = panel === "trace" ? null : "trace"; rerender(); }, title: "Trazabilidad con requisitos" }, icon("check-square-o"), "Requisitos"),
      h("button", { type: "button", class: inspector ? "on" : "", onclick: () => { inspector = !inspector; if (!inspector && panel === "node") panel = null; rerender(); }, title: "Inspector de componentes SAIL (tecla I)" }, icon("code"), "Inspector"));
    frag.appendChild(bar);
    if (panel === "screens") {
      const groups = [["page", "Páginas del site"], ["record", "Vistas de registro"], ["form", "Formularios y tareas"], ["dialog", "Diálogos"]];
      const p = h("div", { class: "px-panel", role: "dialog", "aria-label": "Pantallas" }, h("h3", null, `${(SPEC.app || {}).name || "Prototipo"} · ${screens.length} pantallas`, h("button", { type: "button", style: { border: 0, background: "none", cursor: "pointer" }, "aria-label": "Cerrar", onclick: () => { panel = null; rerender(); } }, icon("times"))));
      groups.forEach(([t, lbl]) => {
        const list = screens.filter((s) => (s.type || "page") === t);
        if (!list.length) return;
        p.appendChild(h("h4", null, lbl));
        list.forEach((s) => p.appendChild(h("button", { type: "button", class: "it" + (s.id === route.screen || dialogs.some((d) => d.screen === s.id) ? " cur" : ""), onclick: () => { panel = null; showScreen(s.id); } }, s.pattern ? h("span", { class: "pc" }, s.pattern) : null, screenLabel(s), h("span", { class: "rq" }, arr(s.req).join(", ")))));
      });
      frag.appendChild(p);
    }
    if (panel === "trace") {
      const reqs = arr(SPEC.requirements);
      const cov = (id) => screens.filter((s) => arr(s.req).includes(id) || arr(s.views).some((v) => arr(v.req).includes(id)));
      const p = h("div", { class: "px-panel", role: "dialog", "aria-label": "Trazabilidad" }, h("h3", null, "Trazabilidad con el diseño funcional", h("button", { type: "button", style: { border: 0, background: "none", cursor: "pointer" }, "aria-label": "Cerrar", onclick: () => { panel = null; rerender(); } }, icon("times"))));
      if ((SPEC.app || {}).source) p.appendChild(h("div", { class: "meta" }, "Fuente: ", (SPEC.app || {}).source));
      const inScope = reqs.filter((r) => !r.outOfScope && !r.noScreen);
      const aparte = reqs.length - inScope.length;
      p.appendChild(h("h4", null, `Requisitos (${inScope.filter((r) => cov(r.id).length).length}/${inScope.length} cubiertos` + (aparte ? `; ${aparte} sin pantalla propia o fuera del prototipo)` : ")")));
      p.appendChild(h("table", null, h("tbody", null, reqs.map((r) => { const c = cov(r.id); const why = !c.length && (r.noScreen ? "Sin pantalla propia: " + r.noScreen : r.outOfScope ? "Fuera del prototipo: " + r.outOfScope : ""); return h("tr", null, h("td", { class: c.length || why ? "" : "miss" }, r.id), h("td", null, r.title), h("td", null, c.length ? c.map((s) => screenLabel(s)).join(", ") : why ? h("span", { class: "meta" }, why) : h("span", { class: "miss" }, "Sin pantalla"))); }))));
      const orphans = screens.filter((s) => !arr(s.req).length);
      if (orphans.length) { p.appendChild(h("h4", null, "Pantallas sin requisito")); orphans.forEach((s) => p.appendChild(h("div", { class: "meta" }, screenLabel(s)))); }
      const qs = arr(SPEC.openQuestions);
      const PRI = { CRITICA: ["🔴", 0], IMPORTANTE: ["🟡", 1], MEJORA: ["🟢", 2] };
      if (qs.length) { p.appendChild(h("h4", null, `Preguntas abiertas (${qs.length})`)); qs.slice().sort((a, b) => ((PRI[a.priority] || [0, 3])[1]) - ((PRI[b.priority] || [0, 3])[1])).forEach((q) => p.appendChild(h("div", { class: "q" }, h("strong", null, `${PRI[q.priority] ? PRI[q.priority][0] + " " : ""}${q.id} `), q.text, q.screen ? h("div", { class: "meta", style: { padding: 0 } }, "Pantalla: " + (screenLabel(byId[q.screen]) || q.screen)) : null))); }
      const asum = [];
      if (SPEC.app && SPEC.app.$assumption) asum.push([{ title: "Aplicación" }, SPEC.app.$assumption]); // p. ej. la versión de Appian supuesta
      screens.forEach((s) => arr(s.assumptions).forEach((a) => asum.push([s, a])));
      screens.forEach((s) => (function walk(o) { if (!o || typeof o !== "object") return; if (o.$assumption) asum.push([s, o.$assumption]); for (const k in o) if (k !== "$assumption") walk(o[k]); })(s.interface || s.views));
      if (asum.length) { p.appendChild(h("h4", null, `Supuestos a validar (${asum.length})`)); asum.forEach(([s, a]) => p.appendChild(h("div", { class: "q", style: { borderColor: "#0078d4", background: "#f0f6fc" } }, a, h("div", { class: "meta", style: { padding: 0 } }, screenLabel(s))))); }
      frag.appendChild(p);
    }
    if (panel === "node" && inspector && inspected) {
      const n = NODES[inspected] || {};
      const shallow = {};
      const big = (v) => JSON.stringify(v).length > 400 || /"(contents|columns|steps|tabs|items|cards|panes)"/.test(JSON.stringify(v));
      for (const key in n) { const v = n[key]; shallow[key] = Array.isArray(v) && v.some((x) => x && typeof x === "object" && x.type) && big(v) ? `[${v.length} componente(s)]` : v && typeof v === "object" && v.type && big(v) ? `${v.type}(…)` : v; }
      const p = h("div", { class: "px-panel", role: "dialog", "aria-label": "Componente" }, h("h3", null, n.type || "Componente", h("button", { type: "button", style: { border: 0, background: "none", cursor: "pointer" }, "aria-label": "Cerrar", onclick: () => { panel = null; inspected = null; rerender(); } }, icon("times"))));
      p.appendChild(h("div", { class: "meta" }, `Pantalla: ${cur.id}${cur.pattern ? " · patrón " + cur.pattern : ""}${arr(cur.req).length ? " · " + arr(cur.req).join(", ") : ""}${cur.ref ? " · " + cur.ref : ""}`));
      if (n.$note) p.appendChild(h("div", { class: "q", style: { borderColor: "#0078d4", background: "#f0f6fc" } }, n.$note));
      if (n.$assumption) p.appendChild(h("div", { class: "q" }, h("strong", null, "Supuesto: "), n.$assumption));
      p.appendChild(h("h4", null, "Parámetros SAIL"));
      const sail = {}; const proto = {};
      for (const key in shallow) (key.startsWith("$") ? proto : sail)[key] = shallow[key];
      p.appendChild(h("pre", null, JSON.stringify(sail, null, 2)));
      if (Object.keys(proto).length) { p.appendChild(h("h4", null, "Solo prototipo ($)")); p.appendChild(h("pre", null, JSON.stringify(proto, null, 2))); }
      frag.appendChild(p);
    }
    return frag;
  }
  let inspected = null;
  const tip = h("div", { class: "px-tip", hidden: true });
  function summarize(n) {
    if (!n) return "";
    const keys = ["label", "style", "size", "color", "backgroundColor", "contentsWidth", "width", "padding", "labelPosition", "template", "stepStyle"];
    const bits = keys.filter((k) => n[k] != null && typeof n[k] !== "object").map((k) => `${k}: ${JSON.stringify(n[k])}`);
    return `${n.type}(${bits.slice(0, 3).join(", ")}${bits.length > 3 ? ", …" : ""})`;
  }
  document.addEventListener("mouseover", (e) => {
    if (!inspector) return;
    const t = e.target.closest("[data-sail]");
    document.querySelectorAll(".px-hov").forEach((x) => x.classList.remove("px-hov"));
    if (!t || t.closest(".px-panel,.px-bar")) { tip.hidden = true; return; }
    t.classList.add("px-hov");
    tip.textContent = summarize(NODES[t.getAttribute("data-k")]) || t.getAttribute("data-sail");
    const r = t.getBoundingClientRect();
    tip.style.left = Math.max(4, r.left) + "px"; tip.style.top = Math.max(4, r.top - 22) + "px"; tip.hidden = false;
  });
  document.addEventListener("click", (e) => {
    if (!inspector || e.target.closest(".px-panel,.px-bar")) return;
    const t = e.target.closest("[data-sail]");
    e.preventDefault(); e.stopPropagation();
    if (t) { inspected = t.getAttribute("data-k"); panel = "node"; rerender(); }
  }, true);
  document.addEventListener("keydown", (e) => {
    if (e.target.closest && e.target.closest("input,textarea,select,[contenteditable]")) return;
    if (e.key === "i" || e.key === "I") { inspector = !inspector; rerender(); }
    if (e.key === "Escape") { if (confirmBox) confirmBox = null; else if (panel) panel = null; else if (dialogs.length) dialogs.pop(); rerender(); }
  });

  /* ---------------- main render ---------------- */
  const root = h("div", { id: "px-root", style: { height: "100%" } });
  function rerender() {
    const active = document.activeElement;
    const fid = active && active.id && active.id.startsWith("f-") ? active.id : null;
    const sel = fid && typeof active.selectionStart === "number" ? [active.selectionStart, active.selectionEnd] : null;
    const scrolls = Array.from(document.querySelectorAll(".dlg-c")).map((x) => x.scrollTop);
    const y = window.scrollY;
    REQ = []; VALS = []; pathSeq = 0;
    for (const k in NODES) delete NODES[k];
    const scr = byId[route.screen];
    let content = renderScreen(scr, route.params, route.view);
    const wrapped = scr && scr.chrome === false ? h("div", { class: "site", style: { background: "#fff" } }, content) : siteShell(content);
    const frag = document.createDocumentFragment();
    frag.appendChild(wrapped);
    dialogs.forEach((d, i) => frag.appendChild(renderDialog(d, i)));
    if (confirmBox) frag.appendChild(renderConfirm());
    frag.appendChild(chrome());
    frag.appendChild(tip);
    root.replaceChildren(frag);
    document.body.classList.toggle("px-insp", inspector);
    document.body.classList.toggle("px-capture", capture);
    if (!inspector) tip.hidden = true;
    drawCharts();
    layoutNav();
    window.scrollTo(0, y);
    document.querySelectorAll(".dlg-c").forEach((x, i) => (x.scrollTop = scrolls[i] || 0));
    if (fid) { const el = document.getElementById(fid); if (el) { el.focus({ preventScroll: true }); if (sel && el.setSelectionRange) try { el.setSelectionRange(sel[0], sel[1]); } catch (e) {} } }
    const top = dialogs.length ? byId[dialogs[dialogs.length - 1].screen] : scr;
    const tctx = top ? screenCtx(top, dialogs.length ? dialogs[dialogs.length - 1].params : route.params) : {};
    document.title = `${top ? interp(top.title || "", tctx) : ""} · ${(SPEC.app || {}).name || "Prototipo"}`.replace(/^ · /, "");
  }
  function drawCharts() { document.querySelectorAll(".chart").forEach((c) => c.__draw && c.clientWidth && c.__draw(c.clientWidth)); }
  function layoutNav() { document.querySelectorAll(".hb, .cbr").forEach((c) => c.__layout && c.__layout()); }
  let rsz; window.addEventListener("resize", () => { clearTimeout(rsz); rsz = setTimeout(() => { drawCharts(); layoutNav(); }, 120); });
  function firstRecordId(scr) { const r = rowsOf(scr.dataset ? "data!" + scr.dataset : "recordType!" + scr.recordType)[0]; return r && r.id; }
  function showScreen(id, opts) {
    opts = opts || {};
    if (opts.id != null && !opts.params) opts.params = { id: opts.id }; // atajo: show("registro", {id: 4})
    const scr = byId[id];
    if (!scr) return false;
    if ((scr.type || "page") === "dialog") {
      const host = opts.host || scr.openFrom || (route && route.screen) || screens.find((s) => (s.type || "page") === "page").id;
      const hs = byId[host];
      hist.length = 0; route = null;
      go(host, opts.hostParams || (hs && hs.type === "record" ? { id: firstRecordId(hs) } : {}));
      openDialog(id, opts.params || (scr.dataset || scr.recordType ? { id: firstRecordId(scr) } : {}));
    } else {
      hist.length = 0; route = null;
      go(id, opts.params || (scr.type === "record" ? { id: firstRecordId(scr) } : {}), { view: opts.view });
    }
    if (opts.state) for (const k in opts.state) S[k] = clone(opts.state[k]);
    if (opts.step != null) UI["wiz:" + id] = opts.step;
    if (opts.showValidation) { invalid[id] = true; if (opts.step != null) invalid[id + ":s" + opts.step] = true; }
    if (opts.ui) Object.assign(UI, opts.ui);
    rerender();
    return true;
  }

  function start() {
    document.body.appendChild(root);
    const cs = getComputedStyle(document.documentElement);
    for (const [k, v] of [["POSITIVE", "--positive"], ["NEGATIVE", "--negative"], ["WARN", "--warn"], ["INFO", "--info"]]) { const x = cs.getPropertyValue(v).trim(); if (rgbOf(x)) SEMHEX[k] = x; }
    const lk = linkOn((BRAND.site && BRAND.site.backgroundColor) || "#0f203a");
    if (lk) document.documentElement.style.setProperty("--lnk-dark", lk);
    const hash = (location.hash || "").replace(/^#/, "");
    const home = (SPEC.site && SPEC.site.home) || ((SPEC.site && arr(SPEC.site.pages)[0]) || {}).screen || (screens[0] || {}).id;
    if (!(hash && showScreen(hash))) { go(home, {}); rerender(); }
    if (/capture/.test(location.search)) { capture = true; rerender(); }
  }

  window.PROTO = {
    spec: SPEC,
    show: showScreen,
    setCapture: (on) => { capture = !!on; inspector = false; panel = null; rerender(); },
    setInspector: (on) => { inspector = !!on; rerender(); },
    state: S,
    rerender,
    ready: true,
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
