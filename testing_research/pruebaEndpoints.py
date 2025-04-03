from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel
import pruebaW
import subprocess
from fastapi import WebSocket, WebSocketDisconnect

app = FastAPI()




class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"probando otro endpoint"}


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}

@app.get("/whisper")
def transcriptionTest():
    try:
        result = subprocess.run(["python", "pruebaW.py"], capture_output=True, text=True)
        output = result.stdout
        if result.returncode != 0:
            return {"error": result.stderr}
        
        return {"message": "Transcripción completada", "output": output}
    
    except Exception as e:
        return {"error": str(e)}
