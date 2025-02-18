from models import *
from fastapi import FastAPI, HTTPException, status
import mariadb
from mariadb import Cursor

def validate_authentication(user_id: int, passwd: str):
    def query(cursor: Cursor):
        cursor.execute(f"select Name, IsAdmin from User where Name = {user_id} and Password = {passwd}")
        response = cursor.fetchone()
        
        if (response):
            user = User(id=user_id, name=response[0], is_admin=response[1])

    user = None
    exec_query(query)
    return user

def exec_query(callback):
    conn = mariadb.connect(**conn_params)
    cursor = conn.cursor()
    callback(cursor)
    cursor.close()
    conn.close()


app = FastAPI()


@app.get("/")
async def root():
    return { "message": "El server funciona :)" }

@app.post("/login")
def login(user_id: int, password: str):
    user = validate_authentication(user_id, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso denegado"
        )
    return user

@app.get("/products")
async def get_products():
    def query(cursor: Cursor):
        cursor.execute("select * from Product")
        data = cursor.fetchall()
        
        for product in data:
            products.append(Product(name=product[0], price=product[1]))

    products = list()
    exec_query(query)
    return products

@app.post("/products/new")
def create_product(product: Product):
    pass

@app.post("/products/delete")
def rempve_product(product_name: str):
    pass

@app.get("/combos")
async def get_combos():
    def query(cursor: Cursor):
        cursor.execute("select * from Combo")
        response = cursor.fetchall()

        for combo in response:
            combos.append(Combo(name=combo[0], price=combo[1]))

    combos = list()
    exec_query(query)
    return combos;

@app.post("/combos/new")
def create_combo(combo: Combo):
    pass

@app.delete("/combos/delete")
def remove_combo(combo_name: str):
    pass

def create_sale(sale: Sale):
    pass


conn_params = {
    "user": "dbeaver_user",
    "password": "DBeaver123",
    "host": "localhost",
    "database": "TeraPollos"
}