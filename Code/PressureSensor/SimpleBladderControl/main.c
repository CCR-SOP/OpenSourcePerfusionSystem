/* --COPYRIGHT--,BSD
 * Copyright (c) 2016, Texas Instruments Incorporated
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * *  Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 *
 * *  Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * *  Neither the name of Texas Instruments Incorporated nor the names of
 *    its contributors may be used to endorse or promote products derived
 *    from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
 * THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
 * OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
 * OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
 * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 * --/COPYRIGHT--*/
#include <msp430f5529.h>
#include "grlib.h"
#include "button.h"
#include "driverlib.h"
#include "touch_F5529LP.h"
#include "LcdDriver/kitronix320x240x16_ssd2119_spi.h"
#include "Images/images.h"

//Touch screen context
touch_context g_sTouchContext;

#define DEBOUNCE_TOUCHES 100
Graphics_Button btn_inflate;
Graphics_Button btn_deflate;
Graphics_Button btn_cycle;

int8_t lbl_inflate[] = "Inflate";
int8_t lbl_deflate[] = "Deflate";
int8_t lbl_cycle[] = "Cycle";

bool g_cycling = false;
bool g_inflating = false;
bool g_deflating = false;
bool g_change_detected = false;

// Cycling
#define COMPARE_VALUE 3000
void timerInit(void);
void timerStart(void);
void timerStop(void);

// Graphic library context
Graphics_Context g_sContext;


void Delay();
void boardInit(void);
void clockInit(void);
void draw_main_page(void);
void init_buttons(void);
void set_inflate(bool on);
void set_deflate(bool on);
void configure_GPIO_pins(void);

const uint8_t PORT_INFLATE = GPIO_PORT_P1;
const uint16_t PIN_INFLATE = GPIO_PIN4;
const uint8_t PORT_DEFLATE = GPIO_PORT_P1;
const uint16_t PIN_DEFLATE = GPIO_PIN5;


#if defined(__IAR_SYSTEMS_ICC__)
int16_t __low_level_init(void) {
    // Stop WDT (Watch Dog Timer)
    WDTCTL = WDTPW + WDTHOLD;
    return(1);
}

#endif



void main(void)
{

    // Initialization routines
    boardInit();
    clockInit();
    timerInit();
    init_buttons();

    // LCD setup using Graphics Library API calls
    Kitronix320x240x16_SSD2119Init();
    Graphics_initContext(&g_sContext, &g_sKitronix320x240x16_SSD2119);
    Graphics_setBackgroundColor(&g_sContext, GRAPHICS_COLOR_BLACK);
    Graphics_setFont(&g_sContext, &g_sFontCmss20b);
    Graphics_clearDisplay(&g_sContext);

    //
    touch_initInterface();

    configure_GPIO_pins();

    draw_main_page();

    //Enter LPM0, enable interrupts
    __bis_SR_register(GIE);

    // Loop to detect touch
    int consecutive_touches = 0;
    while(1)
    {
        touch_updateCurrentTouch(&g_sTouchContext);

        if(g_sTouchContext.touch) {
            consecutive_touches++;
        } else {
            consecutive_touches = 0;
        }

        if (consecutive_touches == DEBOUNCE_TOUCHES)
        {

            g_change_detected = true;
            if(Graphics_isButtonSelected(&btn_inflate,
                                              g_sTouchContext.x,
                                              g_sTouchContext.y))
            {
                set_inflate(!g_inflating);
            }
            else if(Graphics_isButtonSelected(&btn_deflate,
                                                   g_sTouchContext.x,
                                                   g_sTouchContext.y))
            {
                set_deflate(!g_deflating);
            }
            else if(Graphics_isButtonSelected(&btn_cycle,
                                                   g_sTouchContext.x,
                                                   g_sTouchContext.y))
            {
                if (g_cycling) {
                    timerStop();
                    set_inflate(false);
                    set_deflate(false);
                } else {
                    timerStart();
                }
                g_cycling = !g_cycling;
            }

        }
        if (g_change_detected) {
            if (g_inflating) {
                Graphics_drawButton(&g_sContext, &btn_inflate);
            } else {
                Graphics_drawSelectedButton(&g_sContext, &btn_inflate);
            }
            if (g_deflating) {
                Graphics_drawButton(&g_sContext, &btn_deflate);
            } else {
                Graphics_drawSelectedButton(&g_sContext, &btn_deflate);
            }
            if (g_cycling) {
                Graphics_drawButton(&g_sContext, &btn_cycle);
            } else {
                Graphics_drawSelectedButton(&g_sContext, &btn_cycle);
            }
        }
        g_change_detected = false;
    }
}

void create_button(Graphics_Button* btn, int x, int y, int w, int h, int8_t* lbl)
{
    btn->xMin = x;
    btn->xMax = x + w;
    btn->yMin = y;
    btn->yMax = y + h;

    btn->borderWidth = 1;
    btn->selected = false;
    btn->fillColor = GRAPHICS_COLOR_RED;
    btn->borderColor = GRAPHICS_COLOR_RED;
    btn->selectedColor = GRAPHICS_COLOR_BLACK;
    btn->textColor = GRAPHICS_COLOR_BLACK;
    btn->selectedTextColor = GRAPHICS_COLOR_RED;

    btn->textXPos = btn->xMin + 20;
    btn->textYPos = btn->yMin + 15;
    btn->text = lbl;
    btn->font = &g_sFontCm18;
}

void init_buttons(void)
{
    int x = 40, width = 100, y = 60, height = 60;
    create_button(&btn_inflate, x, y, width, height, lbl_inflate);
    create_button(&btn_deflate, x + width + 10, y, width, height, lbl_deflate);
    create_button(&btn_cycle, x, y + height + 10, width, height, lbl_cycle);
}

void draw_main_page(void)
{
    Graphics_setForegroundColor(&g_sContext, GRAPHICS_COLOR_RED);
    Graphics_setBackgroundColor(&g_sContext, GRAPHICS_COLOR_BLACK);
    Graphics_clearDisplay(&g_sContext);
    Graphics_drawStringCentered(&g_sContext, "Bladder Control",
                                AUTO_STRING_LENGTH,
                                159,
                                20,
                                TRANSPARENT_TEXT);

    Graphics_drawButton(&g_sContext, &btn_inflate);
    Graphics_drawButton(&g_sContext, &btn_deflate);
    Graphics_drawButton(&g_sContext, &btn_cycle);

}

void boardInit(void)
{
    // Setup XT1 and XT2
    GPIO_setAsPeripheralModuleFunctionInputPin(
        GPIO_PORT_P5,
        GPIO_PIN2 + GPIO_PIN3 +
        GPIO_PIN4 + GPIO_PIN5
        );
}

void clockInit(void)
{
    UCS_setExternalClockSource(
        32768,
        0);

    // Set Vcore to accomodate for max. allowed system speed
    PMM_setVCore(
        PMM_CORE_LEVEL_3
        );

    // Use 32.768kHz XTAL as reference
    UCS_turnOnLFXT1(
        UCS_XT1_DRIVE_3,
        UCS_XCAP_3
        );

    // Set system clock to max (25MHz)
    UCS_initFLLSettle(
        25000,
        762
        );

    SFR_enableInterrupt(
        SFR_OSCILLATOR_FAULT_INTERRUPT
        );
}

void Delay(){
    __delay_cycles(SYSTEM_CLOCK_SPEED * 3);
}

void configure_GPIO_pins(void)
{
    GPIO_setAsOutputPin(PORT_INFLATE, PIN_INFLATE);
    GPIO_setAsOutputPin(PORT_DEFLATE, PIN_DEFLATE);
}

void timerInit(void)
{
    //Start timer in continuous mode sourced by SMCLK
    Timer_A_initContinuousModeParam initContParam = {0};
    initContParam.clockSource = TIMER_A_CLOCKSOURCE_ACLK;
    initContParam.clockSourceDivider = TIMER_A_CLOCKSOURCE_DIVIDER_32;
    initContParam.timerInterruptEnable_TAIE = TIMER_A_TAIE_INTERRUPT_DISABLE;
    initContParam.timerClear = TIMER_A_DO_CLEAR;
    initContParam.startTimer = false;
    Timer_A_initContinuousMode(TIMER_A1_BASE, &initContParam);

    //Initialize compare mode
    Timer_A_clearCaptureCompareInterrupt(TIMER_A1_BASE,
        TIMER_A_CAPTURECOMPARE_REGISTER_0
        );

    Timer_A_initCompareModeParam initCompParam = {0};
    initCompParam.compareRegister = TIMER_A_CAPTURECOMPARE_REGISTER_0;
    initCompParam.compareInterruptEnable = TIMER_A_CAPTURECOMPARE_INTERRUPT_ENABLE;
    initCompParam.compareOutputMode = TIMER_A_OUTPUTMODE_OUTBITVALUE;
    initCompParam.compareValue = COMPARE_VALUE;
    Timer_A_initCompareMode(TIMER_A1_BASE, &initCompParam);


}

void timerStart(void)
{
    Timer_A_startCounter(TIMER_A1_BASE, TIMER_A_CONTINUOUS_MODE);
    Timer_A_enableInterrupt(TIMER_A1_BASE);
}

void timerStop(void)
{
    Timer_A_disableInterrupt(TIMER_A1_BASE);
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

//******************************************************************************
//
//This is the TIMER1_A3 interrupt vector service routine.
//
//******************************************************************************
#if defined(__TI_COMPILER_VERSION__) || defined(__IAR_SYSTEMS_ICC__)
#pragma vector=TIMER1_A0_VECTOR
__interrupt
#elif defined(__GNUC__)
__attribute__((interrupt(TIMER1_A0_VECTOR)))
#endif
void TIMER1_A0_ISR (void)
{
    uint16_t compVal = Timer_A_getCaptureCompareCount(TIMER_A1_BASE,
            TIMER_A_CAPTURECOMPARE_REGISTER_0)
            + COMPARE_VALUE;

    g_change_detected = true;
    if (g_inflating) {
        set_inflate(false);
        set_deflate(true);
    } else {
        set_inflate(true);
        set_deflate(false);
    }
    //Add Offset to CCR0
    Timer_A_setCompareValue(TIMER_A1_BASE,
        TIMER_A_CAPTURECOMPARE_REGISTER_0,
        compVal
        );
}
