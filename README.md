# Nassau Candy Distributor - Product Profitability & Margin Performance

Which products really make money, and which ones only look successful? This project analyses 10,194 order lines (Jan 2024 - Dec 2025) of Nassau Candy Distributor to find the products and divisions that drive gross profit, and the products that are a margin risk.

## Main findings
- Total sales 141,784, gross profit 93,443, gross margin **65.9%**.
- Five Wonka chocolate bars give **95.1% of all gross profit**. The same 5 of 15 products reach 80% of revenue and 80% of profit, so the business depends heavily on one range.
- **Kazookles** has decent sales but only a **7.7% margin** (price 3.25, cost 3.00). Lickable Wallpaper (50%) and Wonka Gum (52%) also earn well below the chocolate bars.
- The "Other" division makes 6.9% of revenue but only 4.7% of profit.
- Every product has a fixed price and unit cost, so margin volatility is 0 and weak margins do not fix themselves.

## What is in this repository
| Path | What it is |
|---|---|
| `app.py` | Streamlit dashboard (4 modules, filters for date range, division, margin threshold and product search) |
| `notebooks/Nassau_Candy_Profitability_Analysis.ipynb` | Full analysis: cleaning, metrics, product and division analysis, Pareto, cost diagnostics, recommendations |
| `data/Nassau_Candy_Distributor.csv` | Source data |
| `reports/Research_Paper.pdf` | Research paper (EDA, insights, recommendations) |
| `reports/Executive_Summary.pdf` | One-page executive summary |
| `reports/figures/` | Charts used in the paper |
| `requirements.txt` | Python packages needed |

## Dashboard modules
1. **Product Profitability Overview** - margin leaderboard and profit contribution charts
2. **Division Performance** - revenue vs profit, revenue share vs profit share, margin distribution
3. **Cost vs Margin Diagnostics** - cost-sales scatter plot, margin risk flags (repricing / cost renegotiation / discontinuation review)
4. **Profit Concentration** - Pareto charts and dependency indicators

## Run it on your computer
```
pip install -r requirements.txt
streamlit run app.py
```
To run the notebook, open `notebooks/Nassau_Candy_Profitability_Analysis.ipynb` in Jupyter and run all cells (it needs pandas, numpy, matplotlib and seaborn).

## Tools
Python (pandas, numpy, matplotlib, seaborn), Plotly, Streamlit.

## Author
Tabish Afzal
