import json
import re
from pathlib import Path


def read_text_tree(root: str, glob: str = "*.md") -> str:
    base = Path(root)
    if not base.exists():
        return ""
    chunks = []
    for path in sorted(base.glob(glob)):
        if path.is_file():
            chunks.append(f"\n// ===== {path.as_posix()} =====\n{path.read_text(encoding='utf-8', errors='ignore')}\n")
    return "".join(chunks)


def extract_json_object(text: str):
    if not text:
        raise ValueError("empty JSON text")
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return json.loads(fenced.group(1))
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found")
    return json.loads(text[start:end + 1])


def stable_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
