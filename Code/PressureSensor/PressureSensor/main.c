#include <driverlib.h>
#include <stdio.h>
#include "SSC_I2C_Pressure.h"

bool g_newread = true;
uint8_t msb, lsb;

int main(void)
{
    int psi = 0;
    WDT_A_hold(WDT_A_BASE);

    ssc_init();

    while (1) {
        g_newread = true;
        ssc_start_read();
        __bis_SR_register(LPM0_bits + GIE);

        psi = convert_to_psi(msb, lsb);
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
            if (g_newread) {
                msb = UCB1RXBUF;
                g_newread = false;
                UCB1CTL1 |= UCTXSTP;  //issue stop
            } else {
                lsb = UCB1RXBUF;
                __bic_SR_register_on_exit(LPM0_bits);

            }
            break;
        }
    }
}
