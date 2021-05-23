from typing import Optional, List, Dict
import uvicorn
from fastapi import Body, FastAPI
from pydantic import BaseModel,validator, Field
import joblib
from enum import Enum
import numpy as np
import pandas as pd


app = FastAPI()
iso_model = open("isolation_forest.pkl","rb")
iso_clf =  joblib.load(iso_model)

abrasion_mapping={'Good resistant to abrasion and crushing':0.1954023,
       'Medium resistant to abrasion and crushing': 0.3908046,
       'Good resistant to abrasion and medium crush resistance':0.16666667,
       'Medium Resistant to abrasion and Good crush resistance': 0.08045977,
       'Low abrasion and crush resistance':0.001}

fatigue_mapping={'Less fatigue resistance': 0.66666667,'Good fatigue resistance':0.23563218,
      'Medium fatigue resistance':0.23563218}


normaliz_dict={'Approximate_Mass_[kg/m]':[0.198,0.34],'Tensile_Strength(1770 Mpa)_[kN]': [31.221,59.5],
'Tensile_Strength(1770 Mpa)_[Kg]': [3190.693,6062.0], 'Tensile_Strength(1960 Mpa)_[kN]': [34.632, 65.9],
'Tensile_Strength(1960 Mpa)_[Kg]': [3527.215, 6713.0]}

 
def checkKey(mapping, key):   
    if key in mapping: 
        return key
    else: 
        return None
 

class Item(BaseModel):
    
    approx_mass: float = Field(..., gt=0, description="The approx_mass must be greater than zero")
    tension_strngth1: float = Field(..., gt=0, description="The tension_strngth1 must be greater than zero")
    tension_strngth2: float = Field(..., gt=0, description="The tension_strngth2 must be greater than zero")
    load1: float = Field(..., gt=0, description="The load1 must be greater than zero")
    load2: float = Field(..., gt=0, description="The load2 must be greater than zero")
    abrasion_resistance:str= Field(...,min_length=8,max_length=50)
    fatigue_resistance: str= Field(...,min_length=5,max_length=50)

    @validator('abrasion_resistance')
    def not_null_abrasion(cls, v):
        out=checkKey(abrasion_mapping,v)
        if out is None:
            raise ValueError
        return v
    
    @validator('fatigue_resistance')
    def not_null_fatigue(cls, v):
        out=checkKey(fatigue_mapping,v)
        if out is None:
            raise ValueError
        return v
    
def feature_normalize(item: Item = Body(..., embed=True)):
     lis=[]
     nominal_lis=[item.approx_mass,item.tension_strngth1,item.load1,
                    item.tension_strngth2,
                    item.load2]

     c=0
     for i in normaliz_dict : 
        nominal_lis[c]=(nominal_lis[c]-normaliz_dict[i][0])/(normaliz_dict[i][1]- normaliz_dict[i][0])
        lis.append(nominal_lis[c])
        c=c+1

     abrasion_key=item.abrasion_resistance
     fatigue_key=item.fatigue_resistance
     abrasion_val= [val for key, val in abrasion_mapping.items() if abrasion_key in key]  
     fatigue_val=[val for key, val in fatigue_mapping.items() if fatigue_key in key] 

     lis.append(abrasion_val[0])
     lis.append(fatigue_val[0])
     return lis

@app.get("/")
async def index():
    return "ANAMOLY DETECTION FOR GONDOLA WIRE ROPE"

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item = Body(..., embed=True)):
    
    results = {"item_id":item_id,"item": item}
    lis=[item.approx_mass,item.tension_strngth1,item.load1,
                item.tension_strngth2,
                item.load2,
                item.abrasion_resistance,
                item.fatigue_resistance]
    
    output={"item_id":item_id, "item":item}
    return output


@app.post('/predict/{item_id}')
async def predict(item_id: int, item: Item = Body(..., embed=True)):
     
     lis=feature_normalize(item)
     data = pd.DataFrame([lis])
   
     prediction=iso_clf.predict(data)
     if prediction[0]==1:
        out="No Defect Existed"
     else:
        out="Defect Exists"

     output={"item_id":item_id, "prediction":out}
     print(out)
     return out

   