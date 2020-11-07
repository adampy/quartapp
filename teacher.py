from quart import Blueprint, request, current_app
import asyncpg
from utils import hash_func, stringify, is_admin_code_valid, is_teacher_valid

bp = Blueprint("teacher", __name__, url_prefix = "/teacher")

@bp.route('/auth', methods=['POST'])
async def auth():
    '''The route that the client uses to log a user in.'''
    data = await request.form
    username, password = data['username'], data['password']
    results = await is_teacher_valid(username, password)
    if results:
        return str(results), 200
    else:
        return '', 401

@bp.route("/", methods = ["GET", "POST"])
async def main_route():
    '''/teacher route'''
    db = current_app.config['db_handler']

    if request.method == "GET":
        data = await db.fetch("SELECT * FROM teacher;")
        return stringify(data)

    elif request.method == "POST":
        #CHECK FOR ADMIN CODE
        data = await request.form
        if is_admin_code_valid(data['admin']):
            params = [data['forename'], data['surname'], data['username'], data['title']]
            salt, hashed = hash_func(data['password'])
            params.append(salt)
            params.append(hashed)
            await db.execute("INSERT INTO teacher (forename, surname, username, title, salt, password) VALUES ($1, $2, $3, $4, $5, $6)", *params)
            
            teacher_obj = await db.fetchrow("SELECT * FROM teacher WHERE username = $1", data['username'])
            return stringify([teacher_obj]), 201
            
        else:
            return '', 401 # Unauthorized

@bp.route("/<id>", methods = ["GET"])
async def teacher_function():
    db = current_app.config['db_handler']
    id = int(id)

    if request.method == "GET":
        data = await db.fetchrow("SELECT * FROM teacher WHERE id = $1", id)
        return stringify(data), 200