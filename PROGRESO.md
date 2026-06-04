# Diario de progreso — TFM Person Follower

## Sesión 2026-06-04

### Estado al inicio
- El robot seguía "a trompicones": movimiento errático, obstacle avoidance permanentemente saturado, posiciones outliers a 3-5m, FSM oscilando IDLE↔TRACKING constantemente.

### Cambios aplicados

#### detection_node.py
- Defaults alineados con config.yaml (dbscan_min_samples, min/max_leg_cluster_size, max_leg_radius, max_leg_distance)
- Fix interpolate_lidar_points: np.arange → np.linspace (evitaba mismatch por precisión float)
- Circularity filter relajado 0.3 → 0.15 (rechazaba piernas válidas)
- Filtro outliers: candidate_positions filtradas por max_detection_distance (2.5m)

#### tracking_node.py
- obstacle_threshold parametrizado (antes hardcoded 0.65m → ahora 0.35m desde config)
- Zona muerta angular ±8°: elimina micro-oscilaciones cuando la persona está enfrente
- Clamp derivada angular (±0.3): evita pico angular brusco tras pérdida de detección
- Acoplamiento wz-vx: menos giro cuando el robot avanza rápido
- Saturación wz reducida ±1.8 → ±1.0 rad/s
- Reset prev_angle en _stop(): arranque suave tras estado IDLE

#### config.yaml
- target_distance: 0.4 → 1.0m
- max_speed: 0.4 → 0.3 m/s
- obstacle_threshold: 0.35m (excluye estructura del robot)
- max_detection_distance: 2.5m (filtro outliers lejanos)
- detection_loss_frames: 4 → 8 (FSM más estable)
- kalman_q: 0.02 → 0.01 / kalman_r: 0.04 → 0.15 (posición más suave)

### Estado al final
- Robot sigue a la persona de forma estable a ~1m
- Oscilación angular reducida significativamente
- Sin saturación de obstacle avoidance
- FSM estable

---

## Pendiente — próximas sesiones

### Prioridad ALTA
1. **Cámara HOG no detecta** (`cam: False` siempre)
   - Verificar que /dev/video0 funciona: `v4l2-ctl --list-devices` en NUC
   - Probar captura directa: `python3 -c "import cv2; cap=cv2.VideoCapture(0); print(cap.read()[0])"`
   - Si HOG falla: activar MediaPipe (`use_mediapipe: True` en config) o bajar `hog_min_weight` de 0.40 a 0.25
   - Con cámara funcionando: el seguimiento será más robusto en oclusiones LIDAR

2. **Detección LIDAR intermitente**
   - Streak resetea cada 3-4 scans → posición salta → oscilación residual
   - Probar bajar dbscan_eps de 0.12 a 0.10 o subir a 0.15
   - Probar bajar dbscan_min_samples de 4 a 3

### Prioridad MEDIA
3. **Oscilación angular residual**
   - Si sigue molestando: bajar angular_gain de 1.2 a 0.8 en config NUC
   - O aumentar zona muerta de 8° a 12°

4. **Grabación de demostración**
   - Grabar vídeo del robot siguiendo para incluir en TFM
   - Usar `ros2 bag record` para grabar datos de los topics
