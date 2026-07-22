# Capítulo 1 — Introducción y planteamiento del problema

## 1.1 Contexto y motivación

La robótica de servicio en entornos interiores ha experimentado un crecimiento sostenido en los últimos años, impulsado tanto por el avance en las plataformas de software de código abierto (especialmente ROS 2) como por la mejora en la accesibilidad de sensores de bajo coste como los LiDAR de barrido 2D o las cámaras RGB.

En este contexto, el presente TFM surge como extensión directa de un trabajo previo en el que se desarrolló un sistema de seguimiento de personas sobre un robot móvil TurtleBot 2 con base Kobuki. Dicho sistema consiguió detectar y seguir a una persona en movimiento usando un LiDAR RPLIDAR A2M8 y técnicas de clustering (DBSCAN) para identificar el patrón de piernas humanas.

Sin embargo, el sistema original presentaba limitaciones que motivan esta extensión:

- **Sin cartografía:** el robot operaba sin mapa del entorno, lo que impedía cualquier navegación planificada.
- **Sin localización global:** ante la pérdida de la persona, el robot no podía orientarse.
- **Interacción limitada:** no existía un mecanismo claro de inicio/parada del seguimiento por parte del usuario.
- **Sin integración de cámara:** la detección visual no estaba integrada en el bucle de control principal.

## 1.2 Objetivos del TFM

### Objetivo general

Extender el sistema de seguimiento de personas hasta convertirlo en una plataforma de asistencia móvil capaz de navegación autónoma, comprensión del entorno y comunicación con el usuario en interiores.

### Objetivos específicos

1. ✅ **Módulo de interacción:** desarrollar un sistema de inicio/parada del seguimiento basado en gestos detectados por cámara (MediaPipe Pose y Hands). *(Completado 2026-06-17: gesto de mano levantada con MediaPipe Pose; ver `docs/04_diario_desarrollo.md` y `PROGRESO.md`. ⚠️ 2026-07-08: en el montaje de la cámara C270, el gesto de mano derecha no se detectó de forma fiable. **Resuelto en vivo 2026-07-09:** se bajó `gesture_min_visibility` (0.6→0.5) y, tras cambiar físicamente la cámara por una SPCA2650, ambos gestos (inicio con mano derecha, parada con mano izquierda) se dispararon de forma repetida y fiable en varias pruebas reales, sin el workaround manual por SSH — ver `docs/decisiones.md` y `PROGRESO.md`, sesión 2026-07-09. Caveat resuelto 2026-07-15: revisada la desviación cámara-LIDAR (`dev_deg`) con ~2600 muestras reales de la SPCA2650 — mediana 3.2°, sin sesgo sistemático — no hace falta recalibrar `camera_hfov_deg`/`bearing_sign`, ver `PROGRESO.md`.)*

2. ✅ **Cartografía SLAM:** integrar SLAM Toolbox con los datos del LiDAR para construir mapas del entorno en tiempo real. *(Completado — mapa del laboratorio generado y guardado en `maps/`)*

3. 🔄 **Navegación autónoma (Nav2):**
   - Localización basada en AMCL sobre mapa guardado.
   - Planificación de rutas con NavFn o Smac Planner.
   - Navegación a objetivos predefinidos (salas, puntos de interés).
   *(Alcance decidido 2026-07-09: demo mínima completa — AMCL + navegación a
   un punto — ver `docs/decisiones.md`. Preparado sin robot:
   `person_follower/launch/nav2_localization_demo.launch.py` y
   `scripts/nav2_send_goal.py`, ninguno probado todavía. Pendiente de
   ejecutar y validar en el lab.)*

4. ✅ **Fusión sensorial:** mejorar la robustez de la detección de personas combinando LiDAR (geometría) y cámara (confirmación visual). *(Completado 2026-06-25: `visual_detection_node` publica el rumbo de la persona (`/person_bearing`) desde MediaPipe; cuando el LiDAR no encuentra un par de piernas válido, `detection_node` usa ese rumbo para elegir el clúster correcto y seguir publicando posición. Validado sin movimiento: 100% detección, 0 pérdidas, en `validation/runs/fusion_track_20260625/`; ver `docs/04_diario_desarrollo.md` y `PROGRESO.md`. 2026-07-08: validado también con movimiento — la primera toma reveló saltos de detección y saturación angular (causa raíz identificada y corregida: filtro de continuidad + gate de Mahalanobis + rate-limit angular, ver `docs/decisiones.md`). 2026-07-15: corregido un signo invertido en el PD angular de `tracking_node` (causa raíz real del "gira al lado contrario" reportado desde el 13/07) y validado `near_gain` de forma aislada (0.49-0.86m): comportamiento acotado y con el signo correcto, con saturación puntual esperable a corta distancia — ver `docs/decisiones.md` y `PROGRESO.md`. 2026-07-21 (Sesión 4): corregido un sector invertido en la evasión de obstáculos de `tracking_node` (vigilaba la parte trasera del robot, no la delantera — mismo desfase de π que ya se corregía en la fusión); añadido un fallback de pierna única (sin par) en `detection_node` para el hueco de detección al girar (~2-4s → ~1.6s, validado en vivo); subido `continuity_confirm_frames` de 1 a 3 tras estresar con mobiliario denso real (saltos de posición 12.9%→4.6%, saturación 4.9%→0.0%) — ver `docs/decisiones.md` y `PROGRESO.md`. 2026-07-22 (Sesión 5): tras 4 contactos leves reales con mobiliario en dos sesiones, corregido `lin_factor` de la evasión de obstáculos para que llegue a 0.0 de verdad (antes nunca bajaba de 0.4, código muerto) y añadida una maniobra de rodeo (giro + avance corto) para obstáculos sostenidos — dos tomas siguientes en vivo sin contacto; sigue sin resolver el punto ciego de altura del LIDAR 2D (silla de patas finas) — ver `docs/decisiones.md` y `PROGRESO.md`.)*

5. **Guiado de usuarios:** implementar comportamientos de acompañamiento hacia destinos predefinidos del edificio.

6. **Objetivo exploratorio:** investigar el uso de códigos QR para el reconocimiento semántico automático de habitaciones.

## 1.3 Alcance y limitaciones

El desarrollo se realiza sobre el hardware disponible en el laboratorio de robótica de la UJI:

- **Robot:** TurtleBot 2 / base Kobuki
- **NUC:** Intel NUC con Ubuntu 24.04 y ROS 2 Jazzy
- **Sensores:** RPLIDAR A2M8 (LiDAR 2D, 12 m, 10 Hz) + cámara RGB en `/dev/video0` (Logitech C270 hasta 2026-07-09; sustituida esa fecha por una SPCA2650 tras problemas de encuadre del gesto, ver objetivo 1 y `docs/decisiones.md`) + Orbbec Astra (cámara RGBD, integración pendiente)
- **Entorno de prueba:** instalaciones interiores de la UJI

Limitaciones asumidas:
- Navegación en 2D (planta única).
- Detección de personas en el plano horizontal (LiDAR a altura de piernas).
- Red WiFi del laboratorio como canal de comunicación PC↔robot.

## 1.4 Planificación

> **Sin acceso al laboratorio en agosto** (confirmado 2026-07-09): las 9
> sesiones de julio (`docs/sesion_siguiente.md`, "Presupuesto de lab") son
> **todo el tiempo de robot para experimentación/validación que queda**.
> **Sí hay acceso en septiembre, pero reservado para tareas de cierre**
> (demo final para la defensa, comprobación de que el sistema sigue
> funcionando) — no es margen para recuperar validación o Nav2 sin terminar.
> Todo lo que no quede recogido al final de la sesión 9 de julio pasa a
> trabajo futuro documentado; agosto es análisis/redacción de lo ya grabado,
> sin datos nuevos.

| Fase | Descripción | Periodo | Estado |
|------|-------------|---------|--------|
| 1 | Definición, revisión del sistema, redacción inicial | Mayo 2026 | ✅ Completada |
| 2 | Módulo de interacción, integración SLAM, fusión sensorial | Junio 2026 | ✅ Completada |
| 3 | Navegación autónoma completa | Julio 2026 (sesiones 5-6 de 9) | 🔄 Alcance decidido (demo mínima), código preparado sin robot, sin ejecutar todavía |
| 4 | Validación experimental (entorno UJI) | Julio 2026 (sesiones 2-4 de 9) — **no agosto**, sin lab ese mes | 🔄 Iniciada — primera toma sin movimiento registrada 2026-06-25, con movimiento 2026-07-08. Repeticiones y reproducibilidad de métricas pendientes de las sesiones de julio que quedan |
| 5 | Cierre, memoria final, defensa | Agosto-septiembre 2026 | ⏳ Pendiente — agosto sin lab (análisis/redacción de lo grabado en julio); septiembre con lab reservado a cierre (demo final, comprobación del sistema), no a validación nueva |

## 1.5 Estructura de este documento

- **Capítulo 2 – Arquitectura del sistema:** descripción detallada de los nodos, topics y flujo de datos.
- **Capítulo 3 – Herramientas de IA:** declaración de uso de herramientas de inteligencia artificial como apoyo al desarrollo.
- **Capítulo 4 – Diario de desarrollo:** registro cronológico del progreso técnico.
- **Capítulo 5 – Estado del arte:** ver [`docs/05_estado_del_arte.md`](05_estado_del_arte.md) — revisión bibliográfica de sistemas similares, conectada con las decisiones de diseño de este TFM. *(Redactado 2026-07-16, trabajo de escritorio; pendiente de revisión por el autor.)*
- **Capítulo 6 – Implementación:** ver [`docs/06_implementacion.md`](06_implementacion.md) — detalles técnicos de cada módulo desarrollado (algoritmos, fórmulas de control, estructura del paquete). *(Redactado 2026-07-16, trabajo de escritorio; pendiente de revisión por el autor. Documenta también código legado no registrado en `setup.py`, ver §6.11.)*
- **Capítulo 7 (borrador) – Resultados y evaluación:** ver [`docs/07_resultados.md`](07_resultados.md) — andamiaje con los datos ya recogidos, pendiente de completar antes de redactarlo como prosa final.
