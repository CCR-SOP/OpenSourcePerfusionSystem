# -*- coding: utf-8 -*-
"""Simple test program for RabbitMQ receive
Based on Hello World Tutorial example from https://www.rabbitmq.com

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import pika
import sys
import os

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body)

    channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

