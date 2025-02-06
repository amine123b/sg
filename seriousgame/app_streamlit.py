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
MONGO_URI = os.getenv("MONGO_URI")

# Connect to MongoDB Atlas using the URI
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    
    # Ping the MongoDB server to check the connection
    client.admin.command('ping')  # Ping command to check if connection is established
    print("Successfully connected to MongoDB Atlas!")

    # Access the database and collection
    db = client["games_database"]  # Specify the database name
    collection = db["games"]  # Specify the collection name

    # Test: Print collection data (optional)
    print(f"Connected to database: {db.name}")
    print(f"Connected to collection: {collection.name}")
    
except ConnectionError as e:
    print("Failed to connect to MongoDB Atlas:", e)
except Exception as e:
    print("An error occurred:", e)

# Upload Folders
UPLOAD_FOLDER_GUIDES = os.getenv("UPLOAD_FOLDER_GUIDES")
UPLOAD_FOLDER_IMAGES = os.getenv("UPLOAD_FOLDER_IMAGES")


# Admin Credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Function to check admin login
def check_login(username, password):
    print(f"Debug: username={username}, password={password}")
    print(f"Debug: ADMIN_USERNAME={ADMIN_USERNAME}, ADMIN_PASSWORD={ADMIN_PASSWORD}")
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

# Page principale
st.title("SeriousGame édition 2025")
# 📝 Ajout de la description sous le titre
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

# 🔐 **PAGE D'AJOUT DE JEU AVEC LOGIN ADMIN**
elif option == "Ajouter un jeu":
    st.header("🔒 Connexion Administrateur")

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            login_button = st.form_submit_button("Se connecter")

        if login_button:
            if check_login(username, password):
                st.session_state.admin_logged_in = True
                st.success("✅ Connexion réussie !")
            else:
                st.error("❌ Identifiants incorrects. Réessayez.")
    else:
        st.success("✅ Vous êtes connecté en tant qu'administrateur.")

        # Ajout d'un jeu
        st.subheader("🆕 Ajouter un nouveau jeu")
        name = st.text_input("Nom du jeu", placeholder="Entrez le nom du jeu")
        description = st.text_area("Description", placeholder="Décrivez le jeu")
        guide = st.file_uploader("Guide du jeu (PDF)", type=["pdf"])
        affiche = st.file_uploader("Affiche du jeu (JPG/PNG)", type=["jpg", "png"])

        if st.button("Ajouter le jeu"):
            if name and description and guide and affiche:
                # Sauvegarde des fichiers
                guide_path = os.path.join(UPLOAD_FOLDER_GUIDES, guide.name)
                with open(guide_path, "wb") as f:
                    f.write(guide.getbuffer())

                affiche_path = os.path.join(UPLOAD_FOLDER_IMAGES, affiche.name)
                with open(affiche_path, "wb") as f:
                    f.write(affiche.getbuffer())

                # Enregistrement dans MongoDB
                collection.insert_one({
                    "name": name,
                    "description": description,
                    "guide": guide_path,
                    "affiche": affiche_path,
                    "scoring": [],
                    "carbone": None
                })
                st.success(f"✅ Jeu '{name}' ajouté avec succès !")
            else:
                st.error("❌ Veuillez remplir tous les champs.")

        st.markdown("---")

        # Suppression d'un jeu
        st.subheader("🗑️ Supprimer un jeu")
        games = list(collection.find({}))
        if games:
            game_names = {game["name"]: game["_id"] for game in games}
            selected_game = st.selectbox("Sélectionnez un jeu à supprimer :", list(game_names.keys()))

            if st.button("Supprimer le jeu", key="delete_game"):
                collection.delete_one({"_id": ObjectId(game_names[selected_game])})
                st.success(f"🚮 Jeu '{selected_game}' supprimé avec succès !")

        # Bouton de déconnexion
        if st.button("🔓 Se déconnecter"):
            st.session_state.admin_logged_in = False

# 🏆 **PAGE SCORING**
elif option == "Scoring":
    st.header("📊 Attribuer un scoring")
    games = list(collection.find({}))

    if not games:
        st.write("Aucun jeu disponible.")
    else:
        selected_game = st.selectbox("Sélectionnez un jeu :", [game["name"] for game in games])
        game = next(game for game in games if game["name"] == selected_game)

        st.image(game["affiche"], caption="Affiche du jeu", use_container_width =True)

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
            collection.update_one({"_id": ObjectId(game["_id"])}, {"$push": {"scoring": scoring}})
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



        # 
        if st.button("Calculer l'empreinte carbone"):
            # Calcul de l'empreinte carbone totale
            carbone_total = (energie * 0.233) + (materiaux * 2.5) + (transport * 0.1)
            
            # Calcul de l'empreinte carbone par joueur
            carbone_par_joueur = carbone_total / joueurs if joueurs > 0 else carbone_total
            
            # Mise à jour de la base de données
            collection.update_one(
                {"_id": ObjectId(game["_id"])}, 
                {"$set": {
                "carbone": str(carbone_total), 
                "joueurs": str(joueurs), 
                "carbone_par_joueur": str(carbone_par_joueur)
                }})
            # ✅ Message de confirmation
            st.success(f"✅ Empreinte carbone totale : {carbone_total:.2f} kgCO₂")
            st.success(f"👤 Empreinte carbone par joueur : {carbone_par_joueur:.2f} kgCO₂/joueur")
            
    # 📊 **Classement des jeux par empreinte carbone**
    st.subheader("📉 Classement des jeux selon leur empreinte carbone")

    carbon_data = []
    for g in games:
        if "carbone" in g and g["carbone"] is not None:  # Vérifier si la valeur existe
            carbon_data.append({
                "Nom du jeu": g.get("name", "Inconnu"),
                "Empreinte Carbone (kgCO₂)": g.get("carbone", 0),
                "Empreinte Carbone par Joueur (kgCO₂)": g.get("carbone_par_joueur", 0)
            })

    if len(carbon_data) > 0:
        df_carbone = pd.DataFrame(carbon_data)

        # 📊 Classement par empreinte carbone totale
        df_total = df_carbone.sort_values("Empreinte Carbone (kgCO₂)", ascending=True).reset_index(drop=True)
        fig_total = px.bar(
            df_total, 
            x="Nom du jeu", 
            y="Empreinte Carbone (kgCO₂)", 
            title="Classement des jeux par empreinte carbone totale", 
            text="Empreinte Carbone (kgCO₂)"
        )
        fig_total.update_traces(textposition="outside")
        st.plotly_chart(fig_total, use_container_width=True)

        # 📊 Classement par empreinte carbone par joueur
        df_joueur = df_carbone.sort_values("Empreinte Carbone par Joueur (kgCO₂)", ascending=True).reset_index(drop=True)
        fig_joueur = px.bar(
            df_joueur, 
            x="Nom du jeu", 
            y="Empreinte Carbone par Joueur (kgCO₂)", 
            title="Classement des jeux par empreinte carbone par joueur", 
            text="Empreinte Carbone par Joueur (kgCO₂)"
        )
        fig_joueur.update_traces(textposition="outside")
        st.plotly_chart(fig_joueur, use_container_width=True)

        # 📋 Tableau des classements
        st.table(df_carbone)
    else:
        st.write("⚠️ Aucun jeu n'a encore une empreinte carbone enregistrée.")

