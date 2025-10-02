SECTIONS
{
    __romPos = 0;
    header_ROM_START = __romPos;
    header_VRAM = ADDR(.header);
    .header : AT(header_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        header_DATA_START = .;
        build/asm/header.o(.data);
        header_DATA_END = .;
        header_DATA_SIZE = ABSOLUTE(header_DATA_END - header_DATA_START);
    }
    __romPos += SIZEOF(.header);
    header_ROM_END = __romPos;
    header_VRAM_END = .;

    boot_ROM_START = __romPos;
    boot_VRAM = ADDR(.boot);
    .boot : AT(boot_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        boot_DATA_START = .;
        build/assets/boot.o(.data);
        boot_DATA_END = .;
        boot_DATA_SIZE = ABSOLUTE(boot_DATA_END - boot_DATA_START);
    }
    __romPos += SIZEOF(.boot);
    boot_ROM_END = __romPos;
    boot_VRAM_END = .;

    rodata1_ROM_START = __romPos;
    rodata1_VRAM = ADDR(.rodata1);
    .rodata1 : AT(rodata1_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        rodata1_DATA_START = .;
        build/assets/rodata1.o(.data);
        rodata1_DATA_END = .;
        rodata1_DATA_SIZE = ABSOLUTE(rodata1_DATA_END - rodata1_DATA_START);
    }
    __romPos += SIZEOF(.rodata1);
    rodata1_ROM_END = __romPos;
    rodata1_VRAM_END = .;

    text1_ROM_START = __romPos;
    text1_VRAM = ADDR(.text1);
    .text1 : AT(text1_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        text1_DATA_START = .;
        build/assets/text1.o(.data);
        text1_DATA_END = .;
        text1_DATA_SIZE = ABSOLUTE(text1_DATA_END - text1_DATA_START);
    }
    __romPos += SIZEOF(.text1);
    text1_ROM_END = __romPos;
    text1_VRAM_END = .;

    text2_ROM_START = __romPos;
    text2_VRAM = ADDR(.text2);
    .text2 0x8001F10 : AT(text2_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        text2_TEXT_START = .;
        build/asm/1AD0.o(.text);
        . = ALIGN(., 16);
        text2_TEXT_END = .;
        text2_TEXT_SIZE = ABSOLUTE(text2_TEXT_END - text2_TEXT_START);
        text2_DATA_START = .;
        build/asm/1AD0.o(.data);
        build/asm/data/1AE0.data.o(.data);
        . = ALIGN(., 16);
        text2_DATA_END = .;
        text2_DATA_SIZE = ABSOLUTE(text2_DATA_END - text2_DATA_START);
        text2_RODATA_START = .;
        build/asm/1AD0.o(.rodata);
        . = ALIGN(., 16);
        text2_RODATA_END = .;
        text2_RODATA_SIZE = ABSOLUTE(text2_RODATA_END - text2_RODATA_START);
    }
    text2_bss_VRAM = ADDR(.text2_bss);
    .text2_bss (NOLOAD) : SUBALIGN(16)
    {
        FILL(0x00000000);
        text2_BSS_START = .;
        build/asm/1AD0.o(.bss);
        . = ALIGN(., 16);
        text2_BSS_END = .;
        text2_BSS_SIZE = ABSOLUTE(text2_BSS_END - text2_BSS_START);
    }
    __romPos += SIZEOF(.text2);
    __romPos = ALIGN(__romPos, 16);
    . = ALIGN(., 16);
    text2_ROM_END = __romPos;
    text2_VRAM_END = .;

    text3_ROM_START = __romPos;
    text3_VRAM = ADDR(.text3);
    .text3 : AT(text3_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        text3_DATA_START = .;
        build/assets/text3.o(.data);
        text3_DATA_END = .;
        text3_DATA_SIZE = ABSOLUTE(text3_DATA_END - text3_DATA_START);
    }
    __romPos += SIZEOF(.text3);
    text3_ROM_END = __romPos;
    text3_VRAM_END = .;

    rodata2_ROM_START = __romPos;
    rodata2_VRAM = ADDR(.rodata2);
    .rodata2 0x80012840 : AT(rodata2_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        rodata2_DATA_START = .;
        build/asm/data/rodata2.data.o(.data);
        rodata2_DATA_END = .;
        rodata2_DATA_SIZE = ABSOLUTE(rodata2_DATA_END - rodata2_DATA_START);
    }
    __romPos += SIZEOF(.rodata2);
    rodata2_ROM_END = __romPos;
    rodata2_VRAM_END = .;

    text4_ROM_START = __romPos;
    text4_VRAM = ADDR(.text4);
    .text4 : AT(text4_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        text4_DATA_START = .;
        build/assets/text4.o(.data);
        text4_DATA_END = .;
        text4_DATA_SIZE = ABSOLUTE(text4_DATA_END - text4_DATA_START);
    }
    __romPos += SIZEOF(.text4);
    text4_ROM_END = __romPos;
    text4_VRAM_END = .;

    assets_0x000B6240_ROM_START = __romPos;
    assets_0x000B6240_VRAM = ADDR(.assets_0x000B6240);
    .assets_0x000B6240 : AT(assets_0x000B6240_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        assets_0x000B6240_DATA_START = .;
        build/assets/assets_0x000B6240.o(.data);
        assets_0x000B6240_DATA_END = .;
        assets_0x000B6240_DATA_SIZE = ABSOLUTE(assets_0x000B6240_DATA_END - assets_0x000B6240_DATA_START);
    }
    __romPos += SIZEOF(.assets_0x000B6240);
    assets_0x000B6240_ROM_END = __romPos;
    assets_0x000B6240_VRAM_END = .;

    video_ROM_START = __romPos;
    video_VRAM = ADDR(.video);
    .video : AT(video_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        video_DATA_START = .;
        build/assets/video.o(.data);
        video_DATA_END = .;
        video_DATA_SIZE = ABSOLUTE(video_DATA_END - video_DATA_START);
    }
    __romPos += SIZEOF(.video);
    video_ROM_END = __romPos;
    video_VRAM_END = .;

    assets_0x02B7D8EA_ROM_START = __romPos;
    assets_0x02B7D8EA_VRAM = ADDR(.assets_0x02B7D8EA);
    .assets_0x02B7D8EA : AT(assets_0x02B7D8EA_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        assets_0x02B7D8EA_DATA_START = .;
        build/assets/assets_0x02B7D8EA.o(.data);
        assets_0x02B7D8EA_DATA_END = .;
        assets_0x02B7D8EA_DATA_SIZE = ABSOLUTE(assets_0x02B7D8EA_DATA_END - assets_0x02B7D8EA_DATA_START);
    }
    __romPos += SIZEOF(.assets_0x02B7D8EA);
    assets_0x02B7D8EA_ROM_END = __romPos;
    assets_0x02B7D8EA_VRAM_END = .;

    jpeg_images_ROM_START = __romPos;
    jpeg_images_VRAM = ADDR(.jpeg_images);
    .jpeg_images : AT(jpeg_images_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        jpeg_images_DATA_START = .;
        build/assets/jpeg_images.o(.data);
        jpeg_images_DATA_END = .;
        jpeg_images_DATA_SIZE = ABSOLUTE(jpeg_images_DATA_END - jpeg_images_DATA_START);
    }
    __romPos += SIZEOF(.jpeg_images);
    jpeg_images_ROM_END = __romPos;
    jpeg_images_VRAM_END = .;

    assets_0x03AF17FE_ROM_START = __romPos;
    assets_0x03AF17FE_VRAM = ADDR(.assets_0x03AF17FE);
    .assets_0x03AF17FE : AT(assets_0x03AF17FE_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        assets_0x03AF17FE_DATA_START = .;
        build/assets/assets_0x03AF17FE.o(.data);
        assets_0x03AF17FE_DATA_END = .;
        assets_0x03AF17FE_DATA_SIZE = ABSOLUTE(assets_0x03AF17FE_DATA_END - assets_0x03AF17FE_DATA_START);
    }
    __romPos += SIZEOF(.assets_0x03AF17FE);
    assets_0x03AF17FE_ROM_END = __romPos;
    assets_0x03AF17FE_VRAM_END = .;

    empty_data_ROM_START = __romPos;
    empty_data_VRAM = ADDR(.empty_data);
    .empty_data : AT(empty_data_ROM_START) SUBALIGN(16)
    {
        FILL(0x00000000);
        empty_data_DATA_START = .;
        build/assets/empty_data.o(.data);
        empty_data_DATA_END = .;
        empty_data_DATA_SIZE = ABSOLUTE(empty_data_DATA_END - empty_data_DATA_START);
    }
    __romPos += SIZEOF(.empty_data);
    empty_data_ROM_END = __romPos;
    empty_data_VRAM_END = .;

    /DISCARD/ :
    {
        *(*);
    }
}
