#!/usr/bin/env node
/*
 * Genera el DF en Word (.docx) a partir del análisis de un proyecto.
 *
 * Uso: node df_docx.js <carpeta del proyecto> [-o entregables/DF-<proyecto>-v1.1.docx] [--pdf]
 *      node df_docx.js <carpeta del proyecto> --pdf-de <fichero>     solo convierte ese fichero a PDF
 *
 * Lee analisis/funcional.md (el contenido), analisis/decisiones.md (control del documento) y proyecto.md
 * (cliente y «Entregados»). Lo que no ve el cliente se queda fuera: comentarios <!-- … --> (fuentes y
 * estados), piezas, filas y criterios tachados (anulados o respondidos). Las fichas (**HU-07 — …**,
 * **INT-02 — …**) salen como títulos de cuarto nivel. Con prototipo/brand-<id>.json, su color oscuro
 * (site.backgroundColor) en títulos y cabeceras de tabla.
 *
 * Portada, control del documento, índice (con sus entradas; Word pone las páginas al abrirlo), encabezado y pie
 * con confidencialidad, versión y número de página. Markdown admitido: títulos, párrafos con **negrita**,
 * *cursiva* y `código`, listas (una viñeta puede seguir en líneas sangradas), tablas, citas (>), imágenes
 * ![pie](ruta.png) con figuras numeradas.
 *
 * No sobrescribe un Word entregado («Entregados» de proyecto.md, que escribe proyecto.py entregar): sale con 1.
 * --pdf y --pdf-de convierten con LibreOffice (soffice) en un perfil temporal que se borra y dejan el PDF en
 * <p>/entregables/revision/.
 *
 * Requiere Node.js y el paquete docx (npm install docx si no está).
 */
const fs = require("fs");
const path = require("path");
const os = require("os");
const cp = require("child_process");
// docx se busca junto al script, en la carpeta de trabajo y en los paquetes globales de npm
function cargarDocx() {
  const { createRequire } = require("module");
  const sitios = [__filename, path.join(process.cwd(), "x.js")];
  try { sitios.push(path.join(cp.execSync("npm root -g", { stdio: ["ignore", "pipe", "ignore"] }).toString().trim(), "x.js")); } catch (e) { /* sin npm */ }
  for (const s of sitios) { try { return createRequire(s)("docx"); } catch (e) { /* siguiente */ } }
  console.error("Falta el paquete docx de Node. Instálalo en la carpeta de trabajo (npm install docx) o para todo el equipo (npm install -g docx).");
  process.exit(2);
}

const args = process.argv.slice(2);
const CON_VALOR = ["-o", "--pdf-de"];
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const src = args.find((a, i) => !a.startsWith("-") && !(i > 0 && CON_VALOR.includes(args[i - 1])));
if (!src) { console.error("Uso: node df_docx.js <carpeta del proyecto> [-o salida.docx] [--pdf] | --pdf-de <fichero>"); process.exit(2); }
let analisis = path.resolve(src);
if (fs.statSync(analisis).isFile()) analisis = path.dirname(analisis);
if (fs.existsSync(path.join(analisis, "analisis"))) analisis = path.join(analisis, "analisis");
const raiz = path.basename(analisis) === "analisis" ? path.dirname(analisis) : analisis;
const REVISION = path.join(raiz, "entregables", "revision");   // los PDF para revisar, dentro del proyecto

// PDF con LibreOffice en un perfil y un HOME temporales, que se borran: no deja nada fuera del proyecto ni choca con
// un LibreOffice abierto
function aPdf(fichero) {
  const exes = [process.env.SOFFICE, "soffice", "libreoffice"];
  if (process.platform === "win32") exes.push("C:\\Program Files\\LibreOffice\\program\\soffice.exe");
  if (process.platform === "darwin") exes.push("/Applications/LibreOffice.app/Contents/MacOS/soffice");
  const nombre = path.basename(fichero, path.extname(fichero)) + ".pdf", pdf = path.join(REVISION, nombre);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "df-pdf-"));
  try {   // se convierte en la carpeta temporal y solo si sale bien sustituye al PDF que hubiera
    const perfil = require("url").pathToFileURL(path.join(tmp, "perfil")).href, salida = path.join(tmp, "salida");
    const env = { ...process.env, HOME: tmp, TMPDIR: tmp, TMP: tmp, TEMP: tmp };
    for (const exe of exes.filter(Boolean)) {
      const r = cp.spawnSync(exe, [`-env:UserInstallation=${perfil}`, "--headless", "--convert-to", "pdf", "--outdir", salida, fichero],
        { env, encoding: "utf8", timeout: 300000 });
      if (r.error && r.error.code === "ENOENT") continue;
      if (!fs.existsSync(path.join(salida, nombre)))
        return { ok: false, msg: `LibreOffice no ha convertido ${path.basename(fichero)}: ${String(r.stderr || r.stdout || (r.error && r.error.message) || "").trim().slice(-300)}` };
      fs.mkdirSync(REVISION, { recursive: true });
      fs.copyFileSync(path.join(salida, nombre), pdf);
      return { ok: true, pdf };
    }
    return { ok: false, msg: "Sin LibreOffice (soffice): no se genera el PDF; revisa el Word a mano" };
  } finally {
    try { fs.rmSync(tmp, { recursive: true, force: true, maxRetries: 5 }); } catch (e) { /* en Windows puede seguir abierto (EBUSY) */ }
  }
}
if (args.includes("--pdf-de")) {
  const f = opt("--pdf-de") ? path.resolve(opt("--pdf-de")) : "";
  if (!f || !fs.existsSync(f)) { console.error(`No existe ${f || "el fichero de --pdf-de"}`); process.exit(2); }
  const r = aPdf(f);
  console.log(r.ok ? `OK ${r.pdf}` : r.msg);
  process.exit(r.ok ? 0 : 1);
}

const D = cargarDocx();
const { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, ShadingType,
  ImageRun, AlignmentType, TableOfContents, Header, Footer, PageNumber, LevelFormat, BorderStyle, PageBreak,
  PageOrientation } = D;
const leer = (f) => (fs.existsSync(f) ? fs.readFileSync(f, "utf8").replace(/\r\n/g, "\n") : "");
const funcional = leer(path.join(analisis, "funcional.md"));
if (!funcional) { console.error(`No encuentro ${path.join(analisis, "funcional.md")}`); process.exit(2); }
const decisiones = leer(path.join(analisis, "decisiones.md"));
const proyecto = leer(path.join(raiz, "proyecto.md"));
const base = analisis;
const titulo = ((funcional.match(/^# (.+)$/m) || [, "Diseño funcional"])[1]).replace(/\s+—\s+Diseño funcional\s*$/, "");
const cliente = (proyecto.match(/Cliente:\s*([^·\n]+)/) || [, ""])[1].trim();
const version = (funcional.match(/Versi[oó]n:\s*v?([\d.]+)/) || [, "0.1"])[1];
const estadoDoc = (funcional.match(/Estado:\s*([^·\n]+)/) || [, "borrador"])[1].trim();
const slug = titulo.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^\w]+/g, "-").replace(/^-|-$/g, "");
// fecha de la versión (fila de Versiones en decisiones.md) o, si no está, la de hoy
const filaVersion = decisiones.split("\n").find((l) => new RegExp(`^\\|\\s*v?${version.replace(".", "\\.")}\\s*\\|`).test(l));
const fechaVersion = filaVersion ? filaVersion.split("|")[2].trim().split("-").reverse().join("/") : new Date().toLocaleDateString("es-ES");
const out = path.resolve(opt("-o", path.join(raiz, "entregables", `DF-${slug}-v${version}.docx`)));

// Un Word entregado no se toca: los de «Entregados: a.docx, b.docx» de proyecto.md (proyecto.py entregar)
const entregados = ((proyecto.match(/^Entregados:\s*(.*)$/m) || [])[1] || "").split(",").map((x) => x.trim()).filter(Boolean);
if (fs.existsSync(out)) {
  if (entregados.includes(path.basename(out))) {
    console.error(`${path.basename(out)} ya se entregó al cliente («Entregados» de proyecto.md): no se sobrescribe ${out}. ` +
      `Si el análisis ha cambiado, sube la versión; para el PDF de ese Word, --pdf-de ${out}.`);
    process.exit(1);
  }
  console.log(`· ${path.basename(out)} existe y no se ha entregado: se reemplaza`);
}

// La marca del cliente: su color oscuro (site.backgroundColor, que lleva texto blanco encima) en títulos y
// cabeceras de tabla; sin marca, los azules de siempre
function marca() {
  const dir = path.join(raiz, "prototipo");
  const ficheros = fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => /^brand-.+\.json$/i.test(f)).sort() : [];
  if (!ficheros.length) return null;
  try {
    const b = JSON.parse(fs.readFileSync(path.join(dir, ficheros[0]), "utf8"));
    const c = String((b.site && b.site.backgroundColor) || (b.palette && b.palette.navy) || "");
    if (/^#?[0-9a-f]{6}$/i.test(c)) return { fichero: `prototipo/${ficheros[0]}`, color: c.replace("#", "").toUpperCase() };
  } catch (e) { /* abajo */ }
  console.log(`· prototipo/${ficheros[0]} sin un color #RRGGBB en site.backgroundColor: el Word sale con los colores de siempre`);
  return null;
}
const MARCA = marca();
const COLOR = MARCA ? MARCA.color : "1F3864", COLOR2 = MARCA ? MARCA.color : "2F5597";

// Lo que no ve el cliente
function limpiar(md) {
  md = md.replace(/<!--[\s\S]*?-->/g, "");
  const L = md.split("\n"), res = [];
  let saltar = false;
  for (const l of L) {
    if (/^\*\*~~[A-Z]+-\d+~~/.test(l)) { saltar = true; continue; }          // ficha anulada
    if (saltar && (/^#/.test(l) || /^\*\*[A-Z]+-\d+ — /.test(l))) saltar = false;
    if (saltar) continue;
    if (/^\|\s*~~/.test(l)) continue;                                           // fila tachada
    if (/^\s*[-*]\s+~~/.test(l)) continue;                                      // criterio tachado
    if (/^Versi[oó]n:/.test(l)) continue;                                       // va en la portada
    let x = l.replace(/`((?:HU|ACT|ESC|PAN|AV|DOC|INT|PC|RB)-[\d.]+)`/g, "$1");
    const f = x.match(/^\*\*((?:ACT|ESC|HU|PAN|INT)-\d+ — .+?)\*\*\s*$/);
    res.push(f ? `#### ${f[1]}` : x.replace(/\s+$/, ""));
  }
  return res.join("\n").replace(/\n{3,}/g, "\n\n");
}

// Control del documento, desde la tabla «Versiones» de decisiones.md (sin la columna de fuentes)
function control() {
  const m = decisiones.match(/^## Versiones\s*$([\s\S]*?)(?=^## |$(?![\s\S]))/m);
  const filas = m ? m[1].split("\n").filter((l) => /^\|/.test(l) && !/^\|[\s:|-]+\|?\s*$/.test(l)) : [];
  const celdas = (l) => l.replace(/^\||\|\s*$/g, "").split("|").map((c) => c.trim());
  if (!filas.length) return "";
  const cab = celdas(filas[0]).map((c) => c.toLowerCase());
  const usar = cab.map((c, i) => (["fuentes", "aprobación", "aprobacion"].includes(c) ? -1 : i)).filter((i) => i >= 0);
  const entregadas = filas.slice(1).filter((l) => parseFloat(celdas(l)[0].replace(/^v/, "")) >= 1);
  if (!entregadas.length) return "";
  const t = [filas[0], ...entregadas].map((l) => "| " + usar.map((i) => celdas(l)[i] || "").join(" | ") + " |");
  t.splice(1, 0, "|" + usar.map(() => "---").join("|") + "|");
  return `## Control del documento\n\nEstado: ${estadoDoc}.\n\n${t.join("\n")}\n`;
}

const md = control() + "\n" + limpiar(funcional).replace(/^# .+$/m, "");

const FONT = "Calibri", MONO = "Consolas";
const PAGE_W = 11906, MARGIN = 1134, CONTENT_W = PAGE_W - 2 * MARGIN; // A4, márgenes 2 cm

function runs(text, base = {}) {
  text = text.replace(/\b([A-Z]{2,4})-(\d)/g, "$1\u2011$2"); // los IDs (PAN-02) no se parten al final de la línea
  // **negrita**, *cursiva*, `código`; enlaces [t](u) → t
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
  const out = [];
  // ~~tachado~~ y **negrita** pueden llevar marcado dentro (p. ej. **~~RF-007~~ — Título**, ~~`CA-PAN-66.6`~~)
  const re = /(~~(?:(?!~~).)+~~|\*\*[^*]+\*\*|`[^`]+`|(?<![*\w])\*[^*\s][^*]*\*(?!\*))/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const t = m[0];
    if (t.startsWith("**")) out.push(...runs(t.slice(2, -2), { ...base, bold: true }));
    else if (t.startsWith("`")) out.push(new TextRun({ text: t.slice(1, -1), font: MONO, size: (base.size || 21) - 2, ...base, font: MONO }));
    else if (t.startsWith("~~")) out.push(...runs(t.slice(2, -2), { ...base, strike: true }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out.length ? out : [new TextRun({ text: "", ...base })];
}

const cellBorder = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
function table(rows) {
  const n = Math.max(...rows.map((r) => r.length));
  rows = rows.map((r) => r.concat(Array(n - r.length).fill("")));
  // anchos proporcionales al contenido (acotados)
  const len = Array(n).fill(0).map((_, c) => Math.min(60, Math.max(6, ...rows.map((r) => r[c].replace(/[*`]/g, "").length))));
  const tot = len.reduce((a, b) => a + b, 0);
  const small = n >= 5 ? 16 : 18;
  // mínimo por columna: que quepa su palabra más larga (hasta 14 letras) sin partirla letra a letra
  const porLetra = small * 6.2;
  const minW = Array(n).fill(0).map((_, c) => {
    const w = Math.max(...rows.map((r) => Math.max(0, ...r[c].replace(/[*`~]/g, "").split(/\s+/).map((x) => Math.min(14, x.length)))));
    return Math.round(w * porLetra + 200);
  });
  // cada columna tiene su mínimo; el resto del ancho se reparte según el contenido. Si los mínimos no caben,
  // se reducen en proporción (tablas de muchas columnas)
  const sumMin = minW.reduce((a, b) => a + b, 0);
  let widths;
  if (sumMin >= CONTENT_W) widths = minW.map((w) => Math.floor((w * CONTENT_W) / sumMin));
  else widths = minW.map((w, c) => w + Math.floor(((CONTENT_W - sumMin) * len[c]) / tot));
  widths[n - 1] += CONTENT_W - widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({
      tableHeader: i === 0,
      cantSplit: true,
      children: r.map((c, j) => new TableCell({
        width: { size: widths[j], type: WidthType.DXA },
        borders: { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder },
        shading: i === 0 ? { type: ShadingType.CLEAR, fill: COLOR, color: "auto" } : undefined,
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        children: c.split(/<br\s*\/?>/).map((part) => new Paragraph({
          spacing: { after: 0 },
          children: runs(part.trim(), i === 0 ? { bold: true, color: "FFFFFF", size: small } : { size: small }),
        })),
      })),
    })),
  });
}

function callout(text, fill, border) {
  return new Paragraph({
    shading: { type: ShadingType.CLEAR, fill },
    border: { left: { style: BorderStyle.SINGLE, size: 24, color: border, space: 6 } },
    spacing: { before: 80, after: 120 },
    children: runs(text),
  });
}

let fig = 0, missing = 0;
function image(file, caption) {
  const p = path.resolve(base, file);
  if (!fs.existsSync(p)) { missing++; return [new Paragraph({ children: runs(`[Imagen no encontrada: ${file}]`, { color: "C00000" }) })]; }
  const buf = fs.readFileSync(p);
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20); // PNG IHDR
  const maxW = 640, maxH = 820;
  let W = maxW, H = Math.round((h * maxW) / w);
  if (H > maxH) { H = maxH; W = Math.round((w * maxH) / h); }
  fig++;
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, children: [new ImageRun({ type: "png", data: buf, transformation: { width: W, height: H } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: `Figura ${fig} — ${caption}`, italics: true, size: 18 })] }),
  ];
}

const HL = [null, HeadingLevel.HEADING_1, HeadingLevel.HEADING_1, HeadingLevel.HEADING_2, HeadingLevel.HEADING_3, HeadingLevel.HEADING_4, HeadingLevel.HEADING_5];
const body = [], entradas = [];   // entradas del índice: Word pone las páginas al abrirlo; LibreOffice las enseña así
const NIVEL_INDICE = [0, 1, 1, 2, 3];   // # y ## → 1, ### → 2, #### (las fichas) → 3, como headingStyleRange 1-3
const L = md.split("\n");
let i = 0, skippedFirstH1 = false, listInstance = 0;
while (i < L.length) {
  let l = L[i];
  if (/^```/.test(l)) { // bloque de código
    const lang = l.slice(3).trim(); const code = []; i++;
    while (i < L.length && !/^```/.test(L[i])) code.push(L[i++]);
    i++;
    let j = i; while (j < L.length && !L[j].trim()) j++;
    if (lang === "mermaid" && /^!\[/.test(L[j] || "")) continue; // la imagen lo sustituye
    if (lang === "mermaid") body.push(callout("Diagrama pendiente de renderizar (requisito: Playwright + navegador). Código Mermaid:", "FFF2CC", "BF8F00"));
    code.forEach((c) => body.push(new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text: c || " ", font: MONO, size: 16 })] })));
    continue;
  }
  let m;
  if ((m = l.match(/^(#{1,6}) (.+)$/))) {
    const lvl = Math.min(m[1].length, 6);
    if (lvl === 2 && /^(Anexo|Control del documento)/.test(m[2]) && body.length) body.push(new Paragraph({ children: [new PageBreak()] }));
    body.push(new Paragraph({ heading: HL[lvl], keepNext: true, children: runs(m[2].replace(/\*\*/g, "")) }));
    if (NIVEL_INDICE[lvl]) entradas.push({ title: m[2].replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/[`*~]/g, "").trim(), level: NIVEL_INDICE[lvl] });
    i++; continue;
  }
  if ((m = l.match(/^!\[([^\]]*)\]\(([^)]+)\)\s*$/))) { body.push(...image(m[2], m[1])); i++; continue; }
  if (/^\|/.test(l)) {
    const rows = [];
    while (i < L.length && /^\|/.test(L[i])) {
      const r = L[i].replace(/^\||\|\s*$/g, "").split(/(?<!\\)\|/).map((c) => c.trim().replace(/\\\|/g, "|"));
      if (!r.every((c) => /^:?-{2,}:?$/.test(c))) rows.push(r);
      i++;
    }
    body.push(table(rows), new Paragraph({ spacing: { after: 60 }, children: [] }));
    continue;
  }
  if (/^\s*[-*] /.test(l) || /^\s*\d+\. /.test(l)) {
    listInstance++; // cada lista empieza su numeración en 1
    while (i < L.length && (/^\s*[-*] /.test(L[i]) || /^\s*\d+\. /.test(L[i]))) {
      const li = L[i], ind = li.match(/^\s*/)[0].length, num = /^\s*\d+\. /.test(li);
      let texto = li.replace(/^\s*([-*]|\d+\.) /, "");
      i++;
      // la viñeta sigue en las líneas sangradas de debajo que no son otra viñeta
      while (i < L.length && /^\s+\S/.test(L[i]) && !/^\s*([-*]|\d+\.) /.test(L[i])) texto += " " + L[i++].trim();
      body.push(new Paragraph({ numbering: { reference: num ? "num" : "bul", level: Math.min(Math.floor(ind / 2), 3), instance: listInstance }, spacing: { after: 40 }, children: runs(texto) }));
    }
    continue;
  }
  if (/^>/.test(l)) {
    const q = [];
    while (i < L.length && /^>/.test(L[i])) q.push(L[i++].replace(/^>\s?/, ""));
    body.push(callout(q.join(" "), "EAF1FB", "2F5597"));
    continue;
  }
  if (/^---+\s*$/.test(l)) { i++; continue; }
  if (!l.trim()) { i++; continue; }
  // párrafo (une líneas seguidas)
  const para = [l];
  i++;
  while (i < L.length && L[i].trim() && !/^(#|\||```|!\[|>|\s*[-*] |\s*\d+\. |---)/.test(L[i])) para.push(L[i++]);
  const text = para.join(" ");
  if (/CONTRADICCI[ÓO]N/.test(text) || /^🔴/.test(text)) body.push(callout(text, "FDE9E7", "C00000"));
  else if (/^⚠️/.test(text)) body.push(callout(text, "FFF2CC", "BF8F00"));
  else body.push(new Paragraph({ spacing: { after: 100 }, children: runs(text) }));
}

const portada = [
  new Paragraph({ spacing: { before: 3000, after: 300 }, children: [new TextRun({ text: "Diseño funcional", size: 28, color: "595959" })] }),
  new Paragraph({ spacing: { after: 400 }, children: [new TextRun({ text: titulo, bold: true, size: 48, color: COLOR })] }),
  new Paragraph({ children: [new TextRun({ text: cliente ? `Cliente: ${cliente}` : "", size: 24 })] }),
  new Paragraph({ children: [new TextRun({ text: `Versión ${version} · ${estadoDoc}`, size: 24 })] }),
  new Paragraph({ children: [new TextRun({ text: `Fecha: ${fechaVersion}`, size: 24 })] }),
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Índice")] }),
  new TableOfContents("Índice", { hyperlink: true, headingStyleRange: "1-3", cachedEntries: entradas }),
];

const doc = new Document({
  creator: "appian-analisis-funcional",
  title: titulo,
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 32, bold: true, color: COLOR, font: FONT }, paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 26, bold: true, color: COLOR2, font: FONT }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 23, bold: true, color: COLOR2, font: FONT }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } },
      { id: "Heading4", name: "Heading 4", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 21, bold: true, font: FONT }, paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 3 } },
      { id: "Heading5", name: "Heading 5", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 21, bold: true, italics: true, font: FONT }, paragraph: { spacing: { before: 120, after: 60 }, outlineLevel: 4 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bul", levels: [0, 1, 2, 3].map((lv) => ({ level: lv, format: LevelFormat.BULLET, text: ["•", "–", "▪", "·"][lv], alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360 * (lv + 1), hanging: 260 } } } })) },
      { reference: "num", levels: [0, 1, 2, 3].map((lv) => ({ level: lv, format: LevelFormat.DECIMAL, text: `%${lv + 1}.`, alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360 * (lv + 1), hanging: 300 } } } })) },
    ],
  },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 16838, orientation: PageOrientation.PORTRAIT }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: titulo, size: 16, color: "808080" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: `Confidencial · ${cliente ? cliente + " · " : ""}versión ${version} · Página `, size: 16, color: "808080" }),
      new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "808080" }),
      new TextRun({ text: " de ", size: 16, color: "808080" }),
      new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: "808080" }),
    ] })] }) },
    children: [...portada, new Paragraph({ children: [new PageBreak()] }), ...body],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, buf);
  console.log(`OK ${out} (${(buf.length / 1024 / 1024).toFixed(1)} MB, ${fig} figuras${missing ? `, ${missing} imágenes no encontradas` : ""})`);
  if (MARCA) console.log(`Marca: ${MARCA.fichero} (#${MARCA.color} en títulos y cabeceras de tabla)`);
  if (args.includes("--pdf")) {
    const r = aPdf(out);
    console.log(r.ok ? `PDF para revisar: ${r.pdf}` : `· ${r.msg}`);
  }
  process.exit(missing ? 1 : 0);
});
