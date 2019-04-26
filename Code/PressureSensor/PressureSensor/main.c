#include <driverlib.h>
#include <stdio.h>

// JWK, SSC I2C address is hard-coded
#define SENSOR_ADDRESS 0x28
#define BYTES_PER_READING 4
#define I2C_BASE USCI_B1_BASE
// JWK, min/max from datasheet and Honeywell I2C (10% calibration)
// JWK assume part SSCDANT030PG2A3
#define SENSOR_MAX_COUNTS 0x3999
#define SENSOR_MIN_COUNTS 0x0666
#define SENSOR_MAX_PSI  30
#define SENSOR_MIN_PSI 0
int convert_to_psi(void);


unsigned char receiveBuffer[BYTES_PER_READING] = { 0x01, 0x01, 0x01, 0x01};
unsigned char *receiveBufferPointer;
unsigned char receiveCount = 0;

int g_readings = 0;

void i2c_init(void);
void i2c_start(void);

int main(void)
{
    int psi = 0;
    WDT_A_hold(WDT_A_BASE);

	i2c_init();
	i2c_start();

    int last_readings = 0;
    while (1) {
        receiveBufferPointer = (unsigned char *)receiveBuffer;
        receiveCount = BYTES_PER_READING;

        USCI_B_I2C_masterReceiveMultiByteStart(I2C_BASE);
        __bis_SR_register(LPM0_bits + GIE);
        if (g_readings != last_readings) {
            psi = convert_to_psi();
            printf("psi - %d\n", psi);
            last_readings = g_readings;
        }
    }


}

int convert_to_psi(void)
{
    uint16_t compensated = (receiveBuffer[2] << 8 ) | receiveBuffer[3];
    compensated = compensated >> 5;

    int psi = ( (compensated - SENSOR_MIN_COUNTS) * (SENSOR_MAX_PSI - SENSOR_MIN_PSI)
               / (SENSOR_MAX_COUNTS - SENSOR_MIN_COUNTS) ) + SENSOR_MIN_PSI;

    return psi;
}

void i2c_init(void)
{

    //Assign I2C pins to USCI_B0
    GPIO_setAsPeripheralModuleFunctionInputPin(
        GPIO_PORT_P4,
        GPIO_PIN1 + GPIO_PIN2
        );


    USCI_B_I2C_initMasterParam param = {0};
    param.selectClockSource = USCI_B_I2C_CLOCKSOURCE_SMCLK;
    param.i2cClk = UCS_getSMCLK();
    param.dataRate = USCI_B_I2C_SET_DATA_RATE_400KBPS;
    USCI_B_I2C_initMaster(I2C_BASE, &param);

    USCI_B_I2C_setSlaveAddress(I2C_BASE, SENSOR_ADDRESS);
    USCI_B_I2C_setMode(I2C_BASE, USCI_B_I2C_RECEIVE_MODE);
}

void i2c_start(void)
{
    USCI_B_I2C_enable(I2C_BASE);
    USCI_B_I2C_enableInterrupt(I2C_BASE, USCI_B_I2C_RECEIVE_INTERRUPT);

    while (USCI_B_I2C_isBusBusy(I2C_BASE )) ;


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
            //Decrement RX byte counter
            receiveCount--;

            if (receiveCount){
                if (receiveCount == 1) {
                    //Initiate end of reception -> Receive byte with NAK
                    *receiveBufferPointer++ =
                        USCI_B_I2C_masterReceiveMultiByteFinish(I2C_BASE);
                }
                else {
                    //Keep receiving one byte at a time
                    *receiveBufferPointer++ = USCI_B_I2C_masterReceiveMultiByteNext(I2C_BASE);
                }
            }
            else {
                //Receive last byte
                *receiveBufferPointer = USCI_B_I2C_masterReceiveMultiByteNext(I2C_BASE);
                g_readings++;
                __bic_SR_register_on_exit(LPM0_bits);
            }
            break;
        }
    }
}
