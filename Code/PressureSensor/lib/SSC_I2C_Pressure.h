/*
 * SSC_I2C_Pressure.h
 *
 *  Created on: Apr 26, 2019
 *      Author: kakareka
 */

#ifndef SSC_I2C_PRESSURE_H_
#define SSC_I2C_PRESSURE_H_

void ssc_init(void);
void ssc_start_read(void);
int ssc_get_last_psi(void);

#endif /* SSC_I2C_PRESSURE_H_ */
