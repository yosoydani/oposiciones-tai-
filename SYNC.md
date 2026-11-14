# Sincronizar el temario con la web

El temario se escribe en docs de Claude Docs; la web guarda una copia en `data/temas/tNN.html` para funcionar sin Claude. Este procedimiento actualiza esa copia cuando un doc cambia. Se lanza a mano cuando el temario cambia: la sesión del temario apunta los temas cambiados en `temario/coordinacion.md` y se le pide a Claude «sincroniza el temario».

## Pasos

1. **Lista de docs.** Lee el doc del proyecto `temario/indice-temario.md` (herramienta Projects, `project_read`). Su tabla da, para cada tema, el id del doc y el id de la pestaña.
2. **Qué ha cambiado.** `data/temas/index.json` guarda el `rev` importado de cada tema. Para cada tema:
   - `mcp__Claude_Docs__read(ref={"object":"project","id":"<id del doc>"})` da el id del cuerpo (`files[0].content.id`).
   - `mcp__Claude_Docs__read(ref={"object":"node","id":"<id del cuerpo>"}, engine="prose", container={"kind":"project","id":"<id del doc>"}, payload={"kind":"view","sinceRev":<rev guardado>})` devuelve solo lo cambiado desde ese `rev`. Si la respuesta no trae bloques cambiados, el tema está al día: pasa al siguiente.
   - Un tema que no esté en `index.json` cuenta como cambiado.
3. **Importar los cambiados.** Para cada uno:
   - `mcp__Claude_Docs__export(container={"kind":"project","id":"<id del doc>"}, file="<id de la pestaña>", format="html", pictures="fit")`.
   - Si el resultado se guarda en disco («Output too large… saved to»), usa esa ruta.
   - Si llega entero en la conversación (pasa con los temas cortos), **no copies el base64 a mano**: mete erratas y lo corta un filtro. Exporta el tema en PDF (`format="pdf"`, `pictures="fit"`, `paper="a4"`), que siempre se guarda en disco, y conviértelo: `python3 -I scripts/pdf-a-html.py <archivo guardado> /tmp/tNN.html`. El conversor reconoce títulos, listas, negritas y tablas; comparado con una exportación HTML exacta coincide en más del 99,9 % del texto.
   - Después: `python3 -I scripts/importar-tema.py NN <archivo> <rev>`. El script comprueba el tamaño.
4. **Tema nuevo o renombrado.** Si el índice tiene un tema que no está en `data/temario.json`, o el título cambió, actualízalo ahí.
5. **Validar y publicar.**
   - `node scripts/build-manifest.mjs` tiene que terminar sin errores.
   - Si algo cambió, haz commit («Sincronizar temario: temas N, M») y push a `main`. GitHub Actions publica la web sola.
6. **Avisar.** En `temario/coordinacion.md` del proyecto, apartado «Sesión de la web», anota la fecha y los temas actualizados. Si un doc cambió su test de 20 preguntas, apúntalo también: el banco `tNN-propio.json` (preguntas 01-20) habrá que revisarlo a mano.

Si no cambió nada, no hagas commit ni toques `coordinacion.md`.
