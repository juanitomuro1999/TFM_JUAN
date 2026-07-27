# Graph Report - TFM_JUAN  (2026-07-27)

## Corpus Check
- 55 files · ~454,040 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 642 nodes · 795 edges · 62 communities (56 shown, 6 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2ca37c21`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- DetectionNode
- UserInterfaceNode
- TrackingNode
- UserInterfaceNode
- FusionGateSim
- ControlNode
- SLAMNode
- ControlNode
- ControlNode
- VisualDetectionNode
- SingleLegGateSim
- TrackingNode
- plot_run.py
- PersonFollower
- CollisionHandlingNode
- bag_to_csv.py
- launch_robot_pedestrian.bash
- launch_robot.bash
- record_run.sh
- session_start_context.sh
- continue_session.sh
- sync_nuc.sh
- Decisiones de diseño
- Capítulo 5 — Estado del arte
- Julio 2026
- TFM — Desarrollo e implementación de un sistema de seguimiento de personas sobre un robot móvil (Parte 2 – Extensión)
- Capítulo 6 — Implementación
- Prompt — Próxima sesión
- Capítulo 2 — Arquitectura del sistema
- Sesión 2026-07-13 (lab) — Fix de CPU, causa raíz de la oscilación FSM, y bug de convenio angular en tracking_node
- Sesión 2026-06-17
- Diario de progreso — TFM Person Follower
- Sesión 2026-07-15 (lab, en curso) — Puerto USB kobuki/rplidar intercambiado + diagnóstico del "gira al lado contrario"
- Sesión 2026-07-21 (lab, Sesión 4) — Bug de seguridad confirmado y corregido: evasión de obstáculos vigilaba el sector trasero
- Cambios aplicados
- Sesión 2026-06-25
- Sesión 2026-07-08
- Sesión 2026-07-09 (lab, tarde) — Gesto real funcionando + fixes en vivo
- Pendiente — próximas sesiones
- Sesión 2026-07-22 (lab, Sesión 5, continuación 4) — reintentos de `obstaculo`: lin_factor corregido para parar de verdad + maniobra de rodeo
- Sesión 2026-07-17 (trabajo de escritorio, sin robot) — Capítulo 6 redactado + hallazgo de signo confirmado + nuevo hallazgo (sector de obstáculos) sin verificar
- Sesión 2026-07-16 (trabajo de escritorio, sin robot) — Capítulo 5 redactado + fix del fallback de fusión diseñado y verificado sintéticamente
- Sesión 2026-07-22 (lab, Sesión 5, continuación 3) — offset LIDAR medido, obstacle_threshold subido, 10 repeticiones de validación
- legacy_previo/README.md

## God Nodes (most connected - your core abstractions)
1. `Decisiones de diseño` - 34 edges
2. `DetectionNode` - 24 edges
3. `UserInterfaceNode` - 23 edges
4. `UserInterfaceNode` - 22 edges
5. `ControlNode` - 19 edges
6. `Diario de progreso — TFM Person Follower` - 19 edges
7. `ControlNode` - 18 edges
8. `ControlNode` - 18 edges
9. `TrackingNode` - 13 edges
10. `VisualDetectionNode` - 13 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (62 total, 6 thin omitted)

### Community 0 - "DetectionNode"
Cohesion: 0.10
Nodes (12): ndarray, dbscan_labels(), DetectionNode, main(), Node, DBSCAN auto-contenido (sin sklearn) sobre puntos 2D.      Devuelve un array de, Filtro previo y duro, compartido por `_gate_by_continuity` (pares de         pi, Exige `continuity_confirm_frames` scans consecutivos con el mismo         candi (+4 more)

### Community 1 - "UserInterfaceNode"
Cohesion: 0.12
Nodes (7): main(), Bool, Float32MultiArray, Node, Point, String, UserInterfaceNode

### Community 2 - "TrackingNode"
Cohesion: 0.11
Nodes (11): LaserScan, KalmanTracker, main(), Bool, Node, Point, Actualiza con nueva observación.         Retorna la posición filtrada (x, y)., Predicción de posición a dt segundos en el futuro. (+3 more)

### Community 3 - "UserInterfaceNode"
Cohesion: 0.13
Nodes (7): main(), Bool, Float32MultiArray, Node, Point, String, UserInterfaceNode

### Community 4 - "FusionGateSim"
Cohesion: 0.21
Nodes (15): check(), FusionGateSim, Reproduce el hallazgo de 2026-07-13 (docs/decisiones.md): con     _gate_by_cont, Mismo escenario (mueble a 1.34m tras 0.92s), pero con el mecanismo     NUEVO (_, Un cluster espurio de ruido que NO se repite en el mismo sitio entre     scans, Una persona real, cuya posición se repite de forma consistente entre     scans, Con continuity_confirm_frames=1 (valor por defecto en config.yaml), el     comp, _gate_by_continuity (camino de pares de piernas) no debe cambiar de     comport (+7 more)

### Community 5 - "ControlNode"
Cohesion: 0.19
Nodes (3): ControlNode, main(), Node

### Community 6 - "SLAMNode"
Cohesion: 0.13
Nodes (10): main(), Node, Publica un Marker (círculo) para la persona detectada., Publica el mapa actualizado basado en los datos del LIDAR., Publica la transformación estática entre 'map' y 'odom'., Inicializa el suscriptor para manejar el cierre del sistema., Callback para manejar la notificación de cierre del sistema., Callback para recibir la posición de la persona detectada. (+2 more)

### Community 7 - "ControlNode"
Cohesion: 0.20
Nodes (3): ControlNode, main(), Node

### Community 8 - "ControlNode"
Cohesion: 0.19
Nodes (3): ControlNode, main(), Node

### Community 9 - "VisualDetectionNode"
Cohesion: 0.18
Nodes (7): main(), Node, Detecta personas en el frame usando HOG.         Solo analiza la franja central, Detecta persona mediante MediaPipe Pose.         Retorna True si hay ≥ pose_min, Gesto de inicio: mano DERECHA levantada por encima del hombro.         Gesto de, Nodo de detección visual.      Modo HOG  (por defecto): usa el descriptor HOG, VisualDetectionNode

### Community 10 - "SingleLegGateSim"
Cohesion: 0.21
Nodes (12): check(), Un clúster de pierna espurio (falso positivo geométrico, p.ej. una pata     de, Con continuity_confirm_frames=3, una pierna real y consistente debe     confirm, Documental: esta rama solo se alcanza en detect_person cuando     candidate_pos, Réplica mínima del estado y la lógica de gating de DetectionNode     relevante, Un `scan`: dado el centroide de cada clúster ya clasificado como         pierna, Reproduce el caso diagnosticado el 2026-07-15: al girar, una pierna     ocluye, scenario_confirm_frames_mayor_que_uno_exige_consistencia() (+4 more)

### Community 11 - "TrackingNode"
Cohesion: 0.20
Nodes (3): main(), Node, TrackingNode

### Community 12 - "plot_run.py"
Cohesion: 0.22
Nodes (13): load_csv(), load_xy(), main(), position_jumps(), % de muestras de vang saturadas (overall) y restringido a instantes     con pos, Tiempos relativos al primer instante (s)., (t_bag, x, y) ordenados por tiempo, descartando filas invalidas., % de saltos entre muestras consecutivas de posicion cruda > threshold (m). (+5 more)

### Community 13 - "PersonFollower"
Cohesion: 0.27
Nodes (3): main(), PersonFollower, Node

### Community 14 - "CollisionHandlingNode"
Cohesion: 0.36
Nodes (3): CollisionHandlingNode, main(), Node

### Community 15 - "bag_to_csv.py"
Cohesion: 0.47
Nodes (5): SequentialReader, main(), open_reader(), Convierte un builtin_interfaces/Time a segundos float., stamp_to_s()

### Community 16 - "launch_robot_pedestrian.bash"
Cohesion: 0.50
Nodes (3): launch_robot_pedestrian.bash script, ROS_LOCALHOST_ONLY, WEBOTS_HOME

### Community 40 - "Decisiones de diseño"
Cohesion: 0.04
Nodes (41): Antes de tocar nada, lee esto en orden, CLAUDE.md — TFM_JUAN (Person-Following System), Entorno de ejecución — importante, Flujo de trabajo de esta sesión, Qué es este proyecto, Reglas de este proyecto, Retomar la sesión sin fricción, 2026-06-04 — Reescalar parámetros de tracking para eliminar oscilación angular (+33 more)

### Community 41 - "Capítulo 5 — Estado del arte"
Cohesion: 0.05
Nodes (35): 1.1 Contexto y motivación, 1.2 Objetivos del TFM, 1.3 Alcance y limitaciones, 1.4 Planificación, 1.5 Estructura de este documento, Capítulo 1 — Introducción y planteamiento del problema, Objetivo general, Objetivos específicos (+27 more)

### Community 42 - "Julio 2026"
Cohesion: 0.06
Nodes (31): 15 de julio — El robot "giraba al lado contrario": encontrado y corregido el signo invertido del control angular, 16 de julio — Capítulo 5 redactado y fix del fallback de fusión diseñado (trabajo de escritorio), 17 de julio — Capítulo 6 redactado y hallazgo del signo revisado (trabajo de escritorio), 17 de junio — Cámara HOG, MediaPipe y módulo de interacción por gestos, 21 de julio (continuación) — Sesión 5: dos colisiones reales al repetir el escenario de obstáculo, por dos causas distintas, 21 de julio — Sesión 4 de laboratorio: sector de obstáculos corregido, hueco de detección al girar resuelto, gate de continuidad afinado con mobiliario real, 21 de mayo (continuación) — Corrección del movimiento a tirones, 21 de mayo (continuación) — Mapa del laboratorio (+23 more)

### Community 43 - "TFM — Desarrollo e implementación de un sistema de seguimiento de personas sobre un robot móvil (Parte 2 – Extensión)"
Cohesion: 0.07
Nodes (25): 3.1 Declaración de uso, 3.2.1 Asistente de IA conversacional (Claude — Anthropic), 3.2.2 Herramientas de autocompletado de código, 3.2.3 Motores de búsqueda y documentación, 3.2 Herramientas utilizadas, 3.3 Reflexión sobre el uso ético de la IA, 3.4 Estimación del impacto, Capítulo 3 — Uso de herramientas de inteligencia artificial (+17 more)

### Community 44 - "Capítulo 6 — Implementación"
Cohesion: 0.08
Nodes (25): 6.10 Despliegue: lanzamiento y sincronización al robot, 6.11 Código no registrado en `setup.py`, 6.1 Introducción y alcance, 6.2 Estructura del paquete y gestión de configuración, 6.3.1 Fallback de fusión y su confirmación dedicada, 6.3 `detection_node` — clustering, features de pierna y gating, 6.4 `visual_detection_node` — detector dual y gestos, 6.5 `tracking_node` — Kalman de 6 estados, control PD y evasión (+17 more)

### Community 45 - "Prompt — Próxima sesión"
Cohesion: 0.12
Nodes (17): Arreglar confirmación en el fallback de fusión (nuevo, 2026-07-13) — ✅ diseño+verificación sintética hechos 2026-07-16, validado en vivo 2026-07-21, Arreglar la pérdida de detección conjunta al girar — ✅ implementado y validado 2026-07-21 (Sesión 4), Calendario estimado (añadido 2026-07-17), Checklist de cierre de sesión, Estado heredado de la sesión 2026-07-09, tarde (histórico, ya verificado en sesiones posteriores), Estado heredado de la sesión 2026-07-13 (no repetir, solo verificar), Estado heredado de la sesión 2026-07-15 (no repetir, solo verificar), Estado heredado de la sesión 2026-07-21 (Sesión 4 — no repetir, solo verificar) (+9 more)

### Community 46 - "Capítulo 2 — Arquitectura del sistema"
Cohesion: 0.12
Nodes (16): 2.1 Visión general, 2.2 Diagrama de nodos y topics, 2.3.1 `detection_node`, 2.3.2 `visual_detection_node`, 2.3.3 `tracking_node`, 2.3.4 `control_node`, 2.3.5 `collision_handling_node`, 2.3.6 `user_interface_node` (+8 more)

### Community 47 - "Sesión 2026-07-13 (lab) — Fix de CPU, causa raíz de la oscilación FSM, y bug de convenio angular en tracking_node"
Cohesion: 0.18
Nodes (11): Addendum (misma sesión, hora extra): fix del desfase de π implementado y confirmado, Causa raíz de la oscilación FSM: reproducida en vivo, no era (solo) lo que se sospechaba, Confirmación adicional del fix de π con movimiento real (19s, TRACKING activo), Datos recogidos (bags en el NUC, no copiados al repo por peso), Fix de rendimiento: detection_node saturaba un core de CPU (93.7%), Hallazgo mayor: tracking_node no aplica el mismo convenio angular que detection_node, Investigación descartada: posible bug de izquierda/derecha en tracking_node, Objetivo: Sesión 2 del plan (FSM oscilando + near_gain + recalibrar cámara) (+3 more)

### Community 48 - "Sesión 2026-06-17"
Cohesion: 0.22
Nodes (9): Bug de hardware: RPLIDAR con timeout de conexión, Bug de software: kobuki_node no arrancaba con los 3 workspaces sourceados, Causa raíz de la cámara — NO era el umbral, Estado al inicio, MediaPipe instalado offline (mejora sobre HOG), Módulo de interacción por gestos implementado (Objetivo específico 1 del TFM), Pendiente de refinar (NO tocar la lógica de tracking todavía — anotado para sesión dedicada), Pendiente verificado hoy (+1 more)

### Community 49 - "Diario de progreso — TFM Person Follower"
Cohesion: 0.22
Nodes (9): Diario de progreso — TFM Person Follower, Objetivo: reproducibilidad de las métricas de saltos/saturación (Sesión 3 de `docs/sesion_siguiente.md`), Pendiente para la próxima sesión de lab (Sesión 1: cámara), Sesión 2026-07-09 (trabajo de escritorio, sin robot), Sesión 2026-07-21 (lab, Sesión 5, continuación 2) — Segundo golpe, distinto del primero: la evasión frenó a tiempo pero el margen fue insuficiente, Sesión 2026-07-21 (lab, Sesión 5, continuación) — El robot choca con una silla pese al sector ya corregido: límite físico del LIDAR 2D, Sesión 2026-07-22 (lab, Sesión 5, continuación 5) — CONFIRMADO: la silla fina sigue sin detectarse (5º contacto real), límite de sensor cerrado, Sesión 2026-07-23 (lab, Sesión 6) — `obstaculo` N=2 confirmado sin contacto + Nav2 fase A: localización arranca pero no converge tras el primer ciclo (+1 more)

### Community 50 - "Sesión 2026-07-15 (lab, en curso) — Puerto USB kobuki/rplidar intercambiado + diagnóstico del "gira al lado contrario""
Cohesion: 0.25
Nodes (8): Arranque: kobuki y RPLIDAR habían intercambiado de puerto USB, CAUSA RAÍZ REAL encontrada y corregida: signo invertido en el PD angular, Extra (adelanto de la Sesión 5): 8 grabaciones para el Capítulo 7, Objetivo 1 (confirmar fix de π con movimiento real): fix de π confirmado, pero aparece un problema más grave, Objetivo 2 (near_gain): aislado con el signo ya corregido — comportamiento sano, Objetivo 3 (recalibrar cámara SPCA2650): cerrado sin cambios — no hace falta, Objetivo: Sesión 3 del plan (confirmar fix de π con movimiento + near_gain + recalibrar cámara), Sesión 2026-07-15 (lab, en curso) — Puerto USB kobuki/rplidar intercambiado + diagnóstico del "gira al lado contrario"

### Community 51 - "Sesión 2026-07-21 (lab, Sesión 4) — Bug de seguridad confirmado y corregido: evasión de obstáculos vigilaba el sector trasero"
Cohesion: 0.29
Nodes (7): Arranque de sesión, Fallback de pierna única para el hueco de detección al girar (objetivo principal de la sesión), Gate de continuidad estresado con mobiliario denso — continuity_confirm_frames 1→3, Hallazgo del 17/07 verificado y corregido: sector de obstáculos invertido, Notas operativas de la sesión, Reproducibilidad de la tabla 7.4 (Capítulo 7): saltos sí, saturación no, Sesión 2026-07-21 (lab, Sesión 4) — Bug de seguridad confirmado y corregido: evasión de obstáculos vigilaba el sector trasero

### Community 52 - "Cambios aplicados"
Cohesion: 0.29
Nodes (7): Cambios aplicados, config.yaml, detection_node.py, Estado al final, Estado al inicio, Sesión 2026-06-04, tracking_node.py

### Community 53 - "Sesión 2026-06-25"
Cohesion: 0.29
Nodes (7): Causa raíz del fallo de seguimiento, Fix crítico de infraestructura: sklearn roto en el NUC, Fusión cámara+LiDAR (solución elegida), Infraestructura de validación (Capítulo 7), Pendiente para la próxima sesión, Primera toma de validación: `fusion_track_20260625` (sin movimiento), Sesión 2026-06-25

### Community 54 - "Sesión 2026-07-08"
Cohesion: 0.29
Nodes (7): Causa raíz y fix — ver detalle completo en `docs/decisiones.md`, Gesto de activación: no utilizable esta sesión (encuadre de cámara), Notas técnicas, Objetivo: prueba de fusión CON movimiento (validar `near_gain`), Pendiente para la próxima sesión, Primera toma con movimiento: reveló saltos de detección + saturación angular, Sesión 2026-07-08

### Community 55 - "Sesión 2026-07-09 (lab, tarde) — Gesto real funcionando + fixes en vivo"
Cohesion: 0.33
Nodes (6): Arranque brusco: diagnosticado como comportamiento correcto, suavizado igualmente, Bug real encontrado y corregido: barrido/deriva del gate de continuidad, Objetivo: cámara/gesto (Sesión 1 del plan), improvisado sobre la marcha, Otros cambios de sesión, Pendiente / observado sin resolver, Sesión 2026-07-09 (lab, tarde) — Gesto real funcionando + fixes en vivo

### Community 56 - "Pendiente — próximas sesiones"
Cohesion: 0.40
Nodes (5): Pendiente — próximas sesiones, Prioridad ALTA (siguiente sesión), Prioridad MEDIA, Resuelto en sesión 2026-06-17, Resuelto en sesión 2026-06-25

### Community 57 - "Sesión 2026-07-22 (lab, Sesión 5, continuación 4) — reintentos de `obstaculo`: lin_factor corregido para parar de verdad + maniobra de rodeo"
Cohesion: 0.50
Nodes (4): Dos contactos leves más → hallazgo de código: lin_factor nunca paraba del todo, Fix: lin_factor basado en distancia mínima real, con parada dura, Maniobra de rodeo nueva (idea del autor), Sesión 2026-07-22 (lab, Sesión 5, continuación 4) — reintentos de `obstaculo`: lin_factor corregido para parar de verdad + maniobra de rodeo

### Community 58 - "Sesión 2026-07-17 (trabajo de escritorio, sin robot) — Capítulo 6 redactado + hallazgo de signo confirmado + nuevo hallazgo (sector de obstáculos) sin verificar"
Cohesion: 0.50
Nodes (4): Objetivo: redactar el capítulo 6 de la memoria (implementación), pendiente tras el 16/07, Pendiente para la próxima sesión, Relectura del hallazgo del signo invertido (tarea 2) — confirmado, y hallazgo nuevo sin verificar, Sesión 2026-07-17 (trabajo de escritorio, sin robot) — Capítulo 6 redactado + hallazgo de signo confirmado + nuevo hallazgo (sector de obstáculos) sin verificar

### Community 59 - "Sesión 2026-07-16 (trabajo de escritorio, sin robot) — Capítulo 5 redactado + fix del fallback de fusión diseñado y verificado sintéticamente"
Cohesion: 0.50
Nodes (4): Objetivo: tarea de escritorio nº1 de `docs/sesion_siguiente.md` ("redactar capítulo 5 o 6"), Objetivo: tarea de escritorio nº3 de `docs/sesion_siguiente.md` ("diseñar el fix del fallback de fusión"), Pendiente para la próxima sesión, Sesión 2026-07-16 (trabajo de escritorio, sin robot) — Capítulo 5 redactado + fix del fallback de fusión diseñado y verificado sintéticamente

### Community 60 - "Sesión 2026-07-22 (lab, Sesión 5, continuación 3) — offset LIDAR medido, obstacle_threshold subido, 10 repeticiones de validación"
Cohesion: 0.50
Nodes (4): Offset físico LIDAR→borde del robot medido, obstacle_threshold 0.35→0.40m, Pendiente para la próxima sesión, Sesión 2026-07-22 (lab, Sesión 5, continuación 3) — offset LIDAR medido, obstacle_threshold subido, 10 repeticiones de validación, Sesión de lab: 10 tomas grabadas (recta ×2, curva ×3, parada ×1, corto ×3, oclusión ×1)

## Knowledge Gaps
- **247 isolated node(s):** `session_start_context.sh script`, `continue_session.sh script`, `launch_robot.bash script`, `ROS_DOMAIN_ID`, `sync_nuc.sh script` (+242 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Diario de progreso — TFM Person Follower` connect `Diario de progreso — TFM Person Follower` to `Decisiones de diseño`, `Sesión 2026-07-13 (lab) — Fix de CPU, causa raíz de la oscilación FSM, y bug de convenio angular en tracking_node`, `Sesión 2026-06-17`, `Sesión 2026-07-15 (lab, en curso) — Puerto USB kobuki/rplidar intercambiado + diagnóstico del "gira al lado contrario"`, `Sesión 2026-07-21 (lab, Sesión 4) — Bug de seguridad confirmado y corregido: evasión de obstáculos vigilaba el sector trasero`, `Cambios aplicados`, `Sesión 2026-06-25`, `Sesión 2026-07-08`, `Sesión 2026-07-09 (lab, tarde) — Gesto real funcionando + fixes en vivo`, `Pendiente — próximas sesiones`, `Sesión 2026-07-22 (lab, Sesión 5, continuación 4) — reintentos de `obstaculo`: lin_factor corregido para parar de verdad + maniobra de rodeo`, `Sesión 2026-07-17 (trabajo de escritorio, sin robot) — Capítulo 6 redactado + hallazgo de signo confirmado + nuevo hallazgo (sector de obstáculos) sin verificar`, `Sesión 2026-07-16 (trabajo de escritorio, sin robot) — Capítulo 5 redactado + fix del fallback de fusión diseñado y verificado sintéticamente`, `Sesión 2026-07-22 (lab, Sesión 5, continuación 3) — offset LIDAR medido, obstacle_threshold subido, 10 repeticiones de validación`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **What connects `session_start_context.sh script`, `continue_session.sh script`, `launch_robot.bash script` to the rest of the system?**
  _247 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `DetectionNode` be split into smaller, more focused modules?**
  _Cohesion score 0.09803921568627451 - nodes in this community are weakly interconnected._
- **Should `UserInterfaceNode` be split into smaller, more focused modules?**
  _Cohesion score 0.12433862433862433 - nodes in this community are weakly interconnected._
- **Should `TrackingNode` be split into smaller, more focused modules?**
  _Cohesion score 0.10826210826210826 - nodes in this community are weakly interconnected._
- **Should `UserInterfaceNode` be split into smaller, more focused modules?**
  _Cohesion score 0.1282051282051282 - nodes in this community are weakly interconnected._
- **Should `SLAMNode` be split into smaller, more focused modules?**
  _Cohesion score 0.13157894736842105 - nodes in this community are weakly interconnected._