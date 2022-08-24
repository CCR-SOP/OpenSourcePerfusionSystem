# -*- coding: utf-8 -*-
"""Simple test program for sending RabbitMQ topic messages
Based on Topics Tutorial example from https://www.rabbitmq.com

Example:  python -m pytests.pytest_rmq_send_topics alarm.flow.range.over 50
Sends a message of "50" with a topic of alarm.flow.range.over
The subscribers must use the same exchange name (defaults to "perfusion")

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import pika
import sys


exchange_name = 'perfusion'

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.exchange_declare(exchange=exchange_name,  exchange_type='topic')

routing_key = sys.argv[1] if len(sys.argv) > 2 else 'anonymous.info'
message = ' '.join(sys.argv[2:]) or 'Hello World!'
channel.basic_publish(exchange=exchange_name, routing_key=routing_key, body=message)
print(" [x] Sent %r:%r" % (routing_key, message))
connection.close()
