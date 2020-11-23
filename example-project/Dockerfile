FROM python:3.8 AS base

WORKDIR /app

COPY requirements.txt .
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --requirement=requirements.txt


FROM base AS check

COPY requirements-check.txt .
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --requirement=requirements-check.txt

COPY . ./

RUN prospector


FROM base AS run

RUN python3 -m compileall -q /usr/local/lib/python3.8 \
  -x '/usr/local/lib/python3.8/site-packages/pipenv/'

COPY . ./
RUN python3 -m pip install --disable-pip-version-check --no-deps --no-cache-dir --editable=.
RUN python3 -m compileall -q /app/c2cciutils
