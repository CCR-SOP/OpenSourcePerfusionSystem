#include "SSC_I2C_Pressure.h"
#include "driverlib.h"

#define I2C_BASE USCI_B1_BASE
//#define SSCDANT030PG2A3
#define SSCMRND030PG2A3

// JWK, min/max counts from datasheet and Honeywell I2C (10% calibration)
// psi/counts = (SENSOR_MAX_PSI - SENSOR_MIN_PSI) / (float)(SENSOR_MAX_COUNTS - SENSOR_MIN_COUNTS);

#ifdef SSCDANT030PG2A3
const uint8_t SENSOR_ADDRESS = 0x28;
#define SENSOR_MAX_COUNTS  0x3999
#define SENSOR_MIN_COUNTS  0x0666
#define SENSOR_MAX_PSI 30
#define SENSOR_MIN_PSI 0
#endif

#ifdef SSCMRNN015PA3A3
const uint8_t SENSOR_ADDRESS = 0x38;
#define SENSOR_MAX_COUNTS 0x3999
#define SENSOR_MIN_COUNTS 0x0666
#define SENSOR_MAX_PSI 15
#define SENSOR_MIN_PSI 0
#endif

#ifdef SSCMRND030PG2A3
const uint8_t SENSOR_ADDRESS = 0x28;
#define SENSOR_MAX_COUNTS 0x3999
#define SENSOR_MIN_COUNTS 0x0666
#define SENSOR_MAX_PSI 30
#define SENSOR_MIN_PSI 0
#endif

const float SENSOR_RATIO = (float)(SENSOR_MAX_PSI - SENSOR_MIN_PSI) / (float)(SENSOR_MAX_COUNTS - SENSOR_MIN_COUNTS);


bool g_newread = true;
uint8_t msb, lsb;
uint16_t last_psi = 0;
uint16_t convert_to_psi(uint8_t msb, uint8_t lsb);

void ssc_init(void)
{

    //Assign I2C pins to USCI_B0
    GPIO_setAsPeripheralModuleFunctionInputPin(
        GPIO_PORT_P4,
        GPIO_PIN1 + GPIO_PIN2
        );


    USCI_B_I2C_initMasterParam param = {0};
    param.selectClockSource = USCI_B_I2C_CLOCKSOURCE_SMCLK;
    param.i2cClk = UCS_getSMCLK();
    param.dataRate = USCI_B_I2C_SET_DATA_RATE_100KBPS;
    USCI_B_I2C_initMaster(I2C_BASE, &param);

    USCI_B_I2C_setSlaveAddress(I2C_BASE, SENSOR_ADDRESS);
    USCI_B_I2C_setMode(I2C_BASE, USCI_B_I2C_RECEIVE_MODE);

    USCI_B_I2C_enable(I2C_BASE);
    USCI_B_I2C_enableInterrupt(I2C_BASE, USCI_B_I2C_RECEIVE_INTERRUPT);

    while (USCI_B_I2C_isBusBusy(I2C_BASE )) ;
}

void ssc_start_read(void)
{
    uint16_t tmp = convert_to_psi(msb, lsb);
    if (tmp != 0xC0) {
        last_psi = tmp;
    }
    g_newread = true;

    USCI_B_I2C_masterReceiveMultiByteStart(I2C_BASE);
}

uint16_t convert_to_psi(uint8_t msb, uint8_t lsb)
{
    uint16_t psi = 0xC0;
    uint8_t status = (msb & 0xC0);

    if (!status) {
        uint16_t counts = ((msb & 0x3F) << 8) | lsb;
        float milli_psi = ((float)(counts - SENSOR_MIN_COUNTS) * SENSOR_RATIO + SENSOR_MIN_PSI) * 1000.0;
        psi = (uint16_t)milli_psi;
    }
    return psi;
}

int ssc_get_last_psi(void)
{
    return last_psi;
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
                msb = USCI_B_I2C_masterReceiveMultiByteFinish(I2C_BASE);
                g_newread = false;
            } else {
                lsb = USCI_B_I2C_masterReceiveMultiByteNext(I2C_BASE);
                __bic_SR_register_on_exit(LPM0_bits);

            }
            break;
        }
    }
}
