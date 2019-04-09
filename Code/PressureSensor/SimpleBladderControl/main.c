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
Graphics_Button btn_inflate;
Graphics_Button btn_deflate;

// Graphic library context
Graphics_Context g_sContext;


void Delay();
void boardInit(void);
void clockInit(void);
void timerInit(void);
void draw_main_page(void);
void init_buttons(void);
void set_inflate(bool on);
void set_deflate(bool on);
void configure_GPIO_pins(void);

const uint8_t PORT_INFLATE = GPIO_PORT_P4;
const uint16_t PIN_INFLATE = GPIO_PIN1;
const uint8_t PORT_DEFLATE = GPIO_PORT_P3;
const uint16_t PIN_DEFLATE = GPIO_PIN5;

#define DEBOUNCE_TIME 50000
bool g_debouncing = false;

#if defined(__IAR_SYSTEMS_ICC__)
int16_t __low_level_init(void) {
    // Stop WDT (Watch Dog Timer)
    WDTCTL = WDTPW + WDTHOLD;
    return(1);
}

#endif

void main(void)
{

    bool inflating = false;
    bool deflating = false;
    // Initialization routines
    boardInit();
    clockInit();
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

    // Loop to detect touch
    while(1)
    {
        touch_updateCurrentTouch(&g_sTouchContext);

        if(g_sTouchContext.touch)
        {

            if(Graphics_isButtonSelected(&btn_inflate,
                                              g_sTouchContext.x,
                                              g_sTouchContext.y))
            {
                if (inflating) {
                    Graphics_drawButton(&g_sContext, &btn_inflate);
                    inflating = false;
                } else {
                    Graphics_drawSelectedButton(&g_sContext, &btn_inflate);
                    inflating = true;
                }
                set_inflate(inflating);

            }
            else if(Graphics_isButtonSelected(&btn_deflate,
                                                   g_sTouchContext.x,
                                                   g_sTouchContext.y))
            {
                if (deflating) {
                    Graphics_drawButton(&g_sContext, &btn_deflate);
                    deflating = false;
                } else {
                    Graphics_drawSelectedButton(&g_sContext, &btn_deflate);
                    deflating = true;
                }
                set_deflate(deflating);
            }

        }
    }
}

void init_buttons(void)
{
    btn_inflate.xMin = 80;
    btn_inflate.xMax = 150;
    btn_inflate.yMin = 80;
    btn_inflate.yMax = 120;
    btn_inflate.borderWidth = 1;
    btn_inflate.selected = false;
    btn_inflate.fillColor = GRAPHICS_COLOR_RED;
    btn_inflate.borderColor = GRAPHICS_COLOR_RED;
    btn_inflate.selectedColor = GRAPHICS_COLOR_BLACK;
    btn_inflate.textColor = GRAPHICS_COLOR_BLACK;
    btn_inflate.selectedTextColor = GRAPHICS_COLOR_RED;
    btn_inflate.textXPos = 100;
    btn_inflate.textYPos = 90;
    btn_inflate.text = "inflate";
    btn_inflate.font = &g_sFontCm18;

    btn_deflate.xMin = 180;
    btn_deflate.xMax = 250;
    btn_deflate.yMin = 80;
    btn_deflate.yMax = 120;
    btn_deflate.borderWidth = 1;
    btn_deflate.selected = false;
    btn_deflate.fillColor = GRAPHICS_COLOR_RED;
    btn_deflate.borderColor = GRAPHICS_COLOR_RED;
    btn_deflate.selectedColor = GRAPHICS_COLOR_BLACK;
    btn_deflate.textColor = GRAPHICS_COLOR_BLACK;
    btn_deflate.selectedTextColor = GRAPHICS_COLOR_RED;
    btn_deflate.textXPos = 200;
    btn_deflate.textYPos = 90;
    btn_deflate.text = "deflate";
    btn_deflate.font = &g_sFontCm18;

}

void draw_main_page(void)
{
    Graphics_setForegroundColor(&g_sContext, GRAPHICS_COLOR_RED);
    Graphics_setBackgroundColor(&g_sContext, GRAPHICS_COLOR_BLACK);
    Graphics_clearDisplay(&g_sContext);
    Graphics_drawStringCentered(&g_sContext, "Bladder Control",
                                AUTO_STRING_LENGTH,
                                159,
                                45,
                                TRANSPARENT_TEXT);

    Graphics_drawButton(&g_sContext, &btn_inflate);
    Graphics_drawButton(&g_sContext, &btn_deflate);

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

void set_inflate(bool on)
{
    if (on) {
        GPIO_setOutputHighOnPin(PORT_INFLATE, PIN_INFLATE);
    } else {
        GPIO_setOutputLowOnPin(PORT_INFLATE, PIN_INFLATE);
    }
}

void set_deflate(bool on)
{
    if (on) {
        GPIO_setOutputHighOnPin(PORT_DEFLATE, PIN_DEFLATE);
    } else {
        GPIO_setOutputLowOnPin(PORT_DEFLATE, PIN_DEFLATE);
    }
}

