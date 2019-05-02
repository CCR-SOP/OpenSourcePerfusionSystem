#include "SSC_I2C_Pressure.h"

unsigned char bytes_to_read = 0;

// JWK, min/max from datasheet and Honeywell I2C (10% calibration)
// JWK assume part SSCDANT030PG2A3
const uint16_t SENSOR_MAX_COUNTS = 0x3999;
const uint16_t SENSOR_MIN_COUNTS = 0x0666;
const uint16_t SENSOR_MAX_PSI  = 30;
const uint16_t SENSOR_MIN_PSI = 0;
// psi/counts = (SENSOR_MAX_PSI - SENSOR_MIN_PSI) / (float)(SENSOR_MAX_COUNTS - SENSOR_MIN_COUNTS);
// 0-30PSI, 10% - 90% 14 bit sensor (30 - 0) / (0x3999 - 0x0666)
const float SENSOR_RATIO = 0.0022888532845044634;

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
    bytes_to_read = BYTES_PER_READING;

    USCI_B_I2C_masterReceiveMultiByteStart(I2C_BASE);
}

bool ssc_process_byte(void)
{
    bool reading_complete = false;
    bytes_to_read--;

    if (bytes_to_read == 1) {
        //msb = USCI_B_I2C_masterReceiveMultiByteNext(I2C_BASE);
    }
    else {
        //lsb = USCI_B_I2C_masterReceiveMultiByteFinish(I2C_BASE);
        reading_complete = true;

    }

    return reading_complete;

}

uint16_t convert_to_psi(uint8_t msb, uint8_t lsb)
{
    uint16_t psi = 0;
    uint8_t status = (msb & 0xC0) >> 6;

    if (!status) {
        uint16_t counts = (msb << 8) | lsb;
        psi = (counts - SENSOR_MIN_COUNTS) * SENSOR_RATIO + SENSOR_MIN_PSI;
    }
    return psi;
}

int ssc_get_last_psi(void)
{
    return last_psi;
}
