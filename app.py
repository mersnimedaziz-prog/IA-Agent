from flask import Flask

# On crée l'application Flask
app = Flask(__name__)

# On définit la page d'accueil de notre API
@app.route('/')
def home():
    return "Félicitations ! Ton premier serveur de stage fonctionne !"

# On lance le serveur
if __name__ == '__main__':
    app.run(debug=True)