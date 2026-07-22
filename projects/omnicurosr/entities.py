import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class DetectedEntity:
    kind: str          
    value: str         
    label: str         


URL_PATTERN = re.compile(r"https?://[^\s\)]+")
CODE_BLOCK_PATTERN = re.compile(r"```(?:\w+)?\n(.*?)```", re.DOTALL)
LIST_ITEM_PATTERN = re.compile(r"^\s*[-*\d]+[\.\)]?\s+.+", re.MULTILINE)


def detect_entities(source_text: str, answer_text: str) :
    entities = []
    combined = f"{source_text}\n{answer_text}"

    url_match = URL_PATTERN.search(combined)
    if url_match:
        entities.append(DetectedEntity(kind="url", value=url_match.group(0), label="Open Link"))

    code_match = CODE_BLOCK_PATTERN.search(answer_text)
    if code_match:
        entities.append(DetectedEntity(kind="code", value=code_match.group(1).strip(), label=" Copy Code"))

    list_matches = LIST_ITEM_PATTERN.findall(answer_text)
    if len(list_matches) >= 2:   
        list_text = "\n".join(list_matches)
        entities.append(DetectedEntity(kind="list", value=list_text, label="Copy as List"))

    return entities