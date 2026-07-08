#!/usr/bin/env bash
# SessionStart hook: primes Claude to resume the TFM from where it was left,
# per the Claude-Project-OS methodology (see CLAUDE.md).
cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"Recordatorio de continuidad (Claude-Project-OS): si el usuario no da instrucciones especificas en su primer mensaje (p.ej. solo saluda o dice 'continua'), antes de responder lee docs/sesion_siguiente.md y PROGRESO.md, resume en 3-5 lineas el estado actual del TFM y el siguiente paso propuesto en sesion_siguiente.md, y pregunta si se sigue con eso o con otra cosa. No esperes un prompt largo del usuario para arrancar."}}
JSON
