import pika  # client module for rabbit_mq
import trading.main as tradelib
import json
# function called when receiving a message from amqp


def callback(ch, method, properties, body):
    print(decode_message(body)['value'])
    # Main function listener


def decode_message(body):
    message_received = json.loads(body)
    if isinstance(message_received, list) and message_received.length == 8:
        return {'valid': 1,
                'value': {'underlying': message_received[0],
                          'msg': message_received[1],
                          'time': message_received[2]}}
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
