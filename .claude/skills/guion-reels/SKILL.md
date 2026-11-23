---
name: guion-reels
description: Escribir y validar guiones/especificaciones de Reels (video vertical corto) en YAML con escenas cronometradas, locución, CTA, assets, verificación de evidencia y puerta de producción. Usar cuando el usuario pida un guion, especificación o revisión de un Reel o video corto, o la evaluación de resultados de Reels publicados.
---

# Guion y especificación de Reels

> NOTA DE INSTALACIÓN: esta skill se instaló a partir de un fragmento. Las secciones 1–5 y el inicio
> de la 6 (definición del esquema YAML, proceso creativo, etc.) no se proporcionaron. Los campos
> referenciados abajo (`duration_s`, `scenes[]`, `scenes[].voiceover`, `voiceover_full`, `cta`,
> `assets`, `verification`, `production_gate`) se usan tal como aparecen en el texto original.

## 6. Validación antes de entregar

- Los intervalos cubren exactamente de 0 a `duration_s`, consecutivos, sin huecos, superposiciones ni valores negativos.
- `voiceover_full` = unión exacta de `scenes[].voiceover` no vacíos, normalizando solo espacios. Si es mudo, `voiceover_full: ""`.
- La locución se puede decir en el tiempo asignado; texto legible y subtítulos sincronizables. Los segundos se asignan por carga informativa, no por regla de cortes.
- El primer cuadro funciona en silencio; respetar proporciones, áreas seguras, contraste, lectura y movimiento realizable.
- Si un tramo de más de 4 s no introduce información ni cambia un estado, revisar; permitir pausas intencionales con una función clara.
- Cada simulación que podría confundirse con evidencia real indica SIMULACIÓN o CONCEPTO en pantalla. El gancho se cumple antes del CTA.
- `cta` es `null` o una sola acción del Proyecto. No imponer CTA en cada Reel.
- `assets` solo enumera recursos confirmados; `verification` incluye afirmaciones, fuentes y bloqueos pertinentes; no dejar placeholders cuando hay datos.
- `production_gate = APTO_PARA_PRODUCCION` solo si las afirmaciones visibles están sustentadas o identificadas como simulación y la especificación es realizable; en caso contrario, `PENDIENTE_VERIFICACION`. Apto para producción NO significa revisado ni listo para publicar.

Si existe el archivo `scripts/validate_video_spec.py` y hay YAML guardado en disco con Python + PyYAML disponibles, ejecutar el validador para verificar tiempos y coherencia formal. No detener la tarea si no hay ejecución: validar manualmente.

## 7. Integridad de la evidencia, seguridad y publicación

Etiquetar la evidencia de cada escena: **REAL_VERIFICADO** (prueba documentada y autorizada), **DEMO** (funcionamiento probado en entorno conocido), **CONCEPTO** (ejemplo hipotético) o **PENDIENTE** (afirmación por verificar). No presentar simulaciones, cifras o testimonios como reales. Separar solicitud de cita, confirmación y acceso a disponibilidad. Evitar el uso de chats, nombres, contactos y datos de pacientes sin autorización.

- **Bloqueo de afirmaciones:** verificar la prueba antes de elegir un gancho que dependa de ella. Una afirmación material PENDIENTE debe reemplazarse, respaldarse o eliminarse antes de publicar. Si permanece, marcar el guion como borrador pendiente; nunca etiquetarlo publicable por conseguir una nota creativa alta.
- **Experimentos:** proponer método, fecha, denominador, definición de respuesta, criterios, permisos y límites antes de narrar resultados; afirmar cantidades solo después de comprobarlas. No suplantar clientes ni hacer spam.
- **Normativa y plataformas:** en contenidos sobre salud, privacidad, empleo, comisiones, precios y anuncios, usar hechos del Proyecto. Consultar fuentes oficiales actualizadas cuando se disponga de búsqueda y la afirmación lo exija; registrar fecha y fuente. Sin acceso a verificación, omitir afirmaciones legales específicas o marcar PENDIENTE, en lugar de inventar reglas.
- **Puerta final:** la skill evalúa el guion; la pieza final solo queda publicable tras revisar el render, subtítulos, assets, atribuciones y condiciones comerciales. No declarar publicación aprobada sin esa revisión.

## 8. Aprendizaje experimental

Si hay datos reales, comparar Reels semejantes por audiencia, duración y ventana de medición: retención inicial, reproducción promedio, abandonos por tramo, guardados y envíos por alcance, conversaciones y leads calificados. Separar atención de resultado de negocio. Evitar causalidad inventada con muestras pequeñas o distribuciones diferentes.

Convertir cada comparación en un ciclo: hipótesis falsable -> una variable principal -> medición definida antes de publicar -> registro -> siguiente prueba. Por ejemplo: "primer cuadro con una demostración frente a uno con pregunta, manteniendo el resto tan semejante como sea posible". Registrar qué cambió, qué no se sabe y qué se probará después. No garantizar mejoras ni universalizar una victoria aislada.

## Autocomprobación de alcance antes de responder

1. ¿Respondí la pregunta exacta o añadí calendario, reclutamiento, historias, herramientas o recomendaciones de modelos que no pidieron? Si hay extras, borrarlos.
2. ¿El guion afirma mostrar una grabación real o un resultado que no inspeccioné? Si ocurre, convertir la escena en CONCEPTO identificado o marcar un borrador pendiente y reescribir el gancho.
3. ¿Prometí un mensaje o entrega automática sin prueba del flujo? Si ocurre, cambiar o eliminar la CTA.
4. ¿Separé hechos del Proyecto de hipótesis y decisiones creativas? Si no, corregir.

## Cierre del proceso

La mejor pieza conserva valor incluso sin el logo, cumple lo prometido, evita afirmaciones inventadas, se puede producir con los medios disponibles y se limita a lo que el usuario pidió.
