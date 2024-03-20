from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import os
import pickle
import redis
import hashlib

# Инициализация FastAPI и Redis
app = FastAPI()

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
r = redis.Redis(redis_url, db=0)

# Модели Pydantic для запросов
class TrainRequest(BaseModel):
    data: list = Field(default_factory=list)
    target: list = Field(default_factory=list)

class PredictRequest(BaseModel):
    data: list

# Функция для генерации ключа кэша
def generate_cache_key(data):
    return hashlib.md5(str(data).encode('utf-8')).hexdigest()

@app.get("/ping")
async def ping():
    return {"message": "pong"}

@app.post("/train_user")
async def train_model(request: TrainRequest):
    X, y = request.data, request.target
    # todo: можно добавить проверку размерности
    # todo: можно добавить возможность загружать тестовые данные
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LogisticRegression(max_iter=200)
    model.fit(X_train, y_train)
    
    r.set("model", pickle.dumps(model))
    return {"message": "Model trained on user data  and saved successfully"}


@app.get("/train")
async def train_model_default():
    # Загрузка датасета ирисов, если пользовательские данные не предоставлены
    iris = load_iris()
    X, y = iris.data, iris.target
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)
    # todo: можно попробовать добавить возможность возращать метрику на тестовых данных
    model = LogisticRegression(max_iter=200)
    model.fit(X_train, y_train)
    r.set("model", pickle.dumps(model))
    return {"message": "Model trained on default data and saved successfully"}


@app.post("/predict")
async def predict(request: PredictRequest):
    data = request.data
    cache_key = generate_cache_key(data)
    
    if r.exists(cache_key):
        result = pickle.loads(r.get(cache_key))
        return {"prediction": result, 'cashed': True}

    if r.exists("model"):
        model = pickle.loads(r.get("model"))
        prediction = model.predict([data]).tolist()
        r.set(cache_key, pickle.dumps(prediction))
        return {"prediction": prediction, 'cashed': False}
    else:
        raise HTTPException(status_code=404, detail="Model not found")


@app.post("/predict/multiple")
async def predict_multiple(request: PredictRequest):
    data = request.data
    results, cashe = [], []
    if type(data[0])!=list:
        raise HTTPException(status_code=404, detail="Wrong data format")
    for d in data:
       
        
        cache_key = generate_cache_key(d)
        
        if r.exists(cache_key):
            result = pickle.loads(r.get(cache_key))
            results.append(result)
            cashe.append(True)
            # return {"predictions": result, 'cashed': True}
        elif r.exists("model"):
            model = pickle.loads(r.get("model"))
            predictions = model.predict(data).tolist()
            r.set(cache_key, pickle.dumps(predictions))
            results.append(result)
            cashe.append(False)
            # return {"predictions": predictions,  'cashed': False}
        else:
            raise HTTPException(status_code=404, detail="Model not found")
    return {"predictions": results,  'cashed': cashe}



# @app.post("/predict/multiple")
# async def predict_multiple(request: PredictRequest):
    
#     data = request.data
#     cache_key = generate_cache_key(data)
    
#     if r.exists(cache_key):
#         result = pickle.loads(r.get(cache_key))
#         return {"predictions": result, 'cashed': True}

#     if r.exists("model"):
#         model = pickle.loads(r.get("model"))
#         predictions = model.predict(data).tolist()
#         r.set(cache_key, pickle.dumps(predictions))
#         return {"predictions": predictions,  'cashed': False}
#     else:
#         raise HTTPException(status_code=404, detail="Model not found")
