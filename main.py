from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import re

app = FastAPI()
df = pd.read_excel("BCG.xlsx")

df.columns= [re.sub(r"\s*\(.*?\)", "", col) for col in df.columns]


df['revenue growth %']=df.groupby(['Company'])['Total Revenue'].pct_change()*100
df['net income growth %']=df.groupby(['Company'])['Net Income'].pct_change()*100

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chat")
def financial_chatbot(
    company: str = Query(...),
    year: int = Query(...),
    query: str = Query(...)
):
    try:
        data = df[(df["Company"] == company) & (df["Fiscal Year"] == year)].iloc[0]
    except IndexError:
        return {"response": f"Sorry, no data found for {company} in {year}."}

    if query == "What is the total revenue?":
        return {"response": f"The total revenue for {company} in {year} was ${data['Total Revenue']:,} million."}

    elif query == "How has net income changed over the last year?":
        growth = data['net income growth %']
        if pd.isna(growth):
            return {"response": "Net income growth data is not available for this year."}
        direction = "increased" if growth > 0 else "decreased"
        return {"response": f"Net income has {direction} by {abs(growth):.2f}% compared to the previous year."}

    elif query == "What is the cash flow from operating activities?":
        return {"response": f"The cash flow from operating activities for {company} in {year} was ${data['Cash Flow']:,} million."}

    elif query == "What are the total assets and liabilities?":
        return {"response": f"In {year}, {company} had ${data['Total Assets']:,} million in assets and ${data['Total Liabilities']:,} million in liabilities."}

    else:
        return {"response": "Sorry, I can only answer predefined queries."}

@app.get("/chart-data")
def get_chart_data(company: str = Query(...), metric: str = Query(...)):
    if metric not in ["Total Revenue", "Net Income", "Total Assets", "Total Liabilities", "Cash Flow"]:
        return {"error": "Unsupported metric."}


    company_data = df[df["Company"] == company].sort_values("Fiscal Year")

    return {
        "years": company_data["Fiscal Year"].tolist(),
        "values": company_data[metric].tolist(),
        "label": metric
    }
