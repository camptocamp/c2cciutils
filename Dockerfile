FROM ubuntu:22.04 AS base-all
LABEL maintainer Camptocamp "info@camptocamp.com"
SHELL ["/bin/bash", "-o", "pipefail", "-cux"]

RUN --mount=type=cache,target=/var/lib/apt/lists --mount=type=cache,target=/var/cache \
    sed -i '/-backports /d' /etc/apt/sources.list \
    && apt-get update \
    && apt-get install --yes --no-install-recommends python3-pip binutils

# Used to convert the locked packages by poetry to pip requirements format
# We don't directly use `poetry install` because it force to use a virtual environment.
FROM base-all as poetry

# Install Poetry
WORKDIR /tmp
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache \
    python3 -m pip install --disable-pip-version-check --requirement=requirements.txt

# Do the conversion
COPY poetry.lock pyproject.toml ./
ENV POETRY_DYNAMIC_VERSIONING_BYPASS=0.0.0
RUN poetry export --extras=checks --extras=publish --extras=audit --output=requirements.txt \
    && poetry export --with=dev --output=requirements-dev.txt

# Base, the biggest thing is to install the Python packages
FROM base-all as base

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,from=poetry,source=/tmp,target=/poetry \
    python3 -m pip install --disable-pip-version-check --no-deps --requirement=/poetry/requirements.txt

FROM base AS checker

# Force to use a newer version of setuptools
RUN python3 -m pip install --prefix=/usr --no-cache-dir --disable-pip-version-check setuptools==61.3.1 \
    && rm -rf /usr/lib/python3/dist-packages/setuptools* \
    && ln -s /usr/local/lib/python3/dist-packages/setuptools* /usr/lib/python3/dist-packages/

RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,from=poetry,source=/tmp,target=/poetry \
    python3 -m pip install --disable-pip-version-check --no-deps --requirement=/poetry/requirements-dev.txt

FROM base AS run

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN --mount=type=cache,target=/var/lib/apt/lists --mount=type=cache,target=/var/cache \
    . /etc/os-release \
    && apt-get update \
    && apt-get --assume-yes upgrade \
    && apt-get install --assume-yes --no-install-recommends apt-transport-https gnupg curl \
    && echo "deb https://deb.nodesource.com/node_16.x ${VERSION_CODENAME} main" > /etc/apt/sources.list.d/nodesource.list \
    && curl --silent https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - \
    && apt-get update \
    && apt-get install --assume-yes --no-install-recommends nodejs libmagic1 git python3-dev libpq-dev gcc python-is-python3

RUN python3 -m compileall -q -- *

COPY . ./
ARG VERSION=dev
RUN --mount=type=cache,target=/root/.cache \
    --mount=type=cache,target=/root/.npm \
    cd c2cciutils && npm install && cd - \
    && POETRY_DYNAMIC_VERSIONING_BYPASS=${VERSION} python3 -m pip install --disable-pip-version-check --no-deps --editable=. \
    && python3 -m pip freeze > /requirements.txt \
    && python3 -m compileall -q /app/c2cciutils

ENV PATH=/root/.local/bin:$PATH
RUN git config --global --add safe.directory /src
WORKDIR /src
VOLUME /src
