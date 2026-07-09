#!/usr/bin/env bash
# Atajo de continuidad de sesion (Claude-Project-OS). Vive DENTRO del repo a
# proposito: si el portatil del laboratorio no persiste estado entre
# sesiones y hay que clonar de cero, este script se descarga con el
# `git clone` igual que el resto del codigo -- no depende de configuracion
# local de la maquina (.bashrc, perfil de shell, etc).
#
# Uso: desde la raiz del repo, `bash scripts/continue_session.sh`
cd "$(dirname "$0")/.."
claude "Continua el TFM: sigue el flujo de CLAUDE.md, resume el estado leyendo docs/sesion_siguiente.md y PROGRESO.md, y dime en que estamos y cual es el objetivo de hoy."
