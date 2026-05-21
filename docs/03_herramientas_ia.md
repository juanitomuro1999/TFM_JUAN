# Capítulo 3 — Uso de herramientas de inteligencia artificial

## 3.1 Declaración de uso

En el desarrollo de este TFM se han utilizado herramientas de inteligencia artificial (IA) como **apoyo técnico complementario**, de forma análoga al uso de un motor de búsqueda avanzado o una herramienta de documentación automatizada.

La declaración de uso de herramientas de IA es coherente con las directrices actuales de muchas universidades, que reconocen su valor como instrumento de aprendizaje y productividad, siempre que el estudiante mantenga la autoría intelectual del trabajo: la comprensión del problema, las decisiones de diseño, la validación experimental y la interpretación de resultados.

---

## 3.2 Herramientas utilizadas

### 3.2.1 Asistente de IA conversacional (Claude — Anthropic)

**Uso principal:** apoyo en tareas de diagnóstico y depuración de errores en el entorno ROS 2.

**Casos de uso concretos:**

- **Diagnóstico de errores de compilación:** ante mensajes de error de `colcon build`, el asistente ayudó a identificar causas como `ament_cmake` en lugar de `ament_python` en `package.xml`, o la ausencia de `find_packages()` en `setup.py`.

- **Análisis de logs del robot:** en la puesta en marcha del Kobuki, se produjeron errores del tipo `no data stream, is kobuki turned on?` debidos a la confusión entre `/dev/ttyUSB0` (RPLIDAR) y `/dev/ttyUSB1` (Kobuki). El asistente ayudó a interpretar los logs y a identificar el proceso bloqueante mediante `fuser`.

- **Consultas sobre APIs de ROS 2:** dudas sobre el uso de `create_subscription`, `declare_parameter`, o la estructura de un `launch.py` en ROS 2 Jazzy.

- **Revisión de estructura de código:** el asistente señaló la existencia de una doble suscripción a `/system_shutdown` en `tracking_node.py`, un bug que había pasado desapercibido.

**Lo que NO hizo el asistente:**

- No tomó decisiones de diseño del sistema (arquitectura, elección de algoritmos, parámetros).
- No realizó pruebas experimentales ni interpretó resultados.
- No redactó el análisis del estado del arte ni las conclusiones del TFM.

---

### 3.2.2 Herramientas de autocompletado de código

Durante el desarrollo se ha utilizado el autocompletado del IDE (VSCode con Pylance) para acelerar la escritura de código ROS 2 repetitivo (declaración de parámetros, creación de publishers/subscribers).

---

### 3.2.3 Motores de búsqueda y documentación

- **ROS 2 Humble/Jazzy docs:** [docs.ros.org](https://docs.ros.org)
- **SLAM Toolbox wiki:** [slam_toolbox GitHub](https://github.com/SteveMacenski/slam_toolbox)
- **Nav2 docs:** [navigation.ros.org](https://navigation.ros.org)
- **MediaPipe:** [developers.google.com/mediapipe](https://developers.google.com/mediapipe)

---

## 3.3 Reflexión sobre el uso ético de la IA

El uso de herramientas de IA en proyectos de ingeniería plantea cuestiones importantes sobre autoría y aprendizaje. En este proyecto se ha seguido el criterio de:

1. **Comprensión previa:** no se ha copiado código generado por IA sin entenderlo. Cada cambio sugerido por el asistente fue analizado y validado en el robot físico antes de integrarlo.

2. **Responsabilidad del resultado:** el autor del TFM es responsable de todos los bugs, decisiones de diseño y resultados del sistema, independientemente de las herramientas utilizadas.

3. **Transparencia:** este capítulo declara explícitamente el uso de IA, en línea con las buenas prácticas académicas emergentes.

4. **Aprendizaje efectivo:** el uso del asistente como herramienta de diagnóstico ha accelerado el aprendizaje de ROS 2 al proporcionar explicaciones contextualizadas de errores reales durante la puesta en marcha del robot.

---

## 3.4 Estimación del impacto

| Tarea | % desarrollado por el autor | Apoyo IA |
|---|---|---|
| Diseño de la arquitectura del sistema | 100% | No |
| Algoritmo DBSCAN para detección de piernas | 100% | Depuración |
| Filtro de Kalman en tracking_node | 100% | No |
| FSM del control_node | 100% | No |
| Identificación de bugs en setup.py / package.xml | 60% | Diagnóstico |
| Puesta en marcha del robot físico | 90% | Diagnóstico de logs |
| Documentación técnica (este documento) | 100% | No |
| Experimentos y validación | 100% | No |
