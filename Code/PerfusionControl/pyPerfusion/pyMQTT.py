# -*- coding: utf-8 -*-
"""classes for sending/receiving MQTT messages
Assumes RabbitMQ broker installed and uses pika library

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import threading

import pika


class AlarmPublisher:
    def __init__(self, exchange='perfusion', host='localhost'):
        self._lgr = logging.getLogger(__name__)
        self._exchange = exchange
        self._connection = None
        self._channel = None
        self._host = host

    def connect(self):
        self._lgr.info(f'Creating connection to exchange {self._exchange} on {self._host}')
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(host=self._host))
        self._channel = self._connection.channel()
        self._channel.exchange_declare(exchange=self._exchange,  exchange_type='topic')

    def close(self):
        self._connection.close()
        self._lgr.info(f'Closing connection to exchange {self._exchange} on {self._host}')

    def publish(self, routing_key, msg):
        self._lgr.info(f'Publishing {routing_key}:{msg} to {self._exchange}')
        self._channel.basic_publish(exchange=self._exchange, routing_key=routing_key, body=msg)


class AlarmSubscriber:
    def __init__(self, exchange='perfusion', host='localhost'):
        self._lgr = logging.getLogger(__name__)
        self._exchange = exchange
        self._connection = None
        self._channel = None
        self._host = host
        self._queue = None
        self._thread = None
        self._tag = None

    def connect(self):
        self._lgr.info(f'Creating connection to exchange {self._exchange} on {self._host}')
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self._channel = self._connection.channel()

        self._channel.exchange_declare(exchange=self._exchange, exchange_type='topic')

        result = self._channel.queue_declare('', exclusive=True)
        self._queue = result.method.queue

        self._thread = threading.Thread(target=self._run)
        self._thread.name = f'AlarmSubscriber {self._exchange} on {self._host}'
        self._thread.start()

    def subscribe(self, topic_name):
        self._lgr.info('Subscribing to {topic_name}')
        self._channel.queue_bind(exchange=self._exchange,
                                 queue=self._queue,
                                 routing_key=topic_name)

        self._tag = self._channel.basic_consume(queue=self._queue,
                                                on_message_callback=self._callback,
                                                auto_ack=True)

    def cancel(self):
        self._channel.basic_cancel(self._tag)

    def _callback(self, ch, method, properties, body):
        self._lgr.info(f'Received message {method.routing_key}: {body}')
        self.callback(method.routing_key, body)
    
    def _run(self):
        self._channel.start_consuming()

    def callback(self, routing_key, body):
        pass
