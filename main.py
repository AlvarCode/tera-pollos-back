from models import *
from fastapi import (
    FastAPI,
    HTTPException,
    status,
)
import mariadb
from mariadb import (
    Cursor, 
    Connection, 
    IntegrityError, 
    OperationalError
)


def exec_query(callback, send_conn = False):
    conn = mariadb.connect(**conn_params)
    cursor = conn.cursor()
    callback(conn, cursor) if send_conn else callback(cursor)
    cursor.close()
    conn.close()

def exist(target_table: str, pk_name: str, pk_value) -> tuple | None:
    def query(cursor: Cursor):
        nonlocal data
        cursor.execute(f"select * from {target_table} where {pk_name} = ?", (pk_value,))
        data = cursor.fetchone()

    data = None
    exec_query(query)
    return data


def validate_authentication(user_id: int, passwd: str):
    def query(cursor: Cursor):
        nonlocal user
        cursor.execute(f"select Name, IsAdmin from User where ID = ? and Password = ?", (user_id, passwd))
        data = cursor.fetchone()
        
        if (data):
            user = User(id=user_id, name=data[0], is_admin=data[1])

    user = None
    exec_query(query)
    return user

def fetch_products(sql: str) -> list[Product]:
    def query(cursor: Cursor):
        cursor.execute(sql)
        data = cursor.fetchall()

        for product in data:
            products.append(Product(name=product[0], price=product[1]))

    products = list()
    exec_query(query)
    return products


app = FastAPI()


@app.get("/")
async def root():
    return { "message": "El server funciona :)" }

@app.post("/login")
def login(data: LoginRequest):
    user = validate_authentication(data.user_id, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrecta"
        )
    return { "token": user }

@app.get("/products")
async def get_products():
    return fetch_products("select * from Product")

@app.post("/products/new")
def create_product(product: Product):
    def query(conn: Connection, cursor: Cursor):
        try:
            cursor.execute(f"call Create_Product (?, ?)", (product.name, product.price))
            conn.commit()

        except OperationalError:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un producto con el mismo nombre"
            )
            
        except Exception as ex:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error interno del servidor: {ex}"
            )
        
    exec_query(query, True)
    return { "message": "Producto creado exitosamente" }

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

@app.get("/combos/{combo_name}")
def get_combo(combo_name: str):
    def query(cursor: Cursor):
        cursor.execute("call Read_ProductsFromCombo (?)", (combo_name,))
        rows = cursor.fetchall()
        
        for row in rows:
            products.append(
                (Product(name=row[0], price=row[1]), row[2])
            )

    data = exist("Combo", "Name", combo_name)
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El combo '{combo_name}' no existe"
        )
    
    products = list()
    combo = Combo(name=data[0], price=data[1])
    exec_query(query)
    combo.products = products
    return combo

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