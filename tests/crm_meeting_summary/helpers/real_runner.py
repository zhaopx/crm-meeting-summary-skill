from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
EVALS_PATH = REPO_ROOT / "tests" / "crm_meeting_summary" / "evals" / "evals.json"
CRM_SKILL_DIR = Path.home() / ".claude" / "skills" / "crm-meeting-summary"
DEFAULT_CONSTRAINTS = {"language": "zh-CN", "output_mode": "human_only"}
CLAUDE_TIMEOUT_SECONDS = 300

BUNDLE_FILE_MAP = {
    "AccountObj.json": "account",
    "NewOpportunityObj.json": "opportunity",
    "PersonnelObj.json": "person",
    "ContactObj.json": "contact",
}
MEMORY_FILE_GLOB = "*-memory.json"


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

    memory_snippets: list[dict[str, Any]] = []
    for memory_path in sorted(resolved_dir.glob(MEMORY_FILE_GLOB)):
        if not memory_path.is_file():
            continue
        resolved_memory_path = resolve_bundle_file(memory_path)
        ensure_repo_path(resolved_memory_path)
        memory_snippets = [*memory_snippets, read_bundle_json(resolved_memory_path)]

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
        "memory_snippets": memory_snippets,
        "constraints": dict(DEFAULT_CONSTRAINTS),
    }


def build_skill_prompt(input_file_path: Path) -> str:
    return (
        "请使用 /crm-meeting-summary skill。\n"
        f"先读取输入包文件：{input_file_path}\n"
        "输入包是 JSON 文件，不是 PDF。\n"
        "非 PDF 的 Read 调用不要传 pages 字段。\n"
        "按 skill 契约完成输出。\n"
        "最终用户可见结果只保留人类可读总结，不要把 machine JSON 混进最终总结正文。\n"
        "同时按 runtime-contract 保留结构化 audit_payload，供 runner / review / eval 消费。\n"
        "如果包含 review 结果，也不要让 review JSON 覆盖最终总结正文。"
    )


def build_allowed_tools() -> list[str]:
    resolved_repo_root = REPO_ROOT.resolve()
    resolved_skill_dir = CRM_SKILL_DIR.resolve()
    read_roots = [
        resolved_repo_root,
        resolved_skill_dir,
        (resolved_skill_dir / "references").resolve(),
        (resolved_skill_dir / "review").resolve(),
    ]
    read_patterns = [f'Read(//{str(root).lstrip("/")}/**)' for root in read_roots]
    return [
        *read_patterns,
        'Skill(crm-meeting-summary)',
        'Skill(crm-meeting-summary:*)',
    ]


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


def extract_structured_blocks(text: str) -> tuple[list[tuple[int, int, dict[str, Any]]], list[tuple[int, int, dict[str, Any]]]]:
    review_blocks: list[tuple[int, int, dict[str, Any]]] = []
    audit_blocks: list[tuple[int, int, dict[str, Any]]] = []
    fenced_marker = "```json"
    search_start = 0

    while True:
        marker_position = text.find(fenced_marker, search_start)
        if marker_position == -1:
            break

        payload_start = marker_position + len(fenced_marker)
        payload_end = text.find("```", payload_start)
        if payload_end == -1:
            break

        payload = text[payload_start:payload_end].strip()
        block_end = payload_end + 3
        search_start = block_end

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            continue

        if not isinstance(parsed, dict):
            continue

        if {"pass", "review_status", "failure_reasons"}.issubset(parsed.keys()):
            review_blocks.append((marker_position, block_end, parsed))
            continue
        if parsed.get("schema_version") == "crm-meeting-summary-audit-v1":
            audit_blocks.append((marker_position, block_end, parsed))

    return review_blocks, audit_blocks


def extract_review_result(text: str) -> dict[str, Any] | None:
    review_blocks, _ = extract_structured_blocks(text)
    if not review_blocks:
        return None
    return review_blocks[-1][2]


def extract_review_result_from_payload(cli_payload: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidate_texts: list[str] = []
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

    for text in candidate_texts:
        review_result = extract_review_result(text)
        if review_result is not None:
            return review_result
    return None


def extract_audit_payload(text: str) -> dict[str, Any] | None:
    _, audit_blocks = extract_structured_blocks(text)
    if not audit_blocks:
        return None
    return audit_blocks[-1][2]


def extract_audit_payload_from_payload(cli_payload: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidate_texts: list[str] = []
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

    for text in candidate_texts:
        audit_payload = extract_audit_payload(text)
        if audit_payload is not None:
            return audit_payload
    return None


def looks_like_human_summary(text: str) -> bool:
    summary_markers = (
        "会议快照",
        "核心总结与判断",
        "Knowhow 关注点",
        "建议的下一步动作",
        "风险与待确认问题",
    )
    return any(marker in text for marker in summary_markers)


def extract_final_text(cli_payload: list[dict[str, Any]]) -> str:
    candidate_texts: list[str] = []
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

    for text in candidate_texts:
        if not looks_like_human_summary(text):
            continue

        review_blocks, audit_blocks = extract_structured_blocks(text)
        structured_blocks = sorted([*review_blocks, *audit_blocks], key=lambda block: block[0])
        if structured_blocks:
            first_block_start = structured_blocks[0][0]
            summary_text = text[:first_block_start].rstrip()
            if looks_like_human_summary(summary_text):
                return summary_text

        return text.rstrip()
    if candidate_texts:
        return candidate_texts[0]
    raise RealRunnerError("未找到最终 assistant 文本")


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
            "--allowedTools",
            *build_allowed_tools(),
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
        review_result = extract_review_result(final_text)
        if review_result is None:
            review_result = extract_review_result_from_payload(cli_payload)
        audit_payload = extract_audit_payload_from_payload(cli_payload)
        return {
            "raw_response": cli_payload,
            "final_text": final_text,
            "review_result": review_result,
            "audit_payload": audit_payload,
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
        bundle = build_input_bundle_from_path(REPO_ROOT / input_bundle_path)
    else:
        files = [REPO_ROOT / file for file in case["files"]]
        bundle = build_input_bundle(files)
    result = invoke_real_skill(bundle)
    return {"case": case, **result}
