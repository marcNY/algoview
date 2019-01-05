import os
this_file_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(this_file_directory)
paths = {'persistent_queue': os.path.join(
    os.path.dirname(parent_directory), 'persistent_queue')}


if __name__ == '__main__':
    print(paths)
