from pathlib import Path
import pandas as pd
import yaml

from src.similarity_search import search_similar_tests
from src.dils_selector import recommend_dils
from src.report_generator import generate_plan, generate_scenario, generate_report
from src.folder_manager import ensure_run_folder, save_to_run, save_to_output, update_session_log


def load_request(base_dir: Path, yaml_path: Path = None) -> dict:
    if yaml_path is None:
        yaml_path = base_dir / "data" / "04_sample" / "sample_request.yaml"
    with open(yaml_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_questionnaire(base_dir: Path, run_id: str = "EXP-001") -> pd.DataFrame:
    run_dirs = list((base_dir / "runs").glob(f"{run_id}*"))
    if run_dirs:
        q_path = run_dirs[0] / "questionnaire.csv"
        if q_path.exists():
            return pd.read_csv(q_path)

    fallback = base_dir / "data" / "04_sample" / "sample_questionnaire.csv"
    if fallback.exists():
        return pd.read_csv(fallback)
    return pd.DataFrame()


def run_agent(base_dir: Path, request: dict) -> dict:
    """
    テスト依頼を受け取り、類似テスト検索・DiLS推薦・ファイル生成を実行する。
    """
    request_id = request.get("request_id", "EXP-XXX")
    title = request.get("request_title", "未設定")

    similar_tests = search_similar_tests(request, base_dir)
    dils_recs = recommend_dils(request, base_dir)
    questionnaire_df = load_questionnaire(base_dir, request_id)

    run_dir = ensure_run_folder(base_dir, request_id, title)

    plan_text = generate_plan(request, similar_tests, dils_recs)
    scenario_text = generate_scenario(request)
    report_text = generate_report(request, questionnaire_df, dils_recs)

    plan_path = save_to_run(run_dir, "plan.md", plan_text)
    scenario_path = save_to_run(run_dir, "scenario.md", scenario_text)
    report_run_path = save_to_run(run_dir, "report_draft.md", report_text)
    report_out_path = save_to_output(base_dir, request_id, report_text)

    generated = [
        str(plan_path.relative_to(base_dir)),
        str(scenario_path.relative_to(base_dir)),
        str(report_run_path.relative_to(base_dir)),
        str(report_out_path.relative_to(base_dir)),
    ]
    update_session_log(base_dir, request_id, title, generated)

    missing_info = request.get("open_questions", [])

    return {
        "request": request,
        "missing_info": missing_info,
        "similar_tests": similar_tests,
        "dils_recommendations": dils_recs,
        "plan_text": plan_text,
        "scenario_text": scenario_text,
        "report_text": report_text,
        "questionnaire_df": questionnaire_df,
        "generated_files": generated,
        "run_dir": run_dir,
        "report_output_path": report_out_path,
    }
