FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ffmpeg \
    libsndfile1 \
    unzip \
    libavcodec-extra \
    && rm -rf /var/lib/apt/lists/*

# Create models directory and download Vosk model
RUN mkdir -p /usr/local/share/vosk && \
    curl -L -o /usr/local/share/vosk/model.zip https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip && \
    cd /usr/local/share/vosk && unzip model.zip && \
    mv vosk-model-small-ru-0.22 model && \
    rm model.zip

# Copy project files
COPY pyproject.toml ./

# Install uv and dependencies
RUN pip install --no-cache-dir uv \
    && uv pip install --system -e . \
    && rm -rf ~/.cache/uv

# Copy the rest of the application
COPY . .

CMD ["python", "-m", "app.main"]