import pymysql
from sshtunnel import SSHTunnelForwarder
from datetime import datetime, timedelta

def create_ssh_tunnel():
    # Konfigurasi SSH
    ssh_config = {
        'ssh_host': '36.92.168.182',
        'ssh_port': 22,
        'ssh_username': 'nociot',
        'ssh_password': 'telkom!@#321',
    }

    # Konfigurasi Database
    db_config = {
        'db_host': 'localhost',
        'db_port': 3306,
        'db_name': 'lansitec_cat1',
        'db_user': 'admin',
        'db_password': 'Wow0w0!2025'
    }

    try:
        # Membuat SSH tunnel
        tunnel = SSHTunnelForwarder(
            (ssh_config['ssh_host'], ssh_config['ssh_port']),
            ssh_username=ssh_config['ssh_username'],
            ssh_password=ssh_config['ssh_password'],
            remote_bind_address=('127.0.0.1', db_config['db_port'])
        )
        
        # Memulai tunnel
        tunnel.start()

        # Membuat koneksi database melalui tunnel
        connection = pymysql.connect(
            host=db_config['db_host'],
            port=tunnel.local_bind_port,
            user=db_config['db_user'],
            password=db_config['db_password'],
            database=db_config['db_name']
        )

        return tunnel, connection

    except Exception as e:
        print(f"Error saat membuat koneksi: {str(e)}")
        return None, None

def get_all_registration_data():
    tunnel, connection = create_ssh_tunnel()
    
    if tunnel is None or connection is None:
        print("Gagal membuat koneksi")
        return None
    
    try:
        with connection.cursor() as cursor:
            # Query untuk mengambil semua data dari tabel registration
            sql = "SELECT * FROM registration"
            cursor.execute(sql)
            result = cursor.fetchall()
            
            # Mengambil nama kolom
            column_names = [desc[0] for desc in cursor.description]
            
            # Membuat list of dictionaries untuk memudahkan pembacaan data
            formatted_result = []
            for row in result:
                formatted_result.append(dict(zip(column_names, row)))
            
            return formatted_result
            
    except Exception as e:
        print(f"Error saat mengambil data: {str(e)}")
        return None
        
    finally:
        connection.close()
        tunnel.close()

def insert_device_data(imei, serial_number):
    tunnel, connection = create_ssh_tunnel()
    
    if tunnel is None or connection is None:
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
        tunnel.close()

def get_device_count():
    tunnel, connection = create_ssh_tunnel()
    
    if tunnel is None or connection is None:
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
        tunnel.close()

def get_all_devices():
    tunnel, connection = create_ssh_tunnel()
    if tunnel is None or connection is None:
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
        tunnel.close()

def get_registration_data_by_imei(imei=None):
    tunnel, connection = create_ssh_tunnel()
    if tunnel is None or connection is None:
        return None
    
    try:
        with connection.cursor() as cursor:
            if (imei):
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
        tunnel.close()

if __name__ == "__main__":
    # Mengambil dan menampilkan data
    data = get_all_registration_data()
    if data:
        print(f"Total data yang ditemukan: {len(data)}")
        for row in data:
            print(row)