FROM python:3.12.0-slim-bookworm

RUN apt-get update && apt-get install -y git

COPY ./requirements.txt /app/requirements.txt
COPY ./investmentadvisor_be.py /app/investmentadvisor_be.py
COPY ./investmentadvisor_ui.py /app/investmentadvisor_ui.py
COPY ./produkteinstufung /app/produkteinstufung
COPY ./testdaten /app/testdaten
COPY ./chroma_langchain_db /app/chroma_langchain_db
COPY ./.env /app/.env

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

WORKDIR app/

ENTRYPOINT ["streamlit", "run", "investmentadvisor_ui.py", "--server.port=8501", "--server.address=0.0.0.0"]