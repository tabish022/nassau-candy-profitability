import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

st.set_page_config(page_title="Nassau Candy - Profitability Dashboard", layout="wide")

DATA_FILE = Path(__file__).parent / "data" / "Nassau_Candy_Distributor.csv"

# division and factory for each product (from the project brief)
MAPPING = pd.DataFrame({
    "Product Name": [
        "Wonka Bar - Nutty Crunch Surprise", "Wonka Bar - Fudge Mallows", "Wonka Bar - Scrumdiddlyumptious",
        "Wonka Bar - Milk Chocolate", "Wonka Bar - Triple Dazzle Caramel",
        "Laffy Taffy", "SweeTARTS", "Nerds", "Fun Dip", "Fizzy Lifting Drinks",
        "Everlasting Gobstopper", "Hair Toffee", "Lickable Wallpaper", "Wonka Gum", "Kazookles"],
    "Division": [
        "Chocolate", "Chocolate", "Chocolate", "Chocolate", "Chocolate",
        "Sugar", "Sugar", "Sugar", "Sugar", "Other",
        "Sugar", "Sugar", "Other", "Other", "Other"],
    "Factory": [
        "Lot's O' Nuts", "Lot's O' Nuts", "Lot's O' Nuts", "Wicked Choccy's", "Wicked Choccy's",
        "Sugar Shack", "Sugar Shack", "Sugar Shack", "Sugar Shack", "Sugar Shack",
        "Secret Factory", "The Other Factory", "Secret Factory", "Secret Factory", "The Other Factory"],
})


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)

    # clean text columns and fix the product name with the spacing problem
    df["Product Name"] = df["Product Name"].str.strip()
    df["Product Name"] = df["Product Name"].replace(
        {"Wonka Bar -Scrumdiddlyumptious": "Wonka Bar - Scrumdiddlyumptious"})

    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%d-%m-%Y")

    # division and factory come from the mapping table
    df = df.drop(columns="Division").merge(MAPPING, on="Product Name", how="left")

    # remove invalid records
    bad = (df["Sales"] <= 0) | (df["Units"] <= 0) | (df["Cost"] <= 0) | \
          ((df["Sales"] - df["Cost"] - df["Gross Profit"]).abs() > 0.01)
    df = df[~bad].reset_index(drop=True)

    df["Row Margin %"] = df["Gross Profit"] / df["Sales"] * 100
    df["Month"] = df["Order Date"].dt.to_period("M").astype(str)
    return df


def make_product_table(d):
    p = d.groupby(["Product Name", "Division", "Factory"]).agg(
        Sales=("Sales", "sum"),
        Cost=("Cost", "sum"),
        Gross_Profit=("Gross Profit", "sum"),
        Units=("Units", "sum"),
        Orders=("Row ID", "count"),
    ).reset_index()
    p["Margin %"] = p["Gross_Profit"] / p["Sales"] * 100
    p["Profit per Unit"] = p["Gross_Profit"] / p["Units"]
    p["Cost per Unit"] = p["Cost"] / p["Units"]
    p["Revenue Contribution %"] = p["Sales"] / p["Sales"].sum() * 100
    p["Profit Contribution %"] = p["Gross_Profit"] / p["Gross_Profit"].sum() * 100
    return p


def add_flags(p, cutoff):
    median_sales = p["Sales"].median()
    median_cost_unit = p["Cost per Unit"].median()
    flags = []
    for _, r in p.iterrows():
        if r["Margin %"] >= cutoff:
            flags.append("OK")
        elif r["Sales"] < median_sales:
            flags.append("Discontinuation review")
        elif r["Cost per Unit"] > median_cost_unit:
            flags.append("Cost renegotiation")
        else:
            flags.append("Repricing")
    p["Risk Flag"] = flags
    return p


def pareto_table(p, col):
    t = p[["Product Name", col]].sort_values(col, ascending=False).reset_index(drop=True)
    t["Share %"] = t[col] / t[col].sum() * 100
    t["Cumulative %"] = t["Share %"].cumsum()
    return t


def pareto_chart(t, title, color):
    labels = t["Product Name"].str.replace("Wonka Bar - ", "", regex=False)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=labels, y=t["Share %"], name="Share %", marker_color=color), secondary_y=False)
    fig.add_trace(go.Scatter(x=labels, y=t["Cumulative %"], name="Cumulative %",
                             mode="lines+markers", line=dict(color="red")), secondary_y=True)
    fig.add_hline(y=80, line_dash="dash", line_color="black", secondary_y=True)
    fig.update_yaxes(title_text="Share of total %", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative %", range=[0, 105], tickvals=[0, 20, 40, 60, 80, 100], secondary_y=True)
    fig.update_xaxes(tickangle=-45)
    fig.update_layout(title=title, height=500, legend=dict(orientation="h", y=1.1), margin=dict(b=130))
    return fig


df = load_data()

# ---------------- sidebar filters ----------------
st.sidebar.title("Filters")

min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()
date_range = st.sidebar.date_input("Order date range", value=(min_date, max_date),
                                   min_value=min_date, max_value=max_date)

divisions = st.sidebar.multiselect("Division", sorted(df["Division"].unique()),
                                   default=sorted(df["Division"].unique()))

margin_cutoff = st.sidebar.slider("Margin threshold (%)", 0, 100, 55,
                                  help="Products with a gross margin below this value are flagged as margin risks.")

search = st.sidebar.text_input("Search product", placeholder="e.g. Kazookles")

# ---------------- apply filters ----------------
if len(date_range) != 2:
    st.info("Select both a start date and an end date in the sidebar.")
    st.stop()

start, end = date_range
d = df[(df["Order Date"].dt.date >= start) & (df["Order Date"].dt.date <= end)]
d = d[d["Division"].isin(divisions)]
if search.strip():
    d = d[d["Product Name"].str.contains(search.strip(), case=False, regex=False)]

st.title("Nassau Candy Distributor - Product Profitability Dashboard")
st.caption("Which products really make money, and which ones are a margin risk?")

if d.empty:
    st.warning("No data for the selected filters. Change the date range, division or search text.")
    st.stop()

product = make_product_table(d)
product = add_flags(product, margin_cutoff)

total_sales = d["Sales"].sum()
total_profit = d["Gross Profit"].sum()

# ---------------- KPI row ----------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Sales", f"{total_sales:,.0f}")
c2.metric("Gross Profit", f"{total_profit:,.0f}")
c3.metric("Gross Margin", f"{total_profit / total_sales * 100:.1f}%")
c4.metric("Units Sold", f"{d['Units'].sum():,}")
c5.metric("Products Below Threshold", int((product["Margin %"] < margin_cutoff).sum()))

tab1, tab2, tab3, tab4 = st.tabs([
    "Product Profitability", "Division Performance", "Cost vs Margin Diagnostics", "Profit Concentration"])

# ---------------- tab 1: product profitability ----------------
with tab1:
    st.subheader("Product margin leaderboard")
    rank_by = st.radio("Rank products by", ["Gross Margin %", "Gross Profit"], horizontal=True)
    sort_col = "Margin %" if rank_by == "Gross Margin %" else "Gross_Profit"
    board = product.sort_values(sort_col, ascending=False).reset_index(drop=True)
    board.index = board.index + 1

    show = board[["Product Name", "Division", "Sales", "Gross_Profit", "Margin %", "Profit per Unit",
                  "Revenue Contribution %", "Profit Contribution %"]].round(2)
    show = show.rename(columns={"Gross_Profit": "Gross Profit"})
    st.dataframe(show, width="stretch")

    left, right = st.columns(2)
    with left:
        fig = px.bar(board.sort_values("Margin %"), x="Margin %", y="Product Name", orientation="h",
                     color="Margin %", color_continuous_scale="RdYlGn", title="Gross margin % by product")
        fig.add_vline(x=margin_cutoff, line_dash="dash", line_color="red",
                      annotation_text="threshold")
        fig.update_layout(height=500)
        st.plotly_chart(fig, width="stretch")
    with right:
        fig = px.bar(board.sort_values("Profit Contribution %"), x="Profit Contribution %", y="Product Name",
                     orientation="h", title="Profit contribution % by product")
        fig.update_traces(marker_color="seagreen")
        fig.update_layout(height=500)
        st.plotly_chart(fig, width="stretch")

# ---------------- tab 2: division performance ----------------
with tab2:
    st.subheader("Division performance")
    division = d.groupby("Division").agg(
        Products=("Product Name", "nunique"),
        Sales=("Sales", "sum"),
        Gross_Profit=("Gross Profit", "sum"),
        Units=("Units", "sum"),
    ).reset_index()
    division["Margin %"] = division["Gross_Profit"] / division["Sales"] * 100
    division["Revenue Share %"] = division["Sales"] / total_sales * 100
    division["Profit Share %"] = division["Gross_Profit"] / total_profit * 100
    division["Profit - Revenue Share (pts)"] = division["Profit Share %"] - division["Revenue Share %"]
    st.dataframe(division.round(2).rename(columns={"Gross_Profit": "Gross Profit"}),
                 width="stretch", hide_index=True)

    left, right = st.columns(2)
    with left:
        long = division.melt(id_vars="Division", value_vars=["Sales", "Gross_Profit"],
                             var_name="Measure", value_name="Amount")
        long["Measure"] = long["Measure"].replace({"Gross_Profit": "Gross Profit"})
        fig = px.bar(long, x="Division", y="Amount", color="Measure", barmode="group",
                     title="Revenue vs profit by division")
        st.plotly_chart(fig, width="stretch")
    with right:
        long = division.melt(id_vars="Division", value_vars=["Revenue Share %", "Profit Share %"],
                             var_name="Measure", value_name="Share %")
        fig = px.bar(long, x="Division", y="Share %", color="Measure", barmode="group",
                     title="Revenue share vs profit share")
        st.plotly_chart(fig, width="stretch")

    fig = px.box(d, x="Division", y="Row Margin %", color="Division",
                 title="Order-level margin distribution by division")
    st.plotly_chart(fig, width="stretch")

    # simple reading of the table
    for _, r in division.iterrows():
        gap = r["Profit - Revenue Share (pts)"]
        if gap < -1:
            st.write(f"**{r['Division']}**: profit share is {abs(gap):.1f} points lower than its revenue share (structural margin issue).")
        elif gap > 1:
            st.write(f"**{r['Division']}**: profit share is {gap:.1f} points higher than its revenue share (strong efficiency).")

# ---------------- tab 3: cost vs margin ----------------
with tab3:
    st.subheader("Cost vs sales")
    fig = px.scatter(product, x="Sales", y="Cost", color="Margin %", hover_name="Product Name",
                     log_x=True, log_y=True, color_continuous_scale="RdYlGn",
                     title="Total cost vs total sales (hover to see the product)")
    low = min(product["Sales"].min(), product["Cost"].min())
    high = product["Sales"].max()
    fig.add_trace(go.Scatter(x=[low, high], y=[low, high], mode="lines", name="Cost = Sales",
                             line=dict(color="red", dash="dash")))
    fig.update_traces(marker=dict(size=14, line=dict(width=1, color="black")), selector=dict(mode="markers"))
    fig.update_layout(height=550)
    st.plotly_chart(fig, width="stretch")

    st.subheader("Margin risk flags")
    st.write(f"Products with a margin below **{margin_cutoff}%** are flagged. "
             "Low sales means below the median sales of the products shown.")
    flags = product[product["Risk Flag"] != "OK"].sort_values("Margin %")
    if flags.empty:
        st.success("No product is below the margin threshold.")
    else:
        st.dataframe(flags[["Product Name", "Division", "Sales", "Cost per Unit", "Profit per Unit",
                            "Margin %", "Risk Flag"]].round(2), width="stretch", hide_index=True)
        counts = flags["Risk Flag"].value_counts()
        for name, n in counts.items():
            st.write(f"- {name}: {n} product(s)")

    with st.expander("Margin volatility (std. dev. of monthly margin %)"):
        monthly = d.groupby(["Product Name", "Month"]).agg(Sales=("Sales", "sum"), Profit=("Gross Profit", "sum")).reset_index()
        monthly["Monthly Margin %"] = monthly["Profit"] / monthly["Sales"] * 100
        vol = monthly.groupby("Product Name")["Monthly Margin %"].agg(["mean", "std"]).round(2).reset_index()
        vol.columns = ["Product Name", "Avg Monthly Margin %", "Margin Volatility"]
        st.dataframe(vol, width="stretch", hide_index=True)
        st.caption("Each product has a fixed price and unit cost in this data, so volatility is 0. "
                   "Margin differences come from the product itself, not from changes over time.")

# ---------------- tab 4: pareto ----------------
with tab4:
    st.subheader("Profit concentration (Pareto)")
    rev_p = pareto_table(product, "Sales")
    prof_p = pareto_table(product, "Gross_Profit")
    n_total = len(product)
    n_rev = int((rev_p["Cumulative %"] < 80).sum()) + 1
    n_prof = int((prof_p["Cumulative %"] < 80).sum()) + 1

    m1, m2, m3 = st.columns(3)
    m1.metric("Products for 80% of revenue", f"{n_rev} of {n_total}")
    m2.metric("Products for 80% of profit", f"{n_prof} of {n_total}")
    m3.metric("Top 3 products' share of profit", f"{prof_p['Share %'].iloc[:3].sum():.1f}%")

    left, right = st.columns(2)
    with left:
        st.plotly_chart(pareto_chart(rev_p, "Revenue Pareto", "steelblue"), width="stretch")
    with right:
        st.plotly_chart(pareto_chart(prof_p, "Profit Pareto", "seagreen"), width="stretch")

    st.subheader("Dependency indicators")
    top1 = prof_p.iloc[0]
    st.write(f"- Largest profit product: **{top1['Product Name']}** ({top1['Share %']:.1f}% of profit)")
    top_div = d.groupby("Division")["Gross Profit"].sum().sort_values(ascending=False)
    st.write(f"- Largest profit division: **{top_div.index[0]}** ({top_div.iloc[0] / total_profit * 100:.1f}% of profit)")
    top3 = prof_p["Share %"].iloc[:3].sum()
    if n_total >= 4 and top3 > 50:
        st.warning(f"High dependency: the top 3 products give {top3:.1f}% of total gross profit.")
    elif n_total >= 4:
        st.success(f"Profit is fairly spread out: the top 3 products give {top3:.1f}% of gross profit.")
    else:
        st.info("Select more products or divisions to see the dependency indicator.")

    with st.expander("Pareto tables"):
        st.dataframe(rev_p.round(2), width="stretch", hide_index=True)
        st.dataframe(prof_p.round(2), width="stretch", hide_index=True)
