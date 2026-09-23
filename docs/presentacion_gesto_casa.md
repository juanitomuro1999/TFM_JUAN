# Material para la presentación y defensa del TFM

> Recopilado el 2026-09-23, tras la sesión final de laboratorio. Reúne en un
> solo sitio las cifras, figuras y mensajes clave de todo el TFM, con el
> gesto "casa" (último resultado) destacado. Los vídeos de las pruebas los
> tiene el autor. Las figuras nuevas están en `docs/figuras/gesto_casa/` y se
> regeneran con `validation/plot_casa_session.py`.

## 1. Mensaje central (una frase)

Se ha convertido un robot que solo seguía a una persona en un asistente
móvil que **entiende gestos, construye y usa un mapa, navega de forma
autónoma y combina las dos cosas**: el usuario le pide con un gesto que
deje de seguirle y vuelva solo a casa.

## 2. Guion propuesto (≈15 min, 12-14 diapositivas)

| # | Diapositiva | Contenido | Figura / vídeo |
|---|---|---|---|
| 1 | Portada | Título, autor, tutor, UJI 2025-2026 | Foto del TurtleBot 2 |
| 2 | Punto de partida | Sistema previo: seguimiento por LiDAR, sin interacción, sin mapa | — |
| 3 | Objetivos | Los 6 objetivos específicos y su estado (§4 de este documento) | Tabla de objetivos |
| 4 | Plataforma | Kobuki + NUC + RPLIDAR A2M8 + cámara USB, ROS 2 Jazzy | Tabla de hardware del README |
| 5 | Arquitectura | 5 nodos + Nav2; `control_node` como árbitro | `docs/figuras/gesto_casa/arbitraje_velocidad.png` |
| 6 | Interacción por gestos | MediaPipe Pose, 3 gestos mutuamente excluyentes, confirmación por racha | `docs/figuras/gesto_casa/gestos_esquema.png` + vídeo de un gesto |
| 7 | Detección y fusión | Piernas por LiDAR (DBSCAN + features), fallback de pierna única y de fusión con el rumbo de la cámara | `validation/runs/fusion_track_20260625/figs/*` |
| 8 | Seguimiento y seguridad | Kalman 6 estados + PD angular, evasión con parada dura y maniobra de rodeo | Vídeo de evasión + tabla de §7.4ter |
| 9 | SLAM + Nav2 | Mapa del laboratorio con SLAM Toolbox, AMCL, 6/7 objetivos | Captura de RViz del mapa + vídeo de Nav2 |
| 10 | **Gesto "casa"** (lo nuevo) | Seguimiento → tejado → vuelta autónoma; estado HOMING | Vídeo de la toma final + `mapa_vueltas_casa.png` |
| 11 | Resultados del gesto "casa" | 9/11, 15.5 s, 0.27 m, cancelación en 20 ms, 0 falsos positivos | `metricas_homing.png` |
| 12 | Depurar con datos | Tres fallos del seguimiento encontrados en vivo, diagnosticados con los bags y corregidos en la misma sesión | `reenganche_antes_despues.png`, `cronologia_giros.png` |
| 13 | Limitaciones y trabajo futuro | LIDAR 2D (altura), localización junto a obstáculos, persona vs obstáculo, varios destinos | §6 de este documento |
| 14 | Conclusiones | 5 de 6 objetivos cumplidos (el 5, primer paso) + metodología reproducible | — |

Sugerencia para la demo en directo o en vídeo, en este orden:
**mano derecha → seguimiento con un giro → tejado → vuelta a casa**. Es la
escena que resume todo el trabajo en ~40 s.

## 3. Cifras clave (todas medidas en el robot real)

**Gesto "casa" (sesión final, 23/09)** — `docs/07_resultados.md` §7.4quinquies

| | |
|---|---|
| Vueltas a casa pedidas | 12 (6 desde reposo, 5 en pleno seguimiento, 1 cancelada a propósito) |
| Completadas | **9 de 11** (82%) |
| Tiempo gesto → en casa | **15.5 s** de media (11-21 s) |
| Error de llegada | **0.27 m / 8°** de media (tolerancia de Nav2: 0.25 m / 14°) |
| Cancelación con la mano izquierda | Nav2 confirma en **20 ms**, el robot se desplaza ~7 cm |
| Falsos positivos del gesto | **0** en ~4 min de gesticulación libre |
| Tejado de espaldas | 2/2 reconocido (más lento: la cabeza tapa una muñeca) |
| Causa de los 2 fallos | Localización (σ≈0.5 m) con el robot pegado a un obstáculo del mapa: Nav2 no planifica y el robot vuelve a reposo |

**Fixes del seguimiento en la misma sesión**

| Problema | Antes → después |
|---|---|
| El robot "se rallaba" (se enganchaba a reflejos pegados al chasis) | 119 → 0 avisos de obstáculo frontal |
| Se enganchaba a muebles detrás y giraba sobre sí mismo | 13.3% → 3.2% de posiciones detrás (y ningún reenganche detrás) |
| Al girar "se perdía y no sabía" | Ahora gira hacia el último lado visto: 4/4 en el sentido correcto |

**Resultados anteriores**

| Resultado | Cifra | Dónde |
|---|---|---|
| Fusión LiDAR-cámara (sin movimiento) | 100% detección, 0 pérdidas | §7.3 |
| Escenarios estabilizados (recta, curva, parada, corto, oclusión) | 100% detección en 7 de 10 tomas (≥97% en las demás salvo una contaminada), error angular medio 5-47° | §7.4bis |
| Evasión de obstáculos | De 4 contactos a 0 tras corregir `lin_factor` y añadir el rodeo (N=2 sin contacto con mobiliario sólido) | §7.4ter |
| Nav2 | 6/7 objetivos (trayectos de hasta ~8 m, uno esquivando un obstáculo no mapeado) | §7.4quater |
| Carga del NUC con todo en marcha | ~30% por núcleo (4 núcleos), sin saturación | `docs/decisiones.md` 2026-09-23 |

**Verificación sin robot (reproducible):** gestos 16/16 · máquina de estados
con Nav2 simulado 17/17 · reenganche 7/7 · giro de búsqueda 5/5.

## 4. Estado de los objetivos del TFM (`docs/01_introduccion.md` §1.2)

| # | Objetivo | Estado |
|---|---|---|
| 1 | Interacción por gestos | ✅ 3 gestos (seguir, parar/cancelar, casa) validados en el robot |
| 2 | Cartografía SLAM | ✅ Mapa del laboratorio con SLAM Toolbox |
| 3 | Navegación autónoma (Nav2) | ✅ AMCL + planificador + controlador, 6/7 objetivos |
| 4 | Fusión sensorial | ✅ LiDAR + rumbo de cámara, fallbacks de pierna única y fusión |
| 5 | Guiado de usuarios | 🟡 Primer paso: gesto "casa" (vuelta autónoma a un destino). Varios destinos: trabajo futuro |
| 6 | Códigos QR (exploratorio) | ⬜ No abordado |

## 5. Figuras disponibles

| Figura | Qué muestra |
|---|---|
| `docs/figuras/gesto_casa/arbitraje_velocidad.png` | Diagrama: quién manda en la velocidad de la base según el estado |
| `docs/figuras/gesto_casa/gestos_esquema.png` | Los 3 gestos y el comando que produce cada uno |
| `docs/figuras/gesto_casa/mapa_vueltas_casa.png` | Trayectorias de las vueltas a casa sobre el mapa real |
| `docs/figuras/gesto_casa/metricas_homing.png` | Duración y error de llegada de cada vuelta |
| `docs/figuras/gesto_casa/reenganche_antes_despues.png` | Dirección de la "persona" publicada antes/después del fix |
| `docs/figuras/gesto_casa/cronologia_giros.png` | Estados, ángulo de la persona y giros de búsqueda en una toma |
| `validation/runs/*/figs/*.png` | Distancia, ángulo, velocidades y trayectoria de las tomas de julio |
| `maps/mapa_laboratorio.pgm` | Mapa del laboratorio (SLAM Toolbox) |

## 6. Preguntas previsibles del tribunal

**¿Por qué el tejado y no otro gesto?** Es simétrico, así que se reconoce
igual de frente que de espaldas (en el seguimiento, la persona va de
espaldas al robot). No se parece a nada que se haga al caminar y evoca
"casa". Se descartaron los brazos cruzados (las muñecas se tapan) y "las dos
manos arriba" sin juntarlas (demasiado cerca de los gestos de una mano).

**¿Cómo se evita que el seguimiento y Nav2 se peleen por el robot?** Nav2
no publica directamente en la base. `control_node` recibe las dos fuentes y
solo reenvía la del estado activo. Hubo que tener en cuenta un detalle:
el nodo de seguimiento desactivado sigue publicando velocidad cero diez
veces por segundo, y reenviar eso habría anulado a Nav2.

**¿Por qué fallaron 2 de 11?** No fue el gesto ni la máquina de estados.
La estimación de posición del robot (AMCL, ±0.5 m) lo situaba dentro de la
zona de seguridad de un obstáculo del mapa, y el planificador no puede
salir de ahí. El robot volvió a reposo de forma segura. La mejora natural
sería una maniobra previa para "despegarse" del obstáculo antes de pedir
la ruta.

**¿Qué pasa si hay un obstáculo en el camino a casa?** Nav2 lo ve con el
LiDAR en su mapa de costes local y lo rodea. Se probó en la Sesión 7 con un
obstáculo que no estaba en el mapa.

**¿Cómo sabéis que los fixes no rompen lo que ya funcionaba?** Cada cambio
se verificó primero con el código real del nodo en un contenedor ROS 2,
con escenarios sintéticos que reproducen el fallo (antes) y comprueban el
comportamiento normal (después). Luego se comprobó en el robot en la misma
sesión.

**¿Por qué no se detecta la silla de patas finas?** El LiDAR 2D mide un
único plano a ~47 cm: ve las patas, no el asiento. Es una limitación del
sensor, confirmada con datos. La solución pasa por la cámara RGBD
disponible (Orbbec Astra) o un segundo LiDAR.

**¿Qué papel ha tenido la IA en el desarrollo?** Ver
`docs/03_herramientas_ia.md` (declaración de uso de herramientas de IA).

## 7. Limitaciones y trabajo futuro (para la diapositiva 13)

- Obstáculos por encima del plano del LiDAR 2D (sensor RGBD / segundo LiDAR).
- La evasión reactiva no distingue a la persona seguida de un obstáculo.
- Vuelta a casa pegado a obstáculos con localización imprecisa (maniobra
  previa de despegue, mejor ajuste de AMCL).
- El gesto de espaldas es más lento (umbral de visibilidad específico para
  el tejado).
- Objetivo 5 completo: varios destinos (un gesto o un QR por destino, lo que
  enlaza con el objetivo 6).
- Validación con más personas, entornos e iluminación.
