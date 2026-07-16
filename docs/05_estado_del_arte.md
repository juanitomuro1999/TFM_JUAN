# Capítulo 5 — Estado del arte

## 5.1 Introducción y alcance del capítulo

Este capítulo revisa el estado del arte de los subsistemas que componen el
sistema desarrollado en este TFM: detección de personas mediante LiDAR 2D,
estimación de pose humana por visión, fusión sensorial LiDAR-cámara,
interacción humano-robot basada en gestos, seguimiento de estado mediante
filtros bayesianos, evitación de obstáculos y navegación autónoma (SLAM y
planificación de rutas). No pretende ser una revisión exhaustiva de la
robótica de seguimiento de personas, sino situar las decisiones de diseño
tomadas en este proyecto (documentadas en el Capítulo 2 y en
`docs/decisiones.md`) dentro del trabajo previo relevante en cada área, y
justificar por qué se eligió cada enfoque frente a las alternativas.

## 5.2 Sistemas de seguimiento de personas con robots móviles

El seguimiento de personas ("person-following") es un problema clásico de
robótica de servicio que combina percepción, estimación de estado y control
de movimiento. Los enfoques publicados se agrupan típicamente según el
sensor principal empleado:

- **LiDAR puro:** exploran la geometría del entorno mediante barridos 2D o
  3D, apoyándose en el patrón característico de las piernas humanas al
  caminar. Es el enfoque más robusto ante condiciones de iluminación
  variable, pero ambiguo cuando otros objetos del entorno (patas de silla,
  columnas) presentan una geometría similar.
- **Visión pura:** usan cámaras RGB o RGB-D y modelos de detección/pose
  para localizar a la persona en la imagen. Aportan información semántica
  rica (identidad, gestos, orientación del cuerpo) pero son sensibles a
  oclusiones, iluminación y campo de visión limitado.
- **Fusión multisensor:** combinan LiDAR y cámara (y en ocasiones sensores
  de tiempo de vuelo o térmicos) para compensar las debilidades de cada
  modalidad por separado. Zhao et al. (2023) fusionan sensores de tiempo de
  vuelo con una cámara monocular para un robot seguidor de personas,
  mostrando mejoras de robustez frente al uso de una sola modalidad; Zhang
  et al. (2025) proponen seguimiento humano robusto con LiDAR 3D y
  proyección de nube de puntos para robots seguidores de personas.

Los robots comerciales y de investigación de esta familia suelen operar en
bases diferenciales de interior (como el TurtleBot 2/Kobuki usado en este
TFM), donde la maniobrabilidad es alta y el problema de percepción domina
sobre el de cinemática; en cambio, en bases tipo Ackermann para exteriores
(p. ej. Xu et al., 2025, "Auto-Follower") la propia maniobrabilidad limitada
del vehículo introduce restricciones adicionales que no aplican a este
proyecto.

El sistema de este TFM se sitúa en la categoría de fusión multisensor
(LiDAR + cámara), heredando del trabajo previo (Fase 1, ver Capítulo 1) un
detector LiDAR basado en clustering, y añadiendo en la Fase 2 una vía visual
de respaldo (Sección 5.5).

## 5.3 Detección de personas mediante LiDAR 2D (detección de piernas)

La detección de personas a partir de barridos 2D de LiDAR a la altura de
las piernas es una línea de trabajo consolidada. El enfoque dominante
consiste en:

1. Segmentar la nube de puntos del barrido en clústeres (agrupando puntos
   contiguos o próximos entre sí).
2. Filtrar los clústeres según características geométricas compatibles con
   una pierna humana (tamaño, radio, circularidad, curvatura media).
3. Emparejar clústeres en pares plausibles (dos piernas) y, opcionalmente,
   seguir su trayectoria en el tiempo para distinguir el patrón de marcha
   humano de objetos estáticos con geometría similar.

Kim et al. (2020) proponen detección de piernas humanas en un espacio de
características 3D específicamente para robots seguidores de personas con
LiDAR 2D; Chung et al. (2023) abordan el reto de diferenciar múltiples
objetivos en escenarios con varias personas. Un reto documentado de forma
recurrente en la literatura es la ambigüedad geométrica: patas de mesas o
sillas, columnas y otros objetos cilíndricos pueden generar falsos
positivos, y las oclusiones parciales (una pierna tapando a la otra durante
un giro) rompen el emparejamiento. Yan et al. (2018) exploran redes
neuronales totalmente convolucionales sobre los propios barridos 2D como
alternativa a los detectores basados en características geométricas
hechas a mano, precisamente para mejorar la robustez en entornos con
mobiliario denso.

El `detection_node` de este proyecto (§2.3.1) sigue el enfoque clásico
basado en características geométricas: clustering con DBSCAN (reimplementado
sobre `scipy.spatial.cKDTree` por una incompatibilidad de `scikit-learn` en
el NUC, ver `docs/decisiones.md`), filtrado por tamaño/radio de clúster y
emparejamiento por distancia coherente entre piernas. Es una decisión
consciente de mantenerse en la familia de métodos clásicos —frente a
alternativas basadas en aprendizaje profundo como la de Yan et al.
(2018)— por simplicidad de despliegue sin GPU dedicada en el NUC y
por reutilizar el detector ya validado del sistema original (Fase 1). La
limitación de ambigüedad geométrica descrita arriba es exactamente la que
motiva el fallback de fusión con cámara de la Sección 5.5, y el hallazgo,
sin resolver a fecha de este capítulo, de pérdida conjunta de detección
LiDAR+cámara durante giros (`docs/sesion_siguiente.md`, 2026-07-15) es una
instancia concreta del problema de oclusión parcial descrito por Kim et al.
(2020) y Chung et al. (2023).

## 5.4 Estimación de pose humana por visión

La estimación de pose humana en tiempo real a partir de una única cámara
RGB ha avanzado significativamente con arquitecturas ligeras orientadas a
dispositivos móviles. BlazePose (Bazarevsky et al., 2020) es una red
convolucional ligera que produce 33 puntos clave del cuerpo a más de 30 FPS
en hardware móvil sin GPU dedicada, y es la base del solver **MediaPipe
Pose** usado en este proyecto. Su extensión GHUM Holistic (Grishchenko et
al., 2022) añade landmarks 3D de manos y rostro, aunque este TFM solo
requiere los landmarks corporales (hombros, muñecas) para calcular gestos y
rumbo.

Frente a detectores clásicos como HOG (Histogram of Oriented Gradients,
usado en la versión original del sistema), los modelos basados en
landmarks corporales tienen dos ventajas relevantes para este caso de uso:
no requieren que el cuerpo completo esté en el encuadre (HOG sí lo requería,
lo que era inviable a la distancia real de seguimiento, ~1 m — ver
`docs/decisiones.md`) y proporcionan puntos anatómicos con significado
semántico (muñeca, hombro) directamente utilizables para reconocer gestos y
calcular orientación, en vez de solo una caja delimitadora de la persona.
Esto motivó la sustitución de HOG por MediaPipe Pose documentada en el
Capítulo 2 (§2.3.2).

## 5.5 Fusión sensorial LiDAR-cámara para detección robusta

La fusión de LiDAR y cámara para percepción de personas es un área activa,
ya que ambas modalidades tienen debilidades complementarias: el LiDAR
ofrece geometría precisa pero es ambiguo entre objetos de forma similar,
mientras que la cámara ofrece semántica rica pero es sensible a oclusiones
e iluminación y no aporta distancia fiable con una sola cámara monocular.
Los enfoques de fusión en la literatura van desde el "vision-LiDAR servo
tracking" con sensores LiDAR motorizados de 360° combinados con histogramas
de verosimilitud, hasta arquitecturas más recientes de fusión profunda
(p. ej. Dual-Stream Transformer para seguimiento de personas combinando
LiDAR e imagen térmica). En general, la literatura reciente confirma que la
fusión LiDAR-cámara mejora la robustez de la detección de peatones/personas
frente a condiciones adversas respecto al uso de una sola modalidad.

El diseño de este TFM adopta un esquema de fusión más ligero que estos
trabajos, ajustado a los recursos del NUC embarcado y sin cámara de
profundidad: en vez de fusionar en el espacio de características o entrenar
un modelo conjunto, `visual_detection_node` calcula un **rumbo** angular
hacia la persona a partir del punto medio de los hombros detectado por
MediaPipe Pose, y `detection_node` usa ese rumbo únicamente como
**desambiguador** cuando el LiDAR no encuentra un par de piernas válido,
seleccionando el clúster general del LiDAR mejor alineado angularmente
(§2.3.1). Es, en esencia, una fusión tardía (*late fusion*) asimétrica: el
LiDAR sigue siendo la fuente primaria de posición 2D (más precisa en
distancia que una cámara monocular), y la cámara solo interviene como señal
de desambiguación direccional cuando la geometría del LiDAR es insuficiente.
Esta asimetría es una elección deliberada frente a esquemas de fusión más
simétricos de la literatura: evita depender de una calibración extrínseca
precisa cámara-LiDAR (solo se necesita el campo de visión horizontal de la
cámara, `camera_hfov_deg`, y un signo de calibración del rumbo,
`bearing_sign`) a cambio de no aprovechar la cámara cuando el LiDAR sí
detecta un par de piernas válido. El hallazgo documentado en
`docs/sesion_siguiente.md` (2026-07-15) de que LiDAR y cámara pueden perder
a la persona simultáneamente durante un giro es una limitación conocida de
este esquema —ambas modalidades comparten el mismo punto ciego frontal— y
constituye el objetivo de trabajo abierto de la Sesión 4 de laboratorio.

## 5.6 Interacción humano-robot basada en gestos

El reconocimiento de gestos de mano/brazo como canal de interacción
humano-robot es un área extensamente revisada; Cheng et al. (2022) ofrecen
una revisión general de interacción por gestos de mano y brazo, cubriendo
tanto métodos basados en sensores portátiles como en visión. Dentro de los
métodos por visión, la tendencia reciente favorece el uso de landmarks
corporales (como los de MediaPipe Pose/Hands) frente a clasificadores de
imagen completa, por ser más ligeros y no requerir grandes conjuntos de
datos de entrenamiento propios: el gesto se define como una regla geométrica
sobre puntos clave ya extraídos (p. ej., "muñeca por encima del hombro") en
lugar de una clase aprendida end-to-end. Trabajos recientes de control por
gestos con MediaPipe reportan tasas de éxito superiores al 94-96% en tareas
de manipulación/entrega dirigidas por gestos estáticos y dinámicos.

El sistema de este TFM sigue exactamente este enfoque basado en reglas
sobre landmarks: dos gestos discretos (mano derecha levantada por encima
del hombro → iniciar seguimiento; mano izquierda levantada → detenerlo),
definidos como condiciones geométricas sobre los landmarks de MediaPipe
Pose, con un número mínimo de fotogramas de confirmación consecutivos
(`gesture_confirm_frames`) y un tiempo de espera entre comandos
(`gesture_cooldown_s`) para reducir falsos positivos (§2.3.2). Es un
vocabulario de gestos deliberadamente mínimo (dos gestos, frente a los
vocabularios más amplios de trabajos como Cheng et al., 2022), justificado
por que la interacción requerida en este TFM se limita a iniciar y detener
el seguimiento, no a un control fino del robot.

## 5.7 Seguimiento de estado: filtros bayesianos

Una vez detectada la posición de la persona en cada fotograma/barrido, es
necesario estimar su trayectoria (posición y velocidad) de forma continua y
robusta frente a ruido y detecciones perdidas. La familia de filtros de
Bayes —Kalman, su variante extendida (EKF), la no perfumada (UKF) y los
filtros de partículas— es el enfoque estándar en la literatura de
seguimiento de personas con robots móviles desde hace más de dos décadas
(Urrea y Kern, 2021, ofrecen una revisión histórica del uso del filtro de
Kalman en robótica). Schulz et al. y trabajos posteriores comparan filtros
de Kalman frente a filtros de partículas para seguimiento de personas con
robot móvil, y Wang et al. (2010) evalúan la eficiencia computacional de
varios filtros bayesianos para la misma tarea, mostrando que el UKF puede
igualar el rendimiento de un filtro de partículas con mucho menor coste
computacional. Este es un factor relevante para plataformas embarcadas
como el NUC de este proyecto, sin GPU dedicada y compartiendo CPU con
detección LiDAR, MediaPipe y el resto de nodos ROS 2.

El `tracking_node` de este TFM usa un filtro de Kalman lineal (no extendido)
con vector de estado `[x, y, vx, vy]` sobre la posición 2D publicada por
`detection_node` (§2.3.3). Es la opción más ligera computacionalmente de la
familia de filtros bayesianos, adecuada porque el modelo de movimiento
(velocidad aproximadamente constante entre observaciones) y el modelo de
observación (posición 2D directa) son ya lineales, sin necesitar la
linealización local de un EKF ni el coste de un UKF o un filtro de
partículas. Frente al filtro de Kalman, un EKF o UKF aportarían valor si el
modelo de observación fuese no lineal (p. ej., si se estimara directamente
desde ángulo y distancia sin conversión previa a cartesianas), lo cual no es
el caso aquí.

## 5.8 Evitación de obstáculos y control de movimiento

Para convertir la posición estimada de la persona en comandos de velocidad
seguros, la literatura de navegación reactiva ofrece varios métodos
clásicos, entre los que destaca el **Dynamic Window Approach** (DWA; Fox,
Burgard y Thrun, 1997), que restringe la búsqueda al espacio de velocidades
lineales y angulares directamente alcanzables por el robot dadas sus
limitaciones dinámicas, simulando trayectorias a corto plazo dentro de esa
ventana y seleccionando la que evita colisiones. Es uno de los métodos de
evitación de obstáculos reactivos más adoptados en robótica móvil de
interior, y es el que usa Nav2 (Sección 5.9) como uno de sus controladores
locales estándar.

El `tracking_node` de este proyecto implementa una evitación de obstáculos
inspirada en la misma idea —analizar el sector frontal del LiDAR y generar
una fuerza de repulsión angular más reducción de velocidad lineal ante
obstáculos cercanos (§2.3.3)— pero de forma simplificada respecto al DWA
completo: no simula explícitamente trayectorias candidatas dentro de una
ventana de velocidades admisibles, sino que aplica una regla reactiva
directa sobre el sector frontal. Es coherente con el resto de la
arquitectura del proyecto, donde la evitación de obstáculos reactiva
convive con el seguimiento de personas en `tracking_node`, mientras que la
Fase 3 (Nav2) reserva el DWA/planificación completa para la navegación
punto a punto sin seguimiento de personas activo.

## 5.9 Cartografía y navegación autónoma (SLAM y Nav2)

Para la cartografía del entorno, este TFM usa **SLAM Toolbox** (Macenski y
Jambrecic, 2021), la implementación de SLAM 2D de referencia para ROS 2,
que ofrece modos de mapeo síncrono y asíncrono, localización sobre un mapa
ya guardado y fusión cinemática de mapas, entre otras capacidades. Sustituyó
en la Fase 2 a una implementación propia de SLAM básico
(`slam_node`, §2.3.7) desarrollada durante la Fase 1, por ofrecer mayor
robustez, cierre de bucles y serialización de mapas sin mantener código de
SLAM propio.

Para la navegación autónoma planificada (Fase 3, sin ejecutar todavía en el
robot a fecha de este capítulo — ver `docs/sesion_siguiente.md`), el
proyecto usa **Nav2**, sucesor profesional del stack de navegación de ROS 1
para ROS 2 (Macenski et al., 2020, "The Marathon 2"), que separa
planificación global, control local y percepción en módulos cooperantes
orquestados mediante árboles de comportamiento y nodos con ciclo de vida
gestionado. Macenski et al. (2023) ofrecen además una revisión más amplia
de los algoritmos de robótica móvil disponibles en el ecosistema ROS 2, de
la que Nav2 y SLAM Toolbox forman parte. El alcance decidido para este TFM
(`docs/decisiones.md`, 2026-07-09) es una demo mínima de dos fases —
localización con AMCL sobre el mapa ya guardado, y navegación a un único
punto objetivo—, deliberadamente acotada frente a las capacidades completas
de Nav2 (múltiples objetivos, recuperación de comportamientos ante fallos,
costmaps dinámicos), dado el presupuesto de sesiones de laboratorio
restante (Capítulo 1, §1.4).

## 5.10 Síntesis: posicionamiento de este TFM respecto al estado del arte

El sistema desarrollado en este TFM no introduce ningún método
individualmente novedoso frente al estado del arte revisado —cada
subsistema (detección de piernas por clustering, MediaPipe Pose, fusión
tardía LiDAR-cámara, Kalman lineal, evitación reactiva de obstáculos, SLAM
Toolbox, Nav2) reutiliza técnicas ya establecidas en la literatura o en el
ecosistema ROS 2—. Su contribución está en la **integración concreta** de
estas técnicas en una arquitectura ROS 2 modular sobre una plataforma real
con recursos embarcados limitados (NUC sin GPU, cámara USB monocular, sin
`tmux` ni acceso a internet en el robot), y en las adaptaciones prácticas
que esa integración exige y que no siempre están cubiertas en la
literatura de referencia:

- Reimplementación de DBSCAN sobre `scipy.cKDTree` ante una incompatibilidad
  de `scikit-learn` con la versión de Python del NUC (§2.3.1).
- Un esquema de fusión LiDAR-cámara deliberadamente asimétrico y ligero en
  requisitos de calibración, frente a los esquemas de fusión más simétricos
  o basados en aprendizaje profundo de la literatura reciente (§5.5).
- Elección de un filtro de Kalman lineal, no un EKF/UKF, aprovechando que el
  modelo de observación de este sistema concreto ya es lineal (§5.7).
- Un vocabulario de gestos mínimo (dos gestos) ajustado estrictamente a la
  necesidad de iniciar/detener el seguimiento, no a una interacción general
  (§5.6).
- Un alcance de Nav2 recortado a demo mínima por restricciones reales de
  tiempo de laboratorio, documentado como tal en vez de presentado como
  limitación de la técnica (§5.9, Capítulo 1 §1.4).

Esta perspectiva —de integración pragmática sobre plataforma real con
recursos limitados, más que de innovación algorítmica aislada— enmarca las
decisiones técnicas detalladas en el Capítulo 6 y los resultados
experimentales del Capítulo 7.

## Referencias

- Bazarevsky, V., Grishchenko, I., Raveendran, K., Zhu, T., Zhang, F., y
  Grundmann, M. (2020). *BlazePose: On-device Real-time Body Pose Tracking*.
  arXiv:2006.10204. https://arxiv.org/pdf/2006.10204
- Chung, W. et al. (2023). *Leg Detection for Socially Assistive Robots:
  Differentiating Multiple Targets with 2D LiDAR*. En: Springer, LNCS.
  https://link.springer.com/chapter/10.1007/978-981-99-8018-5_7
- Cheng, H., Zhu, Y., Sun, C., y Vieira, A. W. (2022). *Hand and Arm
  Gesture-based Human-Robot Interaction: A Review*. arXiv:2209.08229.
  https://arxiv.org/pdf/2209.08229
- Fox, D., Burgard, W., y Thrun, S. (1997). *The Dynamic Window Approach to
  Collision Avoidance*. IEEE Robotics & Automation Magazine, 4(1), 23-33.
  https://www.ri.cmu.edu/publications/the-dynamic-window-approach-to-collision-avoidance/
- Grishchenko, I., Bazarevsky, V., et al. (2022). *BlazePose GHUM Holistic:
  Real-time 3D Human Landmarks and Pose Estimation*. arXiv:2206.11678.
  https://arxiv.org/pdf/2206.11678
- Kim, B., et al. (2020). *Human-Leg Detection in 3D Feature Space for a
  Person-Following Mobile Robot Using 2D LiDARs*. International Journal of
  Precision Engineering and Manufacturing.
  https://link.springer.com/article/10.1007/s12541-020-00343-7
- Macenski, S., y Jambrecic, I. (2021). *SLAM Toolbox: SLAM for the dynamic
  world*. Journal of Open Source Software, 6(61), 2783.
  https://doi.org/10.21105/joss.02783
- Macenski, S., Martín, F., White, R., y Clavero, J. G. (2020). *The
  Marathon 2: A Navigation System*. IEEE/RSJ International Conference on
  Intelligent Robots and Systems (IROS). arXiv:2003.00368.
  https://arxiv.org/abs/2003.00368
- Macenski, S., et al. (2023). *From the desks of ROS maintainers: A survey
  of modern & capable mobile robotics algorithms in the robot operating
  system 2*. Robotics and Autonomous Systems.
- Urrea, C., y Kern, J. (2021). *Kalman Filter: Historical Overview and
  Review of Its Use in Robotics 60 Years after Its Creation*. Journal of
  Sensors, 2021, 9674015. https://onlinelibrary.wiley.com/doi/10.1155/2021/9674015
- Wang, Z., et al. (2010). *Computationally efficient solutions for
  tracking people with a mobile robot: an experimental evaluation of
  Bayesian filters*. Autonomous Robots, 28(4).
  https://link.springer.com/article/10.1007/s10514-009-9167-2
- Xu, et al. (2025). *Auto-Follower: A Person-Following System for Urban
  Ackermann Human–Machine Collaborative Robotics*. ACM Transactions on
  Autonomous and Adaptive Systems. https://dl.acm.org/doi/10.1145/3787977
- Yan, Z., Duckett, T., y Bellotto, N. (2018). *Tracking People in a Mobile
  Robot From 2D LIDAR Scans Using Full Convolutional Neural Networks for
  Security in Cluttered Environments*. Frontiers in Neurorobotics, 12, 85.
  https://www.frontiersin.org/articles/10.3389/fnbot.2018.00085
- Zhang, et al. (2025). *Robust Human Tracking Using a 3D LiDAR and Point
  Cloud Projection for Human-Following Robots*. Sensors, 25(6), 1754.
  https://www.mdpi.com/1424-8220/25/6/1754
- Zhao, et al. (2023). *Fusion of Time-of-Flight Based Sensors with
  Monocular Cameras for a Robotic Person Follower*. Journal of Intelligent
  & Robotic Systems. https://link.springer.com/article/10.1007/s10846-023-02037-4
