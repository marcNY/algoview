import sys

if (sys.version_info > (3, 0)):
    # Python 3 code in this block
    import queue as queuelib
else:
    import Queue as queuelib

queue = queuelib.Queue()
