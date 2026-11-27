PYTHON ?= python3
.PHONY: demo report figures

demo:
	$(PYTHON) -m src.demo

figures:
	$(PYTHON) -m src.make_figures

report:
	$(PYTHON) -m src.build_pdf
