from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)


# Fonction pour récupérer les données et calculer la somme de 'rsi'
def get_data_from_db(start_date=None, end_date=None):
    conn = sqlite3.connect('../DYN1/bdd/ABTRADING.db')
    cursor = conn.cursor()

    # Construire la requête SQL en fonction des dates sélectionnées
    query = "SELECT * FROM TRADE WHERE 1=1 AND statue = 'Terminé' ORDER BY date_fin DESC;"  # '1=1' est juste pour simplifier l'ajout de conditions
    params = []

    # Si une date de début est fournie, ajouter un filtre pour la date de début
    if start_date:
        query = "SELECT * FROM TRADE WHERE 1=1 AND statue = 'Terminé' AND date_fin >= ?"
        params.append(start_date)

    # Si une date de fin est fournie, ajouter un filtre pour la date de fin
    if end_date:
        query += " AND date_fin <= ? ORDER BY date_fin DESC;"
        params.append(end_date)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]


    sum_gain = 0
    liste_gain= []
    format = "%Y-%m-%d %H:%M:%S.%f"
    format2 = "%Y-%m-%d %H:%M:%S"
    liste_date= []
    for row in rows:
        sum_gain += row[columns.index('gain')]
        liste_gain.append(row[columns.index('gain')])

        datetime_var1 = datetime.strptime(row[columns.index('date_debut')], format2)
        datetime_var2 = datetime.strptime(row[columns.index('date_fin')], format2)

        difference = (datetime_var2 - datetime_var1).total_seconds() / 60
        liste_date.append(difference)

    temps_moy = int(sum(liste_date)/len(liste_date))
    jours = temps_moy // (24 * 60)
    heures = (temps_moy % (24 * 60)) // 60
    minutes = temps_moy % 60
    temps_moy = f"{jours} jour(s), {heures} heure(s), {minutes} minute(s)"

    max_temps = int(max(liste_date))
    jours = max_temps // (24 * 60)
    heures = (max_temps % (24 * 60)) // 60
    minutes = max_temps % 60
    max_temps = f"{jours} jour(s), {heures} heure(s), {minutes} minute(s)"

    plusgg = round(max(liste_gain),2)
    pluspp = round(min(liste_gain),2)
    gain_moyen = round(round(sum_gain/len(rows),4),2)
    sum_gain = round(sum_gain,2)
    nombretrade = len(liste_gain)
    conn.close()
    return columns, rows, sum_gain, gain_moyen, plusgg, pluspp, max_temps, temps_moy, nombretrade


def get_data_long():
    conn = sqlite3.connect('../DYN1/bdd/ABTRADING.db')
    cursor = conn.cursor()

    # Construire la requête SQL en fonction des dates sélectionnées
    query = "SELECT * FROM TRADE WHERE 1=1 AND statue = 'En cours' ORDER BY date_debut DESC;"  # '1=1' est juste pour simplifier l'ajout de conditions
    params = []

    cursor.execute(query, params)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    format2 = "%Y-%m-%d %H:%M:%S"
    liste_date = []
    for row in rows:

        datetime_var1 = datetime.strptime(row[columns.index('date_debut')], format2)
        datetime_var2 = datetime.now()

        difference = (datetime_var2 - datetime_var1).total_seconds() / 60
        liste_date.append(difference)



    max_temps = int(max(liste_date))
    jours = max_temps // (24 * 60)
    heures = (max_temps % (24 * 60)) // 60
    minutes = max_temps % 60
    temps_long = f"{jours} jour(s), {heures} heure(s), {minutes} minute(s)"

    return temps_long, columns, rows


def get_data_row():
    conn = sqlite3.connect('../DYN1/bdd/ABTRADING.db')
    cursor = conn.cursor()

    # Construire la requête SQL en fonction des dates sélectionnées
    query = "SELECT * FROM memecoin ORDER BY date_debut DESC;"  # '1=1' est juste pour simplifier l'ajout de conditions
    params = []

    cursor.execute(query, params)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    return columns, rows

def count_rows_in_date_range(start_date=None, end_date=None):
    import sqlite3

    conn = sqlite3.connect('../DYN1/bdd/ABTRADING.db')
    cursor = conn.cursor()

    # Construire la requête SQL en fonction des dates sélectionnées
    query = "SELECT COUNT(*) FROM TRADE WHERE 1=1"  # '1=1' simplifie l'ajout des conditions
    params = []

    # Si une date de début est fournie, ajouter un filtre pour la date de début
    if start_date:
        query += " AND date_debut >= ?"
        params.append(start_date)

    # Si une date de fin est fournie, ajouter un filtre pour la date de fin
    if end_date:
        query += " AND date_debut <= ? ORDER BY date_fin DESC;"
        params.append(end_date)

    cursor.execute(query, params)
    row_count = cursor.fetchone()[0]  # Récupérer le nombre de lignes

    conn.close()
    return row_count

def compte_nb_en_cour():
    import sqlite3

    conn = sqlite3.connect('../DYN1/bdd/ABTRADING.db')
    cursor = conn.cursor()

    # Construire la requête SQL en fonction des dates sélectionnées
    query = "SELECT COUNT(*) FROM TRADE WHERE 1=1 AND statue = 'En cours' "  # '1=1' simplifie l'ajout des conditions

    cursor.execute(query)
    row_count = cursor.fetchone()[0]  # Récupérer le nombre de lignes

    conn.close()
    return row_count

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
        columns, rows, sum_gain, gain_moyen, plusgg, pluspp, max_temps, temps_moy, nombretrade = get_data_from_db(
            start_date, end_date)
        row_count = count_rows_in_date_range(start_date, end_date)
        nb_en_cour = compte_nb_en_cour()

        # Retourner le rendu du template avec les données
        return render_template('index.html', columns=columns, rows=rows, sum_gain=sum_gain, gain_moyen=gain_moyen,
                               plusgg=plusgg, pluspp=pluspp, max_temps=max_temps, temps_moy=temps_moy,
                               nombretrade=nombretrade, row_count=row_count, nb_en_cour=nb_en_cour)

    except Exception as e:
        # En cas d'erreur, afficher la page d'erreur
        return render_template('error.html', error_message=str(e)), 500
# Fonction pour se connecter à la base de données
def get_db_connection():
    conn = sqlite3.connect('../DYN1/bdd/ABTRADING.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/charts', methods=['GET'])
def charts():
    return render_template('charts.html')


@app.route('/get_daily_data')
def get_daily_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Exécuter la requête SQL pour obtenir la somme des gains et le nombre de lignes par date
    cursor.execute('''
 SELECT 
    date,
    SUM(total_by_date_fin) AS total_by_date_fin,
    SUM(line_count_by_date_debut) AS line_count_by_date_debut
FROM (
    SELECT 
        strftime('%Y-%m-%d', date_fin) AS date,
        SUM(gain) AS total_by_date_fin,
        NULL AS line_count_by_date_debut
    FROM TRADE
    GROUP BY strftime('%Y-%m-%d', date_fin)
    
    UNION ALL
    
    SELECT 
        strftime('%Y-%m-%d', date_debut) AS date,
        NULL AS total_by_date_fin,
        COUNT(*) AS line_count_by_date_debut
    FROM TRADE
    GROUP BY strftime('%Y-%m-%d', date_debut)
) combined
GROUP BY date
ORDER BY date ASC;
    ''')

    # Récupérer les résultats
    data = cursor.fetchall()

    # Organiser les résultats dans un format adapté pour le graphique
    labels = [row[0] for row in data]  # Dates
    sum_data = [row[1] for row in data]  # Somme des gains
    count_data = [row[2] for row in data]  # Nombre de lignes (transactions)

    # Retourner les données sous forme de JSON
    return jsonify({
        "labels": labels,
        "sum_data": sum_data,
        "count_data": count_data
    })


@app.route('/get_monthly_data', methods=['GET'])
def get_monthly_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Exécuter la requête SQL pour obtenir la somme des gains et le nombre de lignes par mois
    cursor.execute('''
    SELECT 
        date,
        SUM(total_by_month_fin) AS total_by_month_fin,
        SUM(line_count_by_month_debut) AS line_count_by_month_debut
    FROM (
        SELECT 
            strftime('%Y-%m', date_fin) AS date,  -- Regroupement par mois
            SUM(gain) AS total_by_month_fin,
            NULL AS line_count_by_month_debut
        FROM TRADE
        GROUP BY strftime('%Y-%m', date_fin)

        UNION ALL

        SELECT 
            strftime('%Y-%m', date_debut) AS date,  -- Regroupement par mois
            NULL AS total_by_month_fin,
            COUNT(*) AS line_count_by_month_debut
        FROM TRADE
        GROUP BY strftime('%Y-%m', date_debut)
    ) combined
    GROUP BY date
    ORDER BY date ASC;
    ''')

    # Récupérer les résultats
    data = cursor.fetchall()

    # Organiser les résultats dans un format adapté pour le graphique
    labels = [row[0] for row in data]  # Mois (année-mois)
    sum_data = [row[1] for row in data]  # Somme des gains par mois
    count_data = [row[2] for row in data]  # Nombre de lignes (transactions) par mois

    # Retourner les données sous forme de JSON
    return jsonify({
        "labels": labels,
        "sum_data": sum_data,
        "count_data": count_data
    })


@app.route('/cours', methods=['GET'])
def cours():

    Trade_le_plus_long, columns, rows = get_data_long()
    nb_en_cour = compte_nb_en_cour()
    return render_template('cours.html', columns=columns, rows=rows, Trade_le_plus_long=Trade_le_plus_long, nb_en_cour=nb_en_cour)


@app.route('/memecoin', methods=['GET'])
def memecoin():

    columns, rows = get_data_row()
    return render_template('memecoin.html', columns=columns, rows=rows)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
