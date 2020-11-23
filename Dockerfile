FROM python:3.8

WORKDIR /app

COPY requirements.txt .
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --requirement requirements.txt

COPY requirements-check.txt .
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --requirement requirements-check.txt

COPY . ./
RUN python3 -m pip install --disable-pip-version-check --no-deps --no-cache-dir --editable .

RUN prospector
