
from flask import Flask, render_template, request, redirect, session, url_for

import mysql.connector
import config

app = Flask(__name__)
app.secret_key = "secret"

def get_db():
    return mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME
    )

# ---------------- DASHBOARD ----------------
# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('home.html')


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')



# ---------------- PRODUCT ----------------
# ---------------- PRODUCT ----------------
@app.route('/product', methods=['GET','POST'])
def product():
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        cur.execute("""
        INSERT INTO PRODUCT(product_name, category, unit_price, threshold_limit)
        VALUES(%s, %s, %s, %s)
        """, (
            request.form['name'],
            request.form['category'],
            request.form['price'],
            request.form['threshold']
        ))
        conn.commit()
        return redirect('/product')

    # Fetch products
    cur.execute("SELECT * FROM PRODUCT")
    data = cur.fetchall()

    return render_template('product.html', data=data)


#---EDIT PRODUCT---
@app.route('/edit_product/<int:id>', methods=['GET','POST'])
def edit_product(id):
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        cur.execute("""
        UPDATE PRODUCT
        SET product_name=%s, category=%s, unit_price=%s, threshold_limit=%s
        WHERE product_id=%s
        """, (
            request.form['name'],
            request.form['category'],
            request.form['price'],
            request.form['threshold'],
            id
        ))
        conn.commit()
        return redirect(url_for('product'))

    cur.execute("SELECT * FROM PRODUCT WHERE product_id=%s", (id,))
    product = cur.fetchone()

    return render_template('edit_product.html', product=product)


#--------DELETE PRODUCT --------
@app.route('/delete_product/<int:id>')
def delete_product(id):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM PRODUCT WHERE product_id=%s", (id,))
        conn.commit()
    except:
        return "Cannot delete: Product is used in purchase or sales!"

    cur.close()
    conn.close()

    return redirect(url_for('product'))

# ---------------- PURCHASE ----------------
@app.route('/purchase', methods=['GET','POST'])
def purchase():
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        try:
            product_id = request.form['product']
            supplier_id = request.form['supplier']
            warehouse_id = request.form['warehouse']
            qty = int(request.form['qty'])

            # get price safely
            cur.execute("SELECT unit_price FROM PRODUCT WHERE product_id=%s",(product_id,))
            res = cur.fetchone()

            if not res:
                return "Product not found!"

            price = res[0]
            total_cost = price * qty

            # insert purchase
            cur.execute("""
            INSERT INTO PURCHASE(product_id,supplier_id,warehouse_id,quantity_purchased,purchase_date,total_cost)
            VALUES(%s,%s,%s,%s,CURDATE(),%s)
            """,(product_id,supplier_id,warehouse_id,qty,total_cost))

            # update inventory
            cur.execute("""
            SELECT quantity FROM INVENTORY 
            WHERE product_id=%s AND warehouse_id=%s
            """,(product_id,warehouse_id))

            res = cur.fetchone()

            if res:
                cur.execute("""
                UPDATE INVENTORY
                SET quantity = quantity + %s
                WHERE product_id=%s AND warehouse_id=%s
                """,(qty,product_id,warehouse_id))
            else:
                cur.execute("""
                INSERT INTO INVENTORY(product_id,warehouse_id,quantity)
                VALUES(%s,%s,%s)
                """,(product_id,warehouse_id,qty))

            conn.commit()
            return redirect('/purchase')

        except Exception as e:
            return str(e)

    cur.execute("SELECT * FROM PURCHASE")
    data = cur.fetchall()

    cur.execute("SELECT * FROM PRODUCT")
    products = cur.fetchall()

    cur.execute("SELECT * FROM SUPPLIER")
    suppliers = cur.fetchall()

    cur.execute("SELECT * FROM WAREHOUSE")
    warehouses = cur.fetchall()

    return render_template('purchase.html',data=data,
                           products=products,
                           suppliers=suppliers,
                           warehouses=warehouses)


# ---------------- SUPPLIER ----------------
@app.route('/supplier', methods=['GET','POST'])
def supplier():
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        cur.execute("""
        INSERT INTO SUPPLIER(supplier_name, contact, address)
        VALUES(%s,%s,%s)
        """,(request.form['name'],
             request.form['contact'],
             request.form['address']))
        conn.commit()
        return redirect('/supplier')

    cur.execute("SELECT * FROM SUPPLIER")
    data = cur.fetchall()

    return render_template('supplier.html', data=data)

@app.route('/inventory')
def inventory():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT warehouse_id, warehouse_name
    FROM WAREHOUSE
    """)

    warehouses = cur.fetchall()

    return render_template('inventory.html', warehouses=warehouses)

@app.route('/inventory_view/<int:id>')
def inventory_view(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT p.product_name, i.quantity, p.threshold_limit
    FROM INVENTORY i
    JOIN PRODUCT p ON i.product_id = p.product_id
    WHERE i.warehouse_id = %s
    """,(id,))

    data = cur.fetchall()

    return render_template('inventory_view.html', data=data)

# ---------------- EDIT SUPPLIER ----------------
@app.route('/edit_supplier/<int:id>', methods=['GET','POST'])
def edit_supplier(id):
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        cur.execute("""
        UPDATE SUPPLIER
        SET supplier_name=%s, contact=%s, address=%s
        WHERE supplier_id=%s
        """, (
            request.form['name'],
            request.form['contact'],
            request.form['address'],
            id
        ))
        conn.commit()
        return redirect('/supplier')

    cur.execute("SELECT * FROM SUPPLIER WHERE supplier_id=%s", (id,))
    supplier = cur.fetchone()

    return render_template('edit_supplier.html', supplier=supplier)
# ---------------- DELETE  SUPPLIER ----------------
@app.route('/delete_supplier/<int:id>')
def delete_supplier(id):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM SUPPLIER WHERE supplier_id=%s", (id,))
        conn.commit()
    except:
        return "Cannot delete: Supplier is used in purchase!"

    cur.close()
    conn.close()

    return redirect(url_for('supplier'))
# ---------------- WAREHOUSE ----------------
@app.route('/warehouse', methods=['GET','POST'])
def warehouse():
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        cur.execute("""
        INSERT INTO WAREHOUSE(warehouse_name,location,capacity)
        VALUES(%s,%s,%s)
        """,(request.form['name'],request.form['location'],request.form['capacity']))
        conn.commit()
        return redirect('/warehouse')

    cur.execute("SELECT * FROM WAREHOUSE")
    data = cur.fetchall()

    return render_template('warehouse.html', data=data)


# ---------------- EDIT WAREHOUSE ----------------
@app.route('/edit_warehouse/<int:id>', methods=['GET','POST'])
def edit_warehouse(id):
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        cur.execute("""
        UPDATE WAREHOUSE
        SET warehouse_name=%s, location=%s, capacity=%s
        WHERE warehouse_id=%s
        """, (
            request.form['name'],
            request.form['location'],
            request.form['capacity'],
            id
        ))
        conn.commit()
        return redirect('/warehouse')

    cur.execute("SELECT * FROM WAREHOUSE WHERE warehouse_id=%s", (id,))
    warehouse = cur.fetchone()

    return render_template('edit_warehouse.html', warehouse=warehouse)
#----------DELETE WAREHOUSE ------
@app.route('/delete_warehouse/<int:id>')
def delete_warehouse(id):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM WAREHOUSE WHERE warehouse_id=%s", (id,))
        conn.commit()
    except:
        return "Cannot delete: Warehouse is used in inventory or sales!"

    cur.close()
    conn.close()

    return redirect(url_for('warehouse'))

@app.route('/sales', methods=['GET','POST'])
def sales():
    conn = get_db()
    cur = conn.cursor()

    if 'cart' not in session:
        session['cart'] = []

    message = ""

    if request.method == 'POST':

        # ADD TO CART
        if 'add' in request.form:
            pid = request.form['product']
            qty = int(request.form['qty'])

            cur.execute("SELECT product_name, unit_price FROM PRODUCT WHERE product_id=%s", (pid,))
            p = cur.fetchone()

            session['cart'].append({
                'id': pid,
                'name': p[0],
                'price': float(p[1]),
                'qty': qty,
                'total': qty * float(p[1])
            })
            session.modified = True

        # GENERATE BILL
        if 'bill' in request.form:

            if len(session['cart']) == 0:
                message = "Cart is empty!"
            else:
                warehouse = request.form['warehouse']

                # 🔥 CHECK STOCK BEFORE SELLING
                for item in session['cart']:

                    # current stock
                    cur.execute("""
                    SELECT quantity FROM INVENTORY
                    WHERE product_id=%s AND warehouse_id=%s
                    """,(item['id'], warehouse))
                    stock_data = cur.fetchone()

                    if not stock_data:
                        message = f"No stock found for {item['name']} in this warehouse!"
                        break

                    stock = stock_data[0]

                    # threshold
                    cur.execute("""
                    SELECT threshold_limit FROM PRODUCT
                    WHERE product_id=%s
                    """,(item['id'],))
                    threshold = cur.fetchone()[0]

                    # 🚫 BLOCK if stock goes below threshold
                    if stock - item['qty'] < threshold:
                        message = f"Cannot sell {item['name']}! Threshold limit reached."
                        break

                # ❌ IF ANY ERROR → STOP SALE
                if message != "":
                    cur.execute("SELECT * FROM PRODUCT")
                    products = cur.fetchall()

                    cur.execute("SELECT * FROM WAREHOUSE")
                    warehouses = cur.fetchall()

                    total = sum(i['total'] for i in session['cart'])

                    return render_template('sales.html',
                                           products=products,
                                           warehouses=warehouses,
                                           cart=session['cart'],
                                           total=total,
                                           message=message)

                # ✅ PROCEED SALE
                for item in session['cart']:
                    cur.execute("""
                    INSERT INTO SALES(product_id, warehouse_id, quantity_sold, sale_date, total_amount)
                    VALUES(%s,%s,%s,CURDATE(),%s)
                    """,(item['id'], warehouse, item['qty'], item['total']))

                    cur.execute("""
                    UPDATE INVENTORY
                    SET quantity = quantity - %s
                    WHERE product_id=%s AND warehouse_id=%s
                    """,(item['qty'], item['id'], warehouse))

                conn.commit()

                session['last_bill'] = {
                    "items": session['cart'],
                    "total": sum(i['total'] for i in session['cart'])
                }

                session['cart'] = []

                return redirect('/bill')

    cur.execute("SELECT * FROM PRODUCT")
    products = cur.fetchall()

    cur.execute("SELECT * FROM WAREHOUSE")
    warehouses = cur.fetchall()

    total = sum(i['total'] for i in session['cart'])

    return render_template('sales.html',
                           products=products,
                           warehouses=warehouses,
                           cart=session['cart'],
                           total=total,
                           message=message)
@app.route('/delete_cart_item/<int:index>')
def delete_cart_item(index):
    if 'cart' in session:
        cart = session['cart']

        if 0 <= index < len(cart):
            cart.pop(index)
            session['cart'] = cart
            session.modified = True

    return redirect('/sales')

@app.route('/low_stock_view/<int:id>')
def low_stock_view(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT p.product_name, i.quantity, p.threshold_limit
    FROM INVENTORY i
    JOIN PRODUCT p ON i.product_id = p.product_id
    WHERE i.warehouse_id = %s
    AND i.quantity <= p.threshold_limit
    """, (id,))

    data = cur.fetchall()

    return render_template('low_stock_view.html', data=data)

@app.route('/sales_history')
def sales_history():
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT s.sales_id,
               p.product_id,
               p.product_name,
               w.warehouse_name,
               s.quantity_sold,
               s.sale_date,
               s.total_amount
        FROM SALES s
        JOIN PRODUCT p ON s.product_id = p.product_id
        JOIN WAREHOUSE w ON s.warehouse_id = w.warehouse_id
        ORDER BY s.sales_id DESC
    """)

    sales = cur.fetchall()

    return render_template('sales_history.html', sales=sales)
@app.route('/bill')
def bill():
    bill_data = session.get('last_bill')

    if not bill_data:
        return "No bill found"

    return render_template('bill.html', bill=bill_data)


@app.route('/low_stock')
def low_stock():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT warehouse_id, warehouse_name
    FROM WAREHOUSE
    """)

    warehouses = cur.fetchall()

    return render_template('low_stock.html', warehouses=warehouses)

@app.route('/top_products')
def top_products():
    conn = get_db()
    cur = conn.cursor()

    warehouse_id = request.args.get('warehouse_id')

    # Get all warehouses
    cur.execute("SELECT warehouse_id, warehouse_name FROM WAREHOUSE")
    warehouses = cur.fetchall()

    data = []

    if warehouse_id:
        cur.execute("""
            SELECT 
                p.product_id, 
                p.product_name, 
                SUM(s.quantity_sold) AS total_qty, 
                w.warehouse_name,
                sup.supplier_name,
                sup.supplier_id
            FROM SALES s
            JOIN PRODUCT p ON s.product_id = p.product_id
            JOIN WAREHOUSE w ON s.warehouse_id = w.warehouse_id
            JOIN SUPPLIER sup ON p.supplier_id = sup.supplier_id
            WHERE s.warehouse_id = %s
            GROUP BY p.product_id, p.product_name, w.warehouse_name, sup.supplier_name, sup.supplier_id
            ORDER BY total_qty DESC
        """, (warehouse_id,))
        
        data = cur.fetchall()

    # ✅ ALWAYS RETURN (VERY IMPORTANT)
    return render_template(
        'top_products.html',
        warehouses=warehouses,
        data=data
    )

@app.route('/view_supplier/<int:supplier_id>')
def view_supplier(supplier_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM SUPPLIER WHERE supplier_id=%s", (supplier_id,))
    supplier = cur.fetchone()

    return render_template('view_supplier.html', supplier=supplier)


    return render_template('top_products.html',
                           warehouses=warehouses,
                           data=data)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)