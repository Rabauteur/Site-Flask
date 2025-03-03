from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime, timedelta
import paramiko
import subprocess
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)


def geoiplookup_command(ip):
    # Préparer la commande bash avec l'IP spécifiée
    command = f"geoiplookup {ip} | awk -F: '{{print $2}}' | awk -F, '{{print $2}}'"

    try:
        # Exécuter la commande bash et récupérer la sortie
        result = subprocess.check_output(command, shell=True, text=True)

        # Supprimer les espaces inutiles
        result = result.strip()

        return result
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de la commande : {e}")
        return None

def get_data_from_db(start_date=None, end_date=None):

    ssh_intermediate_host = '192.99.220.209'  # Adresse IP ou hostname du serveur intermédiaire
    ssh_intermediate_user = 'mbaronnet'
    ssh_intermediate_password = 'mwt6Dh-7f>8GNSH'


    ssh_host = '192.99.220.213'
    ssh_user = 'mbaronnet'  # Nom d'utilisateur pour SSH
    ssh_password = 'mwt6Dh-7f>8GNSH'  # Mot de passe pour SSH (ou utilise une clé privée)

    # Paramètres de connexion MySQL
    mysql_host = '192.99.220.213'  # L'adresse MySQL sur le serveur, souvent localhost ou 127.0.0.1
    mysql_user = 'root'  # Utilisateur MySQL, par exemple 'root'
    mysql_password = '@T0ll#Msql!'  # Le mot de passe de l'utilisateur MySQL
    mysql_database = 'ASTROMARY'  # Le nom de la base de données MySQL

    try:
        # Connexion SSH au serveur intermédiaire
        ssh_intermediate_client = paramiko.SSHClient()
        ssh_intermediate_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_intermediate_client.connect(
            hostname=ssh_intermediate_host,
            username=ssh_intermediate_user,
            password=ssh_intermediate_password
        )
        print("Connexion SSH au serveur intermédiaire réussie")

        # Lancer une commande sur le serveur intermédiaire pour accéder au serveur final
        cmd_to_connect_final = f"sudo ssh {ssh_user}@{ssh_host}"
        stdin, stdout, stderr = ssh_intermediate_client.exec_command(cmd_to_connect_final)

        # Vérifier si la commande s'est exécutée sans erreur
        if stderr.channel.recv_exit_status() != 0:
            print("Erreur lors de la connexion au serveur final via le serveur intermédiaire :")
            print(stderr.read().decode())
            return

        print("Connexion SSH au serveur final réussie (via serveur intermédiaire)")

        # Connexion à la base de données MySQL via le serveur final
        conn = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )

        if conn.is_connected():
            print("Connexion réussie à la base de données MySQL")

        # Création d'un curseur pour exécuter la requête
        cursor = conn.cursor()

        # Construire la requête SQL en fonction des dates sélectionnées
        query = "select id, first_name, last_name, date_order, email, ip_order, amount from orders where order_status = 'VALID' and payment_type = 'AXEPTA_BNP' and date_order >= CURDATE() - INTERVAL 6 HOUR ORDER BY date_order DESC;"  # '1=1' est juste pour simplifier l'ajout de conditions
        params = []

        # Si une date de début est fournie, ajouter un filtre pour la date de début
        if start_date:
            query = "select id, first_name, last_name, date_order, email, ip_order, amount from orders where order_status = 'VALID' and payment_type = 'AXEPTA_BNP' and date_order >= DATE_SUB(%s, INTERVAL 6 HOUR)"
            params.append(start_date)

        # Si une date de fin est fournie, ajouter un filtre pour la date de fin
        if end_date:
            query += " AND date_order <= DATE_SUB(%s, INTERVAL 6 HOUR) ORDER BY date_order DESC;"
            params.append(end_date)
        cursor.execute(query, params)
        rows = cursor.fetchall()


    except paramiko.AuthenticationException as ssh_error:
        print(f"Erreur de connexion SSH : {ssh_error}")
    except mysql.connector.Error as mysql_error:
        print(f"Erreur de connexion MySQL : {mysql_error}")

    pays_ue = [
        "Allemagne", "Autriche", "Belgique", "Bulgarie", "Chypre", "Croatie",
        "Danemark", "Espagne", "Estonie", "Finlande", "France", "Grèce",
        "Hongrie", "Irlande", "Italie", "Lettonie", "Lituanie", "Luxembourg",
        "Malte", "Pays-Bas", "Pologne", "Portugal", "République tchèque",
        "Roumanie", "Slovaquie", "Slovénie", "Suède"
    ]

    columns = [desc[0] for desc in cursor.description]+ ['ip_pays_achat']
    sum_tva = 0
    liste_date= []
    liste_UE= []
    liste_Hors_UE= []
    for i, row in enumerate(rows):
        ip_order = row[columns.index('ip_order')]
        date_order = datetime.strptime(f'{row[columns.index('date_order')]}', '%Y-%m-%d %H:%M:%S')
        nouvelle_date = date_order + timedelta(hours=6)
        ip_pays = f'{geoiplookup_command(ip_order)}'
        if ip_pays in pays_ue:
            liste_UE.append(ip_pays)
            sum_tva += row[columns.index('amount')]
        else:
            liste_Hors_UE.append(ip_pays)
        row = list(row)
        row[3] = nouvelle_date.strftime('%Y-%m-%d %H:%M:%S')
        row.append(ip_pays)
        rows[i] = tuple(row)


        # Ajouter la ligne avec la nouvelle colonne ipx2

    nombre_commande = len(rows)
    nombre_UE = len(liste_UE)
    nombre_Hors_ue = len(liste_Hors_UE)

    # Fermeture des connexions
    if 'cursor' in locals() and cursor:
        cursor.close()
    if 'conn' in locals() and conn.is_connected():
        conn.close()
    if 'ssh_client' in locals() and ssh_client.get_transport().is_active():
        ssh_client.close()

    print("Connexions fermées.")

    return columns, rows, sum_tva, nombre_commande, nombre_UE, nombre_Hors_ue



@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_message="Une erreur interne est survenue."), 500

# Gestionnaire d'erreurs pour les erreurs 404 (page non trouvée)
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_message="Page non trouvée."), 404


@app.route('/', methods=['GET'])
def index():
    try:
        # Récupérer les dates depuis les paramètres de la requête GET
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Si les dates sont présentes, les convertir au format 'YYYY-MM-DD' pour la requête SQL
        if start_date:
            try:
                # Valider et formater la date de début
                datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                start_date = None

        if end_date:
            try:
                # Valider et formater la date de fin
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                end_date = None

        # Appeler les fonctions pour récupérer les données de la base de données
        columns, rows, sum_tva, nombre_commande, nombre_UE, nombre_Hors_ue = get_data_from_db(
            start_date, end_date)


        # Retourner le rendu du template avec les données
        return render_template('index.html', columns=columns, rows=rows, sum_tva=sum_tva, nombre_commande=nombre_commande, nombre_UE=nombre_UE, nombre_Hors_ue=nombre_Hors_ue)

    except Exception as e:
        # En cas d'erreur, afficher la page d'erreur
        return render_template('error.html', error_message=str(e)), 500
# Fonction pour se connecter à la base de données


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
