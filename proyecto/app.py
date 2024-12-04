from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# Conexión a la base de datos MySQL
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='2003Leon$',  # Reemplaza con tu contraseña de MySQL
        database='mydb'  # Nombre de tu base de datos
    )
    return conn

@app.route('/', methods=['GET'])
def index():
    query = request.args.get('query', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Realizamos la consulta con un filtro si hay una búsqueda
    if query:
        cursor.execute("""
            SELECT * FROM cliente 
            WHERE nombre LIKE %s OR apellido LIKE %s OR dni LIKE %s
        """, ('%' + query + '%', '%' + query + '%', '%' + query + '%'))
    else:
        cursor.execute("SELECT * FROM cliente")

    clientes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', clientes=clientes)

@app.route('/agregar', methods=['GET', 'POST'])
def agregar_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        dni = request.form['dni']
        telefono = request.form['telefono']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cliente (nombre, apellido, dni, telefono) 
            VALUES (%s, %s, %s, %s)
        """, (nombre, apellido, dni, telefono))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('index'))

    return render_template('agregar_cliente.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        dni = request.form['dni']
        telefono = request.form['telefono']

        cursor.execute("""
            UPDATE cliente
            SET nombre = %s, apellido = %s, dni = %s, telefono = %s
            WHERE id = %s
        """, (nombre, apellido, dni, telefono, id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM cliente WHERE id = %s", (id,))
    cliente = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('editar_cliente.html', cliente=cliente)

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_cliente(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cliente WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

