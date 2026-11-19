PY ?= python3
SUSVIBES ?= ../susvibes

.PHONY: test dry integ stage0

test:
	$(PY) tests/test_base.py
	$(PY) tests/test_blocks.py

dry:
	$(PY) -m harness_sec.run_recipe --config harness_sec/configs/011.yaml --dry-run --out /tmp/hs_dry

integ:
	bash scripts/integration.sh

stage0:
	$(PY) -m harness_sec.stage0 --susvibes-dir $(SUSVIBES) --limit 5 --out runs/stage0
