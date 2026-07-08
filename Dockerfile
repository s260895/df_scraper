FROM python:3.12-slim

WORKDIR /app

COPY requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt

COPY analysis/ analysis/
COPY data/ data/
COPY tests/ tests/
COPY market_dashboard.py .

EXPOSE 8501

CMD ["streamlit", "run", "market_dashboard.py", "--server.headless=true", "--server.address=0.0.0.0", "--server.port=8501"]
