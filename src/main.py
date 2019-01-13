import pika  # client module for rabbit_mq
import trading.main as tradelib
import json
import time
# function called when receiving a message from amqp

# TODO: cancel message execution if received more than 30 seconds before


def callback(ch, method, properties, body):
    order_message = decode_message(body)['value']
    underlying = order_message['underlying'].strip()
    msg = order_message['description'].strip()

    # We get a dictionnary out of executing message
    output = tradelib.execute_message(underlying, msg)

    # we merge both dictionaries
    order_message = {**order_message, **output}
    ch.basic_publish(exchange='',
                     routing_key='executed_signals',
                     body=json.dumps(order_message))
    # Main function listener


def decode_message(body):
    message_received = json.loads(json.loads(body.decode('utf-8')))

    if isinstance(message_received, dict) and 'underlying' in message_received and 'description' in message_received:
        return {'valid': 1,
                'value': message_received}
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
