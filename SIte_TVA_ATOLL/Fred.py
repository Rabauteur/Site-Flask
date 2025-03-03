import paramiko
import mysql.connector
from mysql.connector import Error

# Paramètres de connexion SSH
ssh_host = '192.99.220.213'
ssh_user = 'mbaronnet'  # Nom d'utilisateur pour SSH
ssh_password = 'mwt6Dh-7f>8GNSH'  # Mot de passe pour SSH (ou utilise une clé privée)

# Paramètres de connexion MySQL
mysql_host = '192.99.220.213'  # L'adresse MySQL sur le serveur, souvent localhost ou 127.0.0.1
mysql_user = 'root'  # Utilisateur MySQL, par exemple 'root'
mysql_password = '@T0ll#Msql!'  # Le mot de passe de l'utilisateur MySQL
mysql_database = 'ASTROMARY'  # Le nom de la base de données MySQL

try:
    # Connexion SSH au serveur distant
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Accepte la clé de l'hôte sans vérification
    ssh_client.connect(ssh_host, username=ssh_user, password=ssh_password)

    print("Connexion SSH réussie")

    # Une fois connecté en SSH, tu peux utiliser mysql.connector pour te connecter à MySQL

    # Connexion à la base de données MySQL via le serveur distant
    conn = mysql.connector.connect(
        host=mysql_host,  # Habituellement localhost si MySQL tourne sur le même serveur
        user=mysql_user,  # Utilisateur MySQL
        password=mysql_password,  # Mot de passe MySQL
        database=mysql_database  # Base de données à utiliser
    )

    if conn.is_connected():
        print("Connexion réussie à la base de données MySQL")

    # Création d'un curseur pour exécuter la requête
    cursor = conn.cursor()

    # Exemple de requête
    query = """
    SELECT id, first_name, last_name, date_order, email, ip_order, amount
    FROM orders
    WHERE order_status = 'VALID'
    AND payment_type = 'AXEPTA_BNP'
    AND date_order >= CURDATE() - INTERVAL 1 DAY - INTERVAL 6 HOUR
    """

    cursor.execute(query)
    results = cursor.fetchall()

    for row in results:
        print(row)

except paramiko.AuthenticationException as ssh_error:
    print(f"Erreur de connexion SSH : {ssh_error}")
except mysql.connector.Error as mysql_error:
    print(f"Erreur de connexion MySQL : {mysql_error}")
finally:
    # Fermeture des connexions
    if 'cursor' in locals() and cursor:
        cursor.close()
    if 'conn' in locals() and conn.is_connected():
        conn.close()
    if 'ssh_client' in locals() and ssh_client.get_transport().is_active():
        ssh_client.close()

    print("Connexions fermées.")
