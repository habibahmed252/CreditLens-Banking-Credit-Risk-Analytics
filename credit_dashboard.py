import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Credit Card Default Risk Dashboard", page_icon="💳", layout="wide")

DATA_PATH = "credit _ Data.xls"

MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep"]
STATUS = [f"Repayment_Status_{m}" for m in MONTHS]
BILL = [f"Bill_Amount_{m}" for m in MONTHS]
PAY = [f"Payment_Amount_{m}" for m in MONTHS]

@st.cache_data
def load_data():
    df = pd.read_excel(DATA_PATH, header=1)
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
    df["Avg_Delay"] = late.mean(axis=1)
    df["Zero_Payment_Months"] = (df[PAY] == 0).sum(axis=1)
    df["Avg_Bill"] = df[BILL].mean(axis=1)
    df["Avg_Payment"] = df[PAY].mean(axis=1)
    df["Utilization"] = df["Avg_Bill"] / df["Credit_Limit"]
    df["Payment_Ratio"] = (df[PAY].sum(axis=1) / bill_total.where(bill_total > 0)).fillna(1).clip(0, 1)

    df["Gender"] = df["Gender"].map({1: "Male", 2: "Female"})
    df["Education_Level"] = df["Education_Level"].map({1: "Graduate school", 2: "University", 3: "High school", 4: "Others"})
    df["Marital_Status"] = df["Marital_Status"].map({1: "Married", 2: "Single", 3: "Others"})
    return df

data = load_data()

# ---------------- Theme ----------------
with st.sidebar:
    st.markdown("### Appearance")
    dark = st.toggle("Dark mode", value=True)
    st.divider()
    st.markdown("### Filters")
    gender = st.multiselect("Gender", sorted(data["Gender"].dropna().unique()), default=sorted(data["Gender"].dropna().unique()))
    edu = st.multiselect("Education", list(data["Education_Level"].dropna().unique()), default=list(data["Education_Level"].dropna().unique()))
    marital = st.multiselect("Marital status", list(data["Marital_Status"].dropna().unique()), default=list(data["Marital_Status"].dropna().unique()))
    age = st.slider("Age range", int(data["Age"].min()), int(data["Age"].max()), (int(data["Age"].min()), int(data["Age"].max())))
    limit = st.slider("Credit limit (NT$)", int(data["Credit_Limit"].min()), int(data["Credit_Limit"].max()),
                      (int(data["Credit_Limit"].min()), int(data["Credit_Limit"].max())), step=10000)

if dark:
    C = dict(bg="#0b1626", card="#12233b", card2="#16294a", text="#e8f0f8", sub="#8fa8c4",
             grid="#1f3a5f", teal="#2dd4bf", cyan="#22d3ee", accent="#38bdf8", navy="#2563eb", track="#1b3153")
else:
    C = dict(bg="#eef3f9", card="#ffffff", card2="#f4f8fd", text="#12233b", sub="#5b7290",
             grid="#d9e4f0", teal="#0d9488", cyan="#0891b2", accent="#0284c7", navy="#1e40af", track="#dce8f5")

st.markdown(f"""
<style>
.stApp {{ background: {C['bg']}; }}
[data-testid="stSidebar"] {{ background: {C['card']}; }}
[data-testid="stSidebar"] * {{ color: {C['text']} !important; }}
h1, h2, h3, p, label, .stMarkdown, [data-testid="stCaptionContainer"] {{ color: {C['text']} !important; }}
.header-pill {{
    background: linear-gradient(145deg, {C['card']}, {C['card2']});
    border: 1px solid {C['grid']};
    border-radius: 18px;
    padding: 18px 26px;
    margin-bottom: 4px;
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;
}}
.dash-card {{
    background: linear-gradient(145deg, {C['card']}, {C['card2']});
    border: 1px solid {C['grid']};
    border-radius: 18px;
    padding: 14px 12px 6px 12px;
    box-shadow: 0 4px 18px rgba(0,0,0,0.14);
    margin-bottom: 6px;
}}
.kpi-title {{ color: {C['sub']}; font-size: 12.5px; font-weight: 600; letter-spacing: .4px; text-transform: uppercase; }}
.kpi-value {{ color: {C['text']}; font-size: 32px; font-weight: 800; line-height: 1.15; margin: 4px 0; }}
.kpi-note {{ color: {C['sub']}; font-size: 12.5px; }}
.section-title {{ color: {C['text']}; font-size: 16px; font-weight: 700; margin: 2px 0 2px 4px; }}
.legend-row {{ display:flex; justify-content:space-between; font-size:13px; padding:5px 4px; border-bottom:1px solid {C['grid']}; }}
</style>
""", unsafe_allow_html=True)

f = data[data["Gender"].isin(gender) & data["Education_Level"].isin(edu) & data["Marital_Status"].isin(marital)
         & data["Age"].between(*age) & data["Credit_Limit"].between(*limit)]

st.markdown(f"""
<div class="header-pill">
  <div>
    <div style="font-size:24px; font-weight:800; color:{C['text']};">💳 Credit Card Default Risk</div>
    <div style="color:{C['sub']}; font-size:13.5px; margin-top:3px;">Exploratory analysis of 30,000 credit card customers · Apr - Sep 2005</div>
  </div>
  <div style="color:{C['sub']}; font-size:13px; text-align:right;">Repayment Behavior Dashboard<br><b style="color:{C['teal']};">EDA · Python · Pandas</b></div>
</div>
""", unsafe_allow_html=True)

if f.empty:
    st.warning("No customers match the selected filters.")
    st.stop()

rate = f["Default_Next_Month"].mean()

def style_fig(fig, height=260, title=None):
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=40 if title else 12, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=C['text'], size=12),
        title=dict(text=title, font=dict(size=14, color=C['text']), x=0.03) if title else None,
        xaxis=dict(gridcolor=C['grid'], zeroline=False),
        yaxis=dict(gridcolor=C['grid'], zeroline=False),
    )
    return fig

def rate_bar(df, col, title, highlight=None, order=None, height=260):
    g = df.groupby(col)["Default_Next_Month"].agg(rate="mean", n="size").reset_index()
    if order:
        g[col] = pd.Categorical(g[col], order, ordered=True)
        g = g.sort_values(col)
    g["rate"] = g["rate"] * 100
    colors = [C['accent'] if highlight and x == highlight else C['navy'] for x in g[col]]
    fig = go.Figure(go.Bar(x=g[col].astype(str), y=g["rate"], text=g["rate"].round(1).astype(str) + "%",
                           textposition="outside", marker_color=colors, marker_line_width=0))
    fig.update_traces(textfont_color=C['text'])
    fig.update_layout(yaxis_range=[0, min(100, g["rate"].max() + 14)], showlegend=False,
                      xaxis_title="", yaxis_title="Default rate (%)")
    return style_fig(fig, height, title)

# ============ ROW 1: [big number + sparkline | status bar | radar] ============
left, center, right = st.columns([1.05, 2.1, 1.2])

with left:
    st.markdown('<div class="dash-card" style="padding:16px 18px 8px 18px;">', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-title">Default rate</div>'
                f'<div class="kpi-value">{rate:.1%}</div>'
                f'<div class="kpi-note">{len(f):,} customers · portfolio avg 22.1%</div>', unsafe_allow_html=True)
    spark = f[[f"Repayment_Status_{m}" for m in MONTHS]].clip(lower=0).mean()
    fig_s = go.Figure(go.Scatter(x=MONTHS, y=spark.values, mode="lines", line=dict(color=C['teal'], width=2.5),
                                 fill="tozeroy", fillcolor="rgba(45,212,191,0.15)" if dark else "rgba(13,148,136,0.12)"))
    fig_s.update_layout(yaxis=dict(visible=False), xaxis=dict(gridcolor="rgba(0,0,0,0)", color=C['sub']))
    st.plotly_chart(style_fig(fig_s, 110, "Avg months of delay trend"), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="dash-card" style="padding:16px 18px;">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Risk segments</div>', unsafe_allow_html=True)
    seg = (f.assign(Segment=pd.cut(f["Months_Delayed"], [-1, 0, 1, 6], labels=["Never late", "Late once", "Late 2+ times"]))
            .groupby("Segment", observed=True)["Default_Next_Month"].agg(Customers="size", Rate="mean").reset_index())
    for _, row in seg.iterrows():
        share = row["Customers"] / len(f)
        color = C['teal'] if row["Rate"] < 0.15 else (C['accent'] if row["Rate"] < 0.35 else C['navy'])
        st.markdown(f"""
        <div style="margin-top:11px;">
          <div style="display:flex; justify-content:space-between; font-size:12.5px;">
            <span style="color:{C['text']}; font-weight:600;">{row['Segment']}</span>
            <span style="color:{C['sub']};">{row['Customers']:,} · <b style="color:{color};">{row['Rate']:.0%}</b></span>
          </div>
          <div style="background:{C['track']}; border-radius:8px; height:8px; margin-top:4px;">
            <div style="background:{color}; width:{share*100:.0f}%; height:8px; border-radius:8px;"></div>
          </div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with center:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    status_labels = {-2: "Revolving", -1: "Paid in full", 0: "Min payment", 1: "1 mo late", 2: "2 mo late",
                     3: "3 mo late", 4: "4 mo late", 5: "5 mo late", 6: "6 mo late", 7: "7 mo late", 8: "8 mo late", 9: "9+ mo late"}
    sep = f.copy()
    sep["status_lbl"] = sep["Repayment_Status_Sep"].clip(-2, 9).map(status_labels)
    st.plotly_chart(rate_bar(sep, "status_lbl", "Default rate by latest repayment status (September)",
                             highlight="2 mo late", order=list(status_labels.values()), height=430),
                    use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    axes = ["Months delayed", "Max delay", "Utilization", "Payment ratio", "Zero-pay months"]
    cols_map = ["Months_Delayed", "Max_Delay", "Utilization", "Payment_Ratio", "Zero_Payment_Months"]
    prof = f.groupby("Default_Next_Month")[cols_map].mean()
    scaled = (prof / f[cols_map].max()).fillna(0)
    fig_r = go.Figure()
    for val, name, col in [(0, "No default", C['teal']), (1, "Default", C['accent'])]:
        vals = scaled.loc[val].tolist()
        fig_r.add_trace(go.Scatterpolar(r=vals + vals[:1], theta=axes + axes[:1], name=name,
                                        line=dict(color=col, width=2.5), fill="toself", opacity=0.55))
    fig_r.update_layout(title="Behavior profile", showlegend=True,
                        legend=dict(orientation="h", y=-0.12, font=dict(color=C['sub'])),
                        polar=dict(bgcolor="rgba(0,0,0,0)",
                                   radialaxis=dict(visible=False, gridcolor=C['grid']),
                                   angularaxis=dict(gridcolor=C['grid'], tickfont=dict(color=C['sub'], size=11))))
    st.plotly_chart(style_fig(fig_r, 300), use_container_width=True)
    st.markdown(f"""<div style="color:{C['sub']}; font-size:12.5px; padding:0 6px 8px 6px; line-height:1.6;">
        A customer <b style="color:{C['accent']};">2 months late</b> defaults at <b style="color:{C['accent']};">69%</b>
        vs <b style="color:{C['teal']};">14%</b> for a current customer. 52% of defaulters were already late the month before.</div>""",
        unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============ ROW 2: [KPIs | line compare | donut + legend] ============
l2, c2, r2 = st.columns([1.05, 2.1, 1.2])

with l2:
    st.markdown('<div class="dash-card" style="padding:16px 18px;">', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-title">Avg credit limit</div>'
                f'<div class="kpi-value">NT${f["Credit_Limit"].mean()/1000:,.0f}K</div>'
                f'<div class="kpi-note">per customer</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-card" style="padding:16px 18px;">', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-title">Avg utilization</div>'
                f'<div class="kpi-value">{f["Utilization"].mean():.0%}</div>'
                f'<div class="kpi-note">avg bill / limit</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-card" style="padding:16px 18px;">', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-title">Never late</div>'
                f'<div class="kpi-value">{(f["Months_Delayed"] == 0).mean():.0%}</div>'
                f'<div class="kpi-note">only 11.7% of them default</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    trend = pd.DataFrame({"Month": MONTHS,
                          "Average bill": [f[f"Bill_Amount_{m}"].mean() for m in MONTHS],
                          "Average payment": [f[f"Payment_Amount_{m}"].mean() for m in MONTHS]})
    fig_t = go.Figure()
    fig_t.add_trace(go.Scatter(x=trend["Month"], y=trend["Average bill"], name="Average bill",
                               mode="lines+markers", line=dict(color=C['accent'], width=3), fill="tozeroy",
                               fillcolor="rgba(56,189,248,0.10)"))
    fig_t.add_trace(go.Scatter(x=trend["Month"], y=trend["Average payment"], name="Average payment",
                               mode="lines+markers", line=dict(color=C['teal'], width=3), fill="tozeroy",
                               fillcolor="rgba(45,212,191,0.10)"))
    fig_t.update_layout(yaxis_title="NT$", legend=dict(orientation="h", y=-0.16, font=dict(color=C['sub'])))
    st.plotly_chart(style_fig(fig_t, 300, "Average monthly bill vs payment"), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r2:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    fig_d = go.Figure(go.Pie(labels=["No default", "Default"], values=[1 - rate, rate], hole=.68,
                             marker_colors=[C['navy'], C['accent']], textinfo="none", sort=False))
    fig_d.add_annotation(text=f"<b>{rate:.1%}</b>", showarrow=False, font=dict(size=24, color=C['text']))
    fig_d.update_layout(showlegend=False)
    st.plotly_chart(style_fig(fig_d, 210, "Portfolio split"), use_container_width=True)
    st.markdown(f"""
    <div class="legend-row"><span style="color:{C['text']};"><b style="color:{C['accent']};">●</b> Default</span><span style="color:{C['sub']};">{f['Default_Next_Month'].sum():,}</span></div>
    <div class="legend-row" style="border-bottom:none;"><span style="color:{C['text']};"><b style="color:{C['navy']};">●</b> No default</span><span style="color:{C['sub']};">{len(f) - f['Default_Next_Month'].sum():,}</span></div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============ ROW 3: [utilization | limit quintile | months delayed] ============
b1, b2, b3 = st.columns(3)
with b1:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    util_band = pd.cut(f["Utilization"], [-10, 0, .25, .5, .75, 1, 100],
                       labels=["<=0", "0-25%", "25-50%", "50-75%", "75-100%", ">100%"])
    st.plotly_chart(rate_bar(f.assign(ub=util_band), "ub", "Default rate by utilization", highlight="75-100%"), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with b2:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    lim_q = pd.qcut(f["Credit_Limit"], 5, duplicates="drop")
    lim_q = lim_q.cat.rename_categories([f"{int(i.left/1000)}K-{int(i.right/1000)}K" for i in lim_q.cat.categories])
    st.plotly_chart(rate_bar(f.assign(lq=lim_q), "lq", "Default rate by credit limit"), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with b3:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    fb = f.copy()
    fb["Months delayed"] = fb["Months_Delayed"].astype(str) + " of 6"
    st.plotly_chart(rate_bar(fb, "Months delayed", "Default rate by months delayed"), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============ ROW 4: [education | gender | age] ============
d1, d2, d3 = st.columns(3)
with d1:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.plotly_chart(rate_bar(f, "Education_Level", "Default rate by education"), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with d2:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.plotly_chart(rate_bar(f, "Gender", "Default rate by gender"), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with d3:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    age_band = pd.cut(f["Age"], [20, 30, 40, 50, 60, 80], labels=["21-30", "31-40", "41-50", "51-60", "60+"])
    st.plotly_chart(rate_bar(f.assign(ab=age_band), "ab", "Default rate by age group"), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f"<div style='color:{C['sub']}; font-size:12px; text-align:center; margin-top:14px;'>Data: Default of Credit Card Clients · UCI Machine Learning Repository · Descriptive analysis only</div>", unsafe_allow_html=True)
