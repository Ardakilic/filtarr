# Filtarr — all commands run inside Docker (python:3-slim); no local Python
# or pip packages needed. Requires only Docker and make.
#
#   make            # everything: STLs + previews + README images
#   make generate   # STLs + interactive preview HTMLs
#   make docs       # README images (<folder>/docs/*.png)
#   make vendor     # fetch the latest three.js module build into vendor/
#   make image      # (re)build the Docker build image
#   make clean      # delete all generated outputs
#
# Fit tolerances can be overridden per run (see README -> Fit tuning):
#   make generate GEN_ARGS="--clear-friction 0.32"

IMAGE    := filtarr-build
RUN      := docker run --rm -v "$(CURDIR)":/app -w /app
GEN_ARGS ?=

.PHONY: all generate docs vendor image clean

all: generate docs

image:
	docker build -t $(IMAGE) .

generate: image
	$(RUN) $(IMAGE) python3 generate.py $(GEN_ARGS)

docs: image
	$(RUN) $(IMAGE) python3 tools/render_docs.py

vendor:
	$(RUN) python:3-slim python3 tools/fetch_three.py

clean:
	rm -rf deep27/stl v60/stl deep27/docs v60/docs
	rm -f deep27/preview*.html v60/preview*.html
