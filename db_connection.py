import pymysql
from datetime import datetime

def create_connection():
    # Konfigurasi Database Lokal
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'admin',  # Sesuaikan dengan user MySQL lokal Anda
        'password': 'Wow0w0!2025',  # Sesuaikan dengan password MySQL lokal Anda
        'database': 'lansitec_cat1'  # Sesuaikan dengan nama database Anda
    }

    try:
        # Membuat koneksi database langsung
        connection = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )

        return connection

    except Exception as e:
        print(f"Error saat membuat koneksi: {str(e)}")
        return None

def get_all_registration_data():
    connection = create_connection()
    
    if connection is None:
        print("Gagal membuat koneksi")
        return None
    
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM registration"
            cursor.execute(sql)
            result = cursor.fetchall()
            
            column_names = [desc[0] for desc in cursor.description]
            formatted_result = []
            for row in result:
                formatted_result.append(dict(zip(column_names, row)))
            
            return formatted_result
            
    except Exception as e:
        print(f"Error saat mengambil data: {str(e)}")
        return None
        
    finally:
        connection.close()

def insert_device_data(imei, serial_number):
    connection = create_connection()
    
    if connection is None:
        print("Failed to establish connection")
        return False
    
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO device (imei, serial_number) VALUES (%s, %s)"
            cursor.execute(sql, (imei, serial_number))
            connection.commit()
            return True
            
    except Exception as e:
        print(f"Error inserting data: {str(e)}")
        return False
        
    finally:
        connection.close()

def get_device_count():
    connection = create_connection()
    
    if connection is None:
        print("Failed to establish connection")
        return 0
    
    try:
        with connection.cursor() as cursor:
            sql = "SELECT COUNT(*) FROM device"
            cursor.execute(sql)
            result = cursor.fetchone()
            return result[0] if result else 0
            
    except Exception as e:
        print(f"Error getting device count: {str(e)}")
        return 0
        
    finally:
        connection.close()

def get_all_devices():
    connection = create_connection()
    
    if connection is None:
        return []
    
    try:
        with connection.cursor() as cursor:
            sql = "SELECT imei, serial_number FROM device"
            cursor.execute(sql)
            result = cursor.fetchall()
            return [{'imei': row[0], 'serial_number': row[1]} for row in result]
            
    except Exception as e:
        print(f"Error getting devices: {str(e)}")
        return []
        
    finally:
        connection.close()

def get_registration_data_by_imei(imei=None):
    connection = create_connection()
    
    if connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            if imei:
                sql = "SELECT * FROM registration WHERE payload_id_1 = %s"
                cursor.execute(sql, (imei,))
            else:
                sql = "SELECT * FROM registration"
                cursor.execute(sql)
            
            result = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            return [dict(zip(column_names, row)) for row in result]
            
    except Exception as e:
        print(f"Error getting registration data: {str(e)}")
        return None
        
    finally:
        connection.close()

if __name__ == "__main__":
    data = get_all_registration_data()
    if data:
        print(f"Total data yang ditemukan: {len(data)}")
        for row in data:
            print(row)
