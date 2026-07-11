# Build image for the Filtarr generators — see Makefile.
# python:3-slim = latest stable Python 3 on Debian slim (pre-built wheels work,
# small footprint).
FROM python:3-slim

# Liberation Sans: metric-compatible Arial substitute for the lid engraving
RUN apt-get update \
 && apt-get install -y --no-install-recommends fonts-liberation \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app
