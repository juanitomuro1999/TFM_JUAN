# LLM Council — Valoración de disposición para depósito/defensa del TFM

**Fecha:** 2026-10-14
**Pregunta original del usuario:** "askcouncil sobre el tfm y dame una valoración"

---

## Pregunta enmarcada (framed question)

Un Trabajo Fin de Máster (TFM) de robótica está siendo evaluado para decidir si está listo para
depositarse y defenderse ante un tribunal.

**PROYECTO:** "Seguimiento de personas y navegación autónoma en un robot móvil" (TurtleBot 2 + ROS 2
Jazzy), Juan Muñoz Rovira, Máster en Sistemas Inteligentes, Universitat Jaume I.

**ESTADO ACTUAL DE LA MEMORIA** (verificado directamente contra los archivos, no de memoria):
- 32 páginas, 333 párrafos, 10 tablas, 10 figuras.
- Estructura: Resumen → Cap.1 Introducción → Cap.2 Estado del arte → Cap.3 Arquitectura → Cap.4
  Implementación → Cap.5 Resultados → Cap.6 Conclusiones → Referencias (18, todas con DOI verificado
  contra Crossref/arXiv) → Apéndice A (uso de IA) → Apéndice B (diario de desarrollo). Versión
  paralela completa en inglés, verificada en sincronía con la española.
- Objetivos (texto literal de la memoria): 5 objetivos específicos. 4 marcados "Objetivo completado":
  interacción gestual, cartografía SLAM, navegación Nav2 (6 de 7 metas logradas), fusión LiDAR-cámara.
  El 5º (guiado a varios destinos) solo tiene "primer paso validado": el gesto "casa" logró 9 de 11
  vueltas (82%), 0,27 m de error medio de llegada, en UNA ÚNICA sesión de laboratorio. Un objetivo
  exploratorio (reconocimiento de habitaciones por código QR) quedó sin probar, declarado así
  explícitamente como pendiente.
- Conclusiones (texto literal, 3 párrafos): reconoce abiertamente que "la aportación de este TFM no
  es un algoritmo nuevo, sino hacer que [los módulos] funcionen juntos... con recursos limitados";
  cita explícitamente las "limitaciones de muestra" del capítulo de resultados como el límite real de
  esta validación.
- Historial: el tutor (Enric Cervera) revisó una versión anterior y pidió una lista larga de cambios
  (reestructurar capítulos, mover el estado del arte antes de la arquitectura, mover herramientas de
  IA y diario de desarrollo a apéndices, referencias al final como bibliografía, quitar la primera
  persona y el tono coloquial, arreglar figuras confusas, añadir contexto de hardware, estimación de
  costes, ejemplos con datos reales, desarrollar más las conclusiones). Todos esos puntos se aplicaron
  y se verificaron uno por uno releyendo el documento final.
- Limitaciones admitidas por escrito: muestra pequeña en varios escenarios, sin repeticiones
  sistemáticas en parada/oclusión, Nav2 validado en una sola sesión, objetivo 5 validado una sola vez
  con 11 intentos.
- Límite de páginas (25-30) autoimpuesto por el autor; sin confirmar si es norma oficial del máster.

**LO QUE SE PIDE:** un veredicto claro, distinguiendo "imprescindible antes de entregar" de "mejora
opcional". No dar por bueno nada solo porque el autor diga que ya está aplicado.

---

## Ronda 1 — Respuestas de los advisors

### The Contrarian
Veredicto: no se deposita todavía, pero no por el contenido — por dos agujeros administrativos que
nadie ha cerrado, y que son más peligrosos que cualquier limitación metodológica porque pueden tumbar
el depósito sin que el tribunal llegue a leer una sola línea.

(a) Imprescindible antes de entregar:
1. El límite de 25-30 páginas. El propio enunciado admite que no se sabe si es normativa oficial del
   máster o una cifra que el autor se puso a sí mismo. Si es norma oficial con tope duro, depositar en
   32 páginas es un fallo puramente formal, ajeno a la calidad del trabajo, y se resuelve en diez
   minutos consultando la normativa del TFM. No depositar sin cerrar esto primero.
2. La verificación de los cambios del tutor se hizo "releyendo el documento final" — pero ¿quién dio
   el visto bueno, el autor o el tutor? Autoverificación no es autorización. Si el procedimiento de la
   UJI exige firma expresa del tutor para depositar, eso tiene que estar confirmado, no asumido.

(b) No bloquea el depósito, pero sí la defensa — y aquí la honestidad del documento es un arma de
doble filo: el tribunal no lee el capítulo de limitaciones para premiar la sinceridad, lo lee para
saber dónde apretar. Las tres preguntas ya están servidas en bandeja: Nav2 validado en una sola
sesión, el objetivo 5 con 11 intentos totales, el QR nunca probado. Sin respuestas concretas y
ensayadas para esas tres, la defensa cojea aunque la memoria esté impecable. De propina: llamar
"objetivo completado" a algo validado una única vez sin repeticiones es una inconsistencia
terminológica barata de arreglar — cambiar "completado" por "validado" en Nav2 cuesta una palabra y
quita munición al tribunal.

### The First Principles Thinker
"¿Está lista la memoria?" da por hecho que la respuesta vive en el contenido. No es así: hay dos
huecos de proceso —no de contenido— y son los únicos bloqueantes reales.

Uno: el margen de 25-30 páginas es una referencia que el propio autor se puso; el texto mismo admite
que no está confirmado como norma del máster. Decidir si cortar de 32 a 30 es resolver el problema
equivocado. Lo imprescindible no es recortar — es una pregunta de dos minutos a secretaría o al
tutor. Si no hay norma oficial, la restricción se descarta entera; si existe, se ajusta maquetación,
nunca las secciones de limitaciones honestas, que son de lo más sólido del documento.

Dos, y más grave: el tutor, Enric Cervera, pidió una lista larga de cambios sobre una versión
anterior; el autor la aplicó y la verificó él mismo, uno por uno. Pero autoverificarse no es lo mismo
que la aprobación del tutor sobre ESTA versión final, y no hay constancia de que la haya dado. Esto
no es una alerta nueva: un consejo anterior (29-sep, mismo repo) ya señaló que el tutor debía dar el
visto bueno antes de defender, y semanas después sigue sin resolverse. Eso sí es imprescindible
cerrarlo.

Sobre el fondo: la muestra pequeña no es un defecto, es honestidad metodológica bien declarada;
"arreglarla" con más ensayos sería inventar trabajo que el TFM no exige. Pulir figuras o ampliar el
objetivo 5 es opcional y no debe retrasar nada.

### The Expansionist
Mientras otros miembros del consejo buscan qué falta, yo miro qué hay aquí que se está
infravalorando.

Este TFM no es "4 de 5 objetivos cumplidos": es SLAM, fusión LiDAR-cámara, Nav2 y reconocimiento
gestual funcionando integrados sobre hardware limitado (TurtleBot 2, no un robot de laboratorio
puntero). El propio texto lo dice: la aportación es hacer que los módulos funcionen juntos con
recursos escasos. Eso es exactamente lo que vale en robótica aplicada —más que un algoritmo nuevo
aislado— y debería ser el titular de la defensa, no una disculpa envuelta en limitaciones.

El objetivo 5 al 82% (9/11, 0,27 m de error) no es una debilidad que esconder: es una prueba de
concepto con número real, lista para convertirse en gancho de una publicación de workshop (IROS/ICRA
tienen tracks de sistemas aplicados con listones mucho más bajos que esto), en semilla de un TFG/TFM
de continuación, o en pieza de portfolio para entrevistas en el sector. Yo no la dejaría como
"limitación" en la conclusión: la convertiría en una sección de trabajo futuro con propuesta concreta
de escalado (más sesiones, el QR pendiente como siguiente hito).

La versión inglesa en paralelo, ya verificada, es un activo que casi nadie en un TFM explota: sube el
repo a GitHub con visibilidad internacional ahora, mientras está fresco.

Sobre las 32 páginas: ese límite de 25-30 ni siquiera está confirmado como norma oficial. No recortes
contenido honesto y verificado por una autoimposición dudosa.

Veredicto: lo único imprescindible es confirmar la norma real de páginas. Todo lo demás —incluyendo
pulir más las limitaciones— es amplificar una base sólida, no corregir un defecto.

### The Outsider
Leo esto sin saber nada del campo ni del historial del proyecto, así que señalo lo que le saltaría a
cualquier lector nuevo, no lo que ve un experto en robótica.

Lo único que de verdad podría bloquear esto: ¿el tutor ha visto y aprobado esta versión FINAL, con los
cambios ya aplicados, o solo dio el visto bueno conceptual a la lista de cambios sobre la versión
anterior? El texto dice que se verificó cada punto releyendo el documento final — pero no dice que el
tutor haya hecho esa misma relectura sobre el resultado concreto. Antes de depositar, confirma esa
aprobación explícita sobre el documento actual, no sobre la lista de peticiones. Sin eso, nada más de
lo que sigue importa.

Segundo, algo que un lector ingenuo detecta enseguida: mezclas "5 objetivos específicos" con un
"objetivo exploratorio" (QR) sin marcar con claridad, en el propio texto, cuál es compromiso formal y
cuál es extra. Un tribunal que lea rápido puede leer "QR sin probar" como un objetivo fallido en vez de
un bonus declarado. Es un arreglo de una frase en la introducción, pero evita una pregunta incómoda en
la defensa.

Tercero: el límite de 25-30 páginas es autoimpuesto, no verificado como norma oficial. No lo trates
como problema hasta confirmarlo con la normativa del máster — y si no es oficial, olvídalo: 32
páginas es razonable para este contenido, no es ni remotamente un TFM inflado.

Cuarto, lo que NO me preocupa pese a parecer alarmante a primera vista: el N=1 en casi todas las
validaciones (Nav2, "casa", oclusión). Cualquiera ve ahí una muestra pequeña, pero el documento ya lo
admite por escrito en conclusiones. Admitirlo es la jugada correcta: neutraliza la objeción antes de
que el tribunal la "descubra".

Veredicto: depositable. Imprescindible solo: confirmar el visto bueno del tutor sobre la versión
final, y aclarar la jerarquía de objetivos. Páginas, repeticiones extra, más referencias — todo
opcional, no bloqueante.

### The Executor
Veredicto: LISTO PARA DEPOSITAR. El contenido no es el problema.

Imprescindible (dos acciones de un día, ninguna de investigación/laboratorio):
1. Confirmar si el límite de 25-30 páginas es normativa oficial del máster o autoimpuesto. Verifiqué
   PROGRESO.md y docs/sesion_siguiente.md del repo (grep por "tutor", "visto bueno", "páginas",
   "límite") y no hay rastro de que ese límite esté documentado como norma ni de un visto bueno final
   del tutor sobre la versión actual — ambos puntos están abiertos sin dueño. Acción: correo a
   secretaría / normativa de TFM del Máster en Sistemas Inteligentes (UJI). Si es oficial, recortar
   2-7 páginas es edición de una tarde, no reescritura.
2. Conseguir el visto bueno explícito del tutor sobre ESTA versión final (el historial solo muestra
   que pidió cambios sobre una versión anterior, no que haya releído la final). Sin eso no hay
   depósito formal en la mayoría de másteres.

Todo lo demás ya pasó el filtro de ejecución y no se reabre: cambios del tutor aplicados y releídos
uno a uno, 18 referencias con DOI verificado, inglés sincronizado.

Las limitaciones admitidas por escrito (objetivo 5 con una sola sesión/n=11, QR sin probar) no son
trabajo pendiente sino honestidad ya declarada — no hay que generar más datos antes de depositar.

Opcional, no bloquea: pulir figuras, una frase más de trabajo futuro, preparar (habladas, no
escritas) las respuestas a las 3 preguntas obvias del tribunal.

---

## Ronda 2 — Revisión por pares (anonimizada A-E)

Mapeo real (revelado aquí, oculto durante la revisión): A=Contrarian, B=First Principles, C=Expansionist, D=Outsider, E=Executor.

### Revisor 1
1. Más fuerte: B. Ancla lo imprescindible en un hecho verificable: cita un consejo previo (29-sep,
   mismo repo) que ya exigió el visto bueno de Cervera sobre la versión final — confirmado: existe
   (`council-transcript-20260929.md`), y "tutor" sigue sin aparecer en PROGRESO.md ni
   sesion_siguiente.md. E también verifica, pero solo constata ausencia; B aporta el hecho concreto y
   su recurrencia.
2. Mayor punto ciego: C. Ignora por completo el visto bueno del tutor y recomienda depositar sin
   mencionarlo.
3. Qué se les escapó a los cinco: la trayectoria del límite de páginas — el 29-sep ya se recortó de 36
   a 28 para caber en el mismo margen 25-30; ahora está en 32, otra vez por encima. Ninguno pregunta
   qué se añadió desde entonces ni por qué no se recomprobó el recuento al editar.

### Revisor 2
1. Más sólida: B. Trata el aviso como reincidente, no nuevo — ese es el nivel de urgencia correcto.
2. Mayor punto ciego: C. Omite el visto bueno del tutor y recomienda "subir el repo a GitHub ahora"
   cuando ya está en GitHub. D confunde el n=11 del "gesto casa" con los casos N=1 (Nav2, oclusión).
3. Qué falló en las cinco: ninguna localizó el consejo del 29-sep, pese a que E sí grepeó el repo —
   no buscó dentro de memoria/2_Documentos_de_trabajo/council/.

   *(Verificación propia del revisor: confirma por grep que no hay menciones de "tutor"/"Cervera" en
   PROGRESO.md ni sesion_siguiente.md; confirma que el repo ya está en GitHub
   (github.com/juanitomuro1999/TFM_JUAN); confirma la imprecisión factual de D sobre "N=1 en casi
   todas las validaciones" cuando "casa" es n=11.)*

### Revisor 3
1. Más sólida: B — el consejo previo (línea 178 del transcript) ya decía literalmente que el tutor
   debía dar su visto bueno antes de defender, y sigue sin constar que lo haya dado. E también
   verificó con grep pero miró solo 2 archivos y no encontró esa carpeta de consejos.
2. Mayor punto ciego: C — ignora el visto bueno del tutor, que A, B, D y E señalan como el único
   bloqueo real.
3. Ninguna de las cinco revisó el historial del propio repo antes de opinar: el 29-sep ya se cortó de
   36 a 28 páginas tratando el margen 25-30 como vinculante; ahora está en 32 — se ha vuelto a superar
   un límite que antes sí importaba.

### Revisor 4
1. Más fuerte: B. Coincide con E en el diagnóstico, pero su dato clave es verificable: cita un consejo
   LLM previo que concluyó que el tutor debía dar el visto bueno. Confirmado leyendo ese archivo.
2. Mayor punto ciego: C. Ignora el riesgo de autorización del tutor y aconseja publicar en GitHub y
   presentarlo a IROS/ICRA sin plantear si eso exige su visto bueno antes. D también se equivoca en
   algo comprobable: dice que el QR no está "marcado con claridad" como exploratorio, pero
   docs/01_introduccion.md ya lo etiqueta como "Objetivo exploratorio", separado de los 5 específicos.
3. Lo que los cinco pasaron por alto: ninguno miró el repositorio más allá del brief. La carpeta
   memoria/4_Envios/2026-10-14/ muestra un envío fechado hoy mismo — la entrega al tutor ya está en
   marcha. E buscó en los archivos equivocados (diarios técnicos del robot, no del proceso de la
   memoria).

   *(Nota adicional del revisor, fuera de las 200 palabras: en memoria/1_Entrega_profesor/ hay un
   archivo "TFM_Memoria_reducida corrección marina.docx" — una pasada de corrección de Marina que no
   aparecía en el brief dado al consejo.)*

### Revisor 5
1. Más sólida: B. Separa bien proceso de contenido, y su punto fuerte no es especulación: contrastado
   con el repo, es exacto. El consejo previo del 29-sep ya exigió el visto bueno de Cervera, y ni
   PROGRESO.md ni sesion_siguiente.md muestran que se haya resuelto.
2. Mayor punto ciego: C. No menciona el visto bueno del tutor ni una vez, y repite casi palabra por
   palabra lo que el consejo del 29-sep ya identificó como su propio mayor punto ciego entonces:
   convertir n=11/82% en gancho de publicación en vez de tratarlo con cautela.
3. Lo que los cinco ignoraron: ninguno consultó el consejo del 29-sep, que ya ordenaba explícitamente
   "re-chequear el límite de páginas tras añadir contenido" — chequeo que nunca se hizo (28→32
   páginas). Las 32 páginas no son un misterio nuevo: son el coste previsto de seguir aquel consejo
   sin cerrar el ciclo.

---

## Verificación directa contra el repositorio (hecha por el orquestador, no por un sub-agente)

Varios revisores de pares fueron más allá del texto y comprobaron el repo por su cuenta. Dado que esto
cambiaba el veredicto de forma material, se verificó directamente antes de incluirlo en la síntesis:

- **`memoria/2_Documentos_de_trabajo/council/council-transcript-20260929.md` existe** y contiene,
  literalmente:
  - Línea 13: *"Ayer se redujo la memoria de trabajo (`TFM_Memoria_reducida.docx`) de 36 a 28 páginas
    para caber en el margen de 25-30."* — el margen 25-30 SÍ se trató como vinculante entonces.
  - Línea 178: *"**The tutor (Enric Cervera) should sign off** on adding a new validated result days
    before the defense — this is new academic content, not just a formatting fix."*
  - Línea 179: *"**Yesterday's 36→28 page cut was never rechecked** for collateral damage..."*
  - Línea 191: *"Do the diagram-to-image conversion last, and re-check the total page count stays
    within 25-30 afterward."*
- **`PROGRESO.md`**: grep de `tutor|Cervera|visto bueno` → **0 resultados**. Las únicas coincidencias
  de "límite" son sobre el alcance físico del LiDAR, sin relación con páginas o el tutor.
- **`docs/01_introduccion.md`, línea 55**: el objetivo QR SÍ está etiquetado aparte como *"6.
  Objetivo exploratorio"*, separado de los 5 objetivos específicos — contradice el punto del Outsider
  (Response D) sobre falta de jerarquía clara, al menos en el capítulo fuente.
- **`git log`**: el último commit del repositorio es del 2026-07-31. No hay ningún commit posterior
  (incluyendo nada de la reestructuración de Enric, el consejo del 29-sep, ni los cambios de esta
  semana) — todo ese trabajo lleva más de dos meses sin commitear. No hay evidencia en git de que una
  defensa haya tenido lugar en septiembre.

Esta verificación confirma que la advertencia de B/D/E no es una sospecha nueva, sino la misma
advertencia que un consejo anterior sobre este mismo repositorio ya hizo hace dos semanas — y que
sigue abierta.

---

## Síntesis del Chairman

### Dónde coincide el consejo
Los 5 advisors, de forma independiente, no señalaron ningún defecto de contenido, rigor técnico o
redacción como bloqueante. La reestructuración pedida por Enric, la verificación de DOIs, la
sincronización ES/EN — todo eso pasa el filtro. Los 5 coinciden también en que la muestra pequeña (n=11
en el objetivo 5, sesión única de Nav2, sin repeticiones en oclusión/parada) no es un defecto que
corregir antes de depositar, sino honestidad metodológica ya declarada por escrito en las
conclusiones, y así debe quedarse. Los 5 señalan el límite de páginas como algo a verificar, no a
resolver recortando por la vía rápida. Y 3 de 5 (Contrarian, First Principles, Executor) califican
explícitamente el visto bueno del tutor sobre la versión final como imprescindible; los otros 2
(Expansionist, Outsider) lo tratan como lo único que de verdad podría bloquear, aunque no lo
prioricen tan alto.

### Dónde choca el consejo
Contrarian y Executor dicen "no depositar sin cerrar esto" (puerta dura); Expansionist y Outsider
dicen "depositable ya, esto se confirma en paralelo" (puerta blanda). La diferencia real es de
secuencia, no de contenido: todos coinciden en qué hay que cerrar, discrepan en si bloquea el envío o
puede ir a la vez. Más de fondo: Expansionist propone reencuadrar el objetivo 5 como gancho de
publicación (IROS/ICRA) y subir el repo a GitHub ya — pero la verificación directa muestra que el
repo ya está en GitHub, y que convertir un resultado de n=11 en gancho de publicación es exactamente
el error que el consejo anterior (29-sep) ya señaló como su propio mayor punto ciego. Este consejo
estuvo a punto de repetirlo.

### Puntos ciegos que el consejo detectó
Este es el hallazgo central de esta sesión, y pesa más que cualquier opinión individual: cuatro de los
cinco revisores de pares, sin que se les pidiera, fueron más allá del texto entregado y comprobaron el
propio repositorio — y encontraron un consejo LLM anterior sobre este mismo TFM, de hace exactamente
dos semanas. Verificado directamente, línea por línea: el 29 de septiembre la memoria se recortó
deliberadamente de 36 a 28 páginas "para caber en el margen de 25-30" — ese margen sí se trató como
restricción real y vinculante entonces, no es una cifra arbitraria que ahora se pueda descartar sin
más. Ese mismo consejo ordenó explícitamente re-chequear el recuento de páginas tras cualquier cambio,
y señaló que el tutor debía dar su visto bueno sobre nuevo contenido validado antes de la defensa.
Hoy, dos semanas y una reestructuración completa después, la memoria está en 32 páginas —de nuevo por
encima del margen que antes sí se respetó— y no hay ningún rastro en los archivos de seguimiento del
proyecto de que el tutor haya dado su visto bueno sobre la versión final, ni de que se haya repetido
el recuento de páginas. Esto no es una sospecha nueva: es una advertencia que ya se hizo sobre este
mismo trabajo hace dos semanas, y que sigue sin cerrarse.
Punto menor: el Outsider dijo que el objetivo QR no estaba claramente separado de los 5 objetivos
específicos; verificado en docs/01_introduccion.md, sí lo está ("6. Objetivo exploratorio"). Ese punto
concreto no aplica, al menos en el capítulo fuente.

### La recomendación
Depositable en contenido, no depositable en proceso — todavía. La memoria en sí (estructura, rigor,
redacción, honestidad sobre limitaciones) no es el obstáculo y no necesita más trabajo de fondo. El
obstáculo real son dos preguntas administrativas, ambas ya identificadas hace dos semanas por un
consejo anterior sobre este mismo repositorio, y ninguna resuelta todavía: (1) si el límite de 25-30
páginas es una norma oficial del máster o una referencia propia —ya se trató como vinculante una vez
(recorte 36→28), no se puede seguir tratando como "a confirmar" indefinidamente—; y (2) si Enric
Cervera ha visto y aprobado esta versión final, con toda la reestructuración ya aplicada, o solo
aprobó conceptualmente la lista de cambios sobre la versión anterior. Autoverificación no sustituye la
aprobación del tutor. Hasta que esas dos respuestas existan, depositar es prematuro — no porque el
documento esté mal, sino porque nadie fuera de este proceso ha confirmado que cumple esas dos
condiciones.

### Lo primero que hay que hacer
Escribir hoy a Enric Cervera adjuntando la versión final y pidiendo dos cosas explícitas: (1)
confirmación de que esta versión incorpora todo lo que pidió y está lista para depositar, y (2) si
sabe si el límite de páginas del máster es una norma dura. Es la única acción que cierra ambos
bloqueantes a la vez, y es la misma persona quien puede responder a los dos.
