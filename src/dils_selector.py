import pandas as pd
from pathlib import Path


def load_dils_master(base_dir: Path) -> pd.DataFrame:
    path = base_dir / "data" / "03_reference" / "dils_master.csv"
    return pd.read_csv(path)


def compute_dils_score(dils: pd.Series, request: dict) -> dict:
    score = 0
    reasons = []
    cautions = []

    required_data = request.get("required_data", [])
    target_function = request.get("target_function", "").lower()

    # 必要設備を満たすか（50点）
    equipment_score = 0
    if "gaze_log" in required_data and str(dils.get("eye_tracker")) == "あり":
        equipment_score += 25
        reasons.append("Eye Trackerが搭載されており、視線ログの取得が可能です")
    elif "gaze_log" in required_data:
        cautions.append("Eye Trackerがないため視線ログを取得できません")

    if "hmi" in target_function.lower() and "高精細HMI" in str(dils.get("hmi_display", "")):
        equipment_score += 25
        reasons.append("高精細HMI表示設備があり、警告表示の制御が可能です")
    elif str(dils.get("hmi_display", "")) not in ("", "なし"):
        equipment_score += 10
        reasons.append("HMI表示設備があります")

    score += equipment_score

    # テスト種別に合うか（30点）
    suitable = str(dils.get("suitable_tests", "")).lower()
    if "hmi" in suitable or "視認性" in suitable or "反応時間" in suitable:
        score += 30
        reasons.append("HMI視認性評価・反応時間計測に適したDiLSです")
    elif "基本機能" in suitable:
        score += 15
        reasons.append("基本的な評価には対応しています")

    # 稼働可能か（20点）
    if str(dils.get("status", "")) == "稼働可能":
        score += 20
        reasons.append("現在稼働中です")
    else:
        cautions.append(f"現在の稼働状況：{dils.get('status', '不明')}")

    return {"score": score, "reasons": reasons, "cautions": cautions}


def recommend_dils(request: dict, base_dir: Path) -> list[dict]:
    df = load_dils_master(base_dir)
    results = []
    for _, row in df.iterrows():
        result = compute_dils_score(row, request)
        results.append({
            "dils_id": row["dils_id"],
            "name": row["name"],
            "features": row["features"],
            "score": result["score"],
            "reasons": result["reasons"],
            "cautions": result["cautions"],
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
