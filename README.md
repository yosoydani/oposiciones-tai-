# Test TAI

Web estática para preparar la oposición TAI (Técnico Auxiliar de Informática del Estado). Sirve para hacer tests por tema o exámenes oficiales, corregidos como en el examen (acierto +1, fallo −1/3, blanco 0), con la explicación de cada respuesta y el nivel por tema.

No necesita servidor ni base de datos. Es HTML, JavaScript y archivos JSON, y se publica en GitHub Pages con cada push a `main`.

## Estructura

```
index.html                 La aplicación entera
data/temario.json          Los 33 temas, sus bloques y el enlace a cada tema escrito
data/bancos/*.json         Un archivo por test: el de cada tema o cada examen oficial
data/manifest.json         Lista de bancos. Lo genera el script; no se edita a mano
scripts/build-manifest.mjs Valida los bancos y genera el manifiesto
.github/workflows/deploy.yml  Valida y publica en GitHub Pages
```

## Añadir contenido

**Un tema escrito:** en `data/temario.json`, pon el enlace del tema en su campo `doc`.

**Un test:** crea `data/bancos/<id>.json` y haz push. El nombre del archivo es el id del banco. Usa `t11-propio.json` para el test propio del tema 11, o `oficial-2024-libre.json` para un examen oficial. No cambies el id de un banco ya publicado: el historial guarda las respuestas por `banco:pregunta`.

```json
{
  "titulo": "Tema 11 · test de autoevaluación",
  "fuente": "propio",
  "tema": 11,
  "convocatoria": null,
  "minutos": 15,
  "preguntas": [
    {
      "id": "01",
      "tema": 11,
      "enunciado": "Texto de la pregunta",
      "opciones": ["a", "b", "c", "d"],
      "correcta": 1,
      "explicacion": "Por qué es la b y por qué no las demás. Admite **negrita**."
    }
  ]
}
```

- `fuente`: `"propio"` o `"oficial"`. Los oficiales aparecen como examen completo en «Hacer test».
- `correcta`: índice desde 0 (0 = a, 1 = b…).
- `tema` en cada pregunta: obligatorio en los exámenes oficiales, que mezclan temas. Así cuentan en el nivel de cada tema.
- `minutos`: tiempo del examen completo. Si falta, se dan 45 segundos por pregunta.
- `"anulada": true`: la pregunta se oculta (preguntas anuladas por el tribunal). Así no hace falta borrarla.
- `convocatoria`: texto libre, por ejemplo `"2024 · libre"`.

Antes de hacer push puedes validar con `node scripts/build-manifest.mjs`. El workflow ejecuta lo mismo y no publica si hay errores.

## Probar en local

```
node scripts/build-manifest.mjs
python3 -m http.server 8000
```

y abre http://localhost:8000. Abrir `index.html` con doble clic no funciona, porque el navegador bloquea la lectura de los JSON.

## Progreso

Los resultados se guardan en el `localStorage` de cada navegador. Para pasarlos de un dispositivo a otro, usa Historial → Exportar progreso, y luego Importar progreso en el otro.
