FROM python:3.10-slim-bullseye


ENV PYTHONUNBUFFERED=1
ENV PORT=8080

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libtool \
    make \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app


COPY app.py .
COPY chatgpt_api_service.py .
COPY diff_file_parser.py .
COPY PRoofread_env.py .
COPY requirements.txt .
COPY tree_sitter_setup_for_java.py .

RUN git clone https://github.com/tree-sitter/tree-sitter-java.git

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p build && python tree_sitter_setup_for_java.py

RUN mkdir -p final_comments \
             files/parsing_diff \
             files/relevant_data_from_ast_ \
             chatgpt_results

EXPOSE 8080

CMD ["python", "app.py"]
