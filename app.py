from flask import Flask, request, jsonify, render_template
import datetime
import matplotlib
matplotlib.use('Agg')  # Important - doit être défini avant les imports des modules
import absorption
import desorption

app = Flask(__name__)

# ==================== ROUTES FLASK ====================

@app.route('/')
def index():
    """Page d'accueil avec les deux options"""
    return render_template('index.html', active_page='home', current_year=datetime.datetime.now().year)

@app.route('/absorption')
def absorption_page():
    """Page pour l'absorption"""
    return render_template('absorption.html', active_page='absorption', current_year=datetime.datetime.now().year)

@app.route('/desorption')
def desorption_page():
    """Page pour la désorption"""
    return render_template('desorption.html', active_page='desorption', current_year=datetime.datetime.now().year)

@app.route('/calculer_absorption', methods=['POST'])
def calculer_absorption():
    """Endpoint pour calculer l'absorption"""
    data = request.json
    
    L = float(data['L'])
    G = float(data['G'])
    m = float(data['m'])
    y0 = float(data['y0'])
    x0 = float(data['x0'])
    objectif_type = data['objectif_type']
    
    # Initialisation des paramètres d'objectif
    valeur_cible = None
    taux_cible = None
    nb_etages_cible = None
    
    if objectif_type == 'fraction':
        valeur_cible = float(data['valeur_cible'])
    elif objectif_type == 'taux':
        taux_cible = float(data['taux_cible']) / 100
    elif objectif_type == 'etages':
        nb_etages_cible = int(data['nb_etages_cible'])
    
    resultats = absorption.tracer_diagramme_absorption(
        L, G, m, y0, x0, objectif_type, valeur_cible, taux_cible, nb_etages_cible
    )
    
    return jsonify(resultats)

@app.route('/calculer_desorption', methods=['POST'])
def calculer_desorption():
    """Endpoint pour calculer la désorption"""
    data = request.json
    
    L = float(data['L'])
    G = float(data['G'])
    m = float(data['m'])
    y0 = float(data['y0'])
    x0 = float(data['x0'])
    objectif_type = data['objectif_type']
    
    # Initialisation des paramètres d'objectif
    valeur_cible = None
    taux_cible = None
    nb_etages_cible = None
    
    if objectif_type == 'fraction':
        valeur_cible = float(data['valeur_cible'])
    elif objectif_type == 'taux':
        taux_cible = float(data['taux_cible']) / 100
    elif objectif_type == 'etages':
        nb_etages_cible = int(data['nb_etages_cible'])
    
    resultats = desorption.tracer_diagramme_desorption(
        L, G, m, y0, x0, objectif_type, valeur_cible, taux_cible, nb_etages_cible
    )
    
    return jsonify(resultats)

if __name__ == '__main__':
    app.run(debug=True)