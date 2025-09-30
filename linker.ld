OUTPUT_ARCH(mips)
ENTRY(_start)

/* Define memory regions */
SECTIONS
{
    /* Code starts at the N64 standard KSEG0 address */
    .text 0x80000000 : {
        KEEP(*(.data))   /* from binary blob re2_code.bin */
        *(.text*)
    }

    /* Assets blob follows immediately after code */
    .assets : {
        KEEP(*(.data*))
    }

    /* Provide a stack top just for safety */
    __stack_top = 0x807FFFFF;
}
