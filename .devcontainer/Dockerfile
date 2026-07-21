FROM python:3.12-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=2.1.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYSPARK_PYTHON=python \
    PYSPARK_DRIVER_PYTHON=python

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        openjdk-17-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

RUN JAVA_HOME_PATH="$(dirname "$(dirname "$(readlink -f "$(command -v java)")")")" \
    && echo "JAVA_HOME=${JAVA_HOME_PATH}" >> /etc/environment \
    && echo "export JAVA_HOME=${JAVA_HOME_PATH}" >> /etc/profile.d/java.sh \
    && echo 'export PATH="$JAVA_HOME/bin:$PATH"' >> /etc/profile.d/java.sh

ENV PATH="/root/.local/bin:${PATH}"

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install --no-cache-dir \
        "poetry==${POETRY_VERSION}" \
        "jupyterlab>=4.0,<5.0" \
        "notebook>=7.0,<8.0" \
        "ipykernel>=6.29,<7.0" \
        "pyspark>=3.5,<4.0"

WORKDIR /workspaces/tse-analytics

EXPOSE 8888

CMD ["bash"]