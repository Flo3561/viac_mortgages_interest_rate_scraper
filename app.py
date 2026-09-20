import pandas as pd
import streamlit as st
from pathlib import Path

DATA_PATH = Path("data/rates.csv")

st.set_page_config(page_title="VIAC Hypothekenzinsen Analyse", layout="wide")

st.title("VIAC Hypothekenzinsen Analyse")
st.markdown(
    "Visualisierung der historischen VIAC-Hypothekensätze aus `data/rates.csv`."
)


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df["interestRate"] = pd.to_numeric(df["interestRate"], errors="coerce")
    return df.sort_values(["date", "product", "term"])


def get_sort_key(term: str) -> tuple:
    if term == "SARON":
        return (0, 0)
    try:
        years = int(term.split()[0])
        return (1, years)
    except Exception:
        return (2, term)


if not DATA_PATH.exists():
    st.error("Die Datendatei `data/rates.csv` wurde nicht gefunden. Bitte erst die Scrape-Daten erzeugen.")
    st.stop()

data = load_data(DATA_PATH)

product_options = sorted(data["product"].unique())
selected_products = st.sidebar.multiselect("Produkt wählen", product_options, default=product_options)

filtered_by_product = data[data["product"].isin(selected_products)]
term_options = sorted(filtered_by_product["term"].unique(), key=get_sort_key)
selected_terms = st.sidebar.multiselect("Laufzeit wählen", term_options, default=term_options)

min_date = data["date"].dt.date.min()
max_date = data["date"].dt.date.max()
selected_dates = st.sidebar.date_input("Zeitraum", [min_date, max_date], min_value=min_date, max_value=max_date)

if len(selected_dates) != 2:
    st.sidebar.error("Bitte einen Start- und Endtermin wählen.")
    st.stop()

start_date, end_date = selected_dates

filtered = filtered_by_product[
    (filtered_by_product["term"].isin(selected_terms))
    & (filtered_by_product["date"].dt.date >= start_date)
    & (filtered_by_product["date"].dt.date <= end_date)
]

st.sidebar.write("---")
st.sidebar.markdown("**Hinweis:** Die Daten werden aus `data/rates.csv` geladen.")

if filtered.empty:
    st.warning("Keine Daten für die gewählten Filter gefunden.")
    st.stop()

st.subheader("Zinssatzverlauf")
line_data = filtered.pivot_table(index="date", columns="term", values="interestRate")
st.line_chart(line_data)

st.subheader("Aktuelle Werte je Laufzeit")
latest = (
    filtered.sort_values("date")
    .groupby(["product", "term"], as_index=False)
    .last()
    .sort_values(
        ["product", "term"],
        key=lambda col: col.map(lambda v: get_sort_key(v) if col.name == "term" else v),
    )
)
st.dataframe(latest[["date", "product", "term", "interestRate"]].reset_index(drop=True))

st.subheader("Rohdaten")
st.dataframe(filtered.reset_index(drop=True))
