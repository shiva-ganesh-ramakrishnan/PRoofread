FROM python:3.10-slim-bullseye


RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    curl \
    libtool \
    make \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY build/my-languages.so /build/my-languages.so

COPY app.py .

COPY chatgpt_api_service.py .

COPY diff_file_parser.py .

COPY PRoofread_env.py .

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080


RUN mkdir /app/final_comments

RUN mkdir /app/files
RUN mkdir /app/files/parsing_diff
RUN mkdir /app/files/relevant_data_from_ast_


RUN mkdir /app/chatgpt_results

CMD ["python", "app.py"]
