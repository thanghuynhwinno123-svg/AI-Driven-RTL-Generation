import json
import re


def _context(lines, index, before=2, after=6):
    start = max(0, index - before)
    end = min(len(lines), index + after + 1)
    return "\n".join(lines[start:end])


def _find_source_location(text):
    patterns = [
        r'"([^"]+\.sv)"\s*,\s*(\d+)',
        r'([A-Za-z0-9_./-]+\.sv)\s*[: ,]+\s*(\d+)',
        r'File:\s*([A-Za-z0-9_./-]+\.sv).*?Line:\s*(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1), int(match.group(2))
    return None, 0


def _make_error(kind, message, context, file_name=None, line_no=0, source="vcs", infrastructure=False):
    if file_name is None or line_no is None:
        line_no = 0
    return {
        "kind": kind,
        "source": source,
        "severity": "error",
        "file": file_name or "",
        "line": int(line_no),
        "is_source_location": bool(file_name and line_no),
        "is_infrastructure": bool(infrastructure),
        "message": message.strip(),
        "context": context.strip(),
    }


def _runtime_error_kind(line):
    if re.search(r"^\s*FAIL\s*:", line, re.IGNORECASE | re.MULTILINE):
        return "tb_oracle_mismatch"
    if re.search(r"\b(expected|expect)\b.*\b(got|actual)\b|\bMISMATCH\b", line, re.IGNORECASE):
        return "tb_oracle_mismatch"
    return "runtime_or_assertion"


def _is_noise_error_line(line):
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith('echo "ERROR:') or stripped.startswith("echo 'ERROR:"):
        return True
    if re.fullmatch(r"\d+\s+errors?", stripped, re.IGNORECASE):
        return True
    if stripped.startswith("CPU time:"):
        return True
    if re.search(r"srun: error:.*exit code", stripped, re.IGNORECASE):
        return True
    return False


def _has_vcs_simulation_report(log_text):
    text = log_text or ""
    return bool(
        re.search(r"V\s*C\s*S\s+S\s*i\s*m\s*u\s*l\s*a\s*t\s*i\s*o\s*n\s+R\s*e\s*p\s*o\s*r\s*t", text, re.IGNORECASE)
        or re.search(r"VCS\s+Simulation\s+Report", text, re.IGNORECASE)
    )


def _has_finish(log_text):
    return bool(re.search(r"\$finish\b", log_text or "", re.IGNORECASE))


def _has_real_nonzero_or_infra_failure(log_text):
    text = log_text or ""
    if re.search(r"\bsrun:\s+error:", text, re.IGNORECASE):
        return True
    if re.search(r"\b(exit code|exited with|returned non-zero|non[- ]zero)\b", text, re.IGNORECASE):
        return True
    return False


def parse_vcs_log(log_text: str):
    lines = (log_text or "").splitlines()
    errors = []
    consumed = set()

    for idx, line in enumerate(lines):
        code = re.search(r"Error-\[([^\]]+)\]", line)
        if not code:
            continue
        window = _context(lines, idx, 0, 8)
        file_name, line_no = _find_source_location(window)
        errors.append(_make_error(code.group(1), line, window, file_name, line_no))
        consumed.update(range(idx, min(len(lines), idx + 9)))

    for idx, line in enumerate(lines):
        if idx in consumed or _is_noise_error_line(line):
            continue
        if "FAIL_WATCHDOG:" in line or "WATCHDOG_TIMEOUT" in line:
            window = _context(lines, idx, 2, 4)
            file_name, line_no = _find_source_location(window)
            errors.append(_make_error("watchdog_timeout", line, window, file_name, line_no))
            continue
        if re.match(r"\s*ERROR:\s*No module found", line, re.IGNORECASE):
            errors.append(_make_error("tool_setup", line, _context(lines, idx, 1, 3), infrastructure=True))
            continue
        if re.match(r"\s*Error:\s*", line, re.IGNORECASE):
            window = _context(lines, idx, 2, 5)
            file_name, line_no = _find_source_location(window)
            errors.append(_make_error(_runtime_error_kind(window), line, window, file_name, line_no))
            continue
        if re.search(r"(\$fatal\b|\$error\b|Assertion failed|ASSERTION FAILED|UVM_FATAL|UVM_ERROR)", line, re.IGNORECASE):
            window = _context(lines, idx, 2, 5)
            file_name, line_no = _find_source_location(window)
            errors.append(_make_error(_runtime_error_kind(window), line, window, file_name, line_no))
            continue
        if re.search(r"^\s*FAIL\s*:|\b(TEST|SIMULATION|CHECK|SCOREBOARD)\s+(FAILED|FAIL)\b|\bMISMATCH\b", line, re.IGNORECASE):
            window = _context(lines, idx, 2, 5)
            file_name, line_no = _find_source_location(window)
            errors.append(_make_error("tb_oracle_mismatch", line, window, file_name, line_no))

    has_finish = _has_finish(log_text)
    has_report = _has_vcs_simulation_report(log_text)
    clean_sim_completed = has_finish and has_report

    if not errors and not clean_sim_completed and _has_real_nonzero_or_infra_failure(log_text):
        errors.append(_make_error("unknown", "VCS did not complete cleanly", (log_text or "")[-2000:]))

    passed = len(errors) == 0 and clean_sim_completed
    status = "pass" if passed else ("fail" if errors else "incomplete")
    return {
        "schema_version": "1.0",
        "tool": "vcs",
        "passed": passed,
        "status": status,
        "has_finish": has_finish,
        "has_vcs_simulation_report": has_report,
        "errors": errors[:20],
    }


def diagnosis_to_text(diagnosis) -> str:
    return json.dumps(diagnosis, indent=2, ensure_ascii=False)
