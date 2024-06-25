from flask import Blueprint, request, jsonify, send_file
from app import db
from app.models.player_model import Player_Model
from app.models.series_model import Series_Model
from app.models.series_player_model import Series_Players_Model
import csv
from io import StringIO

# Create a Blueprint for series routes
results_bp = Blueprint('results_bp', __name__)

@results_bp.route('/update_player_points', methods=['POST'])
def update_player_points():
    try:
        data = request.get_json()
        player_id = data.get('playerId')
        series_id = data.get('seriesId')
        total_points = data.get('total_points')

        # Optional parameters
        tisch_points = data.get('tisch_points')
        won_games = data.get('won_games')
        lost_games = data.get('lost_games')

        # Check if a record with the same series_id and player_id exists
        existing_record = Series_Players_Model.query.filter_by(SeriesID=series_id, PlayerID=player_id).first()

        # If the record exists, delete it
        if existing_record:
            db.session.delete(existing_record)
            db.session.commit()

        # Prepare the parameters for insertion
        insert_params = {
            'series_id': series_id,
            'player_id': player_id,
            'total_points': total_points
        }
        
        # Include optional parameters if they exist
        if tisch_points is not None:
            insert_params['table_points'] = tisch_points
        if won_games is not None:
            insert_params['won_games'] = won_games
        if lost_games is not None:
            insert_params['lost_games'] = lost_games

        # Insert the new record
        Series_Players_Model.insert_series_player_record(**insert_params)

        return jsonify(success=True)

    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=str(e)), 500
 
@results_bp.route('/api/get_series_rank', methods=['GET'])
def get_series_rank():
    try:
        # Get the series_id from query parameters
        series_id = request.args.get('series_id')

        # Ensure series_id is provided
        if not series_id:
            return jsonify(success=False, error="series_id is required"), 400

        # Get the players ordered by total points
        players_ordered_by_points = Series_Players_Model.select_series_players_ordered_by_total_points(series_id)

        # Build the result array
        result = []
        for player in players_ordered_by_points:
            player_info = Player_Model.query.filter_by(PlayerID=player.PlayerID).first()
            if player_info:
                result.append({
                    'player_name': player_info.name,
                    'player_id': player.PlayerID,
                    'total_points': player.TotalPoints
                })

        return jsonify(success=True, data=result)

    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

@results_bp.route('/api/check_series', methods=['GET'])
def check_series():
    championship_id = request.args.get('championship_id')
    selected_series_id = request.args.get('selected_series_id')


    series_belongs_to_championship = check_series_in_championship(championship_id, selected_series_id)

    return jsonify({'belongs': series_belongs_to_championship})

def check_series_in_championship(championship_id, selected_series_id):
    selected_series = Series_Model.select_series(selected_series_id)
    selected_series_champ_id = selected_series.ChampionshipID
    print('81', selected_series_champ_id, ' ',championship_id)
    return str(selected_series_champ_id) == str(championship_id)

        # Return True if selected_series_id belongs to championship_id, otherwise False
def init_routes(app):
    app.register_blueprint(results_bp)



@results_bp.route('/api/get_championship_rank', methods=['GET'])
def get_championship_rank():
    try:
        # Get the championship_id from query parameters
        championship_id = request.args.get('championship_id')

        # Ensure championship_id is provided
        if not championship_id:
            return jsonify(success=False, error="championship_id is required"), 400

        # Get all series for the championship
        series_list = Series_Model.select_series(championship_id=championship_id)
        
        # Sort series by SeriesID (ascending)
        series_list = sorted(series_list, key=lambda x: x.SeriesID)

        # Aggregate player points across all series
        player_points = {}
        series_ids = [series.SeriesID for series in series_list]

        for series in series_list:
            players_ordered_by_points = Series_Players_Model.select_series_players_ordered_by_total_points(series.SeriesID)

            for player in players_ordered_by_points:
                if player.PlayerID not in player_points:
                    player_info = Player_Model.query.filter_by(PlayerID=player.PlayerID).first()
                    player_points[player.PlayerID] = {
                        'player_name': player_info.name,
                        'player_id': player.PlayerID,
                        'total_points': 0,
                        'series_points': {}
                    }
                player_points[player.PlayerID]['total_points'] += player.TotalPoints
                player_points[player.PlayerID]['series_points'][series.SeriesID] = player.TotalPoints

        # Create CSV file
        csv_file = StringIO()
        csv_writer = csv.writer(csv_file)

        # Header row
        header = ['player_id', 'player_name'] + [f'series_{i}' for i in range(1, len(series_ids) + 1)] + ['total_points']
        csv_writer.writerow(header)

        # Data rows
        for player_id, data in player_points.items():
            row = [player_id, data['player_name']] + [data['series_points'].get(series_id, 0) for series_id in series_ids] + [data['total_points']]
            csv_writer.writerow(row)

        csv_file.seek(0)

        # Save the CSV file to a temporary location
        csv_filename = f"championship_{championship_id}_rank.csv"
        with open(csv_filename, "w", newline='') as f:
            f.write(csv_file.getvalue())

        # Prepare the JSON result
        result = sorted(player_points.values(), key=lambda x: x['total_points'], reverse=True)
        return jsonify(success=True, data=result)

    except Exception as e:
        return jsonify(success=False, error=str(e)), 500
    
@results_bp.route('/check_series_player_records', methods=['GET'])
def check_series_player_records():
    try:
        series_id = request.args.get('series_id')

        if not series_id:
            return jsonify(success=False, error="series_id is required"), 400

        existing_records = Series_Players_Model.select_series_player_records(series_id=series_id, min_total_points=1)

        if existing_records:
            return jsonify(success=True, exists=True)
        else:
            return jsonify(success=True, exists=False)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500