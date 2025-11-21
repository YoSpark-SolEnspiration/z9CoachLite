# app.py — Z9CoachLite
#
# Lite daily-use app:
# - Mood check-in
# - Simple DISC sliders
# - Stage suggestion via z9_core (with safe fallbacks)
# - Local JSON logging
# - Lite PDF export

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import streamlit as st

# ---- Try to use z9_core; fall back to simple logic if imports change ----

try:
    from z9_core.analysis import analyze_profile  # type: ignore
except Exception:
    analyze_profile = None  # type: ignore


try:
    from z9_core.stage import map_disc_to_stage  # type: ignore
except Exception:

    def map_disc_to_stage(d: float, i: float, s: float, c: float) -> str:
        """Fallback: very simple D/ I/ S/ C → stage mapping."""
        traits = {"D": d, "I": i, "S": s, "C": c}
        dominant = max(traits, key=traits.get)
        # Dumb but safe mapping just so app works even if core changes
        mapping = {
            "D": "Stage 4 — Initiative vs. Guilt",
            "I": "Stage 5 — Identity vs. Role Confusion",
            "S": "Stage 6 — Intimacy vs. Isolation",
            "C": "Stage 7 — Generativity vs. Stagnation",
        }
        return mapping.get(dominant, "Stage 5 — Identity vs. Role Confusion")


# ---- Local helpers --------------------------------------------------------

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CHECKIN_FILE = DATA_DIR / "lite_checkins.json"


def load_checkins() -> list[Dict[str, Any]]:
    if not CHECKIN_FILE.exists():
        return []
    try:
        return json.loads(CHECKIN_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_checkin(entry: Dict[str, Any]) -> None:
    entries = load_checkins()
    entries.append(entry)
    CHECKIN_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def summarize_traits(traits: Dict[str, float]) -> str:
    total = sum(traits.values()) or 1.0
    lines = []
    lines.append("Your DISC trait snapshot for today:\n")
    for trait in ["D", "I", "S", "C"]:
        val = traits.get(trait, 0.0)
        pct = (val / total) * 100
        if pct >= 40:
            label = "dominant"
        elif pct >= 25:
            label = "supporting"
        elif pct > 0:
            label = "background"
        else:
            label = "inactive"

        name = {
            "D": "Dominance",
            "I": "Influence",
            "S": "Steadiness",
            "C": "Conscientiousness",
        }[trait]

        lines.append(f"- {trait} ({name}): {pct:5.1f}% → {label}")
    lines.append(
        "\nUse your dominant style as a starting point today, "
        "but deliberately give one supporting or background style a small job to do."
    )
    return "\n".join(lines)


def compute_trait_score(traits: Dict[str, float]) -> float:
    # Simple: mean of D/I/S/C
    if not traits:
        return 0.0
    return sum(traits.values()) / len(traits)


def compute_harmony_ratio(traits: Dict[str, float]) -> float:
    # 100 = perfectly balanced, lower = uneven
    if not traits:
        return 0.0
    vals = list(traits.values())
    mean = sum(vals) / len(vals)
    if mean == 0:
        return 0.0
    variance = sum((v - mean) ** 2 for v in vals) / len(vals)
    # Normalize into a 0–100-ish "harmony" score
    raw = max(0.0, 100.0 - variance * 2.0)
    return max(0.0, min(100.0, raw))


# ---- Import PDF generator -------------------------------------------------

from pdf_export import generate_lite_report  # type: ignore


# ---- Streamlit app --------------------------------------------------------

st.set_page_config(
    page_title="Z9CoachLite — Daily Check-In",
    layout="centered",
)

st.title("✨ Z9CoachLite — Daily Identity Check-In")
st.write(
    "Lite version of the Z9 Coach ecosystem.\n\n"
    "Use this to log your **mood**, tune your **DISC traits**, and see a "
    "simple **stage alignment** for the day."
)

# Sidebar: context + future upgrade hooks
with st.sidebar:
    st.header("Z9 Ecosystem")
    st.markdown(
        "- **Free** → simple DISC + mood\n"
        "- **Lite (this)** → daily check-ins + stage lens\n"
        "- **Pro** → full spiral reports, coaching logic\n"
        "- **Plus** → wearables, Sol’s Fairy AI, district dashboards (WL-T2)\n"
    )
    st.markdown("---")
    st.caption("Data is stored locally in this environment for now.")


# ---- 1. Daily mood check-in ----------------------------------------------

st.subheader("1️⃣ How are you feeling right now?")

mood_label = st.selectbox(
    "Choose the mood that best fits:",
    [
        "😔 Drained",
        "😐 Neutral",
        "🙂 Steady",
        "😄 Energized",
        "🧠 Focused & Inspired",
    ],
)

mood_score_map = {
    "😔 Drained": 1,
    "😐 Neutral": 2,
    "🙂 Steady": 3,
    "😄 Energized": 4,
    "🧠 Focused & Inspired": 5,
}

mood_score = mood_score_map[mood_label]

mood_notes = st.text_area(
    "Anything you want to remember about today (context, wins, stressors)?",
    placeholder="Optional — this can help future you see patterns.",
)


# ---- 2. Trait sliders -----------------------------------------------------

st.subheader("2️⃣ Set your DISC sliders for today")

st.write(
    "Use these sliders to reflect how strongly each trait is showing up *today*, "
    "not in your whole life. This powers your Lite identity snapshot."
)

col1, col2 = st.columns(2)

with col1:
    d_val = st.slider("D — Dominance (drive, push)", 0, 100, 40, 5)
    s_val = st.slider("S — Steadiness (support, patience)", 0, 100, 40, 5)

with col2:
    i_val = st.slider("I — Influence (energy, expression)", 0, 100, 40, 5)
    c_val = st.slider("C — Conscientiousness (detail, structure)", 0, 100, 40, 5)

traits = {"D": float(d_val), "I": float(i_val), "S": float(s_val), "C": float(c_val)}


# ---- 3. Optional perceived stage -----------------------------------------

st.subheader("3️⃣ Optional: Which stage feels most like you today?")

perceived_stage = st.selectbox(
    "If you had to pick one Erikson-style stage today, which resonates?",
    [
        "(skip)",
        "Stage 3 — Initiative vs. Guilt",
        "Stage 4 — Industry vs. Inferiority",
        "Stage 5 — Identity vs. Role Confusion",
        "Stage 6 — Intimacy vs. Isolation",
        "Stage 7 — Generativity vs. Stagnation",
    ],
)


# ---- 4. Analyze button ----------------------------------------------------

st.markdown("---")
if st.button("🔍 Analyze My Day"):
    # Use core analysis when available
    if analyze_profile is not None:
        try:
            profile = analyze_profile(
                traits["D"], traits["I"], traits["S"], traits["C"],
                stage_label=None if perceived_stage == "(skip)" else perceived_stage,
            )
            trait_score = float(profile.get("trait_score", 0.0))
            harmony_ratio = float(profile.get("harmony_ratio", 0.0))
        except Exception:
            profile = {}
            trait_score = compute_trait_score(traits)
            harmony_ratio = compute_harmony_ratio(traits)
    else:
        profile = {}
        trait_score = compute_trait_score(traits)
        harmony_ratio = compute_harmony_ratio(traits)

    auto_stage = map_disc_to_stage(
        traits["D"], traits["I"], traits["S"], traits["C"]
    )

    # ---- Log entry locally ----
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "mood_label": mood_label,
        "mood_score": mood_score,
        "mood_notes": mood_notes,
        "traits": traits,
        "trait_score": trait_score,
        "harmony_ratio": harmony_ratio,
        "perceived_stage": None if perceived_stage == "(skip)" else perceived_stage,
        "auto_stage": auto_stage,
    }
    save_checkin(entry)

    # ---- Show results ----
    st.success("✅ Check-in saved and analyzed.")

    st.subheader("Your Lite Identity Snapshot")
    col_a, col_b = st.columns(2)

    with col_a:
        st.metric("Composite Trait Score", f"{trait_score:.1f}")
        st.metric("Harmony Ratio", f"{harmony_ratio:.1f}%")

    with col_b:
        st.metric("Suggested Stage (Auto)", auto_stage)
        if perceived_stage != "(skip)":
            st.metric("Your Chosen Stage", perceived_stage)

    st.markdown("### Trait Breakdown")
    st.code(summarize_traits(traits))

    st.markdown("### Today’s Mood Anchor")
    st.write(f"**Mood:** {mood_label} (score {mood_score})")
    if mood_notes.strip():
        st.caption(f"_Note:_ {mood_notes.strip()}")

    # ---- PDF Export button ----
    st.markdown("---")
    st.subheader("📥 Download Today’s Lite Report")

    pdf_bytes = generate_lite_report(
        {
            "trait_score": trait_score,
            "harmony_ratio": harmony_ratio,
            "stage": auto_stage,
            "trait_summary": summarize_traits(traits),
        }
    )

    st.download_button(
        "Download Lite PDF",
        pdf_bytes,
        file_name="Z9CoachLite_Report.pdf",
        mime="application/pdf",
    )

    # ---- Recent history preview ----
    st.markdown("---")
    st.subheader("Recent Check-ins (Lite)")
    history = load_checkins()
    if history:
        last_items = list(reversed(history[-7:]))
        for h in last_items:
            st.markdown(
                f"- **{h['timestamp']}** — Mood: {h['mood_label']}, "
                f"Stage: {h['auto_stage']}, Harmony: {h['harmony_ratio']:.1f}%"
            )
    else:
        st.caption("No history yet — today is your first Lite check-in.")


# ---- Footer ---------------------------------------------------------------

st.markdown(
    """
---
© 2025 **KYLE DUSAN HENSON JR LC** + **YO SPARK: SOL ENSPIRATION LC**  
Licensed under **Enterprise4Eternity, LC**  
"""
)
