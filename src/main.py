import pika  # client module for rabbit_mq
import trading.main as tradelib
import json
import time
# function called when receiving a message from amqp


def callback(ch, method, properties, body):

    order_message = decode_message(body)['value']
    underlying = order_message['underlying']
    msg = order_message['msg']
    start_time = time.time()
    order_id = tradelib.execute_message(underlying, msg)
    end_time = time.time()

    order_message['order_id'] = order_id
    order_message['start_execution_time'] = start_time
    order_message['end_execution_time'] = end_time

    ch.basic_publish(exchange='',
                     routing_key='executed_signals',
                     body=json.dumps(order_message))
    # Main function listener


def decode_message(body):
    message_received = json.loads(body)
    message_received = message_received.replace(
        '[', '').replace('"', '').replace(']', '').split(',')

    if isinstance(message_received, list) and len(message_received) == 8:
        return {'valid': 1,
                'value': {'underlying': message_received[0],
                          'msg': message_received[1],
                          'time': message_received[3]}}
    else:
        return {'valid': 0, 'value': message_received}


def Main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))

    channel = connection.channel()

    channel.queue_declare(queue='hello')
    channel.basic_consume(callback,
                          queue='hello',
                          no_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == "__main__":
    Main()
