import os
from data.consts import PATH
from data.storage import Storage
class LocalStorage(Storage):

    def __init__(self):
        super().__init__()

    def save(key: str, data: str):
        dir_path = f'{PATH}{key}'
        os.makedirs(dir_path, exist_ok=True)

        with open(f'{dir_path}.html', 'wb+') as document:
            document.write(data)

    def load(key: str):
        dir_path = f'{PATH}{key}'
        with open(f'{dir_path}.html', 'r') as file:
            document = file.read()
        
        return document