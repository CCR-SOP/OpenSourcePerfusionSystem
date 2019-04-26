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
#define BYTES_PER_READING 4
#define I2C_BASE USCI_B1_BASE
// JWK, min/max from datasheet and Honeywell I2C (10% calibration)
// JWK assume part SSCDANT030PG2A3
#define SENSOR_MAX_COUNTS 0x3999
#define SENSOR_MIN_COUNTS 0x0666
#define SENSOR_MAX_PSI  30
#define SENSOR_MIN_PSI 0



int convert_to_psi(void);
void ssc_init(void);
void ssc_start_read(void);
int ssc_get_last_psi(void);
bool ssc_process_byte(void);

#endif /* SSC_I2C_PRESSURE_H_ */
