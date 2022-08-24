# -*- coding: utf-8 -*-
"""Simple test program for pyMQTT publisher

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import sys
import time
import logging

from pyPerfusion.pyMQTT import AlarmSubscriber
import pyPerfusion.utils as utils

# lgr = logging.getLogger()
# utils.setup_stream_logger(lgr, logging.DEBUG)
# pika_lgr = logging.getLogger('pika')
# pika_lgr.setLevel(logging.WARNING)

class localSubscriber(AlarmSubscriber):
    def callback(self, routing_key, body):
        print(f'Received topic {routing_key} with message {body}')


if len(sys.argv) < 2:
    print('Usage: pytest_pymqtt_sub {topic}')
    sys.exit(0)

topic = sys.argv[1]

sub = localSubscriber()
sub.connect()
sub.subscribe(topic)
print(f'Subscribed to {topic}')
print('Hit Ctrl-C to stop listening for messsages')

while True:
    try:
        time.sleep(0.2)
    except KeyboardInterrupt:
        break

sub.cancel()
