# Makefile for Patchanka translation files.
#
# Requires:
#   - pylupdate6 (from PyQt6 dev tools)
#   - lrelease (from Qt6 linguist tools)
#
# On Debian/Ubuntu:
#   sudo apt install pyqt6-dev-tools qt6-l10n-tools
#
# Usage:
#   make            # Update .ts from source and compile to .qm
#   make update     # Only update .ts from source
#   make compile    # Only compile .ts to .qm
#   make clean      # Remove generated .qm files

PYLUPDATE ?= pylupdate6
LRELEASE  ?= lrelease

LOCALE_DIR := patchanka/locale
TS_FILES   := $(wildcard $(LOCALE_DIR)/*.ts)
QM_FILES   := $(TS_FILES:.ts=.qm)

SRC_FILES  := $(shell find patchanka -name "*.py" -not -path "*/locale/*")

.PHONY: all update compile clean force

all: compile

# Update .ts files from source code
update:
	@mkdir -p $(LOCALE_DIR)
	@for ts in $(TS_FILES); do \
		echo "Updating $$ts"; \
		$(PYLUPDATE) -no-obsolete $(SRC_FILES) -ts $$ts; \
	done

# Compile .ts to .qm
compile: $(QM_FILES)

%.qm: %.ts
	@echo "Compiling $< -> $@"
	$(LRELEASE) $< -qm $@

# Force regeneration even if .ts is not older than sources
force:
	$(MAKE) update
	$(MAKE) compile

clean:
	rm -f $(QM_FILES)
	@echo "Removed generated .qm files"