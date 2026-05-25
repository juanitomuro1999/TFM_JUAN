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

1. **Módulo de interacción:** desarrollar un sistema de inicio/parada del seguimiento basado en gestos detectados por cámara (MediaPipe Pose y Hands).

2. **Cartografía SLAM:** integrar SLAM Toolbox con los datos del LiDAR para construir mapas del entorno en tiempo real.

3. **Navegación autónoma (Nav2):**
   - Localización basada en AMCL sobre mapa guardado.
   - Planificación de rutas con NavFn o Smac Planner.
   - Navegación a objetivos predefinidos (salas, puntos de interés).

4. **Fusión sensorial:** mejorar la robustez de la detección de personas combinando LiDAR (geometría) y cámara (confirmación visual).

5. **Guiado de usuarios:** implementar comportamientos de acompañamiento hacia destinos predefinidos del edificio.

6. **Objetivo exploratorio:** investigar el uso de códigos QR para el reconocimiento semántico automático de habitaciones.

## 1.3 Alcance y limitaciones

El desarrollo se realiza sobre el hardware disponible en el laboratorio de robótica de la UJI:

- **Robot:** TurtleBot 2 / base Kobuki
- **NUC:** Intel NUC con Ubuntu 24.04 y ROS 2 Jazzy
- **Sensores:** RPLIDAR A2M8 (LiDAR 2D, 12 m, 10 Hz) + Logitech C270 (cámara RGB) + Orbbec Astra (cámara RGBD, integración pendiente)
- **Entorno de prueba:** instalaciones interiores de la UJI

Limitaciones asumidas:
- Navegación en 2D (planta única).
- Detección de personas en el plano horizontal (LiDAR a altura de piernas).
- Red WiFi del laboratorio como canal de comunicación PC↔robot.

## 1.4 Planificación

| Fase | Descripción | Periodo | Estado |
|------|-------------|---------|--------|
| 1 | Definición, revisión del sistema, redacción inicial | Mayo 2026 |
| 2 | Módulo de interacción, integración SLAM | Junio 2026 | 
| 3 | Navegación autónoma completa | Julio 2026 |
| 4 | Validación experimental (entorno UJI) | Agosto 2026 | 
| 5 | Cierre, memoria final, defensa | Septiembre 2026 | 

## 1.5 Estructura de este documento

- **Capítulo 2 – Arquitectura del sistema:** descripción detallada de los nodos, topics y flujo de datos.
- **Capítulo 3 – Herramientas de IA:** declaración de uso de herramientas de inteligencia artificial como apoyo al desarrollo.
- **Capítulo 4 – Diario de desarrollo:** registro cronológico del progreso técnico.
- **Capítulo 5 (pendiente) – Estado del arte:** revisión bibliográfica de sistemas similares.
- **Capítulo 6 (pendiente) – Implementación:** detalles técnicos de cada módulo desarrollado.
- **Capítulo 7 (pendiente) – Resultados y evaluación.**
