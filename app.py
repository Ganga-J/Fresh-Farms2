import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

# This is a conceptual example and cannot be run in this environment.
# You need to have a MySQL server running and the 'mysql.connector' library installed.
# To install the library, run: pip install mysql-connector-python

app = Flask(__name__)
CORS(app)

# Database configuration
# IMPORTANT: Replace these with your actual MySQL credentials
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '5134',
    'database': 'freshharvest_db'
}

def get_db_connection():
    """Establishes and returns a new MySQL database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

def create_tables():
    """
    Creates the necessary tables if they do not exist.
    This function should be run once to set up your database.
    """
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()

    # Create users table

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            user_type VARCHAR(50) NOT NULL
        )
        """
    )


    print("Table 'users' checked/created successfully.")

    # Create products table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            unit VARCHAR(50),
            category VARCHAR(100),
            image_url VARCHAR(255),
            farmer_id VARCHAR(36) NOT NULL,
            FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    print("Table 'products' checked/created successfully.")

    conn.commit()
    cursor.close()
    conn.close()

# Call this function to set up your tables when you first run the server
# create_tables()

@app.route('/signup', methods=['POST'])
def signup():
    """Handles user registration and stores them in the MySQL database."""
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('userType')

    if not all([name, email, password, user_type]):
        return jsonify({'message': 'Missing required fields'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Database connection failed'}), 500

    cursor = conn.cursor()
    try:
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'message': 'User with that email already exists'}), 409

        # Hash the password and insert the new user
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        user_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO users (id, name, email, password_hash, user_type) VALUES (%s, %s, %s, %s, %s)",
            (user_id, name, email, password_hash, user_type)
        )
        conn.commit()
        return jsonify({'message': 'Account created successfully!'}), 201

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Error during signup: {err}")
        return jsonify({'message': 'An error occurred during signup'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    """Authenticates a user against the MySQL database."""
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password_hash'], password):
            # Do not return the password hash
            user_data = {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'userType': user['user_type']
            }
            return jsonify({'message': 'Login successful!', 'user': user_data}), 200
        else:
            return jsonify({'message': 'Invalid email or password'}), 401

    except mysql.connector.Error as err:
        print(f"Error during login: {err}")
        return jsonify({'message': 'An error occurred during login'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/products', methods=['GET'])
def get_products():
    """Fetches all products from the database."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        return jsonify(products), 200

    except mysql.connector.Error as err:
        print(f"Error fetching products: {err}")
        return jsonify({'message': 'An error occurred while fetching products'}), 500
    finally:
        cursor.close()
        conn.close()
        
@app.route('/products/<farmer_id>', methods=['GET'])
def get_my_products(farmer_id):
    """Fetches products for a specific farmer."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM products WHERE farmer_id = %s", (farmer_id,))
        products = cursor.fetchall()
        return jsonify(products), 200
    except mysql.connector.Error as err:
        print(f"Error fetching farmer products: {err}")
        return jsonify({'message': 'An error occurred while fetching products'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/add_product', methods=['POST'])
def add_product():
    """Handles adding a new product to the database."""
    data = request.json
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    unit = data.get('unit')
    category = data.get('category')
    image_url = data.get('image_url')
    farmer_id = data.get('farmer_id')
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Database connection failed'}), 500

    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO products (name, description, price, unit, category, image_url, farmer_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (name, description, price, unit, category, image_url, farmer_id)
        )
        conn.commit()
        return jsonify({'message': 'Product added successfully'}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Error adding product: {err}")
        return jsonify({'message': 'An error occurred while adding the product'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/update_product/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Handles updating an existing product."""
    data = request.json
    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Database connection failed'}), 500

    cursor = conn.cursor()
    try:
        # Build the update query dynamically based on provided fields
        query = "UPDATE products SET "
        fields = []
        values = []
        for key, value in data.items():
            fields.append(f"{key} = %s")
            values.append(value)
        
        query += ", ".join(fields)
        query += " WHERE id = %s"
        values.append(product_id)

        cursor.execute(query, tuple(values))
        conn.commit()

        if cursor.rowcount > 0:
            return jsonify({'message': 'Product updated successfully'}), 200
        else:
            return jsonify({'message': 'Product not found'}), 404
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Error updating product: {err}")
        return jsonify({'message': 'An error occurred while updating the product'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Handles deleting a product."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Database connection failed'}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return jsonify({'message': 'Product deleted successfully'}), 200
        else:
            return jsonify({'message': 'Product not found'}), 404
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Error deleting product: {err}")
        return jsonify({'message': 'An error occurred while deleting the product'}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
