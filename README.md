```markdown
# 🌊 Absorption & Désorption - Méthode de McCabe-Thiele

Application web interactive pour simuler les procédés d'absorption et désorption à courants croisés selon la méthode graphique de McCabe-Thiele. Calcule le nombre d'étages théoriques, génère des diagrammes d'équilibre animés, avec métriques de performance.

## ✨ Fonctionnalités

- **Calcul du nombre d'étages** par méthode McCabe-Thiele
- **Trois objectifs** : fraction cible, taux de séparation, nombre d'étages fixé
- **Animation progressive** de la construction graphique
- **Zoom et pan** interactifs sur le diagramme
- **Métriques de performance** : temps calcul (ms) et mémoire utilisée (MB)
- Interface moderne, responsive, design sombre

## 🛠 Stack Technique

- **Backend** : Python, Flask
- **Calculs** : NumPy, Matplotlib
- **Frontend** : HTML5, CSS3, JavaScript Canvas
- **Optimisations** : Cache LRU, recherche par bissection, discrétisation réduite

## 🚀 Installation

```bash
git clone https://github.com/HamchachMohamed/absorption-desorption-mccabe-thiele.git
cd absorption-desorption-mccabe-thiele
pip install -r requirements.txt
python app.py
```

Accédez à `http://127.0.0.1:5000`

## 📁 Structure

```
├── app.py                 # Routes Flask
├── absorption.py          # Logique d'absorption
├── desorption.py          # Logique de désorption
├── templates/             # Templates HTML
├── static/css/style.css   # Styles
└── requirements.txt       # Dépendances
```

## 👨‍💻 Auteur

**HAMCHACH Mohamed** - [GitHub](https://github.com/HamchachMohamed)
