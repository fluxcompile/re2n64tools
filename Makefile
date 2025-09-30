# ====================================================
# Resident Evil 2 (N64) - Decomp Build System
# ====================================================

# Tools
LD      := mips-linux-gnu-ld
OBJCOPY := mips-linux-gnu-objcopy

# Files
ROM_ORIG     := re2.z64                  # original ROM (user-provided)
BUILD_DIR    := build
CODE_BIN     := $(BUILD_DIR)/re2_code.bin
ASSETS_BIN   := $(BUILD_DIR)/re2_assets.bin
CODE_OBJ     := $(BUILD_DIR)/code.o
ASSETS_OBJ   := $(BUILD_DIR)/assets.o
ELF          := $(BUILD_DIR)/re2.elf
ROM          := $(BUILD_DIR)/re2.z64

# Expected SHA1 of original ROM
EXPECTED_HASH := 62ec19bead748c12d38f6c5a7ab0831edbd3d44b

# ====================================================
# Default target: rebuild ROM from blobs
# ====================================================
all: $(ROM)

# Split ROM into code and assets blobs
$(CODE_BIN) $(ASSETS_BIN): $(ROM_ORIG) | $(BUILD_DIR)
	python3 tools/extract_assets.py $(ROM_ORIG) $(BUILD_DIR)

# Wrap binary blobs as linkable objects
$(CODE_OBJ): $(CODE_BIN)
	$(LD) -r -b binary -o $@ $<

$(ASSETS_OBJ): $(ASSETS_BIN)
	$(LD) -r -b binary -o $@ $<

# Link objects into ELF
$(ELF): $(CODE_OBJ) $(ASSETS_OBJ)
	$(LD) -T linker.ld -o $@ $^

# Convert ELF -> raw ROM
$(ROM): $(ELF)
	$(OBJCOPY) -O binary $< $@
	# Pad to 64 MB (N64 cart size)
	dd if=/dev/zero bs=1 count=0 seek=67108864 >> $@

# Verify against known hash
verify: $(ROM)
	@echo "Verifying ROM hash..."
	@sha1sum $(ROM) | awk '{print $$1}' > $(BUILD_DIR)/re2.sha1
	@if [ "$$(cat $(BUILD_DIR)/re2.sha1)" = "$(EXPECTED_HASH)" ]; then \
		echo "✅ Hash match!"; \
	else \
		echo "❌ Hash mismatch!"; \
		echo "Expected: $(EXPECTED_HASH)"; \
		echo "Got:      $$(cat $(BUILD_DIR)/re2.sha1)"; \
	fi

# Utility
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

clean:
	rm -f $(BUILD_DIR)/*

.PHONY: all clean verify
