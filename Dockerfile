FROM python:3.12-slim

WORKDIR /app

COPY server/ .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 3001
EXPOSE 3000

# Run the application
CMD ["python", "main.py"]
