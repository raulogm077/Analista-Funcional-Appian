#!/usr/bin/env node
/*
 * Genera el DDF en Word (.docx) a partir del ddf.md.
 *
 * Uso: node ddf_docx.js ddf.md -o DDF-<proyecto>-v1.0.docx [--titulo "…"] [--cliente AENA] [--version v1.0]
 *
 * - Portada, índice (se actualiza al abrir en Word: «Actualizar tabla»), encabezado y pie con
 *   confidencialidad, versión y número de página.
 * - Markdown admitido: títulos #…#####, párrafos con **negrita**, *cursiva* y `código`, listas
 *   (- y 1.), tablas, citas (>) como recuadro, líneas ---, imágenes ![pie](ruta.png).
 * - Los bloques ```mermaid se omiten si les sigue su imagen (el PNG de render_mermaid.py); si no,
 *   se incluye el código en monoespaciado con el aviso «Diagrama pendiente de renderizar».
 * - Figuras numeradas: «Figura N — pie», en el orden del documento.
 * - Callouts: párrafos que empiezan por ⚠️, 🔴 o contienen «CONTRADICCIÓN» van en recuadro de color.
 *
 * Requiere Node.js y el paquete docx (npm install docx si no está).
 */
const fs = require("fs");
const path = require("path");
let D;
try { D = require("docx"); } catch (e) {
  console.error("Falta el paquete docx de Node: npm install docx"); process.exit(2);
}
const { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, ShadingType,
  ImageRun, AlignmentType, TableOfContents, Header, Footer, PageNumber, LevelFormat, BorderStyle, PageBreak,
  PageOrientation } = D;

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const src = args.find((a, i) => !a.startsWith("--") && !(i > 0 && args[i - 1].startsWith("-")) && a !== "-o");
if (!src) { console.error("Uso: node ddf_docx.js ddf.md -o salida.docx"); process.exit(2); }
const out = opt("-o", src.replace(/\.md$/, ".docx"));
const md = fs.readFileSync(src, "utf8").replace(/\r\n/g, "\n");
const base = path.dirname(path.resolve(src));
const firstH1 = (md.match(/^# (.+)$/m) || [, "Documento de Diseño Funcional"])[1];
const titulo = opt("--titulo", firstH1);
const cliente = opt("--cliente", (md.match(/^- Cliente: (.+)$/m) || [, ""])[1]);
const version = opt("--version", ((md.match(/^- Versión: (v[\d.]+)/m) || [, "v1.0"])[1]));

const FONT = "Calibri", MONO = "Consolas";
const PAGE_W = 11906, MARGIN = 1134, CONTENT_W = PAGE_W - 2 * MARGIN; // A4, márgenes 2 cm

function runs(text, base = {}) {
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
        shading: i === 0 ? { type: ShadingType.CLEAR, fill: "1F3864", color: "auto" } : undefined,
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
const body = [];
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
    if (m[1].length === 1 && !skippedFirstH1) { skippedFirstH1 = true; i++; continue; } // va en la portada
    const lvl = Math.min(m[1].length, 6);
    if (lvl === 2 && body.length) body.push(new Paragraph({ children: [new PageBreak()] }));
    body.push(new Paragraph({ heading: HL[lvl], keepNext: true, children: runs(m[2].replace(/\*\*/g, "")) }));
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
      body.push(new Paragraph({ numbering: { reference: num ? "num" : "bul", level: Math.min(Math.floor(ind / 2), 3), instance: listInstance }, spacing: { after: 40 }, children: runs(li.replace(/^\s*([-*]|\d+\.) /, "")) }));
      i++;
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
  new Paragraph({ spacing: { before: 3000, after: 300 }, children: [new TextRun({ text: "Documento de Diseño Funcional", size: 28, color: "595959" })] }),
  new Paragraph({ spacing: { after: 400 }, children: [new TextRun({ text: titulo.replace(/^DDF\s*·\s*/, ""), bold: true, size: 48, color: "1F3864" })] }),
  new Paragraph({ children: [new TextRun({ text: `Cliente: ${cliente}`, size: 24 })] }),
  new Paragraph({ children: [new TextRun({ text: `Versión: ${version} — Borrador para validación`, size: 24 })] }),
  new Paragraph({ children: [new TextRun({ text: `Fecha: ${new Date().toLocaleDateString("es-ES")}`, size: 24 })] }),
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Índice")] }),
  new TableOfContents("Índice", { hyperlink: true, headingStyleRange: "1-3" }),
  new Paragraph({ children: runs("*(Si el índice aparece vacío, en Word: clic derecho sobre él → Actualizar campos.)*", { size: 16, color: "808080" }) }),
];

const doc = new Document({
  creator: "appian-analisis-funcional",
  title: titulo,
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 32, bold: true, color: "1F3864", font: FONT }, paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 26, bold: true, color: "2F5597", font: FONT }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 23, bold: true, color: "2F5597", font: FONT }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } },
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
      new TextRun({ text: `Confidencial · ${cliente} · ${version} · Página `, size: 16, color: "808080" }),
      new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "808080" }),
      new TextRun({ text: " de ", size: 16, color: "808080" }),
      new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: "808080" }),
    ] })] }) },
    children: [...portada, new Paragraph({ children: [new PageBreak()] }), ...body],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(out, buf);
  console.log(`OK ${out} (${(buf.length / 1024 / 1024).toFixed(1)} MB, ${fig} figuras${missing ? `, ${missing} imágenes no encontradas` : ""})`);
  process.exit(missing ? 1 : 0);
});
