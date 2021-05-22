from pydantic import BaseModel
from datetime import timedelta
from decouple import config
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker


# #========================================================================================
# ########################## *** Machine Status data models *** ###########################
# #========================================================================================

class query_item(BaseModel):
    mac:str
    size:int
    
# #========================================================================================
# ########################## *** Extra User sample Configuration *** ######################
# #========================================================================================
class User(BaseModel):
    userId: str
    password: str

class Settings(BaseModel):
    authjwt_secret_key: str = config("secret")
    authjwt_denylist_enabled: bool = True
    authjwt_denylist_token_checks: set = {"access","refresh"}
    access_expires: int = timedelta(minutes=30)
    refresh_expires: int = timedelta(days=10)






