from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi_jwt_auth import AuthJWT
from starlette.middleware.cors import CORSMiddleware
import routers
from .routers import users,anomaly,machineStatus,vibrations



# app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
app = FastAPI(
    title="Sound APIs",
    description="This is the doc for front-end developers",
    version="0.0.1",
    #redoc_url=None,
    #docs_url = None
)

# For CORS enabling
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    users.router,
    prefix="/v1",
    tags=["users"],
)



@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

app.include_router(
    anomaly.router,
    prefix="/v1",
    tags=["anomaly"],
)

app.include_router(
    vibrations.router,
    prefix="/v1",
    tags=["vibrations"],
)


app.include_router(
    machineStatus.router,
    prefix="/v0",
    tags=["machineStatus"],
)


@app.get("/")
async def root():
    return {"message": "Hello This is Sound Applications main Page!"}

# #========================================================================================
# ########################## *** Anomaly Detection code *** ###############################
# #========================================================================================

# #initializing important parameters class instance to access the important parameter values
# conf = audio_parameters()

# '''This post request receives the audio file in compressed format 
# and returns the simple spectogram of that file'''

# @app.post("/spectrogram/")
# async def post_spectrogram(files: List[UploadFile] = File(...)):
#     spec_img_return = get_spectrogram(files)
#     return FileResponse(spec_img_return)


# '''This post reqests gets the  list of audio files and return anomaly scores of each audio file
# This function calls the ***get_model_anomaly function which decompressed the file 
# and return anomaly health score''' 

# @app.post("/getAnomaly/")
# async def post_anomaly_score(threshold: str,files: List[UploadFile] = File(...)):

#     json_string = json.dumps(get_model_anomaly_rate(files,threshold))
#     return json_string

# #========================================================================================
# ########################## *** on/off code *** ###############################
# #========================================================================================
