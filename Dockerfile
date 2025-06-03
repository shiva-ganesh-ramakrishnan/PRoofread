FROM python:3.10-slim-bullseye

# Environment setup
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Install system dependencies for building tree-sitter grammars
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libtool \
    make \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY app.py .
COPY chatgpt_api_service.py .
COPY diff_file_parser.py .
COPY PRoofread_env.py .
COPY requirements.txt .
COPY tree_sitter_setup_for_java.py .

# Copy the Tree-sitter grammar repo
COPY tree-sitter-java/ tree-sitter-java/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Build the .so file inside Docker
RUN mkdir -p build && python tree_sitter_setup_for_java.py

# Create required runtime directories
RUN mkdir -p final_comments \
             files/parsing_diff \
             files/relevant_data_from_ast_ \
             chatgpt_results

# Expose the web port
EXPOSE 8080

# Start the app
CMD ["python", "app.py"]
