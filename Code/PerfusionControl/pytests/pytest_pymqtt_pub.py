# -*- coding: utf-8 -*-
"""Simple test program for pyMQTT publisher

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import sys

from pyPerfusion.pyMQTT import AlarmPublisher

if len(sys.argv) < 3:
    print('Usage: pytest_pymqtt_pub {topic} {msg}')
    sys.exit(0)

topic = sys.argv[1]
msg = sys.argv[2]

pub = AlarmPublisher()
pub.connect()
pub.publish(topic, msg)
print(f'Published {topic}:{msg}')
