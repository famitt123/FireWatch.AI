from fastapi import FastAPI

app = FastAPI()
@app.get('/')
def read_root():
    return {'message': 'FireWatch.AI backend server is Running :D'}