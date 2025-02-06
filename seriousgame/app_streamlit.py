import streamlit as st
from pymongo import MongoClient
import os
import pandas as pd
import plotly.express as px
import hashlib
from bson.objectid import ObjectId
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# MongoDB Connection


from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://ortaraki:Omaromar12@cluster0.6tzyu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
db = client["games_database"]  # Explicitly specify the database name
collection = db["games"]


# Upload Folders
UPLOAD_FOLDER_GUIDES = "uploads/guides"
UPLOAD_FOLDER_IMAGES = "uploads/images"

# Create upload folders if they don't exist
os.makedirs(UPLOAD_FOLDER_GUIDES, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_IMAGES, exist_ok=True)

# Page principale
st.title("SeriousGame édition 2025")
st.markdown(
    """
    ### 🎲 Workshop SERIOUS GAME RSE – Explorez la RSE par le jeu !
    Plongez dans une **expérience ludique et interactive** pour découvrir les enjeux de la **Responsabilité Sociétale des Entreprises (RSE)**.
    À travers des jeux dynamiques, explorez des thématiques clés :  
    **Les parties prenantes, les Objectifs de Développement Durable (ODD), le Reporting ESG, les Achats Responsables (ISO 20400),  
    l'Économie Circulaire, l’Efficacité Énergétique, l’Action Climat en entreprise, et bien plus encore.**  

    🔎 **Un atelier unique pour apprendre, échanger et innover autour de la RSE !**
    """,
    unsafe_allow_html=True
)

# Sidebar Menu
st.sidebar.title("Menu")
option = st.sidebar.selectbox(
    "Choisissez une option :",
    ["Accueil", "Ajouter un jeu", "Scoring", "Leaderboard", "Empreinte Carbone"]
)

# 🌟 **PAGE D'ACCUEIL : AFFICHAGE DES JEUX**
if option == "Accueil":
    st.header("📌 Liste des jeux enregistrés")
    games = list(collection.find({}))

    if not games:
        st.write("Aucun jeu n'a été ajouté pour le moment.")
    else:
        for game in games:
            with st.expander(f"🎮 {game['name']}"):
                st.image(game["affiche"], caption="Affiche du jeu", use_container_width=True)
                st.write(f"**Description**: {game['description']}")
                st.write(f"📄 [Télécharger le guide]({game['guide']})")

# 🆕 **PAGE D'AJOUT DE JEU (NO LOGIN REQUIRED)**
elif option == "Ajouter un jeu":
    st.header("🆕 Ajouter un nouveau jeu")

    # Form to add a new game
    with st.form("add_game_form"):
        name = st.text_input("Nom du jeu", placeholder="Entrez le nom du jeu")
        description = st.text_area("Description", placeholder="Décrivez le jeu")
        guide = st.file_uploader("Guide du jeu (PDF)", type=["pdf"])
        affiche = st.file_uploader("Affiche du jeu (JPG/PNG)", type=["jpg", "png"])
        submit_button = st.form_submit_button("Ajouter le jeu")

    if submit_button:
        if name and description and guide and affiche:
            try:
                # Save uploaded files with unique names
                guide_filename = f"{uuid.uuid4()}_{guide.name}"
                guide_path = os.path.join(UPLOAD_FOLDER_GUIDES, guide_filename)
                with open(guide_path, "wb") as f:
                    f.write(guide.getbuffer())

                affiche_filename = f"{uuid.uuid4()}_{affiche.name}"
                affiche_path = os.path.join(UPLOAD_FOLDER_IMAGES, affiche_filename)
                with open(affiche_path, "wb") as f:
                    f.write(affiche.getbuffer())

                # Insert game data into MongoDB
                collection.insert_one({
                    "name": name,
                    "description": description,
                    "guide": guide_path,
                    "affiche": affiche_path,
                    "scoring": [],
                    "carbone": None
                })
                st.success(f"✅ Jeu '{name}' ajouté avec succès !")
            except Exception as e:
                st.error(f"❌ Une erreur s'est produite : {e}")
        else:
            st.error("❌ Veuillez remplir tous les champs.")

# 🏆 **PAGE SCORING**
elif option == "Scoring":
    st.header("📊 Attribuer un scoring")
    games = list(collection.find({}))

    if not games:
        st.write("Aucun jeu disponible.")
    else:
        selected_game = st.selectbox("Sélectionnez un jeu :", [game["name"] for game in games])
        game = next(game for game in games if game["name"] == selected_game)

        st.image(game["affiche"], caption="Affiche du jeu", use_container_width=True)

        # Critères de scoring
        fond = st.slider("Fond", min_value=1, max_value=5, step=1)
        originalite = st.slider("Originalité/Innovation", min_value=1, max_value=5, step=1)
        cohesion = st.slider("Cohésion d'équipe", min_value=1, max_value=5, step=1)
        esthetique = st.slider("Esthétique/Forme/Packaging", min_value=1, max_value=5, step=1)
        fun = st.slider("Fun", min_value=1, max_value=5, step=1)

        if st.button("Enregistrer le scoring"):
            scoring = {
                "fond": fond,
                "originalite": originalite,
                "cohesion": cohesion,
                "esthetique": esthetique,
                "fun": fun
            }
            collection.update_one({"_id": game["_id"]}, {"$push": {"scoring": scoring}})
            st.success("✅ Scoring enregistré avec succès !")

# 🔥 **PAGE LEADERBOARD**
elif option == "Leaderboard":
    st.header("🏆 Classement des Jeux")
    games = list(collection.find({}))

    if not games:
        st.write("Aucun jeu disponible.")
    else:
        leaderboard_data = []
        for game in games:
            if game["scoring"]:
                scores = game["scoring"]
                avg_score = sum(
                    s["fond"] + s["originalite"] + s["cohesion"] + s["esthetique"] + s["fun"]
                    for s in scores
                ) / (5 * len(scores))
                leaderboard_data.append({
                    "Nom du jeu": game["name"],
                    "Score moyen": round(avg_score, 2)
                })

        df = pd.DataFrame(leaderboard_data)
        df = df.sort_values("Score moyen", ascending=False).reset_index(drop=True)

        st.plotly_chart(px.bar(df, x="Nom du jeu", y="Score moyen", title="Classement des jeux"))
        st.table(df)

# 🌱 **PAGE EMPREINTE CARBONE**
elif option == "Empreinte Carbone":
    st.header("♻️ Calcul de l'empreinte carbone")
    games = list(collection.find({}))

    if not games:
        st.write("Aucun jeu disponible.")
    else:
        selected_game = st.selectbox("Sélectionnez un jeu :", [game["name"] for game in games])
        game = next(game for game in games if game["name"] == selected_game)

        st.image(game["affiche"], caption="Affiche du jeu", use_container_width=True)

        # Entrée de données pour empreinte carbone
        energie = st.number_input("Consommation d'énergie (kWh)", min_value=0.0, step=0.1, key="energie")
        materiaux = st.number_input("Poids des matériaux utilisés (kg)", min_value=0.0, step=0.1, key="materiaux")
        transport = st.number_input("Distance de transport (km)", min_value=0.0, step=1.0, key="transport")
        joueurs = st.number_input("Nombre de joueurs", min_value=1, step=1, key="joueurs")

        if st.button("Calculer l'empreinte carbone"):
            # Calcul de l'empreinte carbone totale
            carbone_total = (energie * 0.233) + (materiaux * 2.5) + (transport * 0.1)

            # Calcul de l'empreinte carbone par joueur
            carbone_par_joueur = carbone_total / joueurs if joueurs > 0 else carbone_total

            # Mise à jour de la base de données
            collection.update_one(
                {"_id": game["_id"]},
                {"$set": {
                    "carbone": str(carbone_total),
                    "joueurs": str(joueurs),
                    "carbone_par_joueur": str(carbone_par_joueur)
                }}
            )
            st.success(f"✅ Empreinte carbone totale : {carbone_total:.2f} kgCO₂")
            st.success(f"👤 Empreinte carbone par joueur : {carbone_par_joueur:.2f} kgCO₂/joueur")