#!/usr/bin/env python3
"""Validador formal de especificaciones de Reels (skill guion-reels).

Comprueba tiempos y coherencia formal de un spec YAML. No evalúa la calidad
creativa ni verifica afirmaciones: solo detecta incoherencias de forma.

Uso:
    python3 validate_video_spec.py spec.yaml [otro.yaml ...] [--max-wps 3.0]

Salida: 0 = sin errores (puede haber avisos), 1 = hay errores,
2 = archivo ilegible o falta PyYAML.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

# --- Esquema asumido (ver "Esquema YAML (provisional)" en SKILL.md). ---
# Si las secciones 1-5 de la skill definen otros nombres, cambiarlos aquí.
REQUIRED_TOP = ("duration_s", "scenes", "voiceover_full", "cta",
                "assets", "verification", "production_gate")
START, END = "start_s", "end_s"
VOICEOVER, ON_SCREEN, EVIDENCE = "voiceover", "on_screen_text", "evidence"
EVIDENCE_LABELS = ("REAL_VERIFICADO", "DEMO", "CONCEPTO", "PENDIENTE")
GATE_OK, GATE_PENDING = "APTO_PARA_PRODUCCION", "PENDIENTE_VERIFICACION"

EPS = 1e-3              # tolerancia (s) para continuidad de intervalos
REVIEW_SCENE_S = 4.0    # tramos más largos: revisión manual
DEFAULT_MAX_WPS = 3.0   # umbral heurístico de palabras/segundo; ajustable

# "TODO" va en mayúsculas exactas: "todo" es una palabra común en español.
PLACEHOLDER_CS = re.compile(r"\b(TODO|TBD|FIXME|XXX+)\b")
PLACEHOLDER_CI = re.compile(
    r"lorem ipsum|placeholder|\{\{.*?\}\}|\[(insertar|completar)[^\]]*\]"
    r"|<(insertar|completar)[^>]*>|\bpor definir\b",
    re.IGNORECASE,
)


class Report:
    def __init__(self) -> None:
        self.errors: list[tuple[str, str]] = []
        self.warnings: list[tuple[str, str]] = []
        self.summary: list[str] = []

    def error(self, where: str, msg: str) -> None:
        self.errors.append((where, msg))

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append((where, msg))


def is_number(x: object) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def norm_ws(s: str) -> str:
    return " ".join(s.split())


def fmt(x: float) -> str:
    return f"{x:g}"


def fold(s: str) -> str:
    """Mayúsculas sin tildes, para buscar SIMULACIÓN/SIMULACION/CONCEPTO."""
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn").upper()


def strings_in(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in strings_in(v)]
    if isinstance(value, list):
        return [s for v in value for s in strings_in(v)]
    return []


def walk(value: object, path: str = ""):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from walk(v, f"{path}.{k}" if path else str(k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(value, str):
        yield path, value


def first_diff(a: str, b: str) -> int:
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return min(len(a), len(b))


def check_scenes(data: dict, duration: float | None, max_wps: float, r: Report):
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        r.error("scenes", "debe ser una lista con al menos una escena")
        return [], []

    voiceovers: list[str] = []
    evidences: list[str] = []
    prev_end: float | None = None
    last_end: float | None = None

    for i, sc in enumerate(scenes):
        where = f"scenes[{i}]"
        if not isinstance(sc, dict):
            r.error(where, "cada escena debe ser un mapping (clave: valor)")
            prev_end = last_end = None
            continue
        if "id" in sc:
            where += f" (id={sc['id']})"

        start, end = sc.get(START), sc.get(END)
        times_ok = True
        for key, val in ((START, start), (END, end)):
            if not is_number(val):
                r.error(where, f"falta {key} numérico")
                times_ok = False
            elif val < 0:
                r.error(where, f"{key} negativo ({fmt(val)})")
                times_ok = False
        if times_ok and end <= start:
            r.error(where, f"{END} ({fmt(end)}) debe ser mayor que {START} ({fmt(start)})")
            times_ok = False

        if is_number(start):
            if i == 0 and abs(start) > EPS:
                r.error(where, f"la primera escena debe empezar en 0, empieza en {fmt(start)}")
            elif prev_end is not None and start > prev_end + EPS:
                r.error(where, f"hueco de {fmt(start - prev_end)} s entre {fmt(prev_end)} y {fmt(start)}")
            elif prev_end is not None and start < prev_end - EPS:
                r.error(where, f"superposición de {fmt(prev_end - start)} s con la escena anterior "
                               f"(termina en {fmt(prev_end)}, esta empieza en {fmt(start)})")
        prev_end = last_end = end if is_number(end) else None

        vo = sc.get(VOICEOVER)
        if vo is None:
            vo = ""
        if not isinstance(vo, str):
            r.error(where, f"{VOICEOVER} debe ser texto, \"\" o null")
            vo = ""
        voiceovers.append(vo)

        if times_ok:
            dur = end - start
            words = len(vo.split())
            if words and words / dur > max_wps:
                r.warn(where, f"{words} palabras en {fmt(dur)} s = {words / dur:.1f} palabras/s "
                              f"(umbral {fmt(max_wps)}); comprobar que se puede decir y subtitular en ese tiempo")
            if dur > REVIEW_SCENE_S + EPS:
                r.warn(where, f"tramo de {fmt(dur)} s (> {fmt(REVIEW_SCENE_S)} s): revisar que introduzca "
                              f"información o cambie un estado, o que sea una pausa con función clara")

        ev = sc.get(EVIDENCE)
        if ev not in EVIDENCE_LABELS:
            r.error(where, f"{EVIDENCE} debe ser uno de {', '.join(EVIDENCE_LABELS)} (recibido: {ev!r})")
        else:
            evidences.append(ev)
            if ev == "CONCEPTO":
                shown = fold(" ".join(strings_in(sc.get(ON_SCREEN))))
                if "SIMULACION" not in shown and "CONCEPTO" not in shown:
                    r.warn(where, f"escena CONCEPTO sin 'SIMULACIÓN' ni 'CONCEPTO' en {ON_SCREEN}; "
                                  f"obligatorio si podría confundirse con evidencia real")

    if duration is not None and last_end is not None and abs(last_end - duration) > EPS:
        r.error("scenes", f"la última escena termina en {fmt(last_end)} s pero duration_s es {fmt(duration)}")

    return voiceovers, evidences


def check_voiceover_full(data: dict, voiceovers: list[str], r: Report) -> int:
    expected = " ".join(norm_ws(v) for v in voiceovers if norm_ws(v))
    vf = data.get("voiceover_full")
    if not isinstance(vf, str):
        r.error("voiceover_full", "debe ser texto; usar \"\" si el Reel es mudo")
        return len(expected.split())
    actual = norm_ws(vf)
    if actual != expected:
        i = first_diff(actual, expected)
        lo = max(0, i - 25)

        def snippet(s: str) -> str:
            return ("…" if lo else "") + s[lo:i + 25] + ("…" if len(s) > i + 25 else "")

        r.error("voiceover_full",
                "no coincide con la unión de scenes[].voiceover (solo se normalizan espacios); "
                f"primera diferencia en el carácter {i}: "
                f"voiceover_full «{snippet(actual)}» vs escenas «{snippet(expected)}»")
    return len(expected.split())


def check_cta(data: dict, r: Report) -> None:
    cta = data.get("cta")
    if cta is None or isinstance(cta, dict) and cta:
        return
    if isinstance(cta, str):
        if not cta.strip():
            r.error("cta", "texto vacío; usar null si no hay CTA")
    elif isinstance(cta, list):
        if len(cta) > 1:
            r.error("cta", f"{len(cta)} acciones; se admite null o una sola acción")
        elif len(cta) == 1:
            r.warn("cta", "lista de un elemento; usar directamente el texto de la acción")
        else:
            r.error("cta", "lista vacía; usar null si no hay CTA")
    else:
        r.error("cta", "debe ser null o una sola acción")


def check_verification(data: dict, r: Report):
    v = data.get("verification")
    if not isinstance(v, dict):
        r.error("verification", "debe ser un mapping con 'claims' (lista) y 'blockers' (lista)")
        return [], []
    claims = v.get("claims") or []
    blockers = v.get("blockers") or []
    if not isinstance(claims, list):
        r.error("verification.claims", "debe ser una lista")
        claims = []
    if not isinstance(blockers, list):
        r.error("verification.blockers", "debe ser una lista")
        blockers = []

    statuses: list[str] = []
    for i, c in enumerate(claims):
        where = f"verification.claims[{i}]"
        if not isinstance(c, dict):
            r.error(where, "cada afirmación debe ser un mapping con claim, status y source")
            continue
        if not isinstance(c.get("claim"), str) or not c["claim"].strip():
            r.error(where, "falta el texto de la afirmación (claim)")
        status = c.get("status")
        if status not in EVIDENCE_LABELS:
            r.error(where, f"status debe ser uno de {', '.join(EVIDENCE_LABELS)} (recibido: {status!r})")
            continue
        statuses.append(status)
        has_source = isinstance(c.get("source"), str) and c["source"].strip()
        if status == "REAL_VERIFICADO":
            if not has_source:
                r.error(where, "REAL_VERIFICADO sin source: documentar la prueba o cambiar a PENDIENTE")
            if not c.get("checked_on"):
                r.warn(where, "REAL_VERIFICADO sin checked_on: registrar la fecha de la comprobación")
        elif status == "DEMO" and not has_source:
            r.warn(where, "DEMO sin source: indicar dónde y cuándo se probó")
    return statuses, blockers


def check_gate(data: dict, evidences: list[str], statuses: list[str], blockers: list, r: Report) -> None:
    gate = data.get("production_gate")
    if gate not in (GATE_OK, GATE_PENDING):
        r.error("production_gate", f"debe ser {GATE_OK} o {GATE_PENDING} (recibido: {gate!r})")
        return
    if gate != GATE_OK:
        return
    if "PENDIENTE" in evidences:
        r.error("production_gate", f"{GATE_OK} con escenas en evidencia PENDIENTE; usar {GATE_PENDING}")
    if "PENDIENTE" in statuses:
        r.error("production_gate", f"{GATE_OK} con afirmaciones PENDIENTE en verification; usar {GATE_PENDING}")
    if blockers:
        r.error("production_gate", f"{GATE_OK} con {len(blockers)} bloqueo(s) abiertos en verification.blockers")


def validate(data: object, max_wps: float) -> Report:
    r = Report()
    if not isinstance(data, dict):
        r.error("(raíz)", "el spec debe ser un mapping YAML con las claves del esquema")
        return r

    for key in REQUIRED_TOP:
        if key not in data:
            r.error(key, "clave obligatoria ausente")

    duration = data.get("duration_s")
    if not is_number(duration) or duration <= 0:
        if "duration_s" in data:
            r.error("duration_s", "debe ser un número mayor que 0")
        duration = None

    voiceovers, evidences = check_scenes(data, duration, max_wps, r)
    words = check_voiceover_full(data, voiceovers, r)
    check_cta(data, r)

    if "assets" in data and not isinstance(data["assets"], list):
        r.error("assets", "debe ser una lista; usar [] si no hay recursos confirmados")

    statuses, blockers = check_verification(data, r)
    check_gate(data, evidences, statuses, blockers, r)

    if "REAL_VERIFICADO" in evidences and "REAL_VERIFICADO" not in statuses:
        r.warn("verification", "hay escenas REAL_VERIFICADO pero ninguna afirmación REAL_VERIFICADO con fuente")

    for path, s in walk(data):
        m = PLACEHOLDER_CS.search(s) or PLACEHOLDER_CI.search(s)
        if m:
            r.warn(path, f"posible placeholder «{m.group(0)}»: completar con el dato o registrarlo como bloqueo")

    if duration:
        r.summary.append(f"{fmt(duration)} s, {len(voiceovers)} escena(s), {words} palabra(s) de locución "
                         f"({words / duration:.1f} palabras/s sobre la duración total)")
    r.summary.append(f"production_gate declarado: {data.get('production_gate')!r}")
    return r


def load(path: Path) -> object:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise RuntimeError("falta PyYAML (pip install pyyaml); sin él solo se aceptan specs en JSON")
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise RuntimeError(f"YAML inválido: {e}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Valida tiempos y coherencia formal de specs de Reels.")
    ap.add_argument("files", nargs="+", type=Path, help="archivos YAML (o JSON) del spec")
    ap.add_argument("--max-wps", type=float, default=DEFAULT_MAX_WPS,
                    help=f"umbral heurístico de palabras por segundo por escena (por defecto {DEFAULT_MAX_WPS})")
    args = ap.parse_args()
    if args.max_wps <= 0:
        ap.error("--max-wps debe ser mayor que 0")

    exit_code = 0
    for path in args.files:
        print(f"== {path} ==")
        try:
            data = load(path)
        except (OSError, RuntimeError) as e:
            print(f"NO SE PUDO LEER: {e}")
            exit_code = 2
            continue
        r = validate(data, args.max_wps)
        for where, msg in r.errors:
            print(f"ERROR  {where}: {msg}")
        for where, msg in r.warnings:
            print(f"AVISO  {where}: {msg}")
        for line in r.summary:
            print(f"Resumen: {line}")
        print(f"Resultado: {len(r.errors)} error(es), {len(r.warnings)} aviso(s).")
        if r.errors and exit_code == 0:
            exit_code = 1
    print("Nota: validación formal. No verifica afirmaciones ni aprueba la publicación; "
          "eso exige revisar render, subtítulos, assets, atribuciones y condiciones comerciales.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
