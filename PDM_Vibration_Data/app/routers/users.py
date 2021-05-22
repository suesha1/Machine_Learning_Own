from fastapi import APIRouter, Depends,HTTPException
from fastapi_jwt_auth import AuthJWT
import hashlib
from redis import Redis
from ..dependencies import verify_token_header,check_if_token_in_denylist,redis_conn
from ..model import User,Settings
from ..dependencies import Server_config

# FastAPI router
router = APIRouter(
    prefix="/users",
    tags=["users"],
    # dependencies=[Depends(verify_token_header)],
    responses={401: {"description": "Not found"}},
)

# Setup our redis connection for storing the denylist tokens
# redis_conn = Redis(host='localhost', port=6379, db=0, decode_responses=True)
settings = Settings()

# Login API
@router.post('/login')
async def login(user: User, Authorize: AuthJWT = Depends(),summary = 
    'Login API and to issue access and refresh token', 
    description = '30 min validity for access token and 10 days for refresh token'):
    
    # DB connection 
    database_connection = Server_config().create_db_connection('users')
   
    # Get md5 hash from db - Check for authentication
    db_password = (database_connection.execute(
        "SELECT UserPassword from users.usernamepassword WHERE UserId = '" +
        user.userId + "';")).fetchone()
   
    # close the db session
    database_connection.close()
   
    # check from the database about password if match with preset (mysql DB)
    if (db_password is None) or (
            str(hashlib.md5((user.password).encode()).hexdigest()) != db_password[0]):
        raise HTTPException(status_code=401, detail="Bad userId or password")

    access_token = Authorize.create_access_token(subject=user.userId)
    refresh_token = Authorize.create_refresh_token(subject=user.userId)
    return {"access_token": access_token, "refresh_token": refresh_token ,"token_type": "bearer"}

# Standard refresh endpoint. Token in denylist will not
# be able to access this endpoint
@router.post('/token/refresh')
async def refresh(Authorize: AuthJWT = Depends(), summary = 
    'Issue new access token, Refresh token in header is required'):
    
    Authorize.jwt_refresh_token_required()

    current_user = Authorize.get_jwt_subject()
    new_access_token = Authorize.create_access_token(subject=current_user)
    return {"access_token": new_access_token}

# Endpoint for revoking the current users access token
@router.delete('/token/access-revoke')
async def access_revoke(Authorize: AuthJWT = Depends() , summary = 
    'Revoke the access token, Access token in header is required'):

    Authorize.jwt_required()

    # Store the tokens in redis with the value true for revoked.
    # We can also set an expires time on these tokens in redis,
    # so they will get automatically removed after they expired.
    jti = Authorize.get_raw_jwt()['jti']
    redis_conn.setex(jti,settings.access_expires,'true')
    return {"detail":"Access token has been revoke"}

# Endpoint for revoking the current users refresh token
@router.delete('/token/refresh-revoke')
async def refresh_revoke(Authorize: AuthJWT = Depends(), summary = 
    'Revoke the refresh token, Refresh token in header is required'):

    Authorize.jwt_refresh_token_required()

    jti = Authorize.get_raw_jwt()['jti']
    redis_conn.setex(jti,settings.refresh_expires,'true')
    return {"detail":"Refresh token has been revoke"}

# A token in denylist will not be able to access this any more
@router.get('/test/get_user')
async def get_user(Authorize: AuthJWT = Depends(), summary = 
    'Test API to get user back, Access token in header is required'):

    Authorize.jwt_required()
    current_user = Authorize.get_jwt_subject()
    return {"user": current_user}