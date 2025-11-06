from flask import Flask, jsonify, render_template, request
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://Distributori:12345@cluster0.mongodb.net/Distributori"
mongo = PyMongo(app)

# ------------------------------
# API richieste
# ------------------------------

@app.route("/api/distributors")
def get_distributors():
    distributori = list(mongo.db.distributori.find({}, {"_id": 0}).sort("id", 1))
    return jsonify(distributori)

# 1. livello di carburante nei distributori di una provincia
@app.route("/api/distributors/province/<province>/fuel", methods=["GET"])
def fuel_by_province(province):
    distributori = list(
        mongo.db.distributori.find(
            {"provincia": province.upper()},
            {"_id": 0, "id": 1, "nome": 1, "provincia": 1, "benzina": 1, "diesel": 1}
        )
    )

    if not distributori:
        return jsonify({"error": "Nessun distributore trovato per questa provincia"}), 404

    # Aggiungiamo il livello totale
    for d in distributori:
        d["livello_totale"] = (d.get("benzina") or 0) + (d.get("diesel") or 0)

    return jsonify(distributori)

# 2. livello di carburante in un distributore specifico
@app.route("/api/distributors/<int:distributor_id>/fuel", methods=["GET"])
def get_fuel_level(distributor_id):
    distributore = mongo.db.distributori.find_one({"id": distributor_id}, {"_id": 0, "id": 1, "nome": 1, "livello_carburante": 1})
    
    if not distributore:
        return jsonify({"error": "Distributore non trovato"}), 404

    return jsonify(distributore)

# 3. visualizzazione su mappa: forniamo endpoint che restituisce distributori con lat/lon
@app.route("/mappa")
def mappa_distributori():
    distributori = list(
        mongo.db.distributori.find({}, {"_id": 0, "nome": 1, "provincia": 1, "lat": 1, "lon": 1})
    )
    return render_template("mappa.html", distributori=distributori)

# Cambiare il prezzo della benzina o del diesel in tutti i distributori di una provincia
@app.route("/aggiorna_prezzi", methods=["GET", "POST"])
def aggiorna_prezzi():
    if request.method == "POST":
        provincia = request.form.get("provincia").upper().strip()
        tipo = request.form.get("tipo")  # "benzina" o "diesel"
        nuovo_prezzo = float(request.form.get("prezzo"))

        if tipo == "benzina":
            result = mongo.db.distributori.update_many(
                {"provincia": provincia},
                {"$set": {"prezzo_benzina": nuovo_prezzo}}
            )
        else:
            result = mongo.db.distributori.update_many(
                {"provincia": provincia},
                {"$set": {"prezzo_diesel": nuovo_prezzo}}
            )

        return render_template(
            "distributori.html",
            message=f"Aggiornati {result.modified_count} distributori nella provincia {provincia}.",
        )

    return render_template("distributori.html")

@app.route("/map")
def map_view():
    # la pagina caricherà i dati via API /api/distributors/geo
    return render_template("mappa.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")