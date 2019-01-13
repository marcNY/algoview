import pika
import json
import ast


def callback(ch, method, properties, body):
    print(body)


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))

channel = connection.channel()

#queue = channel.queue_declare(queue='hello')
# print(queue.method.message_count)

method_frame, header_frame, body = channel.basic_get('hello')
print(method_frame)
print(header_frame)
a = body.decode('utf-8')
c = json.loads(json.loads(a))

print(c, type(c))
print(len(c))
# channel.basic_consume(callback,
#                       queue='hello',
#                       no_ack=True)
