# Makefile — CPP Studio
# Use with Git Bash (Windows) or any POSIX shell.
SHELL := /bin/sh

# ---- Project meta ----
APP        ?= cpp-studio
VERSION    ?= 0.1.0
OWNER      ?= lucerojc
GHCR       ?= ghcr.io/$(OWNER)
SLIM_IMG    = $(GHCR)/$(APP):slim
FULL_IMG    = $(GHCR)/$(APP):full
SLIM_VER    = $(GHCR)/$(APP):$(VERSION)-slim
FULL_VER    = $(GHCR)/$(APP):$(VERSION)-full

# ---- Paths ----
DATA       ?= $(PWD)/data_sample
ISCC       ?= /c/Users/$(USER)/AppData/Local/Programs/Inno\ Setup\ 6/ISCC.exe
# Example alternatives:
# ISCC ?= /c/Program\ Files\ \(x86\)/Inno\ Setup\ 6/ISCC.exe
# ISCC ?= /c/Program\ Files/Inno\ Setup\ 6/ISCC.exe

.PHONY: build-slim build-full app app-full run-slim run-full batch pdf \
        compose-slim compose-full down clean test \
        release-pip release-docker ghcr-login release-installer release checksum

# ---------------- Core (what you already had, improved) ----------------

build-slim:
	docker build -f Dockerfile.slim -t $(SLIM_IMG) .

build-full:
	docker build -t $(FULL_IMG) .

run-slim: build-slim
	docker run --rm -p 8501:8501 -v "$$PWD:/work" -v "$(DATA):/data" -w /work $(SLIM_IMG) \
	  streamlit run app/streamlit_app.py --server.headless=true --browser.gatherUsageStats=false

run-full: build-full
	# Full runs on 8502 so it never clashes with slim
	docker run --rm -p 8502:8501 -v "$$PWD:/work" -v "$(DATA):/data" -w /work $(FULL_IMG) \
	  streamlit run app/streamlit_app.py --server.headless=true --browser.gatherUsageStats=false

# Back-compat aliases
app: run-slim
app-full: run-full

batch: build-slim
	docker run --rm -v "$$PWD:/work" -w /work $(SLIM_IMG) \
	  cpps-run data_sample --praat-match --per_frame --out cpps_summary.csv

pdf: build-full
	docker run --rm -v "$$PWD:/work" -w /work $(FULL_IMG) \
	  cpps-report --summary cpps_summary.csv --out cpps_batch_report.pdf --paper a4 --margins 0.6

compose-slim:
	docker compose up --build

compose-full:
	docker compose --profile full up --build

down:
	docker compose down --remove-orphans

# ---------------- Dev helpers ----------------

clean:
	rm -rf build dist *.spec **/__pycache__ .pytest_cache || true

test:
	python -m pytest -q

# ---------------- Releases ----------------
# CR_PAT: a GHCR token (or use GH Actions). Example:
#    export GHCR_USER=$(OWNER)
#    export CR_PAT=ghp_XXXXXXXXXXXXXXXXXXXX
#    make ghcr-login release-docker

ghcr-login:
	@test -n "$(GHCR_USER)" || (echo "Set GHCR_USER (e.g., export GHCR_USER=$(OWNER))" && false)
	@test -n "$(CR_PAT)"    || (echo "Set CR_PAT to a GHCR token." && false)
	echo "$$CR_PAT" | docker login ghcr.io -u "$(GHCR_USER)" --password-stdin

release-docker: build-slim build-full
	# Tag with version and latest
	docker tag $(SLIM_IMG) $(SLIM_VER)
	docker tag $(FULL_IMG) $(FULL_VER)
	# Push both tags
	docker push $(SLIM_IMG)
	docker push $(SLIM_VER)
	docker push $(FULL_IMG)
	docker push $(FULL_VER)

release-pip:
	python -m pip install --upgrade pip build
	python -m build
	@echo "Built sdist/wheel in ./dist"

# Build 3 one-folder apps with PyInstaller, merge to dist/cpp-studio, then Inno Setup.
# Requires: scripts/cpps_run_entry.py, scripts/cpps_report_entry.py, scripts/app_launcher.py,
# and installer/cpp-studio.iss (the cleaned one we finalized).
release-installer: clean
	python -m pip install pyinstaller==6.6.0
	# runtime hook to keep Matplotlib cache writable
	mkdir -p build/win
	printf "%s\n" "import os, tempfile" "os.environ.setdefault('MPLCONFIGDIR', tempfile.mkdtemp(prefix='mplcfg-'))" > build/win/runtime_mpl_tempdir.py
	# 1) cpps-run
	pyinstaller --noconfirm --clean --onedir --name cpps-run \
	  --console \
	  --runtime-hook build/win/runtime_mpl_tempdir.py \
	  --collect-data matplotlib --collect-data soundfile \
	  --add-data "reports/report_template.tex;reports" \
	  --add-data "praat/*.praat;praat" \
	  --add-data "logo.png;." \
	  --add-data "docs/EULA.md;docs" \
	  --add-data "docs/README.md;docs" \
	  scripts/cpps_run_entry.py
	# 2) cpps-report
	pyinstaller --noconfirm --clean --onedir --name cpps-report \
	  --console \
	  --runtime-hook build/win/runtime_mpl_tempdir.py \
	  --collect-data matplotlib --collect-data soundfile \
	  --add-data "reports/report_template.tex;reports" \
	  --add-data "praat/*.praat;praat" \
	  --add-data "logo.png;." \
	  --add-data "docs/EULA.md;docs" \
	  --add-data "docs/README.md;docs" \
	  scripts/cpps_report_entry.py
	# 3) GUI Streamlit launcher
	pyinstaller --noconfirm --clean --onedir --name cppstudio-app \
	  --windowed \
	  --runtime-hook build/win/runtime_mpl_tempdir.py \
	  --collect-data matplotlib --collect-data soundfile \
	  --add-data "reports/report_template.tex;reports" \
	  --add-data "praat/*.praat;praat" \
	  --add-data "logo.png;." \
	  --add-data "docs/EULA.md;docs" \
	  --add-data "docs/README.md;docs" \
	  scripts/app_launcher.py
	# Merge into one folder for the installer
	rm -rf dist/$(APP)
	mkdir -p dist/$(APP)
	cp -r dist/cpps-run/*      dist/$(APP)/
	cp -r dist/cpps-report/*   dist/$(APP)/
	cp -r dist/cppstudio-app/* dist/$(APP)/
	# Compile installer (requires ISCC)
	"$(ISCC)" "installer/cpp-studio.iss" || (echo "Adjust ISCC path via ISCC=..."; false)
	@echo "Installer at installer/Output/$(APP)-$(VERSION)-setup.exe"

checksum:
	@sha256sum installer/Output/$(APP)-$(VERSION)-setup.exe || certutil -hashfile installer\\Output\\$(APP)-$(VERSION)-setup.exe SHA256 || true

# Chain everything
release: release-pip release-docker release-installer checksum
	@echo "Release done."
