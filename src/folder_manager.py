from pathlib import Path
from datetime import date


def ensure_run_folder(base_dir: Path, request_id: str, title: str) -> Path:
    safe_title = title.replace("/", "・").replace("\\", "・")
    folder_name = f"{request_id}_{safe_title}"
    run_dir = base_dir / "runs" / folder_name
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def save_to_run(run_dir: Path, filename: str, content: str) -> Path:
    path = run_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def save_to_output(base_dir: Path, request_id: str, content: str) -> Path:
    output_dir = base_dir / "output" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{request_id}_report_draft.md"
    path.write_text(content, encoding="utf-8")
    return path


def update_session_log(base_dir: Path, request_id: str, title: str, generated_files: list[str]) -> None:
    log_path = base_dir / "session_log.md"
    today = date.today().strftime("%Y-%m-%d")

    entry = f"\n---\n\n## {today} {request_id} {title}\n\n"
    entry += "### AIが生成した成果物\n\n"
    for f in generated_files:
        entry += f"- {f}\n"
    entry += "\n"

    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    log_path.write_text(existing + entry, encoding="utf-8")
