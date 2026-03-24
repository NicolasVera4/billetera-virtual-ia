from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from connection.database import get_db
from connection.models import Transaction, TransactionType
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np
from collections import defaultdict

router_ml = APIRouter()

def get_monthly_data(db: Session):
    transactions = db.query(Transaction).all()
    monthly = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for t in transactions:
        key = f"{t.transaction_date.year}-{t.transaction_date.month:02d}"
        if t.type == TransactionType.income:
            monthly[key]["income"] += float(t.amount)
        else:
            monthly[key]["expense"] += float(t.amount)
    return dict(sorted(monthly.items()))

@router_ml.get("/ml/forecast")
def spending_forecast(db: Session = Depends(get_db)):
    monthly = get_monthly_data(db)
    if len(monthly) < 3:
        return {"error": "Se necesitan al menos 3 meses de datos para poder predecir."}
    
    months = sorted(monthly.keys())
    expenses = [monthly[m]["expense"] for m in months]

    X = np.array(range(len(expenses))).reshape(-1,1)
    y = np.array(expenses)
    model = LinearRegression()
    model.fit(X, y)

    next_index = np.array([[len(expenses)]])
    prediction = max(0.0, float(model.predict(next_index)[0]))

    last = months[-1]
    year, month = int(last.split("-")[0]), int(last.split("-")[1])
    if month == 12:
        next_month = f"{year + 1}-01"
    else:
        next_month = f"{year}-{month + 1:02d}"
    
    history = [{"month": m, "expense": monthly[m]["expense"], "income": monthly[m]["income"]} for m in months]

    return {
        "history": history,
        "prediction": {"month": next_month, "predicted_expense": round(prediction, 2)},
        "r2_score": round(float(model.score(X, y)), 3)
    }

@router_ml.get("/ml/anomalies")
def detect_anomalies(db: Session = Depends(get_db)):
    monthly = get_monthly_data(db)

    if len(monthly) < 4:
        return {"error": "Se necesitan al menos 4 meses de datos"}
    
    months = sorted(monthly.keys())

    X = np.array([
        [monthly[m]["expense"], monthly[m]["income"]]
        for m in months
    ])

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(contamination="auto", random_state=42)
    labels = model.fit_predict(X_scaled)
    scores = model.decision_function(X_scaled)

    result = []
    for i, m in enumerate(months):
        result.append({
            "month": m,
            "expense": monthly[m]["expense"],
            "income": monthly[m]["income"],
            "is_anomaly": bool(labels[i] == -1),
            "anomaly_score": float(scores[i])
        })

    return {"months": result}