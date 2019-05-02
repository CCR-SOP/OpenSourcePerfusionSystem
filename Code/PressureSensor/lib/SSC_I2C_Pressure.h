/*
 * SSC_I2C_Pressure.h
 *
 *  Created on: Apr 26, 2019
 *      Author: kakareka
 */

#ifndef SSC_I2C_PRESSURE_H_
#define SSC_I2C_PRESSURE_H_

#include <driverlib.h>

// JWK, SSC I2C address is hard-coded
#define SENSOR_ADDRESS 0x28
#define BYTES_PER_READING 2
#define I2C_BASE USCI_B1_BASE

uint16_t convert_to_psi(uint8_t msb, uint8_t lsb);
void ssc_init(void);
void ssc_start_read(void);
int ssc_get_last_psi(void);
bool ssc_process_byte(void);

#endif /* SSC_I2C_PRESSURE_H_ */
