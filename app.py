from collections import Counter
from datetime import datetime
from pathlib import Path
from uuid import uuid4
import re

import pandas as pd
import plotly.express as px
import streamlit as st
from textblob import TextBlob


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Moonlit Journal",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DATA
# =========================================================

DATA_FOLDER = Path("data")
DATA_FOLDER.mkdir(exist_ok=True)

DATA_FILE = DATA_FOLDER / "journal_entries.csv"


# =========================================================
# MOODS
# =========================================================

MOODS = {
    "Very Happy": {
        "emoji": "☀️",
        "score": 5,
        "color": "#F6C96B",
        "soft": "#FFF3C7",
        "message": "Your entry feels bright, warm, and full of positive energy.",
    },
    "Happy": {
        "emoji": "🌷",
        "score": 4,
        "color": "#F3AFC8",
        "soft": "#FFE2ED",
        "message": "There is a gentle, positive feeling running through this entry.",
    },
    "Neutral": {
        "emoji": "☁️",
        "score": 3,
        "color": "#B8B5D8",
        "soft": "#EEECFA",
        "message": "Your entry feels balanced, reflective, or emotionally neutral.",
    },
    "Low": {
        "emoji": "🌧️",
        "score": 2,
        "color": "#89B8D8",
        "soft": "#DCEFFA",
        "message": "This entry carries some heavier feelings or frustration.",
    },
    "Very Low": {
        "emoji": "🌙",
        "score": 1,
        "color": "#927DAE",
        "soft": "#E9E0F1",
        "message": "Your entry has a noticeably heavy or difficult emotional tone.",
    },
}


# =========================================================
# DAILY JOURNAL PROMPTS
# =========================================================

JOURNAL_PROMPTS = [
    "What made today feel a little different?",
    "What is something small you want to remember from today?",
    "What has been taking up space in your mind lately?",
    "What made you smile today?",
    "What is something you handled better than you expected?",
    "If today had a color, what would it be and why?",
    "What do you wish you could tell your past self?",
    "What are you looking forward to right now?",
    "What drained your energy today?",
    "What gave you energy today?",
    "What is one thing you are proud of today?",
    "What would make tomorrow feel a little softer?",
]

prompt_index = datetime.now().toordinal() % len(JOURNAL_PROMPTS)
daily_prompt = JOURNAL_PROMPTS[prompt_index]


# =========================================================
# AFFIRMATIONS
# =========================================================

AFFIRMATIONS = [
    "tiny progress is still progress ✦",
    "you are allowed to have slow days ☁️",
    "there is no correct way to feel today 🌷",
    "your thoughts deserve somewhere soft to land 🌙",
    "one little moment can still make a day special ✨",
    "rest can be productive too 🎀",
]

affirmation_index = (
    datetime.now().toordinal() + 3
) % len(AFFIRMATIONS)

daily_affirmation = AFFIRMATIONS[
    affirmation_index
]


# =========================================================
# STOP WORDS
# =========================================================

STOP_WORDS = {
    "the", "and", "to", "a", "i", "it", "of", "in",
    "that", "was", "is", "for", "my", "on", "with",
    "this", "but", "so", "me", "have", "had", "be",
    "at", "just", "really", "very", "today", "am",
    "are", "as", "not", "feel", "felt", "about",
    "because", "been", "from", "or", "an", "if",
    "we", "they", "you", "he", "she", "them", "our",
    "your", "its", "do", "did", "has", "were", "can",
}


# =========================================================
# ANALYZE MOOD
# =========================================================

def analyze_mood(text):

    blob = TextBlob(text)

    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    if polarity >= 0.5:
        mood = "Very Happy"

    elif polarity >= 0.15:
        mood = "Happy"

    elif polarity > -0.15:
        mood = "Neutral"

    elif polarity > -0.5:
        mood = "Low"

    else:
        mood = "Very Low"

    settings = MOODS[mood]

    return {
        "mood": mood,
        "emoji": settings["emoji"],
        "mood_score": settings["score"],
        "polarity": polarity,
        "subjectivity": subjectivity,
        "message": settings["message"],
        "color": settings["color"],
        "soft": settings["soft"],
    }


# =========================================================
# LOAD ENTRIES
# =========================================================

def load_entries():

    if not DATA_FILE.exists():

        return pd.DataFrame(
            columns=[
                "ID",
                "Date",
                "Entry",
                "Mood",
                "Mood Score",
                "Polarity",
                "Subjectivity",
            ]
        )

    df = pd.read_csv(DATA_FILE)

    if "ID" not in df.columns:

        df.insert(
            0,
            "ID",
            [
                uuid4().hex[:10]
                for _ in range(len(df))
            ],
        )

        df.to_csv(
            DATA_FILE,
            index=False,
        )

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
    )

    return df


# =========================================================
# SAVE ENTRY
# =========================================================

def save_entry(text, analysis):

    new_entry = pd.DataFrame(
        [
            {
                "ID": uuid4().hex[:10],
                "Date": datetime.now(),
                "Entry": text,
                "Mood": analysis["mood"],
                "Mood Score": analysis["mood_score"],
                "Polarity": analysis["polarity"],
                "Subjectivity": analysis["subjectivity"],
            }
        ]
    )

    old_entries = load_entries()

    updated = pd.concat(
        [
            old_entries,
            new_entry,
        ],
        ignore_index=True,
    )

    updated.to_csv(
        DATA_FILE,
        index=False,
    )


# =========================================================
# DELETE ENTRY
# =========================================================

def delete_entry(entry_id):

    df = load_entries()

    df = df[
        df["ID"] != entry_id
    ]

    df.to_csv(
        DATA_FILE,
        index=False,
    )


# =========================================================
# STREAK
# =========================================================

def calculate_streak(entries):

    if entries.empty:
        return 0

    dates = (
        entries["Date"]
        .dropna()
        .dt.date
        .drop_duplicates()
        .sort_values(
            ascending=False
        )
        .tolist()
    )

    if not dates:
        return 0

    streak = 1

    for i in range(
        len(dates) - 1
    ):

        difference = (
            dates[i]
            - dates[i + 1]
        ).days

        if difference == 1:
            streak += 1

        else:
            break

    return streak


# =========================================================
# COMMON WORDS
# =========================================================

def common_words(entries):

    text = " ".join(
        entries["Entry"]
        .fillna("")
        .astype(str)
        .tolist()
    ).lower()

    words = re.findall(
        r"[a-zA-Z']+",
        text,
    )

    useful_words = [
        word
        for word in words
        if (
            len(word) > 2
            and word not in STOP_WORDS
        )
    ]

    return Counter(
        useful_words
    ).most_common(10)


# =========================================================
# CSS
# =========================================================

st.html(
    """
<style>

/* =====================================================
   GLOBAL
===================================================== */

.stApp {

    background:

        radial-gradient(
            circle at 7% 8%,
            rgba(255, 196, 220, .55),
            transparent 26%
        ),

        radial-gradient(
            circle at 92% 12%,
            rgba(205, 194, 255, .60),
            transparent 27%
        ),

        radial-gradient(
            circle at 82% 85%,
            rgba(255, 231, 168, .45),
            transparent 28%
        ),

        radial-gradient(
            circle at 10% 88%,
            rgba(189, 224, 255, .42),
            transparent 30%
        ),

        linear-gradient(
            135deg,
            #fff9fb,
            #fff4f8,
            #f8f2ff,
            #f4f9ff
        );

    color: #4c3d50;
}


.block-container {

    max-width: 1250px;

    padding-top: 1.7rem;
    padding-bottom: 4rem;
}


/* =====================================================
   CLEAN STREAMLIT
===================================================== */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

[data-testid="stHeader"] {
    background: transparent;
}


/* =====================================================
   HERO
===================================================== */

.journal-hero {

    background:
        linear-gradient(
            125deg,
            rgba(255,255,255,.87),
            rgba(255,239,248,.87),
            rgba(241,235,255,.87)
        );

    border:
        2px solid #59495d;

    border-radius:
        34px;

    padding:
        38px 42px;

    box-shadow:
        9px 9px 0 #f2bdd4,
        12px 12px 0 #59495d;

    position:
        relative;

    overflow:
        hidden;

    margin-bottom:
        35px;
}


.hero-badge {

    display:
        inline-block;

    background:
        #fff1af;

    border:
        2px solid #59495d;

    border-radius:
        999px;

    padding:
        6px 14px;

    font-size:
        .84rem;

    font-weight:
        850;

    transform:
        rotate(-2deg);

    box-shadow:
        2px 2px 0 #59495d;

    margin-bottom:
        18px;
}


.hero-title {

    color:
        #4c3d50;

    font-size:
        clamp(
            2.9rem,
            6vw,
            4.8rem
        );

    line-height:
        .95;

    letter-spacing:
        -2.5px;

    font-weight:
        950;

    margin-bottom:
        18px;
}


.hero-sub {

    color:
        #806e81;

    font-size:
        1.05rem;

    line-height:
        1.7;

    max-width:
        670px;
}


.hero-doodle-one {

    position:
        absolute;

    right:
        48px;

    top:
        32px;

    font-size:
        4.6rem;

    transform:
        rotate(9deg);
}


.hero-doodle-two {

    position:
        absolute;

    right:
        145px;

    bottom:
        25px;

    font-size:
        2rem;

    opacity:
        .7;
}


/* =====================================================
   HEADINGS
===================================================== */

.section-title {

    font-size:
        1.6rem;

    font-weight:
        950;

    color:
        #4c3d50;

    margin-bottom:
        5px;
}


.section-sub {

    color:
        #8a788b;

    margin-bottom:
        17px;
}


/* =====================================================
   PROMPT CARD
===================================================== */

.prompt-card {

    background:
        linear-gradient(
            100deg,
            #fff2ba,
            #ffe2d0,
            #ffddeb
        );

    border:
        2px solid #59495d;

    border-radius:
        24px;

    padding:
        19px 22px;

    box-shadow:
        4px 4px 0 #59495d;

    color:
        #4c3d50;

    margin-bottom:
        22px;
}


.prompt-label {

    font-size:
        .75rem;

    letter-spacing:
        1px;

    text-transform:
        uppercase;

    font-weight:
        900;

    color:
        #9b7587;

    margin-bottom:
        5px;
}


.prompt-text {

    font-size:
        1.05rem;

    font-weight:
        800;
}


/* =====================================================
   TEXT AREA
===================================================== */

div[data-testid="stTextArea"] {

    background:
        rgba(255,255,255,.63);

    border:
        2px dashed #cbb9ca;

    border-radius:
        26px;

    padding:
        14px;

    box-shadow:
        4px 4px 0 rgba(89,73,93,.09);
}


div[data-testid="stTextArea"] textarea {

    border-radius:
        18px !important;

    border:
        1.5px solid #d9c9d7 !important;

    background:
        rgba(255,255,255,.82) !important;

    color:
        #4c3d50 !important;

    min-height:
        190px !important;
}


/* =====================================================
   BUTTONS
===================================================== */

.stButton > button {

    width:
        100%;

    border-radius:
        999px !important;

    border:
        2px solid #59495d !important;

    background:
        linear-gradient(
            90deg,
            #f5bdd5,
            #d8c4f5
        ) !important;

    color:
        #4c3d50 !important;

    font-weight:
        900 !important;

    padding:
        .78rem 1rem !important;

    box-shadow:
        4px 4px 0 #59495d !important;

    transition:
        .15s ease !important;
}


.stButton > button:hover {

    transform:
        translate(-2px,-2px);

    box-shadow:
        6px 6px 0 #59495d !important;
}


/* =====================================================
   MOOD RESULT
===================================================== */

.mood-card {

    border:
        2px solid #59495d;

    border-radius:
        28px;

    padding:
        28px;

    box-shadow:
        6px 6px 0 #59495d;

    text-align:
        center;

    margin-top:
        16px;

    margin-bottom:
        25px;
}


.mood-emoji {

    font-size:
        4.2rem;

    margin-bottom:
        5px;
}


.mood-name {

    font-size:
        2rem;

    font-weight:
        950;

    color:
        #4c3d50;
}


.mood-message {

    color:
        #776577;

    margin-top:
        9px;

    line-height:
        1.6;
}


/* =====================================================
   METRICS
===================================================== */

div[data-testid="stMetric"] {

    background:
        rgba(255,255,255,.75);

    border:
        1.7px solid #d2c2d1;

    border-radius:
        22px;

    padding:
        18px;

    box-shadow:
        4px 4px 0 rgba(89,73,93,.13);
}


div[data-testid="stMetricLabel"] {

    color:
        #877587 !important;

    font-weight:
        750 !important;
}


div[data-testid="stMetricValue"] {

    color:
        #4c3d50 !important;

    font-weight:
        950 !important;
}


/* =====================================================
   CHART CARDS
===================================================== */

div[data-testid="stPlotlyChart"] {

    background:
        rgba(255,255,255,.72);

    border:
        1.8px solid #d3c2d1;

    border-radius:
        26px !important;

    overflow:
        hidden !important;

    padding:
        5px;

    box-shadow:
        5px 5px 0 rgba(89,73,93,.12);
}


div[data-testid="stPlotlyChart"] > div,
div[data-testid="stPlotlyChart"] .js-plotly-plot,
div[data-testid="stPlotlyChart"] .plot-container,
div[data-testid="stPlotlyChart"] .svg-container {

    border-radius:
        26px !important;

    overflow:
        hidden !important;
}


/* =====================================================
   AFFIRMATION
===================================================== */

.affirmation {

    background:
        linear-gradient(
            90deg,
            #ebe4ff,
            #ffe3ee,
            #fff0c9
        );

    border:
        2px solid #59495d;

    border-radius:
        22px;

    padding:
        17px;

    text-align:
        center;

    font-weight:
        850;

    color:
        #59495d;

    box-shadow:
        4px 4px 0 #59495d;

    margin:
        25px 0;
}


/* =====================================================
   JOURNAL ENTRY CARD
===================================================== */

.entry-card {

    background:
        rgba(255,255,255,.75);

    border:
        1.8px solid #d5c5d4;

    border-radius:
        24px;

    padding:
        18px 20px;

    box-shadow:
        4px 4px 0 rgba(89,73,93,.10);

    margin-bottom:
        12px;
}


.entry-date {

    color:
        #9a8598;

    font-size:
        .82rem;

    margin-bottom:
        6px;
}


.entry-mood {

    font-weight:
        900;

    color:
        #59495d;

    margin-bottom:
        8px;
}


.entry-text {

    color:
        #675867;

    line-height:
        1.6;
}


/* =====================================================
   SIDEBAR
===================================================== */

section[data-testid="stSidebar"] {

    background:
        linear-gradient(
            180deg,
            #f5e9f4,
            #eee8ff,
            #e9f4ff
        );

    border-right:
        1.5px solid #d0c0d0;
}


section[data-testid="stSidebar"] * {
    color:
        #59495d;
}


section[data-testid="stSidebar"]
div[data-baseweb="select"] > div {

    background:
        rgba(255,255,255,.77);

    border:
        1.5px solid #cbb9ca;

    border-radius:
        14px;
}


/* =====================================================
   DOWNLOAD
===================================================== */

.stDownloadButton > button {

    width:
        100%;

    border-radius:
        999px;

    border:
        2px solid #59495d;

    background:
        #fff8fb;

    color:
        #59495d;

    font-weight:
        850;

    box-shadow:
        3px 3px 0 #59495d;
}


/* =====================================================
   DIVIDERS
===================================================== */

hr {

    border:
        none;

    border-top:
        1px dashed #cdbbca;

    margin:
        2rem 0;
}


/* =====================================================
   MOBILE
===================================================== */

@media (max-width: 700px) {

    .journal-hero {
        padding:
            27px 24px;
    }

    .hero-doodle-one,
    .hero-doodle-two {
        display:
            none;
    }

}

</style>
"""
)


# =========================================================
# HERO
# =========================================================

st.html(
    """
<div class="journal-hero">

    <div class="hero-badge">
        ✿ little thoughts, big feelings
    </div>

    <div class="hero-title">
        Moonlit Journal
    </div>

    <div class="hero-sub">
        A soft little corner for your thoughts.
        Write whatever is on your mind and watch your
        mood patterns become something you can see.
    </div>

    <div class="hero-doodle-one">
        🌙
    </div>

    <div class="hero-doodle-two">
        ✦ ☁️ ♡
    </div>

</div>
"""
)


# =========================================================
# SIDEBAR
# =========================================================

entries = load_entries()

st.sidebar.title("My Journal 🌷")

st.sidebar.caption(
    "Filter your little archive."
)


if not entries.empty:

    mood_options = sorted(
        entries["Mood"]
        .dropna()
        .unique()
    )

    selected_moods = st.sidebar.multiselect(
        "Mood",
        mood_options,
        default=mood_options,
    )

else:

    selected_moods = []


st.sidebar.divider()


st.sidebar.markdown(
    "### ✦ Journal Stats"
)


if not entries.empty:

    st.sidebar.write(
        f"**{len(entries)}** total entries"
    )

    streak = calculate_streak(
        entries
    )

    st.sidebar.write(
        f"**{streak} day** reflection streak"
        if streak == 1
        else f"**{streak} days** reflection streak"
    )

else:

    st.sidebar.write(
        "Your journal is waiting for its first entry."
    )


# =========================================================
# JOURNAL INPUT
# =========================================================

left, right = st.columns(
    [1.45, 0.55],
    gap="large",
)


with left:

    st.html(
        """
<div class="section-title">
    Dear journal... 💌
</div>

<div class="section-sub">
    No rules. No perfect wording. Just write.
</div>
"""
    )


    st.html(
        f"""
<div class="prompt-card">

    <div class="prompt-label">
        today's reflection prompt
    </div>

    <div class="prompt-text">
        {daily_prompt}
    </div>

</div>
"""
    )


    journal_entry = st.text_area(
        "Journal entry",
        label_visibility="collapsed",
        placeholder=(
            "Today felt...\n\n"
            "Write about your day, your thoughts, "
            "something tiny, something huge — anything."
        ),
    )


    if st.button(
        "Save entry & reveal my mood ✨",
        use_container_width=True,
    ):

        if journal_entry.strip():

            result = analyze_mood(
                journal_entry
            )

            save_entry(
                journal_entry,
                result,
            )

            st.session_state[
                "last_result"
            ] = result

            st.session_state[
                "last_entry"
            ] = journal_entry

            st.rerun()

        else:

            st.warning(
                "Write a little something first 🌷"
            )


with right:

    st.html(
        """
<div class="section-title">
    Tiny reminder ✦
</div>

<div class="section-sub">
    You don't have to make your entry sound profound.
</div>
"""
    )

    st.html(
        f"""
<div class="affirmation">
    {daily_affirmation}
</div>
"""
    )

    st.markdown(
        """
        #### Mood scale

        ☀️ **Very Happy**  
        🌷 **Happy**  
        ☁️ **Neutral**  
        🌧️ **Low**  
        🌙 **Very Low**
        """
    )


# =========================================================
# LATEST RESULT
# =========================================================

if "last_result" in st.session_state:

    result = st.session_state[
        "last_result"
    ]

    st.divider()

    st.html(
        """
<div class="section-title">
    Your entry feels like...
</div>
"""
    )


    st.html(
        f"""
<div
    class="mood-card"
    style="
        background:
        linear-gradient(
            135deg,
            {result['soft']},
            #fffafd
        );
    "
>

    <div class="mood-emoji">
        {result['emoji']}
    </div>

    <div class="mood-name">
        {result['mood']}
    </div>

    <div class="mood-message">
        {result['message']}
    </div>

</div>
"""
    )


    r1, r2, r3 = st.columns(3)

    r1.metric(
        "Mood Score",
        f"{result['mood_score']}/5",
    )

    r2.metric(
        "Sentiment",
        f"{result['polarity']:.2f}",
    )

    r3.metric(
        "Emotional Intensity",
        f"{result['subjectivity']:.2f}",
    )


# =========================================================
# RELOAD AFTER SAVE
# =========================================================

entries = load_entries()


if entries.empty:

    st.divider()

    st.info(
        "Your mood garden will start growing "
        "after your first journal entry 🌱"
    )

    st.stop()


# =========================================================
# FILTER HISTORY
# =========================================================

if selected_moods:

    filtered_entries = entries[
        entries["Mood"].isin(
            selected_moods
        )
    ].copy()

else:

    filtered_entries = entries.copy()


# =========================================================
# SUMMARY
# =========================================================

st.divider()

st.html(
    """
<div class="section-title">
    Your mood garden 🌷
</div>

<div class="section-sub">
    A little snapshot of how your journal has been feeling.
</div>
"""
)


total_entries = len(
    filtered_entries
)

average_mood = (
    filtered_entries["Mood Score"]
    .mean()
)

common_mood = (
    filtered_entries["Mood"]
    .mode()
    .iloc[0]
    if not filtered_entries.empty
    else "—"
)

streak = calculate_streak(
    entries
)


m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "Journal Entries",
    total_entries,
)

m2.metric(
    "Average Mood",
    (
        f"{average_mood:.1f}/5"
        if pd.notna(average_mood)
        else "—"
    ),
)

m3.metric(
    "Most Common Mood",
    common_mood,
)

m4.metric(
    "Reflection Streak",
    f"{streak} days",
)


# =========================================================
# CHART STYLE
# =========================================================

def style_chart(fig):

    fig.update_layout(
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",

        font=dict(
            family="Arial",
            color="#655666",
        ),

        title=dict(
            font=dict(
                size=17,
                color="#4c3d50",
            ),
            x=0.03,
        ),

        margin=dict(
            l=30,
            r=15,
            t=60,
            b=35,
        ),

        showlegend=False,
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor="#d7c8d6",
    )

    fig.update_yaxes(
        gridcolor="#eadfea",
        linecolor="#d7c8d6",
    )

    return fig


# =========================================================
# MOOD TREND
# =========================================================

history = filtered_entries.sort_values(
    "Date"
)


fig_trend = px.line(
    history,
    x="Date",
    y="Mood Score",
    markers=True,
    title="Mood Over Time",
    hover_data=[
        "Mood",
    ],
)


fig_trend.update_traces(
    line=dict(
        color="#C98FB3",
        width=4,
    ),

    marker=dict(
        size=10,
        color="#927DAE",
        line=dict(
            width=2,
            color="#ffffff",
        ),
    ),
)


fig_trend.update_yaxes(
    tickmode="array",

    tickvals=[
        1,
        2,
        3,
        4,
        5,
    ],

    ticktext=[
        "Very Low",
        "Low",
        "Neutral",
        "Happy",
        "Very Happy",
    ],

    range=[
        0.5,
        5.5,
    ],
)


fig_trend = style_chart(
    fig_trend
)


st.plotly_chart(
    fig_trend,
    use_container_width=True,
    config={
        "displayModeBar": False,
    },
)


# =========================================================
# MOOD DISTRIBUTION + WORDS
# =========================================================

chart_left, chart_right = st.columns(
    2,
    gap="large",
)


with chart_left:

    mood_counts = (
        filtered_entries["Mood"]
        .value_counts()
        .reset_index()
    )

    mood_counts.columns = [
        "Mood",
        "Entries",
    ]


    mood_colors = {
        mood: info["color"]
        for mood, info in MOODS.items()
    }


    fig_mood = px.pie(
        mood_counts,
        names="Mood",
        values="Entries",
        hole=0.62,
        title="Mood Mix",
        color="Mood",
        color_discrete_map=mood_colors,
    )


    fig_mood.update_traces(
        textposition="inside",
        textinfo="percent+label",
    )


    fig_mood.update_layout(
        paper_bgcolor="rgba(255,255,255,0)",

        font=dict(
            color="#655666",
        ),

        title=dict(
            font=dict(
                size=17,
                color="#4c3d50",
            ),
            x=.03,
        ),

        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),

        showlegend=False,
    )


    st.plotly_chart(
        fig_mood,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )


with chart_right:

    words = common_words(
        filtered_entries
    )

    if words:

        words_df = pd.DataFrame(
            words,
            columns=[
                "Word",
                "Mentions",
            ],
        )


        fig_words = px.bar(
            words_df.sort_values(
                "Mentions"
            ),
            x="Mentions",
            y="Word",
            orientation="h",
            title="Words That Keep Appearing",
            text="Mentions",
            color_discrete_sequence=[
                "#B79DDB"
            ],
        )


        fig_words.update_traces(
            textposition="outside"
        )

        fig_words = style_chart(
            fig_words
        )


        st.plotly_chart(
            fig_words,
            use_container_width=True,
            config={
                "displayModeBar": False,
            },
        )


# =========================================================
# EXPORT
# =========================================================

st.divider()

export_left, export_right = st.columns(
    [1, 2]
)


with export_left:

    csv_data = entries.to_csv(
        index=False
    ).encode("utf-8")


    st.download_button(
        "Download my journal ↓",
        data=csv_data,
        file_name="moonlit_journal.csv",
        mime="text/csv",
        use_container_width=True,
    )


with export_right:

    st.html(
        """
<div class="affirmation">
    your journal belongs to you ♡
</div>
"""
    )


# =========================================================
# RECENT ENTRIES
# =========================================================

st.divider()

st.html(
    """
<div class="section-title">
    Pages from your journal 📖
</div>

<div class="section-sub">
    Your latest entries, newest first.
</div>
"""
)


recent_entries = (
    filtered_entries
    .sort_values(
        "Date",
        ascending=False,
    )
    .head(12)
)


for _, row in recent_entries.iterrows():

    mood = row["Mood"]

    emoji = (
        MOODS.get(
            mood,
            {},
        )
        .get(
            "emoji",
            "☁️",
        )
    )


    pretty_date = (
        row["Date"]
        .strftime(
            "%d %b %Y · %I:%M %p"
        )
        if pd.notna(
            row["Date"]
        )
        else "Unknown date"
    )


    entry_col, delete_col = st.columns(
        [0.93, 0.07]
    )


    with entry_col:

        safe_entry = (
            str(row["Entry"])
            .replace(
                "&",
                "&amp;",
            )
            .replace(
                "<",
                "&lt;",
            )
            .replace(
                ">",
                "&gt;",
            )
        )


        st.html(
            f"""
<div class="entry-card">

    <div class="entry-date">
        {pretty_date}
    </div>

    <div class="entry-mood">
        {emoji} {mood}
    </div>

    <div class="entry-text">
        {safe_entry}
    </div>

</div>
"""
        )


    with delete_col:

        with st.popover(
            "🗑️",
            use_container_width=True,
        ):

            st.write(
                "Delete this entry?"
            )

            st.caption(
                "This can't be undone."
            )


            if st.button(
                "Delete",
                key=(
                    f"delete_"
                    f"{row['ID']}"
                ),
                use_container_width=True,
            ):

                delete_entry(
                    row["ID"]
                )

                st.rerun()