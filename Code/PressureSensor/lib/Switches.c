#include "Switches.h"
#include "driverlib.h"



#define SW_TRANSITION GPIO_HIGH_TO_LOW_TRANSITION

// IRQ handlers need to be updated manually if Port changes
const uint8_t sw_ports[6] = {GPIO_PORT_P1, GPIO_PORT_P1, GPIO_PORT_P7,
                             GPIO_PORT_P2, GPIO_PORT_P2, GPIO_PORT_P2};
const uint16_t sw_pins[6] = {GPIO_PIN3, GPIO_PIN2, GPIO_PIN4,
                            GPIO_PIN4, GPIO_PIN0, GPIO_PIN2};

bool sw_status[6];

static void _setup_switch(uint8_t port, uint16_t pin)
{

    GPIO_setAsInputPinWithPullUpResistor(port, pin);
    GPIO_enableInterrupt(port, pin);
    GPIO_selectInterruptEdge(port, pin, SW_TRANSITION);
    GPIO_clearInterrupt(port, pin);
}

void sw_init(void)
{
    for (int i=0;i<sizeof(sw_status);i++) {
        sw_status[i] = false;
        _setup_switch(sw_ports[i], sw_pins[i]);
    }
}

static inline void _check_and_ack_sw(uint8_t sw_id)
{
    uint16_t status;
    status = GPIO_getInterruptStatus(sw_ports[sw_id], sw_pins[sw_id]);
    if (status & sw_pins[sw_id]) {
        sw_status[sw_id] = true;
        GPIO_clearInterrupt(sw_ports[sw_id], sw_pins[sw_id]);
    }
}


#if defined(__TI_COMPILER_VERSION__) || defined(__IAR_SYSTEMS_ICC__)
#pragma vector=PORT1_VECTOR
__interrupt
#elif defined(__GNUC__)
__attribute__((interrupt(PORT1_VECTOR)))
#endif
void Port_1 (void)
{
    _check_and_ack_sw(SW_UL);
    _check_and_ack_sw(SW_ML);
}

#if defined(__TI_COMPILER_VERSION__) || defined(__IAR_SYSTEMS_ICC__)
#pragma vector=PORT2_VECTOR
__interrupt
#elif defined(__GNUC__)
__attribute__((interrupt(PORT2_VECTOR)))
#endif
void Port_2 (void)
{
    _check_and_ack_sw(SW_UR);
    _check_and_ack_sw(SW_MR);
    _check_and_ack_sw(SW_LR);
}

#if defined(__TI_COMPILER_VERSION__) || defined(__IAR_SYSTEMS_ICC__)
#pragma vector=PORT7_VECTOR
__interrupt
#elif defined(__GNUC__)
__attribute__((interrupt(PORT7_VECTOR)))
#endif
void Port_7 (void)
{
    _check_and_ack_sw(SW_LL);
}
