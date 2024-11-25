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
from dataclasses import dataclass

import pika


@dataclass
class Msg:
    name: str = 'None'
    sensor_type: str = 'None'
    msg = 'None'


class AlarmPublisher:
    def __init__(self, exchange='perfusion', host='localhost'):
        self._lgr = logging.getLogger(__name__)
        self._exchange = exchange
        self._connection = None
        self._channel = None
        self._host = host

    def is_open(self):
        is_open = False
        if self._connection:
            is_open = self._connection.is_open
        return is_open

    def connect(self):
        self._lgr.info(f'Creating connection to exchange {self._exchange} on {self._host}')
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(host=self._host))
        self._channel = self._connection.channel()
        self._channel.exchange_declare(exchange=self._exchange,  exchange_type='topic')

    def close(self):
        if self._connection:
            self._channel.cancel()
            self._connection.close()
            self._lgr.info(f'Closing connection to exchange {self._exchange} on {self._host}')
        else:
            self._lgr.warning(f'Attempt to close an already closed connection {self._exchange} on {self._host}')

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
        self.__callback = None

    def is_open(self):
        is_open = False
        if self._connection:
            is_open = self._connection.is_open
        return is_open

    def set_callback(self, callback):
        self.__callback = callback

    def connect(self):
        self._lgr.info(f'Creating connection to exchange {self._exchange} on {self._host}')
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self._channel = self._connection.channel()

        self._channel.exchange_declare(exchange=self._exchange, exchange_type='topic')

        result = self._channel.queue_declare('', exclusive=True)
        self._queue = result.method.queue
        # use protected callback to guarantee logging of the message
        self._tag = self._channel.basic_consume(queue=self._queue,
                                                on_message_callback=self._callback,
                                                auto_ack=True)
        self._thread = threading.Thread(target=self._run)
        self._thread.name = f'AlarmSubscriber {self._exchange} on {self._host}'
        self._thread.start()

    def close(self):
        if self.is_open():
            self.cancel()
            self._thread.join()
            try:
                self._connection.close()
            except pika.exceptions.StreamLostError:
                pass

    def subscribe(self, topic_name):
        self._lgr.info(f'Subscribing to {topic_name}')
        self._channel.queue_bind(exchange=self._exchange,
                                 queue=self._queue,
                                 routing_key=topic_name)

    def cancel(self):
        self._channel.basic_cancel(self._tag)

    def _callback(self, ch, method, properties, body):
        self._lgr.info(f'Received message {method.routing_key}: {body}')
        self.__callback(method.routing_key, body)

    def _run(self):
        self._channel.start_consuming()
