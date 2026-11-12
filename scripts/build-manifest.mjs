// Genera data/manifest.json con todos los bancos de data/bancos/ y valida su formato.
// Uso: node scripts/build-manifest.mjs   (falla con código 1 si algún banco tiene errores)
import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const dir = "data/bancos";
const errores = [];
const temario = JSON.parse(readFileSync("data/temario.json", "utf8"));
const temas = new Set(temario.temas.map((t) => t.n));
const bancos = readdirSync(dir).filter((f) => f.endsWith(".json")).sort();

for (const f of bancos) {
  let b;
  try { b = JSON.parse(readFileSync(join(dir, f), "utf8")); }
  catch (e) { errores.push(`${f}: JSON no válido (${e.message})`); continue; }
  if (!b.titulo) errores.push(`${f}: falta "titulo"`);
  if (!["propio", "oficial"].includes(b.fuente)) errores.push(`${f}: "fuente" debe ser "propio" u "oficial"`);
  if (!Array.isArray(b.preguntas) || !b.preguntas.length) { errores.push(`${f}: no tiene preguntas`); continue; }
  const ids = new Set();
  b.preguntas.forEach((q, i) => {
    const at = `${f} pregunta ${q.id ?? i + 1}`;
    if (q.id == null) errores.push(`${at}: falta "id"`);
    else if (ids.has(String(q.id))) errores.push(`${at}: "id" repetido`);
    ids.add(String(q.id));
    const tema = q.tema ?? b.tema;
    const oficial = b.fuente === "oficial";
    // En los exámenes oficiales el tema puede faltar todavía (null).
    if (!(oficial && tema == null) && !temas.has(tema)) errores.push(`${at}: tema ${tema} no existe en temario.json`);
    if (!q.enunciado) errores.push(`${at}: falta "enunciado"`);
    if (!Array.isArray(q.opciones) || q.opciones.length < 2) errores.push(`${at}: "opciones" necesita al menos 2`);
    else if (q.anulada && q.correcta == null) { /* anulada sin respuesta */ }
    else if (!Number.isInteger(q.correcta) || q.correcta < 0 || q.correcta >= q.opciones.length) errores.push(`${at}: "correcta" debe ser un índice de 0 a ${q.opciones.length - 1}`);
    if (!q.explicacion && !q.anulada && !oficial) errores.push(`${at}: falta "explicacion"`);
  });
}

if (errores.length) { console.error(errores.join("\n")); process.exit(1); }
writeFileSync("data/manifest.json", JSON.stringify({ temario: "temario.json", bancos }, null, 2) + "\n");
console.log(`manifest.json: ${bancos.length} bancos`);
