#include <stdio.h>
#include "grlib.h"
#include "button.h"
#include "driverlib.h"
#include "touch_F5529LP.h"
#include "LcdDriver/kitronix320x240x16_ssd2119_spi.h"
#include "SSC_I2C_Pressure.h"
#include "gui/gui.h"
#include "Switches.h"

// Touchscreen
touch_context g_sTouchContext;
#define TOUCHSCREEN_CHECK_MS 100
extern bool g_touched;

// Graphics
Graphics_Context g_sContext;

// Pressure control
uint16_t g_high_mpsi = 400;
uint16_t g_low_mpsi = 100;
uint16_t g_mpsi = 0;

bool g_cycling = false;
bool g_inflating = false;
bool g_deflating = false;
bool g_change_detected = false;

void timer_init(void);
void timer_start(void);
void timer_stop(void);

#define PRESSURE_CHECK_MS 250



void init_clocks(void);
void set_inflate(bool on);
void set_deflate(bool on);
void configure_GPIO_pins(void);

const uint8_t PORT_INFLATE = GPIO_PORT_P1;
const uint16_t PIN_INFLATE = GPIO_PIN4;
const uint8_t PORT_DEFLATE = GPIO_PORT_P1;
const uint16_t PIN_DEFLATE = GPIO_PIN5;

#define SW_CYCLE SW_UL
#define SW_INFLATE SW_LL
#define SW_CONFIG SW_UR
#define SW_DEFLATE SW_LR
#define SW_PLUS SW_UL
#define SW_MINUS SW_LL
#define SW_CONTROL SW_UR
#define SW_HIGHLOW SW_LR

void main(void)
{
    uint16_t last_mpsi = 0;

    init_clocks();
    timer_init();
    ssc_init();
    configure_GPIO_pins();
    sw_init();

    // LCD setup using Graphics Library API calls
    Kitronix320x240x16_SSD2119Init();
    Graphics_initContext(&g_sContext, &g_sKitronix320x240x16_SSD2119);
    Graphics_setBackgroundColor(&g_sContext, GRAPHICS_COLOR_BLACK);
    Graphics_setFont(&g_sContext, &g_sFontCmss20b);
    Graphics_clearDisplay(&g_sContext);
    //touch_initInterface();

    __bis_SR_register(GIE);

    gui_init();
    gui_display();
    timer_start();
    while(1)
    {
        __bis_SR_register(LPM0_bits + GIE);
        g_mpsi = ssc_get_last_psi();
        if (g_mpsi != last_mpsi) {
            if (gui_is_mode_main()) {
                // only update mpsi if on main panel
                gui_update_mpsi();
            }
            last_mpsi = g_mpsi;
        }
        if (g_cycling) {
            if (!g_inflating && g_mpsi <= g_low_mpsi) {
                set_inflate(true);
                set_deflate(false);
                g_change_detected = true;
            } else if (!g_deflating && g_mpsi >= g_high_mpsi) {
                set_deflate(true);
                set_inflate(false);
                g_change_detected = true;
            }
        }
        /*
        if (g_touched) {
            touch_updateCurrentTouch(&g_sTouchContext);
            g_touched = false;
            if (gui_is_mode_config()) {
                sw_status[SW_PLUS] = gui_is_plus(g_sTouchContext.x, g_sTouchContext.y);
                sw_status[SW_MINUS] = gui_is_minus(g_sTouchContext.x, g_sTouchContext.y);
                sw_status[SW_CONTROL] = gui_is_main(g_sTouchContext.x, g_sTouchContext.y);
                sw_status[SW_HIGHLOW] = gui_is_highlow(g_sTouchContext.x, g_sTouchContext.y);
            }
            if (gui_is_mode_main()) {
                sw_status[SW_INFLATE] = gui_is_inflate(g_sTouchContext.x, g_sTouchContext.y);
                sw_status[SW_DEFLATE] = gui_is_deflate(g_sTouchContext.x, g_sTouchContext.y);
                sw_status[SW_CYCLE] = gui_is_cycle(g_sTouchContext.x, g_sTouchContext.y);
                sw_status[SW_CONFIG] = gui_is_config(g_sTouchContext.x, g_sTouchContext.y);
            }

        }
        */
        if (gui_is_mode_main()) {
            if(sw_status[SW_INFLATE])
            {
                set_inflate(!g_inflating);
                gui_toggle_inflate();
                sw_status[SW_INFLATE] = false;
            }
            if (sw_status[SW_DEFLATE]) {
                set_deflate(!g_deflating);
                gui_toggle_deflate();
                sw_status[SW_DEFLATE] = false;
            }
            if (sw_status[SW_CYCLE]) {
                if (g_cycling) {
                    set_inflate(false);
                    set_deflate(false);
                }
                g_cycling = !g_cycling;
                gui_toggle_cycle();
                sw_status[SW_CYCLE] = false;
            }
            if (sw_status[SW_CONFIG]) {
                gui_switch_to_config();
                sw_status[SW_CONFIG] = false;
            }
        }
        else {
            if (sw_status[SW_CONTROL]) {
                gui_switch_to_main();
                sw_status[SW_CONTROL] = false;
            }
            if (sw_status[SW_HIGHLOW]) {
                gui_toggle_highlow();
                sw_status[SW_HIGHLOW] = false;
            }
            if (sw_status[SW_PLUS]) {
                if (gui_is_highmode()) {
                    g_high_mpsi++;
                } else if (g_low_mpsi < g_high_mpsi) {
                    g_low_mpsi++;
                }
                gui_update_mpsi();
                sw_status[SW_PLUS] = false;
            }
            if (sw_status[SW_MINUS]) {
                if (gui_is_highmode()) {
                    if (g_high_mpsi > 0 && g_high_mpsi > g_low_mpsi) {
                        g_high_mpsi--;
                    }
                } else {
                    if (g_low_mpsi > 0) {
                        g_low_mpsi--;
                    }
                }
                gui_update_mpsi();
                sw_status[SW_MINUS] = false;
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

void Delay(){
    __delay_cycles(SYSTEM_CLOCK_SPEED * 3);
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

    // CCR1 will be used for checking touchscreen
    Timer_A_clearCaptureCompareInterrupt(TIMER_A1_BASE,
        TIMER_A_CAPTURECOMPARE_REGISTER_1
        );

    initCompParam.compareRegister = TIMER_A_CAPTURECOMPARE_REGISTER_1;
    initCompParam.compareInterruptEnable = TIMER_A_CAPTURECOMPARE_INTERRUPT_ENABLE;
    initCompParam.compareOutputMode = TIMER_A_OUTPUTMODE_OUTBITVALUE;
    initCompParam.compareValue = TOUCHSCREEN_CHECK_MS;
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

// TIMER1_A1 used for other CCR1+ interrupts on TIMER_A1_BASE
#if defined(__TI_COMPILER_VERSION__) || defined(__IAR_SYSTEMS_ICC__)
#pragma vector=TIMER1_A1_VECTOR
__interrupt
#elif defined(__GNUC__)
__attribute__((interrupt(TIMER1_A1_VECTOR)))
#endif
void TIMER1_A1_ISR (void)
{
    uint16_t next_compare_val;
    switch (__even_in_range(TA1IV,12)) {
    case TA1IV_TACCR1:
        next_compare_val = Timer_A_getCaptureCompareCount(TIMER_A1_BASE,
            TIMER_A_CAPTURECOMPARE_REGISTER_1)
            + TOUCHSCREEN_CHECK_MS;
        Timer_A_setCompareValue(TIMER_A1_BASE,
                                TIMER_A_CAPTURECOMPARE_REGISTER_1,
                                next_compare_val);
        touch_start_adc();
        break;
    };
    Timer_A_clearTimerInterrupt(TIMER_A1_BASE);
}
