from flask import Blueprint, request, jsonify, render_template
from app import db
from app.models import Team_Members_Model, Teams_Model

# Create a Blueprint for team player routes
team_player_bp = Blueprint('team_player_bp', __name__)


@team_player_bp.route('/add_players_to_team', methods=['POST'])
def add_players_to_team():
    data = request.json
    players = data.get('players', [])      
    championshipId= data.get('championshipId')
    teamId=data.get('teamId')  
    teamName=data.get('teamName')  
    if teamId==0 or teamId=='0':
        new_team =Teams_Model.insert_team(championship_id=championshipId,team_name=teamName)
        new_team_id = new_team.TeamID
        teamId=new_team_id
    successful_entries = 0
    failed_entries = 0

    for player in players:
        player_id = player.get('playerId')           
        new_entry = Team_Members_Model.insert_team_member(team_id=teamId,player_id=player_id)
        if new_entry:
            successful_entries += 1
        else:
            failed_entries += 1

    if successful_entries > 0:
        if failed_entries == 0:
            return jsonify({'message': f'All {successful_entries} players added to championship successfully'}), 201
        else:
            return jsonify({'message': f'{successful_entries} players added to championship successfully. {failed_entries} failed entries.'}), 201
    else:
        return jsonify({'message': 'No players were added to the championship'}), 200


@team_player_bp.route('/get_players_by_team/<int:team_id>', methods=['GET'])
def get_players_by_team(team_id):
    players = Team_Members_Model.select_team_members(team_id==team_id)
    if players:
        player_data = [{'playerId': player.PlayerID, 'championshipId': player.ChampionshipID} for player in players]
        return jsonify(player_data), 200
    else:
        return jsonify({'error': 'No players found for this championship'}), 404
    
@team_player_bp.route('/remove_all_players_from_team', methods=['DELETE'])
def remove_all_players_from_team():
    data = request.json
    team_id = data.get('teamId')

    if not team_id:
        return jsonify({'error': 'Missing team ID'}), 400

    # Get all entries for the specified team ID
    entries = Team_Members_Model.query.filter_by(TeamID=team_id).all()

    if entries:
        # Delete each entry
        for entry in entries:
            db.session.delete(entry)
        db.session.commit()
        return jsonify({'message': 'All players removed from team successfully'}), 200
    else:
        return jsonify({'message': 'No players found for the specified team. No action required.'}), 200

@team_player_bp.route('/update_team_name', methods=['PUT'])
def update_team_name():
    # Retrieve data from the request body
    data = request.json
    team_id = data.get('teamId')
    championship_id = data.get('championshipId')
    team_name = data.get('teamName')
    print('name:', team_name, 'id:', team_id)

    # Validate the presence of team ID
    if not team_id:
        return jsonify({'error': 'Missing team ID'}), 400

    try:
        # Call a method that performs the update (assuming it's a class method)
        updated_team = Teams_Model.update_team(
            team_id=team_id, championship_id=championship_id, team_name=team_name
        )

        if not updated_team:
            return jsonify({'error': 'Team not found'}), 404

        # Convert the team object to a dictionary or JSON response
        team_response = {
            'teamId': updated_team.TeamID,
            'championshipId': updated_team.ChampionshipID,
            'teamName': updated_team.team_name
        }
        print('Updated team:', team_response)

        return jsonify({'message': 'Team updated successfully', 'team': team_response}), 200
    except Exception as e:
        # Handle any unexpected errors and return a 500 response
        print('Error updating team:', str(e))
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
    
def init_routes(app):
    app.register_blueprint(team_player_bp)
