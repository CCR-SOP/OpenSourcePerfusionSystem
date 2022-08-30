# -*- coding: utf-8 -*-
"""Simple test program for receiving RabbitMQ Topics
Based on Topics Tutorial example from https://www.rabbitmq.com

Example: python -m pytests.pytest_rmq_rcv_topics "alarm.flow.#.#"
Will print any messages with a topic starting with alarm.flow (e.g. alarm.flow.range.under)
The publisher must use the same exchange name (defaults to "perfusion")


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

channel.exchange_declare(exchange=exchange_name, exchange_type='topic')

result = channel.queue_declare('', exclusive=True)
queue_name = result.method.queue

binding_keys = sys.argv[1:]
if not binding_keys:
    sys.stderr.write("Usage: %s [binding_key]...\n" % sys.argv[0])
    sys.exit(1)

for binding_key in binding_keys:
    channel.queue_bind(
        exchange=exchange_name, queue=queue_name, routing_key=binding_key)

print(' [*] Waiting for logs. To exit press CTRL+C')


def callback(ch, method, properties, body):
    print(" [x] %r:%r" % (method.routing_key, body))


channel.basic_consume(
    queue=queue_name, on_message_callback=callback, auto_ack=True)

channel.start_consuming()
