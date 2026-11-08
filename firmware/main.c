/*
 * TinyDie firmware - ATtiny412, CR2032-powered electronic die.
 *
 * Pinout (SOIC-8):
 *   1 VDD   2 PA6 -> LED group D (centre)
 *   3 PA7 <- button (to GND, internal pull-up)
 *   4 PA1 -> LED group A (top-left + bottom-right)
 *   5 PA2 -> LED group B (top-right + bottom-left)
 *   6 PA0  = UPDI (programming)
 *   7 PA3 -> LED group C (middle-left + middle-right)
 *   8 GND
 *
 * Press the button: the die rolls while held, slows down on release,
 * shows the result for a few seconds, then enters power-down sleep
 * (~0.1 uA) until the next press. No power switch needed.
 */
#define F_CPU 3333333UL /* default: 20 MHz / 6 */

#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <util/delay.h>

#define LA PIN1_bm
#define LB PIN2_bm
#define LC PIN3_bm
#define LD PIN6_bm
#define LED_MASK (LA | LB | LC | LD)
#define BTN PIN7_bm

#define SHOW_MS 4000u

static const uint8_t face[7] = {
    0,
    LD,                /* 1 */
    LA,                /* 2 */
    LA | LD,           /* 3 */
    LA | LB,           /* 4 */
    LA | LB | LD,      /* 5 */
    LA | LB | LC,      /* 6 */
};

static uint16_t rng = 0xACE1;

static uint8_t roll(void)
{
    uint8_t v;
    do { /* xorshift16, rejection-sample 3 bits to 1..6 */
        rng ^= rng << 7;
        rng ^= rng >> 9;
        rng ^= rng << 8;
        v = rng & 7;
    } while (v > 5);
    return v + 1;
}

static void show(uint8_t n)
{
    PORTA.OUT = (PORTA.OUT & ~LED_MASK) | face[n];
}

static inline uint8_t pressed(void) { return !(PORTA.IN & BTN); }

static void delay_ms(uint16_t ms)
{
    while (ms--) _delay_ms(1);
}

ISR(PORTA_PORT_vect)
{
    PORTA.INTFLAGS = BTN; /* wake only */
}

int main(void)
{
    PORTA.DIRSET = LED_MASK;
    PORTA.OUTCLR = LED_MASK;
    PORTA.PIN7CTRL = PORT_PULLUPEN_bm | PORT_ISC_BOTHEDGES_gc;

    /* Free-running timer: its count at the moment of release seeds the RNG. */
    TCA0.SINGLE.CTRLA = TCA_SINGLE_ENABLE_bm;

    set_sleep_mode(SLEEP_MODE_PWR_DOWN);
    sei();

    /* Power-on self test: light every face once. */
    for (uint8_t i = 1; i <= 6; i++) { show(i); delay_ms(120); }
    show(0);

    for (;;) {
        if (pressed()) {
            /* Rolling while held. */
            while (pressed()) {
                rng ^= TCA0.SINGLE.CNT;
                if (!rng) rng = 0xACE1;
                show(roll());
                delay_ms(50);
            }
            delay_ms(20); /* debounce release */

            /* Slow down. */
            for (uint16_t d = 40; d < 300; d += d / 4) {
                show(roll());
                delay_ms(d);
            }
            show(roll());

            /* Hold the result, abort early on a new press. */
            for (uint16_t t = 0; t < SHOW_MS / 10 && !pressed(); t++)
                delay_ms(10);
            if (pressed()) continue;
        }

        show(0);
        sleep_enable();
        sleep_cpu(); /* wakes on button edge */
        sleep_disable();
        delay_ms(20); /* debounce press */
    }
}
