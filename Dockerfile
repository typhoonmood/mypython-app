FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY professional_finance_service.py .
EXPOSE 5000
CMD ["python", "professional_finance_service.py"]
