import pymysql as mysql #Importa Pymysql y lo renombra mysql


def get_connection():
    return mysql.connect(
        host="localhost",
        port=3306,#Puerto de comunicacion con Xampp
        user="root",#Tipo de usuario en Gestor de base de datos
        db="ebanisteria", #Nombre de la base de datos
        password="",#Indica contraseña sin caracteres
        cursorclass=mysql.cursors.DictCursor # Convierte directamente los datos en diccionarios de datos
    )
