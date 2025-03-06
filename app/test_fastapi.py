from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_login():

    response = client.post("/login", params={"username": "articuno", "password": "12345"})
    
    # Verificar que el código de estado sea 200 
    assert response.status_code == 200
    
    # Verificar que la respuesta contiene el token
    token = response.json()
    assert isinstance(token, str)  # Verifica que el token sea un string

def test_login_wrong_username():
    
    response = client.post("/login", params={"username": "moltres", "password": "12345"})
    
    assert response.status_code == 404
    # Verificar que la respuesta es del error que buscamos
    assert response.json() == {"detail": "No User found"}

def test_login_no_username():
    
    response = client.post("/login", params={"username": "", "password": "12345"})
    
    assert response.status_code == 404
    # Verificar que la respuesta es del error que buscamos
    assert response.json() == {"detail": "No User found"}

def test_login_wrong_password():
    
    response = client.post("/login", params={"username": "articuno", "password": "125"})
 
    assert response.status_code == 401
    # Verificar que la respuesta es del error que buscamos
    assert response.json() == {"detail": "Password error"}

def test_login_no_password():
    
    response = client.post("/login", params={"username": "articuno", "password": ""})
 
    assert response.status_code == 401
    # Verificar que la respuesta es del error que buscamos
    assert response.json() == {"detail": "Password error"}
    