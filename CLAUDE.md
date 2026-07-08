# CLAUDE.md — TFM_JUAN (Person-Following System)

> Instanciación de [Claude-Project-OS](https://github.com/juanitomuro1999/Claude-Project-OS).
> Este repo ya tenía documentación propia antes de adoptar la metodología, así
> que este archivo **referencia** esos documentos en vez de duplicarlos.

## Qué es este proyecto

TFM de Juan Muriel Rovira (UJI, 2025–2026): sistema de seguimiento de
personas sobre un TurtleBot 2 / base Kobuki, con ROS 2 Jazzy. Visión general,
hardware, software y estado de fases: [`README.md`](README.md).

## Antes de tocar nada, lee esto en orden

1. [`docs/sesion_siguiente.md`](docs/sesion_siguiente.md) — plan de la
   próxima sesión (acceso al NUC, estado heredado, objetivo propuesto). **Es
   el roadmap vivo — mantenlo como único archivo de "próxima sesión".** No
   crees un `prompt_proxima_sesion_N.md` nuevo cada vez: eso rompe Single
   Source of Truth (existía `docs/prompt_proxima_sesion.md` con este mismo
   propósito duplicado — se consolidó en este archivo y se borró el
   2026-07-08).
2. [`PROGRESO.md`](PROGRESO.md) — diario de sesiones: qué se hizo, qué se
   encontró, causa raíz de bugs resueltos. Es el registro corto y técnico.
3. [`docs/02_arquitectura.md`](docs/02_arquitectura.md) — solo si la tarea
   toca nodos, topics o el flujo de datos.

No leas el resto de `docs/` (01, 03) salvo que la tarea lo requiera
explícitamente — son capítulos de la memoria del TFM, no estado operativo.

## Entorno de ejecución — importante

**El código no se ejecuta en el PC donde abras esta sesión de Claude Code.**
El robot corre en un Intel NUC (`nuc-224`, `ssh user@10.48.0.1`,
`ROS_DOMAIN_ID=24`, Ubuntu 24.04 + ROS 2 Jazzy), accesible solo por SSH y sin
acceso a internet ni `tmux` (ver patrones de `nohup ... & disown` en
`docs/sesion_siguiente.md`). Esta copia local del repo sirve para:

- Editar código y documentación con contexto completo.
- Planificar cambios y revisar el diario/roadmap.
- Preparar commits.

Para probar cambios de verdad hace falta sincronizar al NUC
(`bash sync_nuc.sh`) y ejecutar allí por SSH — Claude Code en esta sesión no
puede hacerlo directamente. Si una tarea requiere validación en el robot,
dilo explícitamente en vez de asumir que el cambio "funciona" sin probarlo.

## Flujo de trabajo de esta sesión

1. Leer `docs/sesion_siguiente.md` + `PROGRESO.md` (estado inmediato).
2. Si la tarea es compleja, plantear un plan antes de tocar código.
3. Implementar (recordando la limitación de entorno de arriba).
4. Actualizar `README.md` si cambia arquitectura o estado de fases; el
   capítulo de `docs/0X` correspondiente si cambia contenido de memoria.
5. Si se tomó una decisión de diseño relevante (parámetros de Kalman/DBSCAN,
   elección de sensor, cambio de arquitectura), añadirla a
   [`docs/05_decisiones.md`](docs/05_decisiones.md) con el motivo.
6. Añadir una entrada fechada en `PROGRESO.md` (estilo diario técnico corto).
   Si aporta contenido para la memoria del TFM, añadir también prosa en
   [`docs/04_diario_desarrollo.md`](docs/04_diario_desarrollo.md).
7. Si se completa un objetivo del TFM, marcarlo en
   [`docs/01_introduccion.md`](docs/01_introduccion.md) (sección 1.2).
8. Dejar `docs/sesion_siguiente.md` actualizado con el plan de la próxima
   sesión — así cualquiera (o Claude, sin memoria de este chat) puede
   continuar sin fricción.
9. Proponer un commit y pedir confirmación antes de crearlo — **el commit en
   sí siempre se confirma con el usuario**. El `git push` posterior, en
   cambio, está pre-autorizado para este proyecto (ver
   `.claude/settings.json`, `permissions.allow`): una vez confirmado el
   commit, empújalo sin volver a preguntar.

## Retomar la sesión sin fricción

- **Atajo:** desde PowerShell, el comando `tfm` (función en el perfil de
  PowerShell de este usuario) se posiciona en este repo y lanza `claude` con
  un prompt de continuación automático — no hace falta escribir nada.
- Como refuerzo, hay un hook de `SessionStart`
  (`.claude/hooks/session_start_context.sh`) que inyecta un recordatorio de
  contexto en cada sesión abierta aquí: si el primer mensaje del usuario no
  trae instrucciones concretas, léase primero `docs/sesion_siguiente.md` y
  `PROGRESO.md` y resúmase el estado antes de esperar más indicaciones. Un
  hook no puede generar un turno de usuario por sí solo — sigue haciendo
  falta que el usuario escriba algo (aunque sea un saludo); el atajo `tfm` es
  lo que de verdad reduce eso a una sola palabra.

## Reglas de este proyecto

- No reescribir la lógica de `tracking_node`/`detection_node` sin leer antes
  `docs/02_arquitectura.md` y la sección relevante de `PROGRESO.md` — hay
  ajustes de parámetros ya validados en el robot real (zona muerta angular,
  Kalman Q/R, DBSCAN eps/min_samples) que no son arbitrarios.
- `docs/01_introduccion.md`, `02_arquitectura.md`, `03_herramientas_ia.md`,
  `04_diario_desarrollo.md` son capítulos de la memoria oficial del TFM — su
  numeración y estilo de prosa son deliberados, no los reestructures como si
  fueran docs técnicos genéricos.
- El código de `legacy_previo/` es una versión anterior heredada, no tocar
  salvo que se pida explícitamente.
