import glob
import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Credit Card Default Risk Dashboard", page_icon="💳", layout="wide",
                   initial_sidebar_state="collapsed")

DATA_PATH = "credit _ Data.xls"   # put the data file next to this script (any name like credit*Data*.xls works)

MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep"]
STATUS = [f"Repayment_Status_{m}" for m in MONTHS]
BILL = [f"Bill_Amount_{m}" for m in MONTHS]
PAY = [f"Payment_Amount_{m}" for m in MONTHS]


def find_data():
    for p in [DATA_PATH] + sorted(glob.glob("credit*ata*.xls*")) + sorted(glob.glob("*.xls*")):
        if os.path.exists(p):
            return p
    return DATA_PATH


@st.cache_data
def load_data(path):
    df = pd.read_excel(path, header=1)
    source_cols = {"Sep": ("PAY_0", "BILL_AMT1", "PAY_AMT1"), "Aug": ("PAY_2", "BILL_AMT2", "PAY_AMT2"),
                   "Jul": ("PAY_3", "BILL_AMT3", "PAY_AMT3"), "Jun": ("PAY_4", "BILL_AMT4", "PAY_AMT4"),
                   "May": ("PAY_5", "BILL_AMT5", "PAY_AMT5"), "Apr": ("PAY_6", "BILL_AMT6", "PAY_AMT6")}
    rename_map = {"ID": "Customer_ID", "LIMIT_BAL": "Credit_Limit", "SEX": "Gender", "EDUCATION": "Education_Level",
                  "MARRIAGE": "Marital_Status", "AGE": "Age", "default payment next month": "Default_Next_Month"}
    for m, (p, b, a) in source_cols.items():
        rename_map.update({p: f"Repayment_Status_{m}", b: f"Bill_Amount_{m}", a: f"Payment_Amount_{m}"})
    df = df.rename(columns=rename_map)

    df["Education_Level"] = df["Education_Level"].replace({0: 4, 5: 4, 6: 4})
    df["Marital_Status"] = df["Marital_Status"].replace({0: 3})
    late = df[STATUS].clip(lower=0)
    bill_total = df[BILL].sum(axis=1)
    df["Months_Delayed"] = (df[STATUS] > 0).sum(axis=1)
    df["Max_Delay"] = late.max(axis=1)
    df["Zero_Payment_Months"] = (df[PAY] == 0).sum(axis=1)
    df["Avg_Bill"] = df[BILL].mean(axis=1)
    df["Avg_Payment"] = df[PAY].mean(axis=1)
    df["Utilization"] = df["Avg_Bill"] / df["Credit_Limit"]
    df["Payment_Ratio"] = (df[PAY].sum(axis=1) / bill_total.where(bill_total > 0)).fillna(1).clip(0, 1)

    df["Gender"] = df["Gender"].map({1: "Male", 2: "Female"})
    df["Education_Level"] = df["Education_Level"].map({1: "Graduate school", 2: "University", 3: "High school", 4: "Others"})
    df["Marital_Status"] = df["Marital_Status"].map({1: "Married", 2: "Single", 3: "Others"})
    return df


data = load_data(find_data())

# ======================= HEADER PLACEHOLDER (filled once the theme is known) =======================
header_ph = st.empty()

# ======================= FILTER BAR + THEME SWITCH (top, full width) =======================
fb1, fb2, fb3, fb4, fb5, fb6 = st.columns([1.25, 1.25, 1.25, 1.4, 1.6, 0.7])
genders = sorted(data["Gender"].dropna().unique())
edus = list(data["Education_Level"].dropna().unique())
maritals = list(data["Marital_Status"].dropna().unique())
with fb1:
    gender = st.multiselect("Gender", genders, default=genders)
with fb2:
    edu = st.multiselect("Education", edus, default=edus)
with fb3:
    marital = st.multiselect("Marital status", maritals, default=maritals)
with fb4:
    age = st.slider("Age range", int(data["Age"].min()), int(data["Age"].max()),
                    (int(data["Age"].min()), int(data["Age"].max())))
with fb5:
    limit = st.slider("Credit limit (NT$)", int(data["Credit_Limit"].min()), int(data["Credit_Limit"].max()),
                      (int(data["Credit_Limit"].min()), int(data["Credit_Limit"].max())), step=10000)
with fb6:
    dark = st.toggle("🌙 Dark mode", value=False)

# ======================= THEME =======================
if dark:
    C = dict(bg1="#030a1a", bg2="#0b2150", card="#0e2146", edge="#1d3a6b", text="#e8f0ff", sub="#8fa8c9",
             grid="#1c3560", bar="#4f93e6", accent="#8cbcf5", track="#1b3560", banner="#06122b", onbg="#ffffff",
             tc="79,147,230", ico="#1d3f7a", input="#12294f",
             shades=["#4f93e6", "#8cbcf5", "#2b5fa8", "#b9d5f9", "#6aa5ee"])
else:
    C = dict(bg1="#0a2a66", bg2="#2b6cc4", card="#ffffff", edge="#d6e4f7", text="#0a2253", sub="#4a5f82",
             grid="#e1ebf8", bar="#0b3b82", accent="#3f87dc", track="#dce8f5", banner="#0a2253", onbg="#ffffff",
             tc="47,111,194", ico="#0a2f6b", input="#f4f8fd",
             shades=["#0a2f6b", "#2f6fc2", "#6fa8e8", "#a9c9f2", "#d3e3f8"])

CSS = """
<style>
.stApp { background: linear-gradient(160deg, @@bg1@@ 0%, @@bg2@@ 100%); background-attachment: fixed; }
[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"], #MainMenu, footer { display: none !important; }
.block-container { max-width: calc(100% - 28px) !important; margin: 14px auto !important;
    padding: 0 22px 14px 22px !important; border: 3px solid rgba(255,255,255,.65); border-radius: 34px;
    background: rgba(255,255,255,.03); }
[data-testid="stVerticalBlock"] { gap: .8rem; }
h1, h2, h3, p, label, .stMarkdown { color: @@text@@; }

/* filter bar sits on the blue frame */
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label, [data-testid="stToggle"] p,
[data-testid="stSlider"] label, [data-testid="stSliderThumbValue"], [data-testid="stSliderTickBarMin"],
[data-testid="stSliderTickBarMax"] { color: @@onbg@@ !important; font-weight: 600; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, input {
    background-color: @@input@@ !important; color: @@text@@ !important; border-color: @@edge@@ !important; border-radius: 12px !important; }
[data-baseweb="select"] * { color: @@text@@; }
span[data-baseweb="tag"] { background-color: @@bar@@ !important; color: #ffffff !important; }
span[data-baseweb="tag"] span { color: #ffffff !important; }
div[data-baseweb="slider"] div[role="slider"] { background-color: @@onbg@@ !important; }

/* title banner */
.banner { width: min(940px, 78%); margin: 0 auto 4px auto; text-align: center; background: @@banner@@;
    border: 3px solid rgba(255,255,255,.85); border-top: none; border-radius: 0 0 46px 46px; padding: 14px 24px 12px 24px;
    box-shadow: 0 8px 26px rgba(0,0,0,.28); }
.banner .t { color: #ffffff; font-size: 36px; font-weight: 800; letter-spacing: 2.5px; text-transform: uppercase; line-height: 1.15; }
.banner .s { color: #b9cdf0; font-size: 13.5px; margin-top: 4px; }
.banner .pill { display: inline-block; margin-top: 6px; background: rgba(255,255,255,.14); color: #ffffff;
    font-size: 12.5px; font-weight: 700; padding: 3px 14px; border-radius: 20px; }

/* every card */
[data-testid="stPlotlyChart"], .dash-card, .kpi, .strip {
    background: @@card@@; border: 1px solid @@edge@@; border-radius: 18px; box-shadow: 0 6px 20px rgba(0,0,0,.18); }
[data-testid="stPlotlyChart"] { padding: 12px 10px 4px 10px; }
.dash-card { box-sizing: border-box; padding: 16px 18px; overflow: hidden; }
.card-title { color: @@text@@; font-size: 13px; font-weight: 800; letter-spacing: .6px; text-transform: uppercase; text-align: center; margin-bottom: 12px; }

/* KPI cards */
.kpi { display: flex; align-items: center; gap: 16px; padding: 14px 18px; min-height: 104px; box-sizing: border-box; }
.kpi .ico { flex: 0 0 58px; height: 58px; border-radius: 50%; background: @@ico@@; display: flex; align-items: center;
    justify-content: center; font-size: 26px; }
.kpi .kt { color: @@text@@; font-size: 13px; font-weight: 800; letter-spacing: .5px; text-transform: uppercase; }
.kpi .kv { color: @@text@@; font-size: 32px; font-weight: 800; line-height: 1.15; }
.kpi .kn { color: @@sub@@; font-size: 12.5px; }

/* table card */
table.tbl { width: 100%; border-collapse: separate; border-spacing: 0 5px; font-size: 14px; }
table.tbl th { background: @@banner@@; color: #ffffff; padding: 9px 10px; font-size: 12.5px; text-align: left; }
table.tbl th:first-child { border-radius: 8px 0 0 8px; } table.tbl th:last-child { border-radius: 0 8px 8px 0; }
table.tbl td { padding: 9px 10px; color: @@text@@; background: @@track@@; }
table.tbl td:first-child { border-radius: 8px 0 0 8px; } table.tbl td:last-child { border-radius: 0 8px 8px 0; }

/* bottom strip */
.strip { display: flex; justify-content: space-between; align-items: center; padding: 14px 22px; border-radius: 24px; flex-wrap: wrap; gap: 10px; }
.strip .it { display: flex; align-items: center; gap: 12px; flex: 1; min-width: 200px; padding: 0 14px; border-right: 1px solid @@edge@@; }
.strip .it:last-child { border-right: none; }
.strip .ico { flex: 0 0 46px; height: 46px; border-radius: 50%; background: @@ico@@; display: flex; align-items: center; justify-content: center; font-size: 21px; }
.strip .st { color: @@text@@; font-size: 12px; font-weight: 800; letter-spacing: .4px; text-transform: uppercase; }
.strip .sv { color: @@text@@; font-size: 22px; font-weight: 800; line-height: 1.2; }
.strip .sn { color: @@sub@@; font-size: 12px; }
.foot { color: #dbe7fb; font-size: 12.5px; text-align: center; margin-top: 4px; line-height: 1.6; }
.foot b { color: #ffffff; }
</style>
"""
for k, v in C.items():
    if isinstance(v, str):
        CSS = CSS.replace(f"@@{k}@@", v)
st.markdown(CSS, unsafe_allow_html=True)

header_ph.markdown(f"""
<div class="banner">
  <div class="t">Credit Card Default Risk Dashboard</div>
  <div class="s">Repayment behavior of 30,000 credit card customers · Apr – Sep 2005</div>
  <div class="pill">✦ Developed by Eng | Habiba Ahmed</div>
</div>""", unsafe_allow_html=True)

# ======================= FILTERING =======================
f = data[data["Gender"].isin(gender) & data["Education_Level"].isin(edu) & data["Marital_Status"].isin(marital)
         & data["Age"].between(*age) & data["Credit_Limit"].between(*limit)]
if f.empty:
    st.warning("No customers match the selected filters.")
    st.stop()

rate = f["Default_Next_Month"].mean()
H = 300  # height of every chart card


def show(fig):
    """Render a Plotly chart full-width (works on old and new Streamlit versions)."""
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


def style_fig(fig, height=H, title=None):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=48 if title else 12, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=C["text"], size=12),
        title=dict(text=f"<b>{title.upper()}</b>" if title else None, font=dict(size=13, color=C["text"]),
                   x=0.5, xanchor="center"),
        xaxis=dict(gridcolor=C["grid"], zeroline=False, tickfont=dict(color=C["sub"])),
        yaxis=dict(gridcolor=C["grid"], zeroline=False, tickfont=dict(color=C["sub"])),
    )
    return fig


def rate_bar(df, col, title, highlight=None, order=None, height=H, horizontal=False):
    g = df.groupby(col, observed=True)["Default_Next_Month"].agg(rate="mean", n="size").reset_index()
    if order:
        g[col] = pd.Categorical(g[col], order, ordered=True)
        g = g.sort_values(col)
    g["rate"] = g["rate"] * 100
    colors = [C["accent"] if highlight and x == highlight else C["bar"] for x in g[col]]
    txt = g["rate"].round(1).astype(str) + "%"
    if horizontal:
        g, colors, txt = g.iloc[::-1], colors[::-1], txt.iloc[::-1]
        fig = go.Figure(go.Bar(y=g[col].astype(str), x=g["rate"], orientation="h", text=txt, textposition="outside",
                               marker_color=colors, marker_line_width=0))
        fig.update_layout(xaxis_range=[0, min(100, g["rate"].max() + 16)], yaxis_title="", xaxis_title="")
    else:
        fig = go.Figure(go.Bar(x=g[col].astype(str), y=g["rate"], text=txt, textposition="outside",
                               marker_color=colors, marker_line_width=0))
        fig.update_layout(yaxis_range=[0, min(100, g["rate"].max() + 14)], xaxis_title="", yaxis_title="")
    fig.update_traces(textfont_color=C["text"], cliponaxis=False)
    fig.update_layout(showlegend=False)
    return style_fig(fig, height, title)


# ======================= ROW 1: KPI CARDS =======================
never_late = (f["Months_Delayed"] == 0).mean()
k1, k2, k3, k4 = st.columns(4)


def kpi(col, icon, title, value, note):
    col.markdown(f"""<div class="kpi"><div class="ico">{icon}</div><div>
      <div class="kt">{title}</div><div class="kv">{value}</div><div class="kn">{note}</div></div></div>""",
                 unsafe_allow_html=True)


kpi(k1, "👥", "Total customers", f"{len(f):,}", "in selected segment")
kpi(k2, "📉", "Default rate", f"{rate:.1%}", "portfolio avg 22.1%")
kpi(k3, "💳", "Avg credit limit", f"NT${f['Credit_Limit'].mean() / 1000:,.0f}K", "per customer")
kpi(k4, "📊", "Avg utilization", f"{f['Utilization'].mean():.0%}", "avg bill / credit limit")

# ======================= ROW 2: status bars | bill vs payment | education donut =======================
r1, r2, r3 = st.columns(3)
with r1:
    status_labels = {-2: "Revolving", -1: "Paid in full", 0: "Min payment", 1: "1 mo late", 2: "2 mo late",
                     3: "3 mo late", 4: "4+ mo late"}
    sep = f.copy()
    sep["status_lbl"] = sep["Repayment_Status_Sep"].clip(-2, 4).map(status_labels)
    fig = rate_bar(sep, "status_lbl", "Default rate by Sept repayment status", highlight="2 mo late",
                   order=list(status_labels.values()))
    fig.update_xaxes(tickangle=-30)
    show(fig)

with r2:
    fig_t = go.Figure()
    fig_t.add_trace(go.Scatter(x=MONTHS, y=[f[f"Bill_Amount_{m}"].mean() for m in MONTHS], name="Average bill",
                               mode="lines+markers", line=dict(color=C["bar"], width=3)))
    fig_t.add_trace(go.Scatter(x=MONTHS, y=[f[f"Payment_Amount_{m}"].mean() for m in MONTHS], name="Average payment",
                               mode="lines+markers", line=dict(color=C["accent"], width=3)))
    fig_t.update_layout(legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center", font=dict(color=C["sub"])))
    show(style_fig(fig_t, H, "Average monthly bill vs payment (NT$)"))

with r3:
    ge = f.groupby("Education_Level")["Default_Next_Month"].agg(n="size", rate="mean").reset_index()
    labels = [f"{a}  {b / len(f):.1%}" for a, b in zip(ge["Education_Level"], ge["n"])]
    fig_e = go.Figure(go.Pie(labels=labels, values=ge["n"], hole=.58, sort=False, textinfo="none",
                             marker=dict(colors=C["shades"][:len(ge)], line=dict(color=C["card"], width=2))))
    fig_e.add_annotation(text=f"<b>{ge['rate'].max():.1%}</b><br><span style='font-size:11px'>highest risk</span>",
                         showarrow=False, font=dict(size=16, color=C["text"]), x=0.2, y=0.5, xref="paper", yref="paper")
    fig_e.update_layout(showlegend=True, legend=dict(orientation="v", x=1.0, y=0.5, xanchor="right",
                                                     font=dict(color=C["text"], size=12)),
                        margin=dict(r=0))
    fig_e.update_traces(domain=dict(x=[0, 0.5], y=[0.04, 0.96]))
    show(style_fig(fig_e, H, "Customers by education"))

# ======================= ROW 3: months delayed | utilization | credit-limit table =======================
b1, b2, b3 = st.columns(3)
with b1:
    fm = f.copy()
    fm["Months delayed"] = fm["Months_Delayed"].astype(str) + " of 6"
    show(rate_bar(fm, "Months delayed", "Default rate by months delayed", horizontal=True))

with b2:
    ub_labels = ["<=0", "0-25%", "25-50%", "50-75%", "75-100%", ">100%"]
    fu = f.assign(ub=pd.cut(f["Utilization"], [-10, 0, .25, .5, .75, 1, 100], labels=ub_labels).astype(str))
    show(rate_bar(fu, "ub", "Default rate by credit utilization", order=ub_labels))

with b3:
    lq = pd.qcut(f["Credit_Limit"], 5, duplicates="drop")
    lq = lq.cat.rename_categories([f"{int(i.left / 1000)}K - {int(i.right / 1000)}K" for i in lq.cat.categories])
    gl = f.assign(lq=lq).groupby("lq", observed=True)["Default_Next_Month"].agg(rate="mean", n="size").reset_index()
    lo, hi = gl["rate"].min(), gl["rate"].max()
    rows = ""
    for _, r in gl.iterrows():
        a = 0.25 + 0.75 * ((r["rate"] - lo) / (hi - lo) if hi > lo else 0.5)
        fg = "#ffffff" if a > 0.55 else C["text"]
        rows += (f"<tr><td>{r['lq']}</td><td style='background:rgba({C['tc']},{a:.2f}); color:{fg};'><b>{r['rate']:.1%}</b></td>"
                 f"<td>{r['n']:,}</td></tr>")
    st.markdown(f"""<div class="dash-card" style="height:{H + 18}px;">
      <div class="card-title">Default rate by credit limit (quintiles)</div>
      <table class="tbl"><tr><th>Credit limit (NT$)</th><th>Default rate</th><th>Customers</th></tr>{rows}</table></div>""",
                unsafe_allow_html=True)

# ======================= ROW 4: risk segments | age | gender | behavior radar =======================
d1, d2, d3, d4 = st.columns(4)
with d1:
    seg = (f.assign(Segment=pd.cut(f["Months_Delayed"], [-1, 0, 1, 6], labels=["Never late", "Late once", "Late 2+ times"]))
           .groupby("Segment", observed=True)["Default_Next_Month"].agg(Customers="size", Rate="mean").reset_index())
    bars = ""
    for _, row in seg.iterrows():
        share = row["Customers"] / len(f)
        bars += f"""<div style="margin-top:16px;">
          <div style="display:flex; justify-content:space-between; font-size:13px;">
            <span style="color:{C['text']}; font-weight:700;">{row['Segment']}</span>
            <span style="color:{C['sub']};">{row['Customers']:,} · <b style="color:{C['text']};">{row['Rate']:.0%}</b></span></div>
          <div style="background:{C['track']}; border-radius:8px; height:10px; margin-top:5px;">
            <div style="background:{C['bar']}; width:{share * 100:.0f}%; height:10px; border-radius:8px;"></div></div></div>"""
    st.markdown(f"""<div class="dash-card" style="height:{H + 18}px;"><div class="card-title">Risk segments</div>{bars}
      <div style="color:{C['sub']}; font-size:11.5px; margin-top:18px;">Bar = share of customers · % = default rate</div></div>""",
                unsafe_allow_html=True)

with d2:
    age_band = pd.cut(f["Age"], [20, 30, 40, 50, 60, 80], labels=["21-30", "31-40", "41-50", "51-60", "60+"])
    ga = f.assign(ab=age_band).groupby("ab", observed=True)["Default_Next_Month"].mean().reindex(age_band.cat.categories) * 100
    fig_a = go.Figure(go.Scatter(x=ga.index.astype(str), y=ga.values, mode="lines+markers+text",
                                 text=[f"{v:.1f}%" if pd.notna(v) else "" for v in ga.values], textposition="top center",
                                 line=dict(color=C["bar"], width=3), marker=dict(size=9, color=C["accent"])))
    fig_a.update_traces(textfont_color=C["text"])
    fig_a.update_layout(yaxis_range=[0, min(100, ga.max() + 16)])
    show(style_fig(fig_a, H, "Default rate by age group"))

with d3:
    show(rate_bar(f, "Gender", "Default rate by gender", horizontal=True))

with d4:
    axes = ["Months delayed", "Max delay", "Utilization", "Payment ratio", "Zero-pay months"]
    cols_map = ["Months_Delayed", "Max_Delay", "Utilization", "Payment_Ratio", "Zero_Payment_Months"]
    prof = f.groupby("Default_Next_Month")[cols_map].mean()
    scaled = (prof / f[cols_map].max()).fillna(0)
    fig_r = go.Figure()
    for val, name, col in [(0, "No default", C["accent"]), (1, "Default", C["bar"])]:
        if val in scaled.index:
            vals = scaled.loc[val].tolist()
            fig_r.add_trace(go.Scatterpolar(r=vals + vals[:1], theta=axes + axes[:1], name=name,
                                            line=dict(color=col, width=2.5), fill="toself", opacity=0.6))
    fig_r.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center", font=dict(color=C["sub"])),
                        polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=False, gridcolor=C["grid"]),
                                   angularaxis=dict(gridcolor=C["grid"], tickfont=dict(color=C["sub"], size=10))))
    show(style_fig(fig_r, H, "Behavior profile"))

# ======================= BOTTOM STRIP (like the reference dashboard) =======================
dflt = f[f["Default_Next_Month"] == 1]
late_share_of_defaults = (dflt["Months_Delayed"] > 0).mean() if len(dflt) else 0
rate_never = f.loc[f["Months_Delayed"] == 0, "Default_Next_Month"].mean()
items = [
    ("✅", "Never late", f"{never_late:.0%}", f"default rate {rate_never:.1%}" if pd.notna(rate_never) else "no customers"),
    ("⏰", "Late at least once", f"{1 - never_late:.0%}", "of selected customers"),
    ("⚠️", "Defaults from late customers", f"{late_share_of_defaults:.0%}", "of all defaults"),
    ("💵", "Avg payment ratio", f"{f['Payment_Ratio'].mean():.0%}", "paid / billed"),
    ("📅", "Avg months delayed", f"{f['Months_Delayed'].mean():.1f} of 6", "Apr – Sep 2005"),
]
st.markdown('<div class="strip">' + "".join(
    f'<div class="it"><div class="ico">{i}</div><div><div class="st">{t}</div><div class="sv">{v}</div><div class="sn">{n}</div></div></div>'
    for i, t, v, n in items) + "</div>", unsafe_allow_html=True)

cur = f.loc[f["Repayment_Status_Sep"] <= 0, "Default_Next_Month"]
l2 = f.loc[f["Repayment_Status_Sep"] == 2, "Default_Next_Month"]
insight = ""
if len(cur) >= 30 and len(l2) >= 30:
    insight = (f"A customer <b>2 months late</b> defaults at <b>{l2.mean():.0%}</b> vs <b>{cur.mean():.0%}</b> for a current customer. ")
st.markdown(f"<div class='foot'>{insight}Data: Default of Credit Card Clients · UCI Machine Learning Repository · "
            f"Descriptive analysis only</div>", unsafe_allow_html=True)
