FROM ubuntu:22.04 AS base

RUN apt update \
    && DEBIAN_FRONTEND=noninteractive apt install --yes --no-install-recommends python3-pip binutils \
    && apt-get clean \
    && rm -r /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /tmp/
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --requirement=/tmp/requirements.txt \
    && rm --recursive --force /tmp/*

COPY Pipfile Pipfile.lock ./
RUN pipenv sync --system --clear \
    && rm --recursive --force /usr/local/lib/python3.*/dist-packages/tests/ /tmp/* /root/.cache/* \
    && (strip /usr/local/lib/python3.*/dist-packages/*/*.so || true)

FROM base AS checker

RUN \
    pipenv sync --system --clear --dev \
    && pip install requirements-detector==0.7 \
    && rm --recursive --force /tmp/* /root/.cache/*

FROM base AS run

RUN python3 -m compileall -q /usr/local/lib/python3.* -x '/pipenv/'

COPY . ./
RUN python3 -m pip install --disable-pip-version-check --no-deps --no-cache-dir --no-deps --editable=.
RUN python3 -m compileall -q /app/
