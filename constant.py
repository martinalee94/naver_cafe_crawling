import os 

MYSQL_SERVER_CONF = {
    "user" : os.environ.get("user"),
    "password" : os.environ.get("password"),
    "host" : os.environ.get("host"),
    "port" : 3306,
    "db" : os.environ.get("db"),
    "charset" : 'utf8mb4'
}