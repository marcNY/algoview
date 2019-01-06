import json

a = b'"[\\"XBTUSD\\",\\"n=entryL1 d=long t=m p=0 q=1 u=1 c=10000 b=1h\\",10,\\"06/01/2019 21:49:38\\",-2,-1,\\"entryL1\\",\\"n=entryL1 d=long t=m p=0 q=1 u=1 c=10000 b=1h\\"]"'
b = json.loads(a)

c = b.replace('[', '').replace('"', '').replace(']', '').split(',')
print(type(b))
print(isinstance(b, list))


print(type(c))
print(c[0])
