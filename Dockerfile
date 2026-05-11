FROM python:3.13-slim AS builder

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir grpcio-tools

RUN bash src/scripts/generate_protos.sh


FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY --from=builder /app/src .

CMD [ "python", "main.py" ]
