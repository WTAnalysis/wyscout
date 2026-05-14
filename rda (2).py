import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from urllib.request import urlopen
from mplsoccer import PyPizza, Radar, add_image, FontManager
from scipy.stats import rankdata


st.set_page_config(layout="wide")
st.title("WT Analysis - Pizza Chart Generator")


# -----------------------------
# Helpers
# -----------------------------

POSITION_ORDER = ["GK", "CB", "LB", "RB", "LWB", "RWB", "DM", "CM", "AM", "LW", "RW", "CF"]

POSITION_REPLACEMENTS = {
    "LWF": "LW", "RWF": "RW",
    "LCMF": "CM", "RCMF": "CM",
    "DMF": "DM", "RDMF": "DM", "LDMF": "DM",
    "AMF": "AM", "RAMF": "RW", "LAMF": "LW",
    "RCB": "CB", "LCB": "CB",
}

LEAGUE_IMAGE_MAP = {
    "Premier League": "https://cdn5.wyscout.com/photos/competition/public/5_140x140.png",
    "League One": "https://cdn5.wyscout.com/photos/competition/public/64_140x140.png",
    "Championship": "https://cdn5.wyscout.com/photos/competition/public/18_140x140.png",
    "Serie A": "https://cdn5.wyscout.com/photos/competition/public/1_140x140.png",
    "League Two": "https://cdn5.wyscout.com/photos/competition/public/67_140x140.png",
    "Scottish Premiership": "https://cdn5.wyscout.com/photos/competition/public/17_140x140.png",
    "MLS": "https://cdn5.wyscout.com/photos/competition/public/324_140x140.png",
    "WSL": "https://cdn5.wyscout.com/photos/competition/public/g886_140x140.png",
    "WSL2": "https://cdn5.wyscout.com/photos/competition/public/g1330_140x140.png",
    "Women's National League": "https://cdn5.wyscout.com/photos/competition/public/g327_140x140.png",
    "PGA League": "https://cdn5.wyscout.com/photos/competition/public/g-557_140x140.png",
    "Women's A-League": "https://cdn5.wyscout.com/photos/competition/public/g370_140x140.png",
    "USL Super League": "https://cdn5.wyscout.com/photos/competition/public/g-985_140x140.png",
    "La Liga": "https://cdn5.wyscout.com/photos/competition/public/4_140x140.png",
    "Bundesliga": "https://cdn5.wyscout.com/photos/competition/public/2_140x140.png",
    "Bundesliga Two": "https://cdn5.wyscout.com/photos/competition/public/19_140x140.png",
    "Ligue 1": "https://cdn5.wyscout.com/photos/competition/public/3_140x140.png",
    "Pro League": "https://cdn5.wyscout.com/photos/competition/public/28_140x140.png",
    "Liga Portugal": "https://cdn5.wyscout.com/photos/competition/public/9_140x140.png",
    "National League": "https://cdn5.wyscout.com/photos/competition/public/135_140x140.png",
    "National League N/S": "https://cdn5.wyscout.com/photos/competition/public/135_140x140.png",
    "English 7th Tier": "https://cdn5.wyscout.com/photos/competition/public/555_140x140.png",
    "U18 Premier League": "https://cdn5.wyscout.com/photos/competition/public/g950_140x140.png",
    "Premier League 2": "https://cdn5.wyscout.com/photos/competition/public/g1592_140x140.png",
    "Professional Development League": "https://cdn5.wyscout.com/photos/competition/public/g1191_140x140.png",
    "INT-FIFACWC": "https://cdn5.wyscout.com/photos/competition/public/g72_140x140.png",
}


FULLBACK_COLS = [
    "Shot assists per 90", "xA per 90", "Assists per 90",
    "xG per 90", "Successful attacking actions per 90",
    "Accurate passes, %", "Accurate progressive passes, %", "Crosses per 90",
    "Accurate crosses, %", "Progressive runs per 90",
    "Successful defensive actions per 90", "Defensive duels won, %",
    "PAdj Sliding tackles", "Shots blocked per 90", "PAdj Interceptions"
]

FULLBACK_PARAMS = [
    "Shot assists", "xA", "Assists",
    "xG", "\nSuccessful \nattacking actions",
    "Accurate passes %", "\nAccurate progressive \npasses %", "Crosses",
    "Accurate crosses %", "Progressive runs",
    "\nSuccessful \ndefensive actions", "\nDefensive \nduels won %",
    "\nPAdj Sliding \ntackles", "Shots blocked", "\nPAdj \nInterceptions"
]


POS_COLS = {
    "LB": FULLBACK_COLS,
    "RB": FULLBACK_COLS,
    "LWB": FULLBACK_COLS,
    "RWB": FULLBACK_COLS,

    "CM": [
        "Non-penalty goals per 90", "xG per 90", "xA per 90",
        "Shot assists per 90", "Touches in box per 90",
        "Accurate passes, %", "Accurate progressive passes, %", "Progressive runs per 90",
        "Accurate passes to final third, %", "Accurate crosses, %",
        "Successful defensive actions per 90", "Defensive duels won, %",
        "PAdj Sliding tackles", "Shots blocked per 90", "PAdj Interceptions"
    ],
    "CB": [
        "Offensive duels won, %", "Shot assists per 90", "xA per 90",
        "xG per 90", "Non-penalty goals per 90",
        "Accurate passes, %", "Accurate lateral passes, %", "Accurate short / medium passes, %",
        "Progressive passes per 90", "Accurate progressive passes, %",
        "Defensive duels won, %", "Successful defensive actions per 90",
        "Aerial duels won, %", "PAdj Interceptions", "Shots blocked per 90"
    ],
    "CF": [
        "Touches in box per 90", "Shots per 90", "Shots on target, %",
        "xG per 90", "Non-penalty goals per 90",
        "Accurate passes, %", "Accurate smart passes, %", "Shot assists per 90",
        "xA per 90", "Assists per 90",
        "Offensive duels per 90", "Offensive duels won, %",
        "Aerial duels won, %", "Successful dribbles, %", "Successful attacking actions per 90"
    ],
    "LW": [
        "Touches in box per 90", "Shots per 90", "Shots on target, %",
        "xG per 90", "Non-penalty goals per 90",
        "Progressive runs per 90", "Accurate crosses, %", "Shot assists per 90",
        "xA per 90", "Assists per 90",
        "Offensive duels per 90", "Offensive duels won, %",
        "Dribbles per 90", "Successful dribbles, %", "Successful attacking actions per 90"
    ],
    "RW": [
        "Touches in box per 90", "Shots per 90", "Shots on target, %",
        "xG per 90", "Non-penalty goals per 90",
        "Progressive runs per 90", "Accurate crosses, %", "Shot assists per 90",
        "xA per 90", "Assists per 90",
        "Offensive duels per 90", "Offensive duels won, %",
        "Dribbles per 90", "Successful dribbles, %", "Successful attacking actions per 90"
    ],
    "DM": [
        "Successful attacking actions per 90", "Shot assists per 90", "xA per 90",
        "Shots per 90", "xG per 90",
        "Accurate passes, %", "Accurate short / medium passes, %", "Accurate through passes, %",
        "Progressive passes per 90", "Accurate progressive passes, %",
        "Successful defensive actions per 90", "Defensive duels per 90",
        "Defensive duels won, %", "PAdj Sliding tackles", "PAdj Interceptions"
    ],
    "AM": [
        "Touches in box per 90", "Shots per 90", "Goal conversion, %",
        "Non-penalty goals per 90", "xG per 90",
        "Accurate passes to penalty area, %", "Accurate crosses, %", "Shot assists per 90",
        "xA per 90", "Assists per 90",
        "Offensive duels per 90", "Offensive duels won, %", "Successful attacking actions per 90",
        "Dribbles per 90", "Successful dribbles, %"
    ],
}


POS_PARAMS = {
    "LB": FULLBACK_PARAMS,
    "RB": FULLBACK_PARAMS,
    "LWB": FULLBACK_PARAMS,
    "RWB": FULLBACK_PARAMS,

    "CM": [
        "Non-penalty goals", "xG", "xA",
        "Shot assists", "Touches in box",
        "Accurate passes %", "\nAccurate progressive \npasses %", "Progressive runs",
        "\nAccurate passes \nto final third %", "Accurate crosses %",
        "\nSuccessful \ndefensive actions", "\nDefensive \nduels won %",
        "\nPAdj Sliding \ntackles", "Shots blocked", "\nPAdj \nInterceptions"
    ],
    "CB": [
        "\nOffensive \nduels won %", "Shot assists", "xA",
        "xG", "\nNon-penalty \ngoals",
        "Accurate passes %", "\nAccurate lateral \npasses %", "\nAccurate short \n& medium passes %",
        "\nProgressive \npasses", "\nAccurate progressive \npasses %",
        "\nDefensive \nduels won %", "\nSuccessful \ndefensive actions",
        "\nAerial \nduels won %", "\nPAdj \nInterceptions", "Shots blocked"
    ],
    "CF": [
        "Touches in box", "Shots", "\nShots on \ntarget %",
        "xG", "Non-penalty goals",
        "Accurate passes %", "\nAccurate smart \npasses %", "Shot assists",
        "xA", "Assists",
        "Offensive duels", "\nOffensive \nduels won %",
        "\nAerial \nduels won %", "\nSuccessful \ndribbles %", "\nSuccessful \nattacking actions"
    ],
    "LW": [
        "Touches in box", "Shots", "\nShots on \ntarget %",
        "xG", "Non-penalty goals",
        "Progressive runs", "Accurate crosses %", "Shot assists",
        "xA", "Assists",
        "Offensive duels", "\nOffensive \nduels won %",
        "Dribbles", "\nSuccessful \ndribbles %", "\nSuccessful \nattacking actions"
    ],
    "RW": [
        "Touches in box", "Shots", "\nShots on \ntarget %",
        "xG", "Non-penalty goals",
        "Progressive runs", "Accurate crosses %", "Shot assists",
        "xA", "Assists",
        "Offensive duels", "\nOffensive \nduels won %",
        "Dribbles", "\nSuccessful \ndribbles %", "\nSuccessful \nattacking actions"
    ],
    "DM": [
        "\nSuccessful \nattacking actions", "Shot assists", "xA",
        "Shots", "xG",
        "Accurate passes %", "\nAccurate \nshort/medium passes %", "\nAccurate \nthrough passes %",
        "\nProgressive \npasses", "\nAccurate \nprogressive passes %",
        "\nSuccessful \ndefensive actions", "Defensive duels",
        "\nDefensive \nduels won %", "\nPAdj \nSliding tackles", "\nPAdj \nInterceptions"
    ],
    "AM": [
        "Touches in box", "Shots", "Goal conversion %",
        "Non-penalty goals", "xG",
        "\nAccurate passes \nto penalty area %", "\nAccurate \ncrosses %", "Shot assists",
        "xA", "Assists",
        "Offensive duels", "\nOffensive \nduels won %", "\nSuccessful \nattacking actions",
        "Dribbles", "\nSuccessful \ndribbles %"
    ],
}


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "Position" not in df.columns:
        st.error("Your file must contain a 'Position' column.")
        st.stop()

    pos_split = df["Position"].astype(str).str.split(",", expand=True)

    while pos_split.shape[1] < 4:
        pos_split[pos_split.shape[1]] = None

    pos_split = pos_split.iloc[:, :4]
    pos_split.columns = ["position1", "position2", "position3", "position4"]

    for col in pos_split.columns:
        pos_split[col] = (
            pos_split[col]
            .astype("string")
            .str.strip()
            .str.upper()
            .replace(POSITION_REPLACEMENTS)
        )

    df = pd.concat([df.drop(columns=["Position"]), pos_split], axis=1)

    return df


def filter_by_position(df: pd.DataFrame, position: str, minutes: int) -> pd.DataFrame:
    position = str(position).strip().upper()

    mask = (
        (df["position1"] == position) |
        (df["position2"] == position) |
        (df["position3"] == position) |
        (df["position4"] == position)
    )

    out = df.loc[mask].copy()

    if "Minutes played" in out.columns:
        out["Minutes played"] = pd.to_numeric(out["Minutes played"], errors="coerce").fillna(0)
        out = out.loc[out["Minutes played"] >= minutes].copy()

    return out


def get_team_name(row_df: pd.DataFrame) -> str:
    for col in ["Team", "Team within selected timeframe"]:
        if col in row_df.columns:
            return str(row_df[col].iloc[0])
    return ""


def get_logo_image(league: str):
    if not league:
        return None

    url = LEAGUE_IMAGE_MAP.get(league)
    if not url:
        return None

    try:
        return Image.open(urlopen(url))
    except Exception:
        return None


def get_rda_image():
    try:
        return Image.open("wtatransnew.png")
    except Exception:
        return None


def build_colors(n: int):
    slice_colors = (
        ["#ea5a00"] * min(5, n)
        + ["#004E89"] * min(5, max(n - 5, 0))
        + ["#630101"] * max(n - 10, 0)
    )
    text_colors = ["#000000"] * min(10, n) + ["#F2F2F2"] * max(n - 10, 0)
    return slice_colors, text_colors


def add_chart_images(fig, rdaimage, leagueimage):
    try:
        if rdaimage is not None:
            add_image(rdaimage, fig, left=0.87, bottom=0.85, width=0.15, height=0.15)
    except Exception:
        pass

    try:
        if leagueimage is not None:
            add_image(leagueimage, fig, left=0.05, bottom=0.01, width=0.125, height=0.125)
    except Exception:
        pass


def validate_template(position, cols, params, df):
    if not cols or not params:
        st.error(f"No metric template configured for position: {repr(position)}")
        st.stop()

    if len(cols) != len(params):
        st.error(f"Template mismatch for {position}: {len(cols)} columns but {len(params)} labels.")
        st.stop()

    missing = [c for c in cols if c not in df.columns]
    if missing:
        st.error(f"Missing columns for {position}: {missing}")
        st.stop()


# -----------------------------
# Upload
# -----------------------------

uploaded_file = st.file_uploader(
    "Upload Wyscout Data (All Metrics, Excel File)",
    type=["xlsx"]
)

if uploaded_file is None:
    st.info("Upload an Excel (.xlsx) file to begin.")
    st.stop()

data_original = pd.read_excel(uploaded_file)

if "Player" not in data_original.columns:
    st.error("Your file must contain a 'Player' column.")
    st.stop()

data = prepare_data(data_original)


# -----------------------------
# UI
# -----------------------------

league = st.selectbox(
    "League",
    options=[
        "", "Bundesliga", "Bundesliga Two", "Championship", "English 7th Tier",
        "La Liga", "League One", "League Two", "Liga Portugal", "Ligue 1", "MLS",
        "National League", "National League N/S", "PGA League", "Premier League",
        "Premier League 2", "Pro League", "Professional Development League",
        "Scottish Premiership", "Serie A", "U18 Premier League", "USL Super League",
        "WSL", "WSL2", "Women's A-League", "Women's National League"
    ]
)

available_positions = [
    p for p in POSITION_ORDER
    if p in set(data[["position1", "position2", "position3", "position4"]].values.ravel())
    and p in POS_COLS
]

position = st.selectbox(
    "Position",
    options=[""] + available_positions,
    key="position_select"
)

position = str(position).strip().upper()

season = st.text_input("Season", value="Enter Season Name")
minutethreshold = st.number_input("Minimum Minutes Played", min_value=0, value=0, step=50)

if not position:
    st.info("Select a position to continue.")
    st.stop()

position_data = filter_by_position(data, position, minutethreshold)

st.subheader("Filtered Data Preview")
st.dataframe(position_data)

if position_data.empty:
    st.warning("No players found for that position at the selected minute threshold.")
    st.stop()

eligible_players = sorted(position_data["Player"].dropna().unique())

playerrequest = st.selectbox(
    "Select Player",
    options=eligible_players,
    key="player_select"
)

playerdata = position_data.loc[position_data["Player"] == playerrequest].copy()

if playerdata.empty:
    st.warning(f"Player '{playerrequest}' not found in the filtered dataset.")
    st.stop()


# -----------------------------
# Fonts and images
# -----------------------------

font_normal = FontManager(
    "https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Regular.ttf"
)
font_italic = FontManager(
    "https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Italic.ttf"
)
font_bold = FontManager(
    "https://raw.githubusercontent.com/google/fonts/main/apache/robotoslab/RobotoSlab[wght].ttf"
)

rdaimage = get_rda_image()
leagueimage = get_logo_image(league)


# -----------------------------
# Shared setup
# -----------------------------

cols = POS_COLS.get(position, [])
params = POS_PARAMS.get(position, [])

validate_template(position, cols, params, position_data)

for c in cols:
    position_data[c] = pd.to_numeric(position_data[c], errors="coerce")
    playerdata[c] = pd.to_numeric(playerdata[c], errors="coerce")

teamname = get_team_name(playerdata)


# -----------------------------
# Tabs
# -----------------------------

tab_pizza, tab_radar, tab_raw_pizza = st.tabs(["📊 Pizza", "🧭 Radar", "📈 Raw Pizza"])


# -----------------------------
# Percentile Pizza
# -----------------------------

with tab_pizza:
    percentile_df = position_data.copy()

    for col in cols:
        percentile_df[col] = pd.to_numeric(percentile_df[col], errors="coerce")
        valid = percentile_df[col].notna()

        if valid.sum() > 0:
            percentile_df.loc[valid, col] = (
                rankdata(percentile_df.loc[valid, col], method="average")
                / valid.sum()
                * 100
            )

    player_percentile = percentile_df.loc[percentile_df["Player"] == playerrequest].copy()

    if player_percentile.empty:
        st.error(f"No percentile row found for {playerrequest}.")
        st.stop()

    values = player_percentile[cols].iloc[0].fillna(0).round(0).astype(int).tolist()

    if len(values) != len(params):
        st.error(f"Pizza mismatch: {len(values)} values vs {len(params)} params.")
        st.stop()

    slice_colors, text_colors = build_colors(len(params))

    baker = PyPizza(
        params=params,
        background_color="#F2F2F2",
        straight_line_color="#F2F2F2",
        straight_line_lw=1,
        last_circle_lw=0,
        other_circle_lw=0,
        inner_circle_size=20
    )

    fig, ax = baker.make_pizza(
        values,
        figsize=(8, 8.5),
        color_blank_space="same",
        slice_colors=slice_colors,
        value_colors=text_colors,
        value_bck_colors=slice_colors,
        blank_alpha=0.4,
        kwargs_slices=dict(edgecolor="#F2F2F2", zorder=2, linewidth=1),
        kwargs_params=dict(
            color="#000000",
            fontsize=11,
            fontproperties=font_normal.prop,
            va="center"
        ),
        kwargs_values=dict(
            color="#000000",
            fontsize=11,
            fontproperties=font_normal.prop,
            zorder=3,
            bbox=dict(
                edgecolor="#000000",
                facecolor="cornflowerblue",
                boxstyle="round,pad=0.2",
                lw=1
            )
        )
    )

    fig.text(
        0.515, 0.975,
        f"{playerrequest} - {teamname} - Percentile Rank (0-100)",
        size=16,
        ha="center",
        fontproperties=font_bold.prop,
        color="#000000"
    )

    fig.text(
        0.515, 0.953,
        f"Compared against other {position} in {league} | Season {season}",
        size=13,
        ha="center",
        fontproperties=font_bold.prop,
        color="#000000"
    )

    fig.text(
        0.99, 0.02,
        f"Data from Wyscout | Metrics are per 90 unless stated | Minimum {minutethreshold} mins played",
        size=9,
        fontproperties=font_italic.prop,
        color="#000000",
        ha="right"
    )

    header_text = "Scoring           Creativity         Attacking" if position in {"RW", "LW", "CF"} else "Attacking        Possession      Defending"

    fig.text(
        0.34, 0.925,
        header_text,
        size=14,
        fontproperties=font_bold.prop,
        color="#000000"
    )

    fig.patches.extend([
        plt.Rectangle((0.31, 0.9225), 0.025, 0.021, fill=True, color="#ea5a00", transform=fig.transFigure, figure=fig),
        plt.Rectangle((0.462, 0.9225), 0.025, 0.021, fill=True, color="#004E89", transform=fig.transFigure, figure=fig),
        plt.Rectangle((0.632, 0.9225), 0.025, 0.021, fill=True, color="#630101", transform=fig.transFigure, figure=fig),
    ])

    add_chart_images(fig, rdaimage, leagueimage)

    st.pyplot(fig, clear_figure=True)


# -----------------------------
# Radar
# -----------------------------

with tab_radar:
    radar_df = position_data.copy()

    for c in cols:
        radar_df[c] = pd.to_numeric(radar_df[c], errors="coerce")

    radar_player = radar_df.loc[radar_df["Player"] == playerrequest]

    if radar_player.empty:
        st.error(f"No radar data found for {playerrequest}.")
        st.stop()

    low = radar_df[cols].min().fillna(0).round(2).tolist()
    high = radar_df[cols].max().fillna(0).round(2).tolist()
    league_avg = radar_df[cols].mean().fillna(0).round(2).tolist()
    player_vals = radar_player[cols].iloc[0].fillna(0).round(2).tolist()

    radar = Radar(
        params=params,
        min_range=low,
        max_range=high,
        round_int=[False] * len(params),
        num_rings=4,
        ring_width=1,
        center_circle_radius=1,
    )

    fig, ax = radar.setup_axis()
    fig.patch.set_facecolor("#F2F2F2")
    ax.set_facecolor("#F2F2F2")

    radar.draw_circles(ax=ax, facecolor="#b3b3b3", edgecolor="#b3b3b3")

    radar.draw_radar_compare(
        player_vals,
        league_avg,
        ax=ax,
        kwargs_radar={"facecolor": "#ea5a00", "alpha": 1},
        kwargs_compare={"facecolor": "#004E89", "alpha": 0.4}
    )

    radar.draw_range_labels(ax=ax, fontsize=10, fontproperties=font_italic.prop)
    radar.draw_param_labels(ax=ax, fontsize=12.5, fontproperties=font_bold.prop, color="black")
    radar.spoke(ax=ax, color="#a6a4a1", linestyle="--", zorder=2)

    ax_limits = ax.get_xlim(), ax.get_ylim()
    cx = (ax_limits[0][0] + ax_limits[0][1]) / 2

    ax.text(
        cx, 6.65,
        f"{playerrequest} compared to {league} ({position}) average in {season}",
        size=17,
        fontproperties=font_bold.prop,
        color="#000000",
        ha="center",
        bbox=dict(facecolor="#f2f2f2", alpha=0.5, edgecolor="#f2f2f2")
    )

    try:
        if rdaimage is not None:
            add_image(rdaimage, fig, left=0.775, bottom=0.725, width=0.15, height=0.15)
        if leagueimage is not None:
            add_image(leagueimage, fig, left=0.135, bottom=0.115, width=0.125, height=0.125)
    except Exception:
        pass

    fig.text(0.17, 0.8525, f"{playerrequest}", size=10, fontproperties=font_bold.prop, color="#000000")
    fig.text(0.17, 0.8275, "League Average", size=10, fontproperties=font_bold.prop, color="#000000")
    fig.text(0.67, 0.12, f"Data from Wyscout | Minimum {minutethreshold} minutes played", size=8, fontproperties=font_bold.prop, color="#000000")

    fig.patches.extend([
        plt.Rectangle((0.15, 0.85), 0.015, 0.015, fill=True, color="#ea5a00", transform=fig.transFigure, figure=fig),
        plt.Rectangle((0.15, 0.825), 0.015, 0.015, fill=True, color="#004E89", transform=fig.transFigure, figure=fig),
    ])

    st.pyplot(fig, clear_figure=True)


# -----------------------------
# Raw Pizza
# -----------------------------

with tab_raw_pizza:
    raw_df = position_data.copy()

    for c in cols:
        raw_df[c] = pd.to_numeric(raw_df[c], errors="coerce")

    raw_player = raw_df.loc[raw_df["Player"] == playerrequest]

    if raw_player.empty:
        st.error(f"No raw data found for {playerrequest}.")
        st.stop()

    low = raw_df[cols].min().fillna(0).round(2).tolist()
    high = raw_df[cols].max().fillna(0).round(2).tolist()
    values = raw_player[cols].iloc[0].fillna(0).round(2).tolist()

    if len(values) != len(params):
        st.error(f"Raw pizza mismatch: {len(values)} values vs {len(params)} params.")
        st.stop()

    slice_colors, text_colors = build_colors(len(params))

    plt.close("all")

    baker = PyPizza(
        params=params,
        min_range=low,
        max_range=high,
        background_color="#F2F2F2",
        straight_line_color="#F2F2F2",
        last_circle_color="#000000",
        last_circle_lw=2.5,
        straight_line_lw=1,
        other_circle_lw=0,
        other_circle_color="#000000",
        inner_circle_size=20,
    )

    fig, ax = baker.make_pizza(
        values,
        figsize=(8, 8),
        color_blank_space="same",
        slice_colors=slice_colors,
        value_colors=text_colors,
        value_bck_colors=slice_colors,
        blank_alpha=0.4,
        param_location=110,
        kwargs_slices=dict(edgecolor="#F2F2F2", linewidth=1),
        kwargs_params=dict(
            color="#000000",
            fontsize=11,
            fontproperties=font_normal.prop,
            va="center"
        ),
        kwargs_values=dict(
            color="#000000",
            fontsize=11,
            fontproperties=font_normal.prop,
            zorder=3,
            bbox=dict(
                edgecolor="#000000",
                facecolor="cornflowerblue",
                boxstyle="round,pad=0.2",
                lw=1
            ),
        ),
    )

    fig.text(
        0.515, 0.975,
        f"{playerrequest} - {teamname}",
        size=16,
        ha="center",
        fontproperties=font_bold.prop,
        color="#000000"
    )

    fig.text(
        0.515, 0.953,
        f"{league} | Season {season} | > {minutethreshold} mins | Compared with other {position}",
        size=12,
        ha="center",
        fontproperties=font_bold.prop,
        color="#000000"
    )

    fig.text(
        0.99, 0.02,
        "Data from Wyscout | Metrics are per 90 unless stated | Raw metrics",
        size=9,
        fontproperties=font_italic.prop,
        color="#000000",
        ha="right"
    )

    header_text = "Scoring           Creativity         Attacking" if position in {"RW", "LW", "CF"} else "Attacking        Possession      Defending"

    fig.text(
        0.34, 0.925,
        header_text,
        size=14,
        fontproperties=font_bold.prop,
        color="#000000"
    )

    fig.patches.extend([
        plt.Rectangle((0.31, 0.9225), 0.025, 0.021, fill=True, color="#ea5a00", transform=fig.transFigure, figure=fig),
        plt.Rectangle((0.462, 0.9225), 0.025, 0.021, fill=True, color="#004E89", transform=fig.transFigure, figure=fig),
        plt.Rectangle((0.632, 0.9225), 0.025, 0.021, fill=True, color="#630101", transform=fig.transFigure, figure=fig),
    ])

    add_chart_images(fig, rdaimage, leagueimage)

    st.pyplot(fig, clear_figure=True)
