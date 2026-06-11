import pandas as pd

from resume_core.scoring import score_tier


def rank_candidates(results):
    df = pd.DataFrame(results)
    df["Tier"] = df["Composite Score"].apply(score_tier)
    ranked = df.sort_values(by="Composite Score", ascending=False).reset_index(drop=True)
    ranked.insert(0, "Rank", ranked.index + 1)
    return ranked
