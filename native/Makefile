# Makefile to build the Patchanka C wrapper.

CC      ?= cc
CFLAGS  ?= -O2 -fPIC -Wall -Wextra
LDFLAGS ?= -shared

PKG_CONFIG ?= pkg-config
PW_CFLAGS  := $(shell $(PKG_CONFIG) --cflags libpipewire-0.3)
PW_LIBS    := $(shell $(PKG_CONFIG) --libs libpipewire-0.3)

TARGET := libpatchanka_pw.so
SRC    := patchanka_pw.c

.PHONY: all clean rebuild

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(PW_CFLAGS) $(LDFLAGS) -o $@ $< $(PW_LIBS)

clean:
	rm -f $(TARGET)

rebuild:
	$(MAKE) clean
	$(MAKE) all