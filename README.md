tinydie

its a dice that lights up!!! you press the button and the lights go all crazy like its rolling and then when u let go it slows down and stops on a number 1 to 6. its so cool

the brain is a tiny chip called ATtiny412 it only has 8 legs but its really smart. when nobody plays with it it goes to sleep so the battery lasts forever (not actually forever but like a really long time) so theres no on off switch you dont need one

how i made it step by step (with pictures): https://sheheryar.xyz/tinydie-board/journal/

| thing | what it is |
|---|---|
| brain chip | ATtiny412-SSNR (8 legs) |
| how big | 45mm x 45mm its like a cookie |
| battery | CR2032 coin battery its on the back |
| made in | KiCad 10 |
| how much $$ | like $1.75 for one dice. or $15 to $31 for 5 of them with the boards and shipping, look in BOM.md |
| mistakes | 0!! i checked |

how it works

ok so a dice has 6 sides right. but you only need 4 groups of lights because the dots always come in pairs like the top left one and the bottom right one are always on together. the middle one is by itself tho

| group | leg on chip | which lights | on for |
|---|---|---|---|
| A | PA1 (leg 4) | top left + bottom right | 2 3 4 5 6 |
| B | PA2 (leg 5) | top right + bottom left | 4 5 6 |
| C | PA3 (leg 7) | middle left + middle right | 6 |
| D | PA6 (leg 2) | middle | 1 3 5 |

the chip has 6 legs you can use. 4 are for lights 1 is the button (PA7 leg 3) and 1 is for putting the program on (PA0 leg 6). so every leg has a job lol

every light has a resistor thats 330 ohms its like a speed bump so the light doesnt get too much power. each light uses 3mA so even a 6 is only 18mA

how does it pick the number?? theres a clock in the chip that counts super super fast and when you hold the button it looks at the clock. nobody can hold it for the exact same time twice so its always a surprise :)

battery: one roll is like 5 seconds and the battery can do about 10000 rolls!!! when its sleeping it uses basically nothing

whats in here

| folder/file | whats in it |
|---|---|
| firmware/ | the program for the chip its in C |
| hardware/tinydie.kicad_pro | the kicad project open this one in KiCad 10 |
| hardware/tinydie.kicad_sch | the schematic (the drawing of how stuff connects) |
| hardware/tinydie.kicad_pcb | the board |
| hardware/fab/ | the files u send to the factory + parts list |
| BOM.md | shopping list |

putting the program on the chip

| step | type this | u need |
|---|---|---|
| 1 | cd firmware | nothing |
| 2 | make | avr-gcc and avr-libc (arch linux: pacman -S avr-gcc avr-libc) |
| 3 | make flash | pymcuprog (pip install pymcuprog) and a usb serial thing |

the program is only 447 bytes and the chip fits 4096 so theres LOTS of room

the usb serial thing has to be 3.3V. plug the wires like this

| usb thing pin | goes to |
|---|---|
| TX | 1k ohm resistor then J1 "U" |
| RX | J1 "U" too (the chip side of the resistor) |
| 3V3 | J1 "V" |
| GND | J1 "G" |

TAKE THE BATTERY OUT BEFORE YOU PLUG IN THE 3V3 WIRE!!! really dont forget

how to make one

| step | what to do |
|---|---|
| 1 | send hardware/fab/tinydie-gerbers.zip to a board factory. pick 2 layers 1.6mm thick and any colour u want. its not hard to make so any factory can do it |
| 2 | buy the stuff in BOM.md |
| 3 | solder the front first. U1, C1, R1 to R7, D1 to D7 and SW1. the little mark on the lights goes to the left side |
| 4 | solder J1 |
| 5 | then the battery holder on the back last |
