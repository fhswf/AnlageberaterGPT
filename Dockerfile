FROM python:3.12.0-slim-bookworm

RUN apt-get update && apt-get install -y git

WORKDIR app/

ENV LANGCHAIN_TRACING_V2=true
ENV LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
ENV LANGCHAIN_API_KEY="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"
ENV LANGCHAIN_PROJECT="anlageberater_gpt"

COPY ./requirements.txt /app/requirements.txt
COPY ./investmentadvisor_be.py /app/investmentadvisor_be.py
COPY ./investmentadvisor_ui.py /app/investmentadvisor_ui.py
COPY ./produkteinstufung /app/produkteinstufung
COPY ./testdaten /app/testdaten
COPY ./chroma_langchain_db /app/chroma_langchain_db

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

EXPOSE 80

ENTRYPOINT ["streamlit", "run", "investmentadvisor_ui.py"]
CMD ["census_app.py"]