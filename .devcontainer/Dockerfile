# Use official Python base image optimized for AI workloads
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim-bullseye

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Basic system tools
    curl \
    wget \
    git \
    build-essential \
    pkg-config \
    cmake \
    \
    # Audio/Video processing
    ffmpeg \
    libsndfile1-dev \
    libsox-dev \
    sox \
    \
    # Image processing
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    \
    # Network tools
    net-tools \
    iputils-ping \
    \
    # Development tools
    vim \
    nano \
    htop \
    tree \
    zip \
    unzip \
    \
    # Python development
    python3-dev \
    python3-pip \
    \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for better security
RUN groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid vscode --shell /bin/bash --create-home vscode \
    && mkdir -p /home/vscode/.cache /home/vscode/.local \
    && chown -R vscode:vscode /home/vscode

# Switch to non-root user
USER vscode
WORKDIR /home/vscode

# Set up Python environment
ENV PATH="/home/vscode/.local/bin:$PATH"
ENV PYTHONPATH="/workspace:$PYTHONPATH"

# Upgrade pip and install basic Python tools
RUN pip install --user --upgrade pip setuptools wheel

# Copy requirements first for better Docker layer caching
COPY --chown=vscode:vscode ../requirements.txt /tmp/requirements.txt
COPY --chown=vscode:vscode ../pyproject.toml /tmp/pyproject.toml

# Install Python dependencies using Tsinghua mirror
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn \
    && pip install --user -r /tmp/requirements.txt

# Install additional development tools
RUN pip install --user \
    # Development tools
    ipython \
    jupyterlab \
    notebook \
    # Code quality
    black \
    isort \
    flake8 \
    mypy \
    pre-commit \
    # Testing
    pytest \
    pytest-cov \
    pytest-asyncio \
    # CLI tools
    click \
    rich \
    typer

# Create necessary directories
RUN mkdir -p \
    /home/vscode/.cache/pip \
    /home/vscode/.cache/huggingface \
    /home/vscode/.cache/torch \
    /home/vscode/.local/share/tts \
    /home/vscode/.cache/seamless_communication \
    /home/vscode/.config

# Set up git configuration
RUN git config --global init.defaultBranch main \
    && git config --global pull.rebase false \
    && git config --global user.name "Dev Container User" \
    && git config --global user.email "dev@container.local"

# Create workspace directory
USER root
RUN mkdir -p /workspace && chown -R vscode:vscode /workspace
USER vscode

# Set working directory
WORKDIR /workspace

# Expose ports for development
EXPOSE 8000 8888 5000

# Default command
CMD ["/bin/bash"] 