# desorption.py
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Important pour Flask - doit être avant l'import de pyplot
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from functools import lru_cache
import time
import psutil
import os

# ==================== RÉUTILISATION DES FONCTIONS D'ABSORPTION ====================

@lru_cache(maxsize=256)
def fractions_to_rapports_molaires_cached(y, x):
    """Convertit les fractions molaires en rapports molaires avec cache"""
    Y = y / (1 - y) if y < 1 else float('inf')
    X = x / (1 - x) if x < 1 else float('inf')
    return Y, X

def fractions_to_rapports_molaires(y, x):
    """Interface publique pour la conversion fractions -> rapports molaires"""
    return fractions_to_rapports_molaires_cached(y, x)


@lru_cache(maxsize=256)
def rapports_molaires_to_fractions_cached(Y, X):
    """Convertit les rapports molaires en fractions molaires avec cache"""
    y = Y / (1 + Y) if Y != float('inf') and Y != float('inf') else 1
    x = X / (1 + X) if X != float('inf') and X != float('inf') else 1
    return y, x

def rapports_molaires_to_fractions(Y, X):
    """Interface publique pour la conversion rapports -> fractions molaires"""
    return rapports_molaires_to_fractions_cached(Y, X)


@lru_cache(maxsize=512)
def courbe_equilibre_Y_cached(X, m):
    """Calcule Y à partir de X pour la courbe d'équilibre avec cache"""
    if X == float('inf') or X > 100:  # Limite pour éviter les débordements
        return float('inf')
    
    # Approximation linéaire pour les petites valeurs
    if m > 0.95 and X < 0.1:
        return m * X
    
    x = X / (1 + X)
    
    if m * x >= 0.99:
        return float('inf')
    
    y = m * x
    if y >= 0.999:
        return float('inf')
    
    Y = y / (1 - y)
    return Y

def courbe_equilibre_Y(X, m):
    """Interface publique pour le calcul de la courbe d'équilibre"""
    return courbe_equilibre_Y_cached(X, m)


def est_monotone_croissante_optimise(Y_eq, tolerance=1e-6):
    """Version optimisée - vérifie seulement 1 point sur 10"""
    if len(Y_eq) < 10:
        return True
    
    step = max(1, len(Y_eq) // 10)
    for i in range(step, len(Y_eq), step):
        if Y_eq[i] < Y_eq[i-step] - tolerance:
            return False
    return True


def trouver_intersection_bissection(X_depart, Y_depart, pente, X_min, X_max, m, 
                                    utiliser_droite_simplifiee, max_iter=50, tolerance=1e-8):
    """Trouve l'intersection par bissection (beaucoup plus rapide)"""
    if X_min >= X_max:
        return None
    
    def f(X):
        Y_droite = pente * (X - X_depart) + Y_depart
        if utiliser_droite_simplifiee:
            Y_eq = m * X
        else:
            Y_eq = courbe_equilibre_Y(X, m)
        
        if Y_eq == float('inf'):
            return float('inf')
        return Y_droite - Y_eq
    
    try:
        f_min = f(X_min)
        f_max = f(X_max)
    except:
        return None
    
    if f_min == float('inf') or f_max == float('inf'):
        return None
    
    if f_min * f_max > 0:
        return None
    
    for _ in range(max_iter):
        X_mid = (X_min + X_max) / 2
        try:
            f_mid = f(X_mid)
        except:
            return None
        
        if f_mid == float('inf'):
            return None
        
        if abs(f_mid) < tolerance:
            return X_mid
        
        if f_min * f_mid <= 0:
            X_max = X_mid
            f_max = f_mid
        else:
            X_min = X_mid
            f_min = f_mid
    
    return (X_min + X_max) / 2


def get_memory_usage():
    """Retourne l'utilisation mémoire du processus en Mo"""
    try:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except:
        return 0


# ==================== FONCTION PRINCIPALE DE DÉSORPTION OPTIMISÉE ====================

def tracer_diagramme_desorption(L, G, m, y0, x0, objectif_type, valeur_cible=None, taux_cible=None, nb_etages_cible=None):
    """
    Trace le diagramme de désorption à courants croisés et retourne l'image en base64 et les résultats
    Version optimisée pour la vitesse et l'utilisation mémoire
    
    objectif_type: 'fraction', 'taux', ou 'etages'
    """
    start_time = time.time()
    mem_start = get_memory_usage()
    
    # Conversion en rapports molaires
    Y0, X0 = fractions_to_rapports_molaires(y0, x0)
    pente = -G / L  # Pente négative pour la désorption (-G/L)
    
    print(f"=== Désorption à courants croisés (optimisé) ===")
    print(f"L = {L}, G = {G}, m = {m}")
    print(f"y0 = {y0}, x0 = {x0}")
    print(f"Y0 = {Y0:.4f}, X0 = {X0:.4f}")
    print(f"Pente -G/L = {pente:.4f}")
    
    # Génération des points pour la courbe d'équilibre (réduit à 200 points)
    X_max = max(0.5, X0 * 1.5)
    X_eq = np.linspace(0, min(X_max, 10), 200)  # Limité à 200 points
    Y_eq = [courbe_equilibre_Y(X, m) for X in X_eq]
    
    # Filtrer les valeurs infinies (vectorisé)
    X_eq = np.array(X_eq)
    Y_eq = np.array(Y_eq)
    mask = ~np.isinf(Y_eq) & (Y_eq < 10)
    X_eq_filtre = X_eq[mask].tolist()
    Y_eq_filtre = Y_eq[mask].tolist()
    
    # Vérifier si la courbe est monotone croissante (version optimisée)
    courbe_monotone = est_monotone_croissante_optimise(Y_eq_filtre)
    utiliser_droite_simplifiee = not courbe_monotone
    
    if utiliser_droite_simplifiee:
        print("⚠️ Courbe d'équilibre non monotone détectée - Utilisation de la droite simplifiée Y = mX")
    
    # Initialisation
    X_entree = X0  # X à l'entrée de l'étage courant
    X_points = [X0]  # Points X à chaque étage
    
    etages = 0
    convergence = False
    resultats_etages = []
    animation_data = []
    
    max_etages = 50  # Maximum autorisé
    X_prev = X0  # Pour détecter la stagnation
    
    # Si l'objectif est le nombre d'étages, on utilise cette valeur comme limite
    if objectif_type == 'etages' and nb_etages_cible is not None:
        max_etages = int(nb_etages_cible)
        print(f"Objectif: {max_etages} étages")
    
    # Calcul des étages avec bissection
    for etage in range(1, max_etages + 1):
        # Point de départ de l'étage (X_entree, 0)
        X_depart = X_entree
        Y_depart = 0  # Le gaz entre toujours avec Y=0
        
        # Recherche de l'intersection par bissection
        X_intersection = trouver_intersection_bissection(
            X_depart, Y_depart, pente,
            0, X_depart, m,  # X diminue, donc intervalle [0, X_depart]
            utiliser_droite_simplifiee
        )
        
        # Fallback sur la méthode linéaire si la bissection échoue
        if X_intersection is None:
            print(f"Fallback vers méthode linéaire à l'étage {etage}")
            X_test = np.linspace(0, X_depart, 1000)  # Réduit à 1000 points
            Y_droite = pente * (X_test - X_depart) + Y_depart
            
            for i in range(len(X_test)-1):
                if utiliser_droite_simplifiee:
                    Y_eq_test = m * X_test[i]
                    Y_eq_next = m * X_test[i+1]
                else:
                    Y_eq_test = courbe_equilibre_Y(X_test[i], m)
                    Y_eq_next = courbe_equilibre_Y(X_test[i+1], m)
                
                if Y_eq_test != float('inf') and Y_eq_next != float('inf') and Y_eq_test >= 0:
                    diff1 = Y_droite[i] - Y_eq_test
                    diff2 = Y_droite[i+1] - Y_eq_next
                    if diff1 * diff2 <= 0:
                        X_intersection = X_test[i]
                        break
        
        if X_intersection is None:
            print(f"Attention: Pas d'intersection trouvée à l'étage {etage}")
            break
        
        if utiliser_droite_simplifiee:
            Y_intersection = m * X_intersection
        else:
            Y_intersection = courbe_equilibre_Y(X_intersection, m)
        
        # Sauvegarder le point d'intersection
        X_points.append(X_intersection)
        
        y_sortie, x_sortie = rapports_molaires_to_fractions(Y_intersection, X_intersection)
        
        # Stockage optimisé (6 décimales seulement)
        resultats_etages.append({
            'etage': etage,
            'X': round(float(X_intersection), 6),
            'Y': round(float(Y_intersection), 6),
            'x': round(float(x_sortie), 6),
            'y': round(float(y_sortie), 6)
        })
        
        # Données pour l'animation - format tuple plus compact
        animation_data.append((
            etage,
            round(float(X_depart), 6),
            round(float(Y_depart), 6),
            round(float(X_intersection), 6),
            round(float(Y_intersection), 6),
            round(float(pente), 6)
        ))
        
        print(f"Étage {etage}: X = {X_intersection:.6f}, Y = {Y_intersection:.6f}, "
              f"x = {x_sortie:.6f}, y = {y_sortie:.6f}")
        
        # Mise à jour pour l'étage suivant
        X_entree = X_intersection
        etages = etage
        
        # Détection de stagnation
        if abs(X_intersection - X_prev) < 1e-10 and etage > 3:
            print(f"Stagnation détectée à l'étage {etage}")
            convergence = True
        
        X_prev = X_intersection
        
        # Vérification de l'objectif
        if objectif_type == 'fraction':
            if x_sortie <= valeur_cible:
                convergence = True
                print(f"Objectif fraction atteint: x = {x_sortie:.6f} ≤ {valeur_cible:.4f}")
                break
        elif objectif_type == 'taux':
            taux = (x0 - x_sortie) / x0
            if taux >= taux_cible:
                convergence = True
                print(f"Objectif taux atteint: {taux*100:.2f}% ≥ {taux_cible*100:.1f}%")
                break
        elif objectif_type == 'etages':
            # L'objectif est d'atteindre le nombre d'étages demandé
            if etage >= nb_etages_cible:
                convergence = True
                print(f"Objectif nombre d'étages atteint: {etage} étages")
                break
    
    print(f"Nombre total d'étages calculés: {etages}")
    
    # ==================== CRÉATION DU DIAGRAMME OPTIMISÉ ====================
    
    # Taille de figure réduite
    plt.figure(figsize=(10, 6))
    
    # Courbe d'équilibre
    if X_eq_filtre and Y_eq_filtre:
        if utiliser_droite_simplifiee:
            plt.plot(X_eq_filtre, Y_eq_filtre, 'r-', linewidth=2, 
                    label="Droite d'équilibre simplifiée Y = mX")
            # Note plus discrète
            plt.text(0.5, 0.95, "⚠️ Droite simplifiée", 
                    transform=plt.gca().transAxes, fontsize=9, ha='center',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="yellow", alpha=0.5))
        else:
            plt.plot(X_eq_filtre, Y_eq_filtre, 'b-', linewidth=2, 
                    label="Courbe d'équilibre Y = f(X)")
    
    # Axes
    plt.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    plt.axvline(x=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    
    # Ligne verticale X = X0 (liquide entrant)
    plt.axvline(x=X0, color='gray', linestyle=':', linewidth=1.5, alpha=0.7, 
                label=f'X₀ = {X0:.4f}')
    
    # Ajouter la cible si c'est une fraction
    if objectif_type == 'fraction' and valeur_cible is not None:
        X_cible = valeur_cible / (1 - valeur_cible) if valeur_cible < 1 else float('inf')
        if X_cible != float('inf') and X_cible < 10:
            plt.axvline(x=X_cible, color='red', linestyle='--', linewidth=1.5, alpha=0.7, 
                       label=f"X cible = {X_cible:.4f}")
    
    # Point de départ
    plt.scatter([X0], [0], color='red', s=150, zorder=10, marker='o',
               label="Point de départ", edgecolors='black', linewidth=1.5)
    
    # Configuration des axes
    plt.xlabel('X (rapport molaire dans le liquide)', fontsize=11)
    plt.ylabel('Y (rapport molaire dans le gaz)', fontsize=11)
    plt.title('Diagramme de désorption à courants croisés', fontsize=13, fontweight='bold')
    
    # Grille
    plt.grid(True, alpha=0.2, linestyle='--', which='both')
    
    # Ajuster les limites
    if X_eq_filtre:
        x_max = max(X_eq_filtre[-1] if X_eq_filtre else 0.5, X0) * 1.1
        y_max = max(max(Y_eq_filtre) if Y_eq_filtre else 1, 1.0) * 1.1
    else:
        x_max = X0 * 1.5
        y_max = 1.0
    
    # Limiter à 10 pour éviter les débordements
    plt.xlim(0, min(x_max, 10))
    plt.ylim(0, min(y_max, 10))
    
    # Métriques de performance
    mem_end = get_memory_usage()
    exec_time = time.time() - start_time
    
    # Ajouter une annotation avec les performances
    texte_param = f"L={L:.1f} G={G:.1f} m={m:.2f} | -G/L={pente:.3f}\n"
    texte_param += f"Temps: {exec_time*1000:.1f}ms | Mémoire: {mem_end-mem_start:.1f}Mo"
    
    if objectif_type == 'fraction':
        texte_param += f"\nObjectif: x ≤ {valeur_cible}"
    elif objectif_type == 'taux':
        texte_param += f"\nObjectif: taux ≥ {taux_cible*100:.1f}%"
    else:
        texte_param += f"\nObjectif: {nb_etages_cible} étages"
    
    plt.text(0.02, 0.98, texte_param, transform=plt.gca().transAxes,
            fontsize=8, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8, edgecolor='orange'))
    
    plt.legend(loc='best', fontsize=8, framealpha=0.8)
    plt.tight_layout()
    
    # Convertir l'image en base64 avec compression
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=90, bbox_inches='tight', 
                facecolor='white')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    graphic = base64.b64encode(image_png).decode('utf-8')
    
    # Reformattage des données d'animation pour le frontend
    animation_data_formatted = []
    for item in animation_data:
        animation_data_formatted.append({
            'etage': item[0],
            'X_depart': item[1],
            'Y_depart': item[2],
            'X_arrivee': item[3],
            'Y_arrivee': item[4],
            'pente': item[5]
        })
    
    # Résultat final avec métriques de performance
    return {
        'graphic': graphic,
        'etages': etages,
        'resultats': resultats_etages,
        'animation_data': animation_data_formatted,
        'Y0': float(Y0),
        'X0': float(X0),
        'pente': float(pente),
        'convergence': convergence,
        'x_max': float(min(x_max, 10)),
        'y_max': float(min(y_max, 10)),
        'courbe_simplifiee': utiliser_droite_simplifiee,
        'performance': {
            'execution_time_ms': round(exec_time * 1000, 2),
            'memory_used_mb': round(mem_end - mem_start, 2),
            'total_memory_mb': round(mem_end, 2)
        }
    }