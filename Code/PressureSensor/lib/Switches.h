/*
 * Switches.h
 *
 *  Created on: May 21, 2019
 *      Author: kakareka
 */

#ifndef SWITCHES_H_
#define SWITCHES_H_

#include <stdbool.h>

extern bool sw_status[6];
void sw_init(void);

#define SW_UL 0
#define SW_ML 1
#define SW_LL 2
#define SW_UR 3
#define SW_MR 4
#define SW_LR 5

#endif /* SWITCHES_H_ */
