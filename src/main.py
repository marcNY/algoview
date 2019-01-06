import pika  # client module for rabbit_mq

# function called when receiving a message from amqp


def callback(ch, method, properties, body):
    message_received = body
    print(" [x] Received %r" % message_received)


# Main function listener
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
