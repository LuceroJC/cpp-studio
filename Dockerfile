# Full image: runs CPPS, Streamlit app, and builds PDF reports.
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    # TeX for PDF reports (minimal but enough for a 1-page LaTeX report)
    texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# Create workspace
WORKDIR /app

# System locales (optional)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install project
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# If packaging as a library:
COPY . .
RUN pip install -e .

# Default command opens Streamlit; override in CI/CLI runs
EXPOSE 8501
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.headless=true", "--browser.gatherUsageStats=false"]
