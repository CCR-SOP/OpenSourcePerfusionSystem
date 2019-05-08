#include <driverlib.h>
#include <stdio.h>
#include "SSC_I2C_Pressure.h"



int main(void)
{
    int psi = 0;
    WDT_A_hold(WDT_A_BASE);


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
    UCS_initFLLSettle(25000, 762);

    UCS_initClockSignal(UCS_SMCLK, UCS_DCOCLK_SELECT, UCS_CLOCK_DIVIDER_16);

    SFR_enableInterrupt(SFR_OSCILLATOR_FAULT_INTERRUPT);

    ssc_init();

    while (1) {

        ssc_start_read();
        __bis_SR_register(LPM0_bits + GIE);

        psi = ssc_get_last_psi();
        printf("psi - %d\n", psi);
    }


}


