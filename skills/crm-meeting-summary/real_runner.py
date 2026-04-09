from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
EVALS_PATH = Path(__file__).resolve().parent / "evals" / "evals.json"
DEFAULT_CONSTRAINTS = {"language": "zh-CN", "output_mode": "human_and_json"}
CLAUDE_TIMEOUT_SECONDS = 180

BUNDLE_FILE_MAP = {
    "AccountObj.json": "account",
    "NewOpportunityObj.json": "opportunity",
    "PersonnelObj.json": "person",
    "ContactObj.json": "contact",
}


class RealRunnerError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def read_bundle_json(path: Path) -> Any:
    try:
        return load_json(path)
    except json.JSONDecodeError as exc:
        raise RealRunnerError(f"目录输入中的 JSON 文件解析失败: {path.name}") from exc


def resolve_bundle_file(path: Path) -> Path:
    if path.is_symlink():
        raise RealRunnerError(f"目录输入不支持符号链接文件: {path.name}")
    try:
        return path.resolve(strict=True)
    except OSError as exc:
        raise RealRunnerError(f"读取目录输入文件失败: {path.name}") from exc


def read_bundle_meeting_record(path: Path) -> str:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RealRunnerError(f"读取 meeting-record.txt 失败: {path}") from exc

    normalized = content.strip()
    if not normalized:
        raise RealRunnerError("meeting-record.txt 内容为空")
    return normalized


def ensure_repo_path(path: Path) -> None:
    try:
        path.resolve().relative_to(REPO_ROOT)
    except ValueError as exc:
        raise RealRunnerError(f"文件必须位于仓库内: {path}") from exc


def build_input_bundle(files: list[Path]) -> dict[str, Any]:
    meeting: dict[str, Any] | None = None
    crm_context: dict[str, Any] = {}
    memory_snippets: list[dict[str, Any]] = []

    for file_path in files:
        ensure_repo_path(file_path)
        payload = load_json(file_path.resolve())
        parts = file_path.parts
        if "meeting-records" in parts:
            meeting = payload["meeting"]
            continue
        if "crm" in parts:
            scope = file_path.parent.name
            crm_context = {**crm_context, scope: payload}
            continue
        if "memory" in parts:
            memory_snippets = [*memory_snippets, payload]

    if meeting is None:
        raise RealRunnerError("缺少 meeting 文件")

    return {
        "meeting": meeting,
        "crm_context": crm_context,
        "memory_snippets": memory_snippets,
        "constraints": dict(DEFAULT_CONSTRAINTS),
    }


def build_input_bundle_from_path(bundle_dir: Path) -> dict[str, Any]:
    resolved_dir = bundle_dir.resolve()
    if not resolved_dir.is_dir():
        raise RealRunnerError(f"input_bundle_path 不是目录: {bundle_dir}")

    ensure_repo_path(resolved_dir)

    meeting_record_path = resolved_dir / "meeting-record.txt"
    if not meeting_record_path.is_file():
        raise RealRunnerError(f"目录输入缺少必需文件: {meeting_record_path.name}")
    resolved_meeting_record_path = resolve_bundle_file(meeting_record_path)
    ensure_repo_path(resolved_meeting_record_path)

    crm_context: dict[str, Any] = {}
    for file_name, scope in BUNDLE_FILE_MAP.items():
        file_path = resolved_dir / file_name
        if not file_path.is_file():
            continue
        resolved_file_path = resolve_bundle_file(file_path)
        ensure_repo_path(resolved_file_path)
        crm_context = {**crm_context, scope: read_bundle_json(resolved_file_path)}

    return {
        "meeting": {
            "title": None,
            "meeting_time": None,
            "initiator": {"id": None, "name": None},
            "account": {"id": None, "name": None},
            "opportunity": {"id": None, "name": None},
            "participants": [],
            "record_text": read_bundle_meeting_record(resolved_meeting_record_path),
            "record_text_path": None,
        },
        "crm_context": crm_context,
        "memory_snippets": [],
        "constraints": dict(DEFAULT_CONSTRAINTS),
    }


def build_skill_prompt(input_file_path: Path) -> str:
    return (
        "请使用 /crm-meeting-summary skill。\n"
        f"先读取输入包文件：{input_file_path}\n"
        "输入包是 JSON 文件，不是 PDF。\n"
        "非 PDF 的 Read 调用不要传 pages 字段。\n"
        "按 skill 契约完成输出。\n"
        "最终结果必须包含完整 machine JSON；如果同时输出人类总结，请把 machine JSON 放在最后，便于提取。"
    )


def parse_cli_payload(stdout: str) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        start = stdout.find("[")
        end = stdout.rfind("]")
        if start == -1 or end == -1 or end <= start:
            raise RealRunnerError("Claude CLI 输出不是可解析的 JSON")
        try:
            parsed = json.loads(stdout[start : end + 1])
        except json.JSONDecodeError as exc:
            raise RealRunnerError("Claude CLI JSON 输出解析失败") from exc

    if not isinstance(parsed, list):
        raise RealRunnerError("Claude CLI 输出结构非法")
    return parsed


def extract_final_text(cli_payload: list[dict[str, Any]]) -> str:
    candidate_texts: list[str] = []
    embedded_machine_outputs: list[str] = []
    for item in reversed(cli_payload):
        if item.get("type") == "result" and isinstance(item.get("result"), str):
            candidate_texts.append(item["result"])
    for item in reversed(cli_payload):
        if item.get("type") != "assistant":
            continue
        message = item.get("message", {})
        for content in reversed(message.get("content", [])):
            if content.get("type") == "text" and isinstance(content.get("text"), str):
                candidate_texts.append(content["text"])
                continue
            if content.get("type") != "tool_use":
                continue
            tool_input = content.get("input", {})
            args = tool_input.get("args")
            if isinstance(args, str) and "【generated machine-readable output】" in args:
                embedded_machine_outputs.append(args)

    for text in candidate_texts:
        try:
            parsed, _ = extract_machine_json(text)
        except (RealRunnerError, json.JSONDecodeError):
            continue
        if isinstance(parsed, dict) and "status" in parsed:
            return text

    for text in embedded_machine_outputs:
        try:
            parsed, meta = extract_machine_json(text)
        except (RealRunnerError, json.JSONDecodeError):
            continue
        if isinstance(parsed, dict) and meta.get("source") == "embedded_machine_output":
            return text

    if candidate_texts:
        return candidate_texts[0]
    raise RealRunnerError("未找到最终 assistant 文本")


def extract_machine_json(final_text: str) -> tuple[dict[str, Any], dict[str, str]]:
    machine_marker = "【generated machine-readable output】"
    if machine_marker in final_text:
        marker_start = final_text.find(machine_marker) + len(machine_marker)
        tail = final_text[marker_start:]
        start = tail.find("{")
        if start != -1:
            brace_depth = 0
            in_string = False
            escape = False
            for index, char in enumerate(tail[start:], start=start):
                if escape:
                    escape = False
                    continue
                if char == "\\":
                    escape = True
                    continue
                if char == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if char == "{":
                    brace_depth += 1
                elif char == "}":
                    brace_depth -= 1
                    if brace_depth == 0:
                        payload = tail[start : index + 1]
                        return json.loads(payload), {"source": "embedded_machine_output"}

    def extract_review_handoff(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]] | None:
        handoff = payload.get("generated_machine_output")
        if isinstance(handoff, dict) and "status" in handoff:
            return handoff, {"source": "review_handoff_json"}
        return None

    fenced_marker = "```json"
    if fenced_marker in final_text:
        start = final_text.rfind(fenced_marker) + len(fenced_marker)
        end = final_text.find("```", start)
        if end == -1:
            raise RealRunnerError("JSON fenced block 未闭合")
        payload = final_text[start:end].strip()
        parsed = json.loads(payload)
        if isinstance(parsed, dict):
            handoff_result = extract_review_handoff(parsed)
            if handoff_result is not None:
                return handoff_result
        return parsed, {"source": "fenced_json"}

    stripped = final_text.strip()
    if stripped.startswith("{"):
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            handoff_result = extract_review_handoff(parsed)
            if handoff_result is not None:
                return handoff_result
        return parsed, {"source": "raw_json"}

    start = final_text.find("{")
    end = final_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        parsed = json.loads(final_text[start : end + 1])
        if isinstance(parsed, dict):
            handoff_result = extract_review_handoff(parsed)
            if handoff_result is not None:
                return handoff_result
        return parsed, {"source": "embedded_json"}

    raise RealRunnerError("未能从最终文本中提取 machine JSON")


def invoke_real_skill(bundle: dict[str, Any]) -> dict[str, Any]:
    input_file_path: Path | None = None
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        delete=False,
        dir=REPO_ROOT,
    ) as file:
        json.dump(bundle, file, ensure_ascii=False, indent=2)
        input_file_path = Path(file.name)

    try:
        prompt = build_skill_prompt(input_file_path)
        command = [
            "claude",
            "-p",
            prompt,
            "--output-format",
            "json",
            "--permission-mode",
            "dontAsk",
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                cwd=REPO_ROOT,
                timeout=CLAUDE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise RealRunnerError(f"Claude CLI 调用超时: {exc.timeout}s") from exc
        except FileNotFoundError as exc:
            raise RealRunnerError("未找到 claude CLI，可执行文件不存在或不在 PATH 中") from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() if exc.stderr else ""
            stdout = exc.stdout.strip() if exc.stdout else ""
            detail = stderr or stdout or "无错误输出"
            raise RealRunnerError(f"Claude CLI 调用失败: {detail}") from exc

        cli_payload = parse_cli_payload(result.stdout)
        final_text = extract_final_text(cli_payload)
        extracted_machine_json, extraction_meta = extract_machine_json(final_text)
        return {
            "raw_response": cli_payload,
            "final_text": final_text,
            "extracted_machine_json": extracted_machine_json,
            "extraction_meta": extraction_meta,
        }
    finally:
        if input_file_path is not None:
            try:
                input_file_path.unlink(missing_ok=True)
            except OSError:
                pass


def load_eval_case(case_id: str) -> dict[str, Any]:
    payload = load_json(EVALS_PATH)
    for case in payload["evals"]:
        if case["id"] == case_id:
            return case
    raise RealRunnerError(f"未找到 eval case: {case_id}")


def run_case(case_id: str) -> dict[str, Any]:
    case = load_eval_case(case_id)
    if "input_bundle_path" in case:
        input_bundle_path = case["input_bundle_path"]
        if not isinstance(input_bundle_path, str) or not input_bundle_path.strip():
            raise RealRunnerError("eval case 中的 input_bundle_path 必须是非空字符串")
        bundle = build_input_bundle_from_path(Path(input_bundle_path))
    else:
        files = [Path(__file__).parent / file for file in case["files"]]
        bundle = build_input_bundle(files)
    result = invoke_real_skill(bundle)
    return {"case": case, **result}
