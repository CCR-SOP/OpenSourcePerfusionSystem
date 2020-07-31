#include <stdio.h>
#include "driverlib.h"
#include "SSC_I2C_Pressure.h"

// Pressure control
bool g_cycling = false;
bool g_inflating = false;
bool g_deflating = false;
bool g_change_detected = false;

void timer_init(void);
void timer_start(void);
void timer_stop(void);

#define PRESSURE_CHECK_MS 250
uint16_t g_high_mpsi = 40;
uint16_t g_low_mpsi = 8;

void Delay();
void init_clocks(void);
void set_inflate(bool on);
void set_deflate(bool on);
void configure_GPIO_pins(void);

const uint8_t PORT_INFLATE = GPIO_PORT_P1;
const uint16_t PIN_INFLATE = GPIO_PIN4;
const uint8_t PORT_DEFLATE = GPIO_PORT_P1;
const uint16_t PIN_DEFLATE = GPIO_PIN5;

void main(void)
{

    init_clocks();
    timer_init();
    ssc_init();

    configure_GPIO_pins();

    __bis_SR_register(GIE);

    uint16_t last_mpsi = 0, mpsi = 0;

    g_cycling = true;

    timer_start();
    while(1)
    {
        __bis_SR_register(LPM0_bits + GIE);
        mpsi = ssc_get_last_psi();
        if (mpsi != last_mpsi) {
            last_mpsi = mpsi;
        }
        if (g_cycling) {
            if (!g_inflating && mpsi <= g_low_mpsi) {
                set_inflate(true);
                set_deflate(false);
                g_change_detected = true;
            } else if (!g_deflating && mpsi >= g_high_mpsi) {
                set_deflate(true);
                set_inflate(false);
                g_change_detected = true;
            }
        }
    }

}

void init_clocks(void)
{

    GPIO_setAsPeripheralModuleFunctionInputPin(
            GPIO_PORT_P5, GPIO_PIN2 + GPIO_PIN3 +
            GPIO_PIN4 + GPIO_PIN5);

    UCS_setExternalClockSource(32768,4000000);

    // Set Vcore to accomodate for max. allowed system speed
    PMM_setVCore(PMM_CORE_LEVEL_3);

    // Use 32.768kHz XTAL as reference
    UCS_turnOnLFXT1(UCS_XT1_DRIVE_3, UCS_XCAP_3);

    UCS_turnOnXT2(UCS_XT2_DRIVE_4MHZ_8MHZ);

    // Set system clock to max (25MHz)
    // Needed by LCD
    UCS_initFLLSettle(25000, 762);

    // Set SMCLK to about 1.5MHz for other peripherals
    // particularly the I2C
    UCS_initClockSignal(UCS_SMCLK, UCS_DCOCLK_SELECT, UCS_CLOCK_DIVIDER_16);

    SFR_enableInterrupt(SFR_OSCILLATOR_FAULT_INTERRUPT);
}

void configure_GPIO_pins(void)
{
    GPIO_setAsOutputPin(PORT_INFLATE, PIN_INFLATE);
    GPIO_setAsOutputPin(PORT_DEFLATE, PIN_DEFLATE);
}

void timer_init(void)
{
    Timer_A_initContinuousModeParam initContParam = {0};
    initContParam.clockSource = TIMER_A_CLOCKSOURCE_ACLK;
    initContParam.clockSourceDivider = TIMER_A_CLOCKSOURCE_DIVIDER_32;
    initContParam.timerInterruptEnable_TAIE = TIMER_A_TAIE_INTERRUPT_DISABLE;
    initContParam.timerClear = TIMER_A_DO_CLEAR;
    initContParam.startTimer = false;
    Timer_A_initContinuousMode(TIMER_A1_BASE, &initContParam);

    // CCR0 will be used for checking current pressure
    Timer_A_clearCaptureCompareInterrupt(TIMER_A1_BASE,
        TIMER_A_CAPTURECOMPARE_REGISTER_0
        );

    Timer_A_initCompareModeParam initCompParam = {0};
    initCompParam.compareRegister = TIMER_A_CAPTURECOMPARE_REGISTER_0;
    initCompParam.compareInterruptEnable = TIMER_A_CAPTURECOMPARE_INTERRUPT_ENABLE;
    initCompParam.compareOutputMode = TIMER_A_OUTPUTMODE_OUTBITVALUE;
    initCompParam.compareValue = PRESSURE_CHECK_MS;
    Timer_A_initCompareMode(TIMER_A1_BASE, &initCompParam);
}

void timer_start(void)
{
    Timer_A_startCounter(TIMER_A1_BASE, TIMER_A_CONTINUOUS_MODE);
}

void timer_stop(void)
{
    Timer_A_stop(TIMER_A1_BASE);
}


void set_inflate(bool on)
{
    if (on) {
        GPIO_setOutputHighOnPin(PORT_INFLATE, PIN_INFLATE);
    } else {
        GPIO_setOutputLowOnPin(PORT_INFLATE, PIN_INFLATE);
    }
    g_inflating = on;
}

void set_deflate(bool on)
{
    if (on) {
        GPIO_setOutputHighOnPin(PORT_DEFLATE, PIN_DEFLATE);
    } else {
        GPIO_setOutputLowOnPin(PORT_DEFLATE, PIN_DEFLATE);
    }
    g_deflating = on;
}


// Timer1_A0_VECTOR used for CCR0 only on TIMER_A1_BASE)
#if defined(__TI_COMPILER_VERSION__) || defined(__IAR_SYSTEMS_ICC__)
#pragma vector=TIMER1_A0_VECTOR
__interrupt
#elif defined(__GNUC__)
__attribute__((interrupt(TIMER1_A0_VECTOR)))
#endif
void TIMER1_A0_ISR (void)
{
    uint16_t next_compare_val;
    next_compare_val = Timer_A_getCaptureCompareCount(
                        TIMER_A1_BASE,
                        TIMER_A_CAPTURECOMPARE_REGISTER_0)
                        + PRESSURE_CHECK_MS;
    Timer_A_setCompareValue(TIMER_A1_BASE,
                            TIMER_A_CAPTURECOMPARE_REGISTER_0,
                            next_compare_val);

    ssc_start_read();
    Timer_A_clearTimerInterrupt(TIMER_A1_BASE);
}
