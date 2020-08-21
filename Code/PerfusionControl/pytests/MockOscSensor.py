import MockSensor
import random
import math


class MockOscSensor(MockSensor.MockSensor):
    """
    Mock sensor which generates an sinusoidal waveform. Derived from MockSensor

    """
    def __init__(self, sensor_name, min_val, max_val, osc_period_ms):
        """ Constructor for MockOscSensor

            ...

            Parameters
            ==========
            min_val : int
                minimum value for normal oscillation
            max_val : int
                maximum value for normal oscillation
            osc_period_ms: int
                oscillation period in milliseconds
        """
        super().__init__(sensor_name, min_val, max_val)
        self.__osc_period_ms = osc_period_ms

    def _update_sample(self):
        val_range = abs(self.alarm_high - self.alarm_low)

        normalized_osc = (0.5 * (math.sin(2 * math.pi * 1.0/(self.__osc_period_ms / 1000.0) * self._time) + 1.0))
        high = self.alarm_high
        low = self.alarm_low
        if self._range_under:
            low = 1.5*self.alarm_low if self.alarm_low < 0 else 0.9 * self.alarm_low
        elif self._range_over:
            high = 0.5*self.alarm_high if self.alarm_high < 0 else 1.1 * self.alarm_high

        val_range = abs(high - low)

        self._current_sample = val_range * normalized_osc + low
        # (f'Time: {self._time:.1f}\t Value: {self._current_sample:0.1f} Range: {val_range} {low} to {high}')