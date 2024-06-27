FROM python:3.12

WORKDIR /
app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000
EXPOSE 3001

CMD ["python", "server/main.py"]
