#include "SSC_I2C_Pressure.h"

unsigned char receiveBuffer[BYTES_PER_READING] = { 0x01, 0x01, 0x01, 0x01};
unsigned char *receiveBufferPointer;
unsigned char receiveCount = 0;

uint16_t last_psi;

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
    param.dataRate = USCI_B_I2C_SET_DATA_RATE_400KBPS;
    USCI_B_I2C_initMaster(I2C_BASE, &param);

    USCI_B_I2C_setSlaveAddress(I2C_BASE, SENSOR_ADDRESS);
    USCI_B_I2C_setMode(I2C_BASE, USCI_B_I2C_RECEIVE_MODE);

    USCI_B_I2C_enable(I2C_BASE);
    USCI_B_I2C_enableInterrupt(I2C_BASE, USCI_B_I2C_RECEIVE_INTERRUPT);

    while (USCI_B_I2C_isBusBusy(I2C_BASE )) ;
}

void ssc_start_read(void)
{
    receiveBufferPointer = (unsigned char *)receiveBuffer;
    receiveCount = BYTES_PER_READING;

    USCI_B_I2C_masterReceiveMultiByteStart(I2C_BASE);
}

bool ssc_process_byte(void)
{
    bool reading_complete = false;
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
        last_psi = convert_to_psi();
        reading_complete = true;

    }

    return reading_complete;

}

int convert_to_psi(void)
{
    uint16_t compensated = (receiveBuffer[2] << 8 ) | receiveBuffer[3];
    compensated = compensated >> 5;

    int psi = ( (compensated - SENSOR_MIN_COUNTS) * (SENSOR_MAX_PSI - SENSOR_MIN_PSI)
               / (SENSOR_MAX_COUNTS - SENSOR_MIN_COUNTS) ) + SENSOR_MIN_PSI;

    return psi;
}

int ssc_get_last_psi(void)
{
    return last_psi;
}
