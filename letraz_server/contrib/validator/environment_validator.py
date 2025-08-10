import os

from dotenv import load_dotenv

load_dotenv()


class DBEnvironmentValidator:
    def __init__(self):
        self.Engines = {
            'POSTGRES_SQL': {'tags': ['postgresql', 'django.db.backends.postgresql'], 'engine_name': 'django.db.backends.postgresql'},
            'MARIADB': {'tags': ['mariadb', 'django.db.backends.mariadb'], 'engine_name': 'django.db.backends.mariadb'},
            'MYSQL': {'tags': ['mysql', 'django.db.backends.mysql'], 'engine_name': 'django.db.backends.mysql'},
            'ORACLE': {'tags': ['oracle', 'django.db.backends.oracle'], 'engine_name': 'django.db.backends.oracle'},
            'SQLITE': {'tags': ['sqlite', 'django.db.backends.sqlite3'], 'engine_name': 'django.db.backends.sqlite3'},
        }

        self.ENGINE: str = os.environ.get('DB_ENGINE')
        self.NAME: str = os.environ.get('DB_NAME')
        self.USER: str = os.environ.get('DB_USER')
        self.PASSWORD: str = os.environ.get('DB_PASSWORD')
        self.HOST: str = os.environ.get('DB_HOST')
        self.PORT: str = os.environ.get('DB_PORT')
        self.SSL_MODE_REQUIRED: str = os.environ.get('DB_SSL_MODE_REQUIRED')
        self.DISABLE_SERVER_SIDE_CURSORS: str = os.environ.get('DB_DISABLE_SERVER_SIDE_CURSORS')
        self.status = False
        self.errors = []
        self.config = {}

    def validate(self):
        engine = None
        status = True
        for engine_name, engine_details in self.Engines.items():
            if str(engine_details.get('engine_name')).strip().lower() == str(self.ENGINE).strip().lower():
                engine = engine_details.get('engine_name')
        if engine is None:
            self.errors.append('Invalid Engine!')
            status = False
        if not self.NAME:
            self.errors.append('DB name not provided!')
            status = False
        if not self.USER:
            self.errors.append('DB username not provided!')
            status = False
        if not self.PASSWORD:
            self.errors.append('DB password not provided!')
            status = False
        if not self.HOST:
            self.errors.append('DB host not provided!')
            status = False
        if not self.PORT:
            self.errors.append('DB port not provided!')
            status = False
        if status:
            self.ENGINE = engine
            self.status = True
            return True
        else:
            self.status = False
            return False

    def get_config(self):
        if self.status:
            self.config = {
                'ENGINE': self.ENGINE,
                'NAME': self.NAME,
                'USER': self.USER,
                'PASSWORD': self.PASSWORD,
                'HOST': self.HOST,
                'PORT': self.PORT,
                'DISABLE_SERVER_SIDE_CURSORS': str(self.DISABLE_SERVER_SIDE_CURSORS).strip().upper() == 'TRUE',
                # Set connection max age to 0 to ensure fresh connections in thread pools
                # This is crucial for SSL environments where stale connections can cause issues
                'CONN_MAX_AGE': 0,
            }
            if str(self.SSL_MODE_REQUIRED).strip().upper() == 'TRUE':
                self.config['OPTIONS'] = {
                    'sslmode': 'require'
                }
        return self.config

