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


#if defined(__TI_COMPILER_VERSION__) || defined(__IAR_SYSTEMS_ICC__)
#pragma vector=USCI_B1_VECTOR
__interrupt
#elif defined(__GNUC__)
__attribute__((interrupt(USCI_B1_VECTOR)))
#endif
void USCI_B1_ISR (void)
{
    switch (__even_in_range(UCB1IV,12)){
        case USCI_I2C_UCRXIFG:
        {
            if (ssc_process_byte()) {
                __bic_SR_register_on_exit(LPM0_bits);
            }
            break;
        }
    }
}
