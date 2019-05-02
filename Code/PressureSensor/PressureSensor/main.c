#include <driverlib.h>
#include <stdio.h>
#include "SSC_I2C_Pressure.h"



int main(void)
{
    int psi = 0;
    WDT_A_hold(WDT_A_BASE);

    ssc_init();

    while (1) {

        ssc_start_read();
        __bis_SR_register(LPM0_bits + GIE);

        psi = ssc_get_last_psi();
        printf("psi - %d\n", psi);
    }


}


