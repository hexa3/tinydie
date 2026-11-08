MCU    = attiny412
TARGET = tinydie
CC     = avr-gcc
CFLAGS = -mmcu=$(MCU) -Os -Wall -Wextra -std=gnu11 -flto
# Arch's avr-gcc doesn't find avr-libc on its own; harmless elsewhere if the dir exists.
AVR_ROOT ?= /usr/lib/avr
ifneq ($(wildcard $(AVR_ROOT)/include),)
CFLAGS += --sysroot=$(AVR_ROOT) -isystem $(AVR_ROOT)/include
endif
# Flash over UPDI with a USB-serial adapter (SerialUPDI). Override: make flash PORT=/dev/ttyUSB1
PORT  ?= /dev/ttyUSB0

all: $(TARGET).hex size

$(TARGET).elf: main.c
	$(CC) $(CFLAGS) -o $@ $^

$(TARGET).hex: $(TARGET).elf
	avr-objcopy -O ihex -R .eeprom $< $@

size: $(TARGET).elf
	avr-size $<

flash: $(TARGET).hex
	pymcuprog write -t uart -u $(PORT) -d $(MCU) -f $< --erase --verify

clean:
	rm -f $(TARGET).elf $(TARGET).hex

.PHONY: all size flash clean
