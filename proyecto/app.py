from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # For flash messages

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='2003Leon$',
            database='mydb',
            connection_timeout=5,
            pool_size=5
        )
        return conn
    except Error as e:
        flash(f'Error connecting to database: {e}', 'error')
        return None

def validate_input(nombre, apellido, dni, telefono):
    """Validate input fields"""
    errors = []
    
    if not nombre or len(nombre) < 2:
        errors.append('Nombre debe tener al menos 2 caracteres')
    
    if not apellido or len(apellido) < 2:
        errors.append('Apellido debe tener al menos 2 caracteres')
    
    # DNI validation (assuming Argentine DNI format)
    if not re.match(r'^\d{7,8}$', dni):
        errors.append('DNI debe contener 7-8 dígitos numéricos')
    
    # Phone validation (assuming Argentine phone format)
    if not re.match(r'^(?:(?:\+54|0)?(?:9\d{10}|\d{10}))$', telefono):
        errors.append('Teléfono debe ser un número válido')
    
    return errors

@app.route('/', methods=['GET'])
def index():
    # Get query and sorting parameters
    query = request.args.get('query', '')
    sort_by = request.args.get('sort_by', 'id')  # Default sort by ID
    sort_order = request.args.get('sort_order', 'desc')  # Default descending order

    # Validate sort_by and sort_order to prevent SQL injection
    valid_columns = ['id', 'nombre', 'apellido']
    valid_orders = ['asc', 'desc']
    
    if sort_by not in valid_columns:
        sort_by = 'id'
    if sort_order not in valid_orders:
        sort_order = 'desc'

    conn = get_db_connection()
    if not conn:
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Construct dynamic SQL query with sorting
        base_query = """
            SELECT * FROM cliente 
            WHERE 1=1
        """
        
        # Add search condition if query exists
        if query:
            base_query += """ 
                AND (nombre LIKE '%{}%' 
                OR apellido LIKE '%{}%' 
                OR dni LIKE '%{}%')
            """.format(query, query, query)
        
        # Add sorting
        base_query += " ORDER BY {} {}".format(sort_by, sort_order)

        cursor.execute(base_query)
        clientes = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('index.html', 
                               clientes=clientes, 
                               query=query, 
                               sort_by=sort_by, 
                               sort_order=sort_order)
    
    except Error as e:
        flash(f'Error al recuperar clientes: {e}', 'error')
        return render_template('index.html', clientes=[], query=query)
@app.route('/agregar', methods=['GET', 'POST'])
def agregar_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        dni = request.form['dni']
        telefono = request.form['telefono']

        # Input validation
        input_errors = validate_input(nombre, apellido, dni, telefono)
        if input_errors:
            for error in input_errors:
                flash(error, 'error')
            return render_template('agregar_cliente.html', 
                                   nombre=nombre, 
                                   apellido=apellido, 
                                   dni=dni, 
                                   telefono=telefono)

        conn = get_db_connection()
        if not conn:
            return redirect(url_for('index'))
        
        try:
            cursor = conn.cursor()
            # Check for existing DNI
            cursor.execute("SELECT id FROM cliente WHERE dni = %s", (dni,))
            if cursor.fetchone():
                flash('Ya existe un cliente con este DNI', 'error')
                return render_template('agregar_cliente.html', 
                                       nombre=nombre, 
                                       apellido=apellido, 
                                       dni=dni, 
                                       telefono=telefono)
            
            cursor.execute("""
                INSERT INTO cliente (nombre, apellido, dni, telefono) 
                VALUES (%s, %s, %s, %s)
            """, (nombre, apellido, dni, telefono))
            conn.commit()
            flash('Cliente agregado exitosamente', 'success')
            
            cursor.close()
            conn.close()
            return redirect(url_for('index'))
        
        except Error as e:
            flash(f'Error al agregar cliente: {e}', 'error')
            return redirect(url_for('index'))

    return render_template('agregar_cliente.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    conn = get_db_connection()
    if not conn:
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            nombre = request.form['nombre']
            apellido = request.form['apellido']
            dni = request.form['dni']
            telefono = request.form['telefono']

            # Input validation
            input_errors = validate_input(nombre, apellido, dni, telefono)
            if input_errors:
                for error in input_errors:
                    flash(error, 'error')
                return render_template('editar_cliente.html', cliente={'id': id, 'nombre': nombre, 'apellido': apellido, 'dni': dni, 'telefono': telefono})

            # Check for existing DNI (excluding current record)
            cursor.execute("SELECT id FROM cliente WHERE dni = %s AND id != %s", (dni, id))
            if cursor.fetchone():
                flash('Ya existe otro cliente con este DNI', 'error')
                return render_template('editar_cliente.html', cliente={'id': id, 'nombre': nombre, 'apellido': apellido, 'dni': dni, 'telefono': telefono})

            cursor.execute("""
                UPDATE cliente
                SET nombre = %s, apellido = %s, dni = %s, telefono = %s
                WHERE id = %s
            """, (nombre, apellido, dni, telefono, id))
            conn.commit()
            flash('Cliente actualizado exitosamente', 'success')
            
            cursor.close()
            conn.close()
            return redirect(url_for('index'))

        # GET method
        cursor.execute("SELECT * FROM cliente WHERE id = %s", (id,))
        cliente = cursor.fetchone()
        
        if not cliente:
            flash('Cliente no encontrado', 'error')
            return redirect(url_for('index'))
        
        cursor.close()
        conn.close()
        return render_template('editar_cliente.html', cliente=cliente)
    
    except Error as e:
        flash(f'Error al editar cliente: {e}', 'error')
        return redirect(url_for('index'))

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_cliente(id):
    conn = get_db_connection()
    if not conn:
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cliente WHERE id = %s", (id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            flash('Cliente eliminado exitosamente', 'success')
        else:
            flash('Cliente no encontrado', 'error')
        
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
    
    except Error as e:
        flash(f'Error al eliminar cliente: {e}', 'error')
        return redirect(url_for('index'))

@app.route('/conexiones/<int:id>', methods=['GET'])
def ver_conexiones(id):
    conn = get_db_connection()
    if not conn:
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cliente WHERE id = %s", (id,))
        cliente = cursor.fetchone()
        cursor.execute("SELECT * FROM conexion WHERE idCliente = %s", (id,))
        conexiones = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('conexiones.html', conexiones=conexiones, cliente_nombre=cliente['nombre'], cliente_apellido=cliente['apellido'])
    
    except Error as e:
        flash(f'Error al obtener conexiones: {e}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)