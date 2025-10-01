# ====================================================
# Resident Evil 2 (N64) - Decomp Build System
# ====================================================

# Tools
CC      := mips-linux-gnu-gcc
AS      := mips-linux-gnu-as
LD      := mips-linux-gnu-ld
OBJCOPY := mips-linux-gnu-objcopy
OBJDUMP := mips-linux-gnu-objdump

# Directories
BUILD_DIR := build
ASM_DIR   := asm
SRC_DIR   := src
ASSETS_DIR:= assets
INCLUDE_DIR := include

# Input / Output
ROM_ORIG  := re2.z64
ELF       := $(BUILD_DIR)/residentevilii.elf
ROM       := $(BUILD_DIR)/residentevilii.z64
LD_SCRIPT := residentevilii.ld

# Expected SHA1 of original ROM
EXPECTED_HASH := 62ec19bead748c12d38f6c5a7ab0831edbd3d44b

# ====================================================
# Flags
# ====================================================

# N64 uses VR4300 (MIPS III, 32-bit ABI)
ASFLAGS  := -march=vr4300 -mabi=32 -I $(INCLUDE_DIR)
CFLAGS   := -O2 -G0 -mabi=32 -march=vr4300

# ====================================================
# File discovery
# ====================================================

# All split binaries, asm, and C (recursively)
BIN_FILES := $(shell find $(ASSETS_DIR) -type f -name '*.bin')
ASM_FILES := $(shell find $(ASM_DIR)   -type f -name '*.s')
C_FILES   := $(shell find $(SRC_DIR)   -type f -name '*.c' 2>/dev/null)

# Objects
BIN_OBJS := $(patsubst $(ASSETS_DIR)/%.bin,$(BUILD_DIR)/$(ASSETS_DIR)/%.o,$(BIN_FILES))
ASM_OBJS := $(patsubst $(ASM_DIR)/%.s,$(BUILD_DIR)/$(ASM_DIR)/%.o,$(ASM_FILES))
C_OBJS   := $(patsubst $(SRC_DIR)/%.c,$(BUILD_DIR)/$(SRC_DIR)/%.o,$(C_FILES))

O_FILES := $(BIN_OBJS) $(ASM_OBJS) $(C_OBJS)

# ====================================================
# Default target
# ====================================================
all: $(ROM)

# ====================================================
# Build rules
# ====================================================

# Assemble MIPS assembly
$(BUILD_DIR)/$(ASM_DIR)/%.o: $(ASM_DIR)/%.s | $(BUILD_DIR)
	@mkdir -p $(dir $@)
	$(AS) $(ASFLAGS) -o $@ $<

# Compile C source
$(BUILD_DIR)/$(SRC_DIR)/%.o: $(SRC_DIR)/%.c | $(BUILD_DIR)
	@mkdir -p $(dir $@)
	$(CC) -c $(CFLAGS) -o $@ $<

# Wrap binary files
$(BUILD_DIR)/$(ASSETS_DIR)/%.o: $(ASSETS_DIR)/%.bin | $(BUILD_DIR)
	@mkdir -p $(dir $@)
	$(LD) -r -b binary -o $@ $<

# Link into ELF
$(ELF): $(O_FILES) $(LD_SCRIPT) | $(BUILD_DIR)
	$(LD) -T $(LD_SCRIPT) -o $@ -Map $(BUILD_DIR)/residentevilii.map

# ELF -> raw ROM
$(ROM): $(ELF)
	$(OBJCOPY) -O binary $< $@
	# Pad to 64 MB (N64 cart size)
	dd if=/dev/zero bs=1 count=0 seek=67108864 >> $@

# ====================================================
# Utilities
# ====================================================

verify: $(ROM)
	@echo "Verifying ROM hash..."
	@sha1sum $(ROM) | awk '{print $$1}' > $(BUILD_DIR)/residentevilii.sha1
	@if [ "$$(cat $(BUILD_DIR)/residentevilii.sha1)" = "$(EXPECTED_HASH)" ]; then \
		echo "✅ Hash match!"; \
	else \
		echo "❌ Hash mismatch!"; \
		echo "Expected: $(EXPECTED_HASH)"; \
		echo "Got:      $$(cat $(BUILD_DIR)/residentevilii.sha1)"; \
	fi

disasm: $(ELF)
	@echo "Generating disassembly files..."
	@python3 tools/generate_disasm_targets.py | bash
	@echo "All disassembly files generated"

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

clean:
	rm -rf $(BUILD_DIR)

.PHONY: all clean verify disasm

print-%:
	@echo $* = $($*)
