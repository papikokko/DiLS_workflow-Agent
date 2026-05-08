import pandas as pd
from pathlib import Path


def load_past_tests(base_dir: Path) -> pd.DataFrame:
    path = base_dir / "data" / "03_reference" / "past_tests.csv"
    return pd.read_csv(path)


def compute_similarity(test: pd.Series, request: dict) -> dict:
    score = 0
    reasons = []

    # 機能領域（40点）
    req_function = request.get("target_function", "").lower()
    test_area = str(test.get("function_area", "")).lower()
    if any(k in test_area for k in ["hmi", "display", "warning"]) and any(
        k in req_function for k in ["hmi", "display", "warning"]
    ):
        score += 40
        reasons.append("機能領域（HMI・表示）が一致しています")
    elif any(k in test_area for k in req_function.split()):
        score += 20
        reasons.append("機能領域が部分的に一致しています")

    # 取得データ（25点）
    req_data = set(request.get("required_data", []))
    test_data = set(str(test.get("required_data", "")).split("/"))
    overlap = req_data & test_data
    if len(overlap) >= 2:
        score += 25
        reasons.append(f"取得データが複数一致しています（{', '.join(overlap)}）")
    elif len(overlap) == 1:
        score += 12
        reasons.append(f"取得データが一部一致しています（{', '.join(overlap)}）")

    # シナリオ条件（20点）
    req_scenarios = set(request.get("preferred_scenario", []))
    test_scenarios = set(str(test.get("scenarios", "")).split("/"))
    if req_scenarios & test_scenarios:
        score += 20
        reasons.append(f"走行シナリオが一致しています（{', '.join(req_scenarios & test_scenarios)}）")

    # DiLS・設備（15点）
    if "DiLS-02" in str(test.get("dils_used", "")):
        score += 15
        reasons.append("DiLS-02（Eye Tracker搭載）を使用した実績があります")

    return {"score": score, "reasons": reasons}


def search_similar_tests(request: dict, base_dir: Path, top_n: int = 3) -> list[dict]:
    df = load_past_tests(base_dir)
    results = []
    for _, row in df.iterrows():
        sim = compute_similarity(row, request)
        results.append({
            "test_id": row["test_id"],
            "title": row["title"],
            "score": sim["score"],
            "reasons": sim["reasons"],
            "dils_used": row.get("dils_used", ""),
            "date": row.get("date", ""),
            "reusable_items": row.get("reusable_items", ""),
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]
