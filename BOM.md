tinydie shoping list

this is all the stuff u need to buy to make the dice and how much it costs. the rule was dont spend more than $35 for everything (parts and boards and shipping)

the prices are guesses from like late 2026 from LCSC and JLCPCB so check them again before u buy ok. shipping is different depending where you live

stuff for one dice

| name on board | how many | what is it | the exact one | footprint | how much each (ish) |
|---|---|---|---|---|---|
| U1 | 1 | the brain chip | Microchip ATTINY412-SSNR | SOIC-8 | $0.75 |
| BT1 | 1 | battery holder (on the back) | MYOUNG BS-07-A1BJ001 | BatteryHolder_MYOUNG_BS-07-A1BJ001_CR2032 | $0.15 |
| - | 1 | CR2032 battery | any | - | $0.40 |
| D1 to D7 | 7 | red lights | 0805, 2.0V | LED_0805 | $0.03 |
| R1 to R7 | 7 | 330 ohm resistor one for every light | 0805 | R_0805 | $0.01 |
| C1 | 1 | 100nF capacitor it keeps the power smooth for the chip | 0805, X7R, 16V or more | C_0805 | $0.01 |
| SW1 | 1 | the button 6mm x 6mm | any | SW_PUSH_6mm | $0.08 |
| J1 | 1 | 3 pins for putting the program on | 2.54mm pin header | PinHeader_1x03_P2.54mm | $0.03 |

one dice is like $1.75 thats so cheap

buying for 5 dice

some stuff only comes in big packs so u get extras (bonus!!)

| what | how much (ish) |
|---|---|
| 5 brain chips | $3.75 |
| 5 battery holders | $0.75 |
| 5 batteries | $2.00 |
| 50 red lights (smallest pack they have) | $1.00 |
| 100 resistors | $0.30 |
| 50 capacitors | $0.30 |
| 5 buttons | $0.40 |
| 1 strip of 40 pins (snap off 3) | $0.30 |
| all the parts | like $8.80 |
| 5 boards (45mm x 45mm, 2 layers, 1.6mm) | like $2.00 |
| shipping boards | $2 to $10 |
| shipping parts | $2 to $10 |
| EVERYTHING | like $15 to $31 |

if u dont have one u also need a usb serial thing (CH340 or CP2102) to put the program on. its like $2 and u need one 1k ohm resistor with it. even if everything costs the most it can its like $33 so still under $35 yay

if its too expensive

| try this | why |
|---|---|
| buy the parts from the same place that makes the boards | then u only pay shipping once |
| get the cheapest 0805 lights and resistors | any 0805 ones fit |
| buy batteries from a store near u | theyre the most expensive small thing |

kicad also made its own parts list its in hardware/fab/tinydie-bom.csv
