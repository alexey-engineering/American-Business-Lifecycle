PYTHON ?= python3
# BDS raw CSVs are committed with pinned checksums, so the reproducible default is offline.
# Set INGEST_ARGS empty to fetch fresh Census CSVs; the pinned digest must still match.
INGEST_ARGS ?= --offline

.PHONY: ingest build analyze test all

ingest:
	$(PYTHON) ingestion/ingest_bds.py $(INGEST_ARGS)

build:
	$(PYTHON) ingestion/build_database.py

analyze:
	$(PYTHON) analysis/exploratory_analysis.py
	$(PYTHON) analysis/compare_bds_bed.py

test:
	$(PYTHON) -m pytest -q tests

all: ingest build analyze test
