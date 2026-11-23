import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Credit Card Default Risk Dashboard", layout="wide")

DATA_PATH = "credit _ Data.xls"  # the dataset file in this repo

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
    df["Avg_Bill"] = df[BILL].mean(axis=1)
    df["Avg_Payment"] = df[PAY].mean(axis=1)
    df["Utilization"] = df["Avg_Bill"] / df["Credit_Limit"]
    df["Payment_Ratio"] = (df[PAY].sum(axis=1) / bill_total.where(bill_total > 0)).fillna(1).clip(0, 1)

    df["Gender"] = df["Gender"].map({1: "Male", 2: "Female"})
    df["Education_Level"] = df["Education_Level"].map({1: "Graduate school", 2: "University", 3: "High school", 4: "Others"})
    df["Marital_Status"] = df["Marital_Status"].map({1: "Married", 2: "Single", 3: "Others"})
    return df

data = load_data()

st.sidebar.header("Filters")
gender = st.sidebar.multiselect("Gender", sorted(data["Gender"].dropna().unique()), default=sorted(data["Gender"].dropna().unique()))
edu = st.sidebar.multiselect("Education", list(data["Education_Level"].dropna().unique()), default=list(data["Education_Level"].dropna().unique()))
marital = st.sidebar.multiselect("Marital status", list(data["Marital_Status"].dropna().unique()), default=list(data["Marital_Status"].dropna().unique()))
age = st.sidebar.slider("Age range", int(data["Age"].min()), int(data["Age"].max()), (int(data["Age"].min()), int(data["Age"].max())))
limit = st.sidebar.slider("Credit limit (NT$)", int(data["Credit_Limit"].min()), int(data["Credit_Limit"].max()), (int(data["Credit_Limit"].min()), int(data["Credit_Limit"].max())), step=10000)

f = data[data["Gender"].isin(gender) & data["Education_Level"].isin(edu) & data["Marital_Status"].isin(marital)
         & data["Age"].between(*age) & data["Credit_Limit"].between(*limit)]

st.title("Credit Card Default Risk Dashboard")
st.caption("Exploratory analysis of 30,000 credit card customers (Apr-Sep 2005) - what predicts next month's default?")

if f.empty:
    st.warning("No customers match the selected filters.")
    st.stop()

default_rate = f["Default_Next_Month"].mean()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Customers", f"{len(f):,}")
c2.metric("Default rate", f"{default_rate:.1%}")
c3.metric("Avg credit limit", f"NT${f['Credit_Limit'].mean():,.0f}")
c4.metric("Avg utilization", f"{f['Utilization'].mean():.1%}")

def rate_bar(df, col, title, xlabel, color="#e76f51"):
    g = df.groupby(col)["Default_Next_Month"].agg(rate="mean", n="size").reset_index()
    g["rate"] = g["rate"] * 100
    fig = px.bar(g, x=col, y="rate", text=g["rate"].round(1).astype(str) + "%",
                 title=title, labels={col: xlabel, "rate": "Default rate (%)"}, color_discrete_sequence=[color])
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_range=[0, max(75, g["rate"].max() + 10)], showlegend=False)
    return fig

# 1. Headline: default rate by latest repayment status
sep = f.copy()
sep["Sep status"] = sep["Repayment_Status_Sep"].clip(-2, 9)
status_labels = {-2: "Paid (revolving)", -1: "Paid in full", 0: "Paid minimum", 1: "1 month late", 2: "2 months late",
                 3: "3 months late", 4: "4 months late", 5: "5 months late", 6: "6 months late", 7: "7 months late",
                 8: "8 months late", 9: "9+ months late"}
sep["Sep status"] = sep["Sep status"].map(status_labels)
order = list(status_labels.values())
g = sep.groupby("Sep status")["Default_Next_Month"].mean().reindex(order).dropna() * 100
fig1 = px.bar(x=g.index, y=g.values, text=[f"{v:.1f}%" for v in g.values],
              title="Default rate by repayment status (September)", color_discrete_sequence=["#e76f51"],
              labels={"x": "Latest repayment status", "y": "Default rate (%)"})
fig1.update_traces(textposition="outside")
fig1.update_layout(yaxis_range=[0, max(75, g.max() + 10)])

# 2. Default rate by number of delayed months
f2 = f.copy()
f2["Months delayed"] = f2["Months_Delayed"].astype(str) + " of 6"
fig2 = rate_bar(f2.assign(md=f2["Months_Delayed"]), "md", "Default rate by months delayed in the last 6 months", "Months delayed", "#2a9d8f")

col_left, col_right = st.columns(2)
col_left.plotly_chart(fig1, use_container_width=True)
col_right.plotly_chart(fig2, use_container_width=True)

# 3. Utilization band
util_band = pd.cut(f["Utilization"], [-10, 0, .25, .5, .75, 1, 100],
                   labels=["<=0", "0-25%", "25-50%", "50-75%", "75-100%", ">100%"])
fig3 = rate_bar(f.assign(ub=util_band), "ub", "Default rate by credit utilization (avg bill / limit)", "Utilization band")

# 4. Credit limit quintile
lim_q = pd.qcut(f["Credit_Limit"], 5, duplicates="drop")
lim_q = lim_q.cat.rename_categories([f"{int(i.left/1000)}K-{int(i.right/1000)}K" for i in lim_q.cat.categories])
fig4 = rate_bar(f.assign(lq=lim_q), "lq", "Default rate by credit-limit quintile", "Credit limit (NT$)", "#264653")

col_left2, col_right2 = st.columns(2)
col_left2.plotly_chart(fig3, use_container_width=True)
col_right2.plotly_chart(fig4, use_container_width=True)

# 5. Demographics (weak but worth showing)
fig5 = rate_bar(f, "Education_Level", "Default rate by education", "Education", "#6d6875")
fig6 = rate_bar(f, "Gender", "Default rate by gender", "Gender", "#b5838d")

col_left3, col_right3 = st.columns(2)
col_left3.plotly_chart(fig5, use_container_width=True)
col_right3.plotly_chart(fig6, use_container_width=True)

# 6. Monthly bill vs payment trend
trend = pd.DataFrame({
    "Month": MONTHS,
    "Average bill": [f.loc[f.index, f"Bill_Amount_{m}"].mean() for m in MONTHS],
    "Average payment": [f.loc[f.index, f"Payment_Amount_{m}"].mean() for m in MONTHS],
})
fig7 = px.line(trend, x="Month", y=["Average bill", "Average payment"], markers=True,
               title="Average monthly bill vs payment", labels={"value": "NT$", "variable": ""})
st.plotly_chart(fig7, use_container_width=True)

# 7. High-risk segment table
st.subheader("Risk segments")
seg = (f.assign(Segment=pd.cut(f["Months_Delayed"], [-1, 0, 1, 6], labels=["Never late", "Late once", "Late 2+ times"]))
        .groupby("Segment", observed=True)["Default_Next_Month"].agg(Customers="size", Default_rate=lambda s: f"{s.mean():.1%}"))
st.table(seg)

st.caption("Data: Default of Credit Card Clients, UCI Machine Learning Repository. Descriptive analysis only - no predictive model.")
