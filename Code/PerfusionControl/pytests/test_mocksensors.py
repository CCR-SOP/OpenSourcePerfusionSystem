import MockOscSensor
import MockSensorModule


try:
    ha_flow = MockOscSensor.MockOscSensor('HA Flow', 10, 20, 2)
    pv_flow = MockOscSensor.MockOscSensor('PV Flow', 5, 10, 4)

    mod1 = MockSensorModule.MockSensorModule('mod1')

    mod1.add_sensor(ha_flow)
    mod1.add_sensor(pv_flow)

    names = mod1.get_sensor_names()
    print(f'{names}')
finally:
    del mod1
