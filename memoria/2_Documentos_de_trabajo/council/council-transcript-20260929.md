# LLM Council — Revisión del TFM antes de la defensa

**Fecha:** 2026-09-29

## Pregunta original del usuario

> Antes de seguir con todo el proceso, pregunta al llm-council, y revisa el TFM.

(En el turno anterior el usuario había pedido: revisar §7.9 porque ya va a presentar el TFM; convertir las figuras del Capítulo 2 de texto ASCII a imágenes reales; y añadir un apartado sobre limitación de hardware del NUC.)

## Pregunta encuadrada para el consejo

Juan Muñoz Rovira va a defender su TFM de forma inminente. Ayer se redujo la memoria de trabajo (`TFM_Memoria_reducida.docx`) de 36 a 28 páginas para caber en el margen de 25-30. Hoy pide tres cambios antes de defender:

1. Reescribir §7.9 "Trabajo pendiente para completar este capítulo" — ya no tiene sentido decir que hay tareas pendientes si va a defenderlo ya.
2. Convertir las figuras del Capítulo 2 (diagramas ASCII en texto monoespaciado: flujo de nodos, máquina de estados, árbol de TF, dependencias del paquete, arquitectura Nav2) en imágenes reales.
3. Añadir un apartado de limitación de hardware: el NUC embarcado no soportaba bien tantos procesos a la vez, con desconexiones ocasionales, lo que obligó a optimizar mucho el código.

**No señalado por el usuario:** §7.8/Capítulo 1/§5.10 siguen diciendo "objetivo 5 sin probar" y "Fase 4 en curso", pero un hito más reciente — el "gesto casa", validado en el robot real el 23/09/2026: 9/11 vueltas a casa completadas (82%), error de llegada 0,27 m/8°, cancelación confirmada por Nav2 en 20 ms, 0 falsos positivos del gesto — no aparece en ningún sitio de la memoria, pese a ser la primera integración real de seguimiento + navegación (primer paso hacia el objetivo 5).

**Pregunta al consejo:** ¿Está la memoria lista para defenderse tal cual? ¿Qué riesgos ve un tribunal en el estado actual, especialmente en el capítulo de resultados y limitaciones? ¿Es correcto el enfoque propuesto para los tres cambios, antes de ejecutarlos?

---

## Respuestas de los asesores

### El Contrarian
El Contrarian's view: not ready to defend. The three fixes he asked for are cosmetic, and the real problem is somewhere else.

**The fatal flaw is Chapter 7, not §7.9.** The memoria tells the tribunal that objective 5 is "untested" and that Phase 4 is "ongoing." It also says the chapter is still "andamiaje de tablas y notas" (scaffolding of tables and notes). Meanwhile his strongest result, gesto casa (82% return home, 0.27 m arrival error, 20 ms cancellation), is missing from the document. If he shows it in the slides, the examiners see a thesis that contradicts itself. If he leaves it out, he defends a weaker thesis than the one he actually built. Either way he loses.

**Change 1 only hides the symptom.** Deleting "pending tasks" leaves §7.8 still saying the validation is unfinished, and the chapter still reads as notes. The fix is to turn §7.9 into "Trabajo futuro" and clean up §7.8 in the same pass. Also, were the stop and occlusion scenarios ever repeated? If not, the sample size is tiny, and the text has to say so honestly rather than just drop the word "pending."

**Change 2 can add new errors.** Redrawing five diagrams under time pressure risks node or topic names that don't match the real code. Examiners who know ROS will notice. Two better options:
- For Figures 2.1 and 2.3, use the real outputs of `rqt_graph` and `view_frames`.
- For the others, check every label against the repo.

Images also take more space than monospace text, so 28 pages could turn into 31.

**Change 3 invites attack unless it has numbers.** "The NUC couldn't cope" will get questions: which processes? What CPU and RAM load? What was disconnecting: the LiDAR, the Kobuki USB link, or Wi-Fi? What exactly was optimized, and by how much? Without figures it sounds like an excuse. With figures it becomes a real contribution.

**Question he's avoiding:** has the memoria already been formally submitted (depositada)? If so, he may not be allowed to edit it. In that case the gesto casa results and the corrections have to go in the slides, and he should explain the gap openly at the start of the defense rather than let an examiner find it.

**Overclaim risk:** 11 attempts, and "0 false positives in ~4 min", are too few to draw firm conclusions. He should present them as a first integration, not as validation of objective 5.

### El First Principles Thinker
He's asking the wrong question. What he's actually asking is: "Does this document honestly show the tribunal the most I achieved?" Right now it doesn't, and none of his three changes fix that.

**The real defect is not the pending-work wording in §7.9. The memoria stops before his best result.** The tribunal will score the thesis against its stated objectives. Chapter 1, §5.10 and §7.8 all tell them objective 5 (follow a person, then navigate) is untested. His one real tracking-plus-navigation integration is missing from the document: 9 of 11 home returns completed, 0.27 m / 8° arrival error, 0 false positives. So he is defending the older, weaker thesis.

**Rewriting §7.9 alone makes things worse.** If the text says validation is closed while §7.8 still says Phase 4 is ongoing and objective 5 is untested, the chapter contradicts itself. Examiners notice that kind of mismatch. The honest fix:
- Delete §7.9.
- Move "more repetitions" into limitations as a sample-size limitation.
- Face item (3) head-on: the chapter itself admits it is still "andamiaje" (scaffolding). Removing the paragraph that says so doesn't remove the scaffolding.

**Before any editing, check whether the memoria is already deposited.** If it is, edits to the .docx are wasted. The fight moves to the slides and his spoken answers. Gesto casa then has to lead the demo and results slides, and he needs a prepared line for why the document says objective 5 is untested.

**The NUC limitation is only worth adding with evidence.** Without it, it reads as an excuse. He needs specifics: which processes were running, what the symptom was (disconnections, CPU saturation), and what he optimized, with before/after figures if he has them. Framed that way it becomes an engineering contribution.

**The ASCII figures come last.** They look unprofessional but won't change the grade. Do them only if time is left over.

**Priority order:**
1. Confirm whether the document can still change.
2. Add gesto casa to Chapter 7, the objectives table and §5.10, and update the objective 5 status to "first integration validated" (about one page; 28 pages leaves room).
3. Remove §7.9 and make §7.8 consistent with the new results.
4. Add the NUC limitation with evidence.
5. Replace the figures.

### El Expansionist
He's about to defend a thesis that leaves out its best result. "Gesto casa" is the first working integration of tracking and navigation on the real robot: 9 of 11 returns home (82%), 0.27 m / 8° arrival error, cancellation confirmed in 20 ms, zero gesture false positives. That is objective 5's first real step. Right now the memoria tells the tribunal "Objetivo 5 sin probar," so he gives up his strongest card and invites the obvious question: "so the two halves never worked together?"

The upside play:

1. **Don't just rewrite §7.9. Replace it.** Turn the "pending work" section into "§7.9 Validación integrada: retorno autónomo a casa por gesto." Put the metrics in one compact table and add two sentences explaining that both failures came from AMCL imprecision (±0.5 m), not from the gesture detection or the state machine. It uses about the same page space, so he stays inside the 30-page limit. Then update three lines: the §7.8 bullet about objective 5, the Ch.1 objectives table ("parcialmente alcanzado"), and the §5.10 synthesis. The chapter goes from "unfinished" to "we closed the loop."

2. **Present the NUC limitation as engineering work, not a confession.** "The NUC couldn't cope" reads as a weakness. "Resource-constrained deployment forced aggressive optimization" is a contribution. If he has any numbers (CPU load before and after, reduced topic rates, nodes merged, lighter MediaPipe model), one sentence with them makes this item part of the method.

3. **Chapter 2 figures: yes, and reuse them.** Real diagrams are the right call. Build them once as clean vector images and put the same files straight into the defense slides. The FSM figure (2.2) should show the new home-return state, so it visually backs up the new result.

4. **For the defense itself:** open or close with a 20-second clip of the robot returning home on the gesture. Tribunals remember a working demo.

Doing only the three requested changes gets him a safe defense. Adding the gesto casa result is what makes it a strong one.

### El Outsider
Reading this cold, the memoria looks unfinished, and his three changes only fix what it looks like.

**What a stranger reads in Chapter 7.** §7.8 says "Objetivo 5 sin probar" and "Phase 4 ongoing." §7.9 lists "pending tasks." Its item (3) literally says the chapter is still made of tables and notes that should be rewritten as prose later. If he only rewrites §7.9's wording, the chapter under it still admits it is a draft. Juan says it's "pretty good" because he knows what was really done, so his eye skips over "sin probar." An examiner won't skip it.

**The biggest problem is missing, not wrong.** The home-gesture result (9 of 11 returns home, 82%) is the only thing here that joins person-following with autonomous navigation, and that is exactly objective 5. The document tells the tribunal he didn't get there. If he demos or mentions the feature on the day, the first question will be "why isn't this in your written work?" That hurts more than any ASCII diagram. At minimum:
- change "sin probar" to "partially validated" and give the numbers
- add one row to the objectives table
- add one short paragraph in Chapter 7

That is about half a page.

**On his three changes:**
1. **§7.9:** Don't just delete it. Rename it "Trabajo futuro" and keep it honest. Don't suggest the repeat tests were done if they weren't.
2. **Diagrams:** Yes. Box-drawing characters look like a draft to anyone outside the field. It is still the least urgent of the three. Warning: images take more space than text, and he is at 28 of 30 pages. Check the page count after.
3. **NUC limitation:** As he phrased it, it sounds like an excuse. It needs concrete facts: which processes were running, what the CPU load was, how often it disconnected, and what exactly was optimized. Without those, a tribunal reads "our computer was bad."

**Suggested order:** first fix the objective-5 contradiction, then §7.9, then the NUC item, and the diagrams last.

### El Executor
It's not ready to defend yet, but it can be fixed today. The biggest risk isn't on his list of three changes. §7.8 says "Objetivo 5 sin probar" and describes Phase 4 as still ongoing. If he demos or mentions the "gesto casa" feature (9/11 returns home, 82%), the tribunal will spot that contradiction within five minutes. Fix that first. His three changes come after it.

**Order for today (about 3–4 h):**

0. **Save a copy first** as `TFM_Memoria_reducida_v2.docx`. Every edit goes into v2.
1. **§7.9 (15 min).** Replace the section with a closing paragraph called "Estado final de la validación" (final state of the validation). It says what was validated, over how many sessions, and moves "repetir escenarios" (repeat the scenarios) into Future Work. Delete sentence (3) about the tables and notes scaffolding entirely. A tribunal should never read a note to the author.
2. **Gesto casa (45 min). Ask Juan before doing it**, because it's outside his three requests. Keep it small:
   - one new subsection 7.x with a 5-row metric table (82%, 15.5 s, 0.27 m / 8°, 20 ms cancellation, 0 false positives), and the 2 failures attributed to AMCL;
   - change the objective 5 row in the Ch.1 table to "Parcial";
   - add one sentence in §5.10;
   - rewrite the "sin probar" bullet in §7.8.
   That's about 1 page, and he has 2 pages spare before the 30-page limit.
3. **NUC limitation (15 min).** One bullet in §7.8. Before writing it, get from Juan one concrete fact about what he optimized: which nodes, the frame rate, or the CPU load. Without it, the tribunal's obvious follow-up ("what exactly did you optimize?") leaves him exposed.
4. **Figures (90 min, highest risk).**
   - Build each figure in Graphviz, export PNG at 300 dpi, and swap it in with python-docx so the existing captions stay.
   - Order: 2.2 FSM → 2.1 → 2.5 → 2.3 → 2.4.
   - The FSM figure (2.2) must include the HOME state, or it contradicts step 2.
   - If time runs out, the remaining figures stay as ASCII. That's ugly, but a tribunal won't fail him for it; it will for the objective 5 contradiction.
5. **Close out (20 min).** Update the table of contents and list of figures, export to PDF, check it's 30 pages or fewer, and check every cross-reference to a figure or section number.

Then make sure his slides say the same thing about objective 5.

---

## Revisión por pares (anonimizada: A=Expansionist, B=Outsider, C=First Principles, D=Executor, E=Contrarian)

### Revisor: Contrarian
1. Strongest: D. It is the only response that turns the diagnosis into a timed, ordered plan he can do today. It saves a v2 copy first. It asks Juan before adding gesto casa, since he didn't request it. It keeps the FSM figure consistent with the new HOME state and allows the ASCII figures to stay if time runs out. It checks the 30-page limit and makes the slides match. Its one gap is that it never asks whether the memoria has already been deposited. C and E both raise that, and D should adopt it as step 0.
2. Biggest blind spot: A. It oversells: 11 trials become "we closed the loop" and a full "Validación integrada" section. It also blames both failures on AMCL without asking whether that was verified. It ignores the "andamiaje" note in Chapter 7, the deposit question, and the need for honest future work. E's overclaim warning is exactly what A lacks.
3. What all five missed: the abstract/resumen and conclusions chapter probably also say objective 5 is untested; the gesto casa numbers need a traceable source (logs/rosbags, date, conditions); the tutor should approve adding a new result days before the defense; nobody prepared answers for the obvious tribunal questions (why only 11 trials, why AMCL failed, how safe the cancellation is).

### Revisor: First Principles
1. Strongest: D. It turns the diagnosis into a time-boxed plan Juan can finish today. It fixes the objective-5 contradiction first and saves a v2 copy before editing. It asks Juan before adding gesto casa. It requires the FSM figure to show the HOME state and allows the ASCII figures to stay if time runs out. Its weakness is that it misses E's overclaim warning and the deposit question raised by C and E.
2. Biggest blind spot: A. It oversells the result — 11 trials become "closing the loop," blames both failures on AMCL without evidence, never asks whether the memoria is deposited, ignores the "andamiaje" note.
3. What all five missed: the tribunal may already have a specific version — any change needs tutor approval and should be flagged openly; the NUC limitation and gesto casa are connected (did disconnections cause the two failed returns?); time spent editing is time not spent rehearsing answers.

### Revisor: Expansionist
1. Strongest: D. It is the only response a person could act on today — v2 copy, objective-5 contradiction first, "andamiaje" note deleted, asks before adding content not requested, FSM must show HOME state, ends with page count/cross-reference/slide-consistency pass.
2. Biggest blind spot: A. All upside, no guardrails — never asks about deposit status, ignores the "andamiaje" admission, overclaims "we closed the loop" on thin data, assumes a video exists.
3. What everyone missed: the abstract/resumen almost certainly repeats "objective 5 untested" and is the first page read; supervisor sign-off; the NUC item and gesto casa are the same story (resource contention may explain the AMCL failures); rehearsal time was never weighed against editing time.

### Revisor: Outsider
1. Strongest: D — the only response Juan can follow step by step today, with time estimates, a backup-first instruction, and a fallback. Gap: never asks whether the memoria is already formally submitted.
2. Biggest blind spot: A — only sees upside, removes future work outright, claims AMCL caused both failures without evidence, treats 11 trials as closing the loop, ignores the "andamiaje" note and the edit-ability question.
3. What all five missed: the abstract and general conclusions read first by the tribunal; possible damage (broken cross-references, orphaned figure numbers) from yesterday's 36→28 page cut, never rechecked; the supervisor should approve changes to objectives' status on defense day; Juan needs prepared answers regardless of whether the text changes.

### Revisor: Executor
1. Strongest: D — the only response that turns the diagnosis into an executable, time-boxed plan with a fallback and a page-limit check. Gap: never asks whether the memoria has already been deposited (C, E do).
2. Biggest blind spot: A — presents 9/11 over ~4 minutes as "we closed the loop" with no small-sample warning, asserts AMCL caused both failures with no evidence, assumes the document can still be edited, skips the "andamiaje" note and the page-limit risk of adding images.
3. What all five missed: supervisor sign-off; version mismatch risk (tribunal may already hold the 28-page PDF); no full reread after the 36→28 cut for orphaned references; evidence (logs/video) for a result that is only 6 days old; Q&A rehearsal time may be worth more than more editing.

---

## Veredicto del presidente (Chairman)

### Where the Council Agrees
- The memoria is **not actually ready to defend** — not because of the three changes Juan listed, but because of something he didn't flag: Chapter 7 (§7.8, §7.9), the Chapter 1 objectives table, and §5.10 all still say objective 5 is "untested" and Phase 4 is "ongoing," while the thesis's most complete and novel real-robot result — **gesto casa** (9/11 home returns, 82%, 0.27 m / 8° arrival error, 20 ms cancellation, 0 false positives, validated 2026-09-23) — is absent from the document entirely. Every advisor and every reviewer independently converged on this as the real risk, bigger than any of the three requested edits.
- Rewriting §7.9 in isolation, as originally requested, **makes the document worse, not better**: it would claim validation is "closed" while §7.8 still says it's unfinished and objective 5 is untested — a direct self-contradiction a tribunal will catch.
- Change 2 (real diagram images) is worth doing but is **lowest priority and carries real risk**: relabeling five diagrams under time pressure can introduce mismatches with the actual code, and images take more vertical space than monospace text — the document is already at 28 of a 25-30 page budget, so this must be checked against the limit afterward.
- Change 3 (NUC hardware limitation) is legitimate but **needs concrete numbers** (which processes, CPU/RAM load, what disconnected, what was optimized and by how much) or it reads as an excuse rather than an engineering finding.
- **Before touching the document at all**, the council unanimously flags one unasked question: has the memoria already been formally submitted ("depositada") to the university? If so, editing the .docx may be moot — the correction has to happen in the slides and in what Juan says out loud at the defense.
- The Executor's response (anonymized as D) was independently picked as the strongest by all five peer reviewers — the only one that turned the diagnosis into a concrete, ordered, time-boxed plan with a safety fallback.

### Where the Council Clashes
The one real disagreement is about **posture**, not facts. The Expansionist (A) says: go big — replace §7.9 outright with a "Validación integrada" section that frames gesto casa as having "closed the loop" on objective 5, updating the objectives table to a strong result.

Every other advisor and every peer reviewer pushed back on exactly this, independently: 11 attempts and ~4 minutes of gesture testing is **too thin a sample** to claim the tracking+navigation integration is "solved." The Contrarian named this explicitly as an overclaim risk; four of five peer-review rounds flagged A's response as the council's biggest blind spot for the same reason.

This is a real tension worth resolving deliberately, not smoothing over: an academic tribunal rewards **honest framing of a genuinely good result** far more than a triumphant claim that invites an easy "n=11?" rebuttal. The council sides with the cautious majority here: present gesto casa as a validated **first step / first integration**, name the small sample size in the text itself, and let the numbers speak for themselves rather than declaring victory.

### Blind Spots the Council Caught
Only visible through peer review — no single advisor response contains all of these:
1. **The abstract/resumen and the final Conclusions chapter** almost certainly repeat the same stale "objective 5 untested" language — and the abstract is the first page any examiner reads. None of the five original responses scoped the fix beyond Ch.1/§5.10/§7.8/§7.9.
2. **Whether the memoria is already formally deposited** with the university. If it is, no .docx edit reaches the tribunal — the correction must happen in the slides and spoken defense, disclosed openly rather than hidden.
3. **The tutor (Enric Cervera) should sign off** on adding a new validated result days before the defense — this is new academic content, not just a formatting fix.
4. **Yesterday's 36→28 page cut was never rechecked** for collateral damage — orphaned cross-references, renumbered figures, or sections that point to material that no longer exists.
5. **The NUC limitation and the two gesto casa failures may be the same story.** Running LiDAR detection, camera/MediaPipe, SLAM/Nav2, and tracking simultaneously on one embedded CPU is a very plausible root cause for the ±0.5 m AMCL imprecision behind both failed home-returns. Told together, the "hardware limitation" item stops sounding like an excuse and becomes the causal explanation for a specific, already-documented result — a materially stronger version of item 3 than standing alone.
6. **Time itself is the scarcest resource today.** Every peer-review round flagged that document polish competes directly with rehearsing answers to the three questions a tribunal will obviously ask: why only 11 trials, what exactly caused the two AMCL failures, and what precisely was optimized on the NUC. That rehearsal time may matter more for the final grade than any further editing.

### The Recommendation
Do not execute the three requested changes as narrowly scoped — that produces a document that is still internally contradictory and still missing its best evidence. Instead, treat the three changes as part of one coherent fix, anchored on reconciling the memoria's own internal story about objective 5:

1. **Gate everything on one question:** confirm with Juan whether the memoria has already been formally submitted/deposited. If yes, redirect all effort to the slides and spoken defense instead of the .docx.
2. **Work on a fresh copy**, never the file that may already be with the tribunal.
3. **Add gesto casa compactly** (one metrics table + a short paragraph) to Chapter 7, update the Chapter 1 objectives-table row and the §5.10 synthesis to "first step validated" — framed cautiously, sample size named explicitly — and check the abstract/resumen and Conclusions chapter for the same stale language.
4. **Rewrite §7.9 as "Trabajo futuro,"** consistent with the now-updated §7.8, not as an isolated cosmetic fix.
5. **Add the NUC limitation with concrete numbers**, explicitly linked to the two gesto casa failures if the causal story holds (ask Juan for the specific facts first — which nodes, what CPU/RAM load, what disconnected).
6. **Do the diagram-to-image conversion last**, and re-check the total page count stays within 25-30 afterward.
7. **Reserve real time to rehearse** answers to the three questions this council identified as the tribunal's obvious follow-ups.

### The One Thing to Do First
**Ask Juan directly, before touching the document again: has the memoria already been formally submitted/deposited to the university?** That single answer determines whether today's work happens in the .docx at all — or entirely in the slides and in what he says out loud at the defense.

---

*Consejo ejecutado con 5 asesores (Contrarian, First Principles, Expansionist, Outsider, Executor) más una ronda de revisión por pares anonimizada, sobre la memoria del TFM de Juan Muñoz Rovira, antes de aplicar los tres cambios solicitados el 2026-09-29.*
