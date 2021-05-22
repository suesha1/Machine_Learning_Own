from fastapi_jwt_auth import AuthJWT
from fastapi import Depends
from redis import Redis
from .model import Settings
import mysql.connector
# #========================================================================================
# ########################## *** Machine Status DB connection  *** ########################
# #========================================================================================

class MachineStatus_Db():

    def __init__(self,hostIp="localhost",username="root",password="password",database="sound_api",auth_plugin="mysql_native_password"):

        self.host = hostIp
        self.user = username
        self.password = password
        self.database = database
        self.auth_plugin = auth_plugin
        self.db = None
    def connect_db():

        self.db = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            auth_plugin=self.auth_plugin)

    def get_db_obj():
        return self.db



# #========================================================================================
# ########################## *** #JWT token related section *** ###############################
# #========================================================================================


# Setup our redis connection for storing the denylist tokens
redis_conn = Redis(host='localhost', port=6379, db=0, decode_responses=True)

# JWT related config and exception handler (To be moved to relevant project file)
@AuthJWT.load_config
def get_config():
    return Settings()

# Create our function to check if a token has been revoked. In this simple
# case, we will just store the tokens jti (unique identifier) in redis.
# This function will return the revoked status of a token. If a token exists
# in redis and value is true, token has been revoked
@AuthJWT.token_in_denylist_loader
def check_if_token_in_denylist(decrypted_token):
    jti = decrypted_token['jti']
    entry = redis_conn.get(jti)
    return entry and entry == 'true'

def verify_token_header(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()


# #========================================================================================
# ########################## *** Sample server Db configuration  *** ######################
# #========================================================================================


class Server_config():
    def __init__(self):
        self.database_ip = config("database_ip")
        self.database_password = config("database_password")
        self.database_username = config("database_username")

    # Returns the database_connection pointer
    def create_db_connection(self,database_name):
        database_connection = sqlalchemy.create_engine('mysql+mysqlconnector://{0}:{1}@{2}/{3}'.format(
            self.database_username, self.database_password, self.database_ip, database_name))
        session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=database_connection))
        return session