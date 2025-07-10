import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from xgboost import XGBRegressor
import warnings

warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

def train_and_predict_best_11(input_excel_path: str, venue: str) -> pd.DataFrame:
    # Load historical dataset
    file_url = "https://raw.githubusercontent.com/Saatu23/t20-fantasy-dataset/main/merged_players_data.csv"
    df = pd.read_csv(file_url)

    # Venue list
    venue_list = [
        "Chennai", "Delhi", "Mumbai", "Kolkata", "Bengaluru", "Hyderabad",
        "Ahmedabad", "Jaipur", "Mohali", "Lucknow", "Dharamsala",
        "Guwahati", "Indore", "Visakhapatnam", "New Chandigarh"
    ]

    # Drop unnecessary columns
    columns_to_drop = [
        "Player", "Player Name", "Team", "Player Type", "Credits",
        "Total fantasy points", "Total current fantasy points",
        "Runs in Powerplay", "Runs in Middle Overs", "Runs in Death Overs",
        "Balls Bowled in Powerplay", "Balls Bowled in Death Overs"
    ]
    columns_to_drop += [v for v in venue_list if v != venue]
    columns_to_drop += [f"{v}_matches" for v in venue_list if v != venue]
    columns_to_drop += [f"{v}_avg_fantasy" for v in venue_list if v != venue]

    df_cleaned = df.drop(columns=columns_to_drop, errors='ignore')

    df_cleaned = df_cleaned.dropna(subset=[
        "Fantasy points per match", f"{venue}_avg_fantasy", "Current Fantasy points per match"
    ])

    # Feature Engineering
    df_cleaned["Experience Weight"] = 1 + (df_cleaned["Matches Played"] / df_cleaned["Matches Played"].max())
    df_cleaned["Venue Performance Weight"] = 1 + (df_cleaned[f"{venue}_avg_fantasy"] / df_cleaned[f"{venue}_avg_fantasy"].max())
    df_cleaned["Adjusted Fantasy Points"] = (
        df_cleaned["Fantasy points per match"] *
        df_cleaned["Experience Weight"] *
        df_cleaned["Venue Performance Weight"]
    )
    df_cleaned["Recent Form"] = df_cleaned["Fantasy points per match"] * 1.2
    df_cleaned["Current Form"] = df_cleaned["Current Fantasy points per match"] * 1.2

    # Split and train
    X = df_cleaned.drop(columns=[
        "Fantasy points per match", "Adjusted Fantasy Points", "Current Fantasy points per match", venue
    ], errors='ignore')
    y = df_cleaned["Adjusted Fantasy Points"]

    xgb_params = {
    'n_estimators': [100, 200, 300],
    'learning_rate': [0.01, 0.1, 0.2],
    'max_depth': [3, 5, 7]
    }

    xgb_model = GridSearchCV(XGBRegressor(random_state=42), xgb_params, cv=3, scoring='neg_mean_absolute_error')
    xgb_model.fit(X, y)

    # Load fantasy input Excel (22 players)
    df_input = pd.read_excel(input_excel_path)

    # Merge with historical data
    merged = df_input.merge(df, on="Player Name", how="left")

    # Fill missing values
    numeric_cols = merged.select_dtypes(include="number").columns
    non_numeric_cols = merged.select_dtypes(exclude="number").columns
    merged[numeric_cols] = merged[numeric_cols].fillna(merged[numeric_cols].median())
    merged[non_numeric_cols] = merged[non_numeric_cols].fillna("Unknown")

    # Feature Engineering for prediction
    merged["Experience Weight"] = 1 + (merged["Matches Played"] / df["Matches Played"].max())
    merged["Venue Performance Weight"] = 1 + (merged[f"{venue}_avg_fantasy"] / df[f"{venue}_avg_fantasy"].max())
    merged["Recent Form"] = merged["Fantasy points per match"] * 1.2
    merged["Current Form"] = merged["Current Fantasy points per match"] * 1.2

    # Predict Fantasy Points
    merged["Predicted Fantasy Points"] = (
        xgb_model.best_estimator_.predict(merged[X.columns]) *
        merged["Experience Weight"] * merged["Venue Performance Weight"]
    )

    merged = merged.sort_values(by="Predicted Fantasy Points", ascending=False)

    # Role-based filtering
    min_required_roles = {"WK": 1, "BAT": 1, "ALL": 1, "BOWL": 1}
    max_allowed_roles = {"WK": 8, "BAT": 8, "ALL": 8, "BOWL": 8}
    selected_players = []
    role_counts = {role: 0 for role in min_required_roles}
    used_indices = set()

    # Step 1: At least 1 from each role
    for role in min_required_roles:
        top_role_player = merged[merged["Player Type_x"] == role].iloc[0]
        selected_players.append(top_role_player)
        role_counts[role] += 1
        used_indices.add(top_role_player.name)

    # Step 2: Fill remaining spots
    for idx, player in merged.iterrows():
        if idx in used_indices:
            continue
        role = player["Player Type_x"]
        if role_counts[role] < max_allowed_roles[role]:
            selected_players.append(player)
            role_counts[role] += 1
        if len(selected_players) == 11:
            break

    # Final output
    top11 = pd.DataFrame(selected_players)
    top11 = top11.sort_values(by="Predicted Fantasy Points", ascending=False)
    top11 = top11[["Player Name", "Credits_x", "Player Type_x", "Team_x"]]
    top11.rename(columns={"Team_x": "Team", "Credits_x": "Credits", "Player Type_x":"Player Type"}, inplace=True)

    # Save output CSV so Flask can serve it
    output_path = "data/predicted_best_11.csv"
    top11.to_csv(output_path, index=False)

    return output_path  # Return path for /predict route to read and render

