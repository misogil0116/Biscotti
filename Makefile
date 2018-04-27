# GNU Make workspace makefile autogenerated by Premake

ifndef config
  config=release
endif

ifndef verbose
  SILENT = @
endif

ifeq ($(config),release)
  biscotti_static_config = release
  biscotti_config = release
endif
ifeq ($(config),debug)
  biscotti_static_config = debug
  biscotti_config = debug
endif

PROJECTS := biscotti_static biscotti

.PHONY: all clean help $(PROJECTS) 

all: $(PROJECTS)

biscotti_static:
ifneq (,$(biscotti_static_config))
	@echo "==== Building biscotti_static ($(biscotti_static_config)) ===="
	@${MAKE} --no-print-directory -C . -f biscotti_static.make config=$(biscotti_static_config)
endif

biscotti:
ifneq (,$(biscotti_config))
	@echo "==== Building biscotti ($(biscotti_config)) ===="
	@${MAKE} --no-print-directory -C . -f biscotti.make config=$(biscotti_config)
endif

clean:
	@${MAKE} --no-print-directory -C . -f biscotti_static.make clean
	@${MAKE} --no-print-directory -C . -f biscotti.make clean

help:
	@echo "Usage: make [config=name] [target]"
	@echo ""
	@echo "CONFIGURATIONS:"
	@echo "  release"
	@echo "  debug"
	@echo ""
	@echo "TARGETS:"
	@echo "   all (default)"
	@echo "   clean"
	@echo "   biscotti_static"
	@echo "   biscotti"
	@echo ""
	@echo "For more information, see http://industriousone.com/premake/quick-start"