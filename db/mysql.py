import pymysql
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from db.constant import MYSQL_SERVER_CONF as MSC

connect_url = rf"mysql+pymysql://{MSC['user']}:{MSC['password']}@{MSC['host']}:{MSC['port']}/{MSC['db']}?charset=utf8mb4"

engine = create_engine(
    connect_url,
    encoding="utf-8",
    pool_size=1024,
    max_overflow=512,
    pool_recycle=240,
    pool_pre_ping=True,
)

LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class MysqlConnector:
    def __init__(self, cursor_type="dict"):
        self.host = MSC["host"]
        self.port = MSC["port"]
        self.user = MSC["user"]
        self.passwd = MSC["password"]
        self.db = MSC["db"]
        self.cursor_type = cursor_type
        self.connector = None

    def __enter__(self):
        self.connector = pymysql.connect(
            user=self.user,
            passwd=self.passwd,
            port=self.port,
            host=self.host,
            db=self.db,
            charset="utf8",
        )
        if self.cursor_type == "tuple":
            self.cursor = self.connector.cursor()
        else:
            self.cursor = self.connector.cursor(pymysql.cursors.DictCursor)

        return self.cursor

    def __exit__(self, exc_type, exc_value, traceback):
        if traceback is None:
            self.connector.commit()
        else:
            self.connector.rollback()

        self.cursor.close()
        self.connector.close()
