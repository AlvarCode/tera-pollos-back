from models import *
from fastapi import (
    FastAPI,
    HTTPException,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
import mariadb
from mariadb import (
    Cursor, 
    Connection, 
    OperationalError
)


def exec_query(callback, use_conn = False):
    conn = mariadb.connect(**conn_params)
    cursor = conn.cursor()
    callback(conn, cursor) if use_conn else callback(cursor)
    cursor.close()
    conn.close()

def exist(target_table: str, pk_name: str, pk_value) -> tuple | None:
    def query(cursor: Cursor):
        nonlocal data
        cursor.execute(f"SELECT * FROM {target_table} WHERE {pk_name} = ?", (pk_value,))
        data = cursor.fetchone()

    data = None
    exec_query(query)
    return data

def validate_authentication(user_id: int, passwd: str):
    def query(cursor: Cursor):
        nonlocal user
        cursor.execute("""
                       SELECT Name, IsAdmin
                       FROM User 
                       WHERE ID = ? AND Password = ?
                       """, (user_id, passwd))
        data = cursor.fetchone()
        
        if (data):
            user = User(id=user_id, name=data[0], is_admin=data[1])

    user = None
    exec_query(query)
    return user

def generate_exception(ex):
    print(f"error: {ex}")
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Error interno del servidor")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
async def root():
    return { "message": "El server funciona :)" }

@app.post("/login")
def login(data: LoginRequest):
    user = validate_authentication(data.user_id, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Usuario o contraseña incorrecta")
    return { "token": user }

@app.get("/products")
async def get_products():
    def query(cursor: Cursor):
        try:
            cursor.execute("SELECT * FROM Product")
            rows = cursor.fetchall()
            for row in rows: products.append(Product(name=row[0], price=row[1]))

        except Exception as ex:
            generate_exception(ex)

    products = list()
    exec_query(query)
    return products

@app.post("/product/new", status_code=status.HTTP_201_CREATED)
def create_product(product: Product):
    def query(conn: Connection, cursor: Cursor):
        try:
            cursor.callproc(f"Create_Product", (product.name, product.price))
            conn.commit()

        except OperationalError as ex:
            print(f"error: {ex}")
            conn.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Ya existe un producto con el mismo nombre")
        
        except Exception as ex:
            conn.rollback()
            generate_exception(ex)
        
    exec_query(query, True)
    return { "message": "Producto creado exitosamente" }

@app.put("/product/update/{product_name}")
def update_product(product_name: str, product: Product):
    def query(conn: Connection, cursor: Cursor):
        try:
            cursor.callproc("Edit_Product", (product_name, product.name, product.price))
            conn.commit()

        except Exception as ex:
            conn.rollback()
            generate_exception(ex)

    exec_query(query, True)
    return { "message": "Producto actualizado satisfactoriamente" }

@app.delete("/product/delete/{product_name}")
def remove_product(product_name: str):
    def query(conn: Connection, cursor: Cursor):
        try:
            cursor.callproc("Delete_Product", (product_name,))
            conn.commit()

        except Exception as ex:
            conn.rollback()
            generate_exception(ex)

    exec_query(query, True)
    return { "message": "Producto eliminado satisfactoriamente" }

@app.get("/combos")
async def get_combos():
    def query(cursor: Cursor):
        try:
            cursor.execute("SELECT * FROM Combo")
            rows = cursor.fetchall()
            for row in rows: combos.append(Combo(name=row[0], price=row[1]))

        except Exception as ex:
            generate_exception(ex)

    combos = list()
    exec_query(query)
    return combos;

@app.get("/combo/{combo_name}")
def get_combo(combo_name: str):
    def query(cursor: Cursor):
        try:
            cursor.callproc("Read_ProductsFromCombo", (combo_name,))
            rows = cursor.fetchall()
            for row in rows:
                products.append({ "product": row[0], "price": row[1], "count": row[2] })
        
        except Exception as ex:
            generate_exception(ex)

    data = exist("Combo", "Name", combo_name)
    
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"El combo '{combo_name}' no existe")
    
    products = list()
    combo = Combo(name=combo_name, price=data[1])
    exec_query(query)
    combo.products = products
    return combo

@app.post("/combo/new", status_code=status.HTTP_201_CREATED)       
def create_combo(combo: Combo):
    def query(conn: Connection, cursor: Cursor):
        try:
            cursor.callproc("Create_Combo", (combo.name, combo.price))
            for product in combo.products:
                cursor.callproc("Create_ComboDetails"
                               (combo.name, product["name"], product["count"]))
            conn.commit()

        except OperationalError as ex:
            conn.rollback()
            print(f"error: {ex}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Ya existe un combo con el mismo nombre")
        
        except Exception as ex:
            conn.rollback()
            generate_exception(ex)

    exec_query(query, True)
    return { "message": "Combo creado satisfactoriamente" }

@app.put("/combo/update/{combo_name}")
def update_combo(combo_name: str, combo: Combo):
    def query(conn: Connection, cursor: Cursor):
        try:
            cursor.callproc("Edit_Combo", (combo_name, combo.name, combo.price))
            conn.commit()

        except Exception as ex:
            conn.rollback()
            generate_exception(ex)

    data = exist("Combo", "Name", combo_name)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="El combo no existe")

    exec_query(query, True)
    return { "message": "Combo actualizado satisfactoriamente" }

@app.delete("/combo/delete/{combo_name}")
def remove_combo(combo_name: str):
    def query(conn: Connection, cursor: Cursor):
        try:
            cursor.callproc("Delete_Combo", (combo_name,))
            conn.commit()

        except Exception as ex:
            conn.rollback()
            generate_exception(ex)

    exec_query(query, True)
    return { "message": "Combo eliminado satisfactoriamente" }

@app.get("/sales")
def get_sales():
    def query(cursor: Cursor):
        try:
            cursor.execute("SELECT * FROM Sale")
            rows = cursor.fetchall()

            for row in rows:
                sales.append(Sale(id=row[0], 
                                  date=row[1], 
                                  total=row[2], 
                                  seller_id=row[3]))

        except Exception as ex:
            generate_exception(ex)

    sales = list()
    exec_query(query)
    return sales

@app.get("/sale/{sale_id}")
def get_sale(sale_id: int):
    def query(cursor: Cursor):
        try:
            cursor.execute("SELECT * FROM User Where SaleID = ?", (sale_id,))
            data = cursor.fetchone()
            print(data)

        except Exception as ex:
            generate_exception(ex)

    # todo: validar existencia

    sale = None
    exec_query(query)
    return sale

@app.post("/sale/new", status_code=status.HTTP_201_CREATED)
def create_sale(sale: SaleDetail):
    def query(conn: Connection, cursor: Cursor):
        try:
            cursor.callproc("Create_Sale", (sale.date, sale.total, sale.seller_id)),
            cursor.execute("SELECT ID FROM User ORDER BY ID DESC LIMIT 1")            
            print(cursor.fetchone())

            if sale.products != None:
                for p_dict in sale.products:
                    pass

            conn.commit()
            
        except OperationalError:
            conn.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="No se puedo crear la venta")
        
        except Exception as ex:
            conn.rollback()
            generate_exception(ex)

    if sale.products == None and sale.combos == None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="La venta no implementa productos ni combos")

    sale = None
    exec_query(query, True)
    return { "message": "Venta creada satisfactoriamente" }


conn_params = {
    "user": "dbeaver_user",
    "password": "DBeaver123",
    "host": "localhost",
    "database": "TeraPollos"
}