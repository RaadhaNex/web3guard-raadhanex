import hashlib
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SolidityFunction:
    name: str
    signature: str
    start_line: int
    end_line: int
    body: str
    visibility: str | None
    modifiers: list[str]


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def normalize_newlines(code: str) -> str:
    return code.replace("\r\n", "\n").replace("\r", "\n")


def lines(code: str) -> list[str]:
    return normalize_newlines(code).splitlines()


def line_text(code: str, line_number: int | None) -> str | None:
    if line_number is None:
        return None
    all_lines = lines(code)
    if line_number < 1 or line_number > len(all_lines):
        return None
    return all_lines[line_number - 1].strip()


def first_match_line(code: str, pattern: str, flags: int = re.IGNORECASE | re.MULTILINE) -> tuple[int | None, re.Match[str] | None]:
    for index, line in enumerate(lines(code), start=1):
        match = re.search(pattern, line, flags=flags)
        if match:
            return index, match
    return None, None


def all_match_lines(code: str, pattern: str, flags: int = re.IGNORECASE | re.MULTILINE) -> list[tuple[int, re.Match[str]]]:
    found: list[tuple[int, re.Match[str]]] = []
    for index, line in enumerate(lines(code), start=1):
        match = re.search(pattern, line, flags=flags)
        if match:
            found.append((index, match))
    return found


def extract_functions(code: str) -> list[SolidityFunction]:
    """Lightweight Solidity function extractor.

    This intentionally avoids executing any compiler. It is a heuristic parser for MVP
    line/function context and should be replaced or complemented with a Solidity AST later.
    """
    code_lines = lines(code)
    functions: list[SolidityFunction] = []
    i = 0
    while i < len(code_lines):
        line = code_lines[i]
        if not re.search(r"\bfunction\b", line):
            i += 1
            continue

        start = i
        signature_lines = [line.strip()]
        while "{" not in " ".join(signature_lines) and i + 1 < len(code_lines):
            i += 1
            signature_lines.append(code_lines[i].strip())
            if ";" in code_lines[i]:
                break

        signature = " ".join(signature_lines)
        if "{" not in signature:
            i += 1
            continue

        brace_count = signature.count("{") - signature.count("}")
        body_lines: list[str] = []
        i += 1
        while i < len(code_lines) and brace_count > 0:
            current = code_lines[i]
            brace_count += current.count("{") - current.count("}")
            body_lines.append(current)
            i += 1
        end = max(start, i - 1)
        full_body = "\n".join([signature, *body_lines])

        name_match = re.search(r"function\s+([A-Za-z_][A-Za-z0-9_]*)", signature)
        name = name_match.group(1) if name_match else "fallback_or_receive"
        visibility_match = re.search(r"\b(public|external|internal|private)\b", signature)
        visibility = visibility_match.group(1) if visibility_match else None
        modifier_tokens = _extract_modifiers(signature)
        functions.append(
            SolidityFunction(
                name=name,
                signature=signature,
                start_line=start + 1,
                end_line=end + 1,
                body=full_body,
                visibility=visibility,
                modifiers=modifier_tokens,
            )
        )
    return functions


def _extract_modifiers(signature: str) -> list[str]:
    before_body = signature.split("{", 1)[0]
    after_params = before_body.rsplit(")", 1)[-1] if ")" in before_body else before_body
    keywords = {
        "public", "external", "internal", "private", "view", "pure", "payable", "virtual", "override", "returns", "memory", "calldata", "storage"
    }
    tokens = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", after_params)
    return [token for token in tokens if token not in keywords]


def function_at_line(functions: list[SolidityFunction], line: int | None) -> SolidityFunction | None:
    if line is None:
        return None
    for fn in functions:
        if fn.start_line <= line <= fn.end_line:
            return fn
    return None


def has_access_control(fn: SolidityFunction) -> bool:
    signature = fn.signature
    body = fn.body
    access_patterns = [
        r"\bonlyOwner\b",
        r"\bonlyRole\b",
        r"\bonlyAdmin\b",
        r"\brequiresAuth\b",
        r"\bauth\b",
        r"\brequire\s*\([^;]*(msg\.sender|_msgSender\s*\(\s*\))[^;]*(owner|admin|role|hasRole|isOwner|authorized|treasury|governance)",
        r"\bif\s*\([^;]*(msg\.sender|_msgSender\s*\(\s*\))[^;]*(owner|admin|role|hasRole|authorized)",
    ]
    return any(re.search(pattern, signature + "\n" + body, flags=re.IGNORECASE | re.DOTALL) for pattern in access_patterns)


def emits_event(fn: SolidityFunction) -> bool:
    return bool(re.search(r"\bemit\s+[A-Za-z_][A-Za-z0-9_]*\s*\(", fn.body))


def is_publicly_reachable(fn: SolidityFunction) -> bool:
    return fn.visibility in {"public", "external"}


def contains_state_write(text: str) -> bool:
    state_write_patterns = [
        r"\b[A-Za-z_][A-Za-z0-9_]*(\[[^\]]+\])?\s*(\+\+|--|[+\-*/]?=)",
        r"\.push\s*\(",
        r"\.pop\s*\(",
        r"delete\s+[A-Za-z_]",
    ]
    return any(re.search(pattern, text) for pattern in state_write_patterns)


def external_call_line_offsets(fn: SolidityFunction) -> list[int]:
    offsets: list[int] = []
    for idx, body_line in enumerate(fn.body.splitlines()):
        if re.search(r"(\.call\s*(\{|\()|\.delegatecall\s*\(|\.staticcall\s*\(|\.transfer\s*\(|\.send\s*\()", body_line):
            offsets.append(idx)
    return offsets


def sensitive_function_name(name: str) -> bool:
    return bool(re.search(
        r"^(mint|burn|pause|unpause|withdraw|sweep|rescue|set|update|upgrade|initialize|change|grant|revoke|claim|airdrop|transferOwnership|setApproval)",
        name,
        flags=re.IGNORECASE,
    ))
