from flask import Flask, render_template, request, jsonify, send_file
from model import train_and_predict_best_11
import pandas as pd

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_players", methods=["POST"])
def get_players():
    data = request.get_json()
    team = data.get("team")
    try:
        df = pd.read_excel("data/squads.xlsx", sheet_name=team)
        players = df["Player Name"].dropna().tolist()
        return jsonify(players)
    except Exception as e:
        print(f"Error reading team {team}:", e)
        return jsonify([])

@app.route("/get_player_info", methods=["POST"])
def get_player_info():
    data = request.get_json()
    player = data.get("player")
    team = data.get("team")
    try:
        df = pd.read_excel("data/squads.xlsx", sheet_name=team)
        row = df[df["Player Name"] == player]
        if not row.empty:
            credit = row["Credits"].values[0]
            ptype = row["Player Type"].values[0]
            return jsonify({"credit": credit, "type": ptype, "team": team})
        else:
            return jsonify({"credit": "", "type": "", "team": team})
    except Exception as e:
        return jsonify({"credit": "", "type": "", "team": team, "error": str(e)})

@app.route("/generate_excel", methods=["POST"])
def generate_excel():
    data = request.get_json()
    teamA_players = data.get("teamA", [])
    teamB_players = data.get("teamB", [])
    teamA_name = data.get("teamA_name")
    teamB_name = data.get("teamB_name")

    rows = []

    try:
        df_a = pd.read_excel("data/squads.xlsx", sheet_name=teamA_name)
        df_b = pd.read_excel("data/squads.xlsx", sheet_name=teamB_name)

        def get_player_data(df, player, team):
            row = df[df["Player Name"] == player]
            if not row.empty:
                return {
                    "Player Name": player,
                    "Credits": row["Credits"].values[0],
                    "Player Type": row["Player Type"].values[0],
                    "Team": team,
                }

        for player in teamA_players:
            rows.append(get_player_data(df_a, player, teamA_name))

        for player in teamB_players:
            rows.append(get_player_data(df_b, player, teamB_name))

        final_df = pd.DataFrame(rows)
        final_df.to_excel("data/fantasy_input.xlsx", index=False)

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/predict", methods=["POST"])
def predict_best_team():
    venue = request.form.get("venue")
    try:
        output_csv_path = train_and_predict_best_11("data/fantasy_input.xlsx", venue)
        df = pd.read_csv(output_csv_path)
        table_data = df.to_dict(orient="records")
        role_counts = df["Player Type"].value_counts().to_dict()
        team_counts = df["Team"].value_counts().to_dict()
        total_credits = df["Credits"].sum()
        credits_left = 100 - total_credits

        return render_template("predicted.html",credits_left=credits_left, team=table_data, role_summary=role_counts,team_summary=team_counts)
    except Exception as e:
        import traceback
        traceback.print_exc()  # Show full error in terminal
        return f"<pre>Error occurred:\n{str(e)}</pre>"

@app.route("/download")
def download_csv():
    return send_file("data/predicted_best_11.csv", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
