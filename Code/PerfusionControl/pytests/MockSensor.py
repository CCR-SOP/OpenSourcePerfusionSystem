from threading import Thread, Lock, Timer, Event
import time

class MockSensor(Thread):
    """
    Base class for mock sensors. Specific mock sensors should derive from this class

    ...

    Attributes
    ----------
    period_update_ms : int
        milliseconds between data updates
    alarm_low : int
        samples below this value should trigger an alarm
    alarm_high : int
        samples above this value should trigger an alarm

    Methods
    -------
    get_sample()
        returns current sample
    _update_sample()
        update the current_sample. Should be overridden by derived classed
    force_overrange(milliseconds)
        forces the future data samples to be over range for specific milliseconds
    force_underrange(milliseconds)
        forces the future data samples to be over range for specific milliseconds

    """

    def __init__(self, sensor_name, min_valid, max_valid):
        Thread.__init__(self)
        self.sensor_name = sensor_name
        self._event_halt = Event()
        self.period_update_ms = 1000
        self.alarm_low = min_valid
        self.alarm_high = max_valid
        self._current_sample = (max_valid - min_valid) / 2.0
        self._thread_update = None
        self._lock = Lock()
        self._range_over = False
        self._range_under = False
        self._timer_range = None
        self.__epoch = time.perf_counter()
        self._time = 0

    def run(self):
        while not self._event_halt.wait(self.period_update_ms/1000.0):
            with self._lock:
                self._time = time.perf_counter() - self.__epoch
                self._update_sample()

    def halt(self):
        self._event_halt.set()

    def _update_sample(self):
        if self._range_over:
            self._current_sample = self.alarm_high + 0.1 * abs(self.alarm_high)
        elif self._range_under:
            self._current_sample = self.alarm_low - 0.1 * abs(self.alarm_low)
        else:
            self._current_sample = (self.alarm_low + self.alarm_high) / 2.0

    def get_sample(self):
        sample = None
        with self._lock:
            sample = self._current_sample
        return sample

    def _resume_valid(self):
        print('Resuming valid data')
        self._range_over = False
        self._range_under = False

    def _start_range_timer(self, milliseconds):
        if self._timer_range:
            self._timer_range.cancel()
        self._timer_range = Timer(milliseconds/1000.0, self._resume_valid)
        self._timer_range.start()

    def force_overrange(self, milliseconds):
        print('Forcing over range')
        self._range_over = True
        self._start_range_timer(milliseconds)

    def force_underrange(self, milliseconds):
        print('Forcing under range')
        self._range_under = True
        self._start_range_timer(milliseconds)





