from quart import Blueprint, request, current_app
import asyncpg
from utils import hash_func, stringify, is_admin_code_valid, is_teacher_valid, HTTPCode

bp = Blueprint("teacher", __name__, url_prefix = "/teacher")

@bp.route('/auth', methods=['POST'])
async def auth():
    '''The route that the client uses to log a user in.'''
    data = await request.form
    username, password = data['username'], data['password']
    results = await is_teacher_valid(username, password)
    if results:
        return str(results), HTTPCode.OK
    else:
        return '', HTTPCode.UNAUTHORIZED

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
        if is_admin_code_valid(data['admin']): # Constant time check to counter time attacks
            params = [data['forename'], data['surname'], data['username'], data['title']]
            salt, hashed = hash_func(data['password'])
            params.append(salt)
            params.append(hashed)
            await db.execute("INSERT INTO teacher (forename, surname, username, title, salt, password) VALUES ($1, $2, $3, $4, $5, $6)", *params)
            
            teacher_obj = await db.fetchrow("SELECT * FROM teacher WHERE username = $1", data['username'])
            return stringify([teacher_obj]), HTTPCode.CREATED
            
        else:
            return '', HTTPCode.UNAUTHORIZED

@bp.route("/<id>", methods = ["GET", "PUT", "PATCH"])
async def teacher_function():
    '''Function defining functionality for a specific teacher.'''
    data = await request.form
    db = current_app.config['db_handler']
    id = int(id)

    if request.method == "GET":
        data = await db.fetchrow("SELECT * FROM teacher WHERE id = $1", id)
        return stringify(data), HTTPCode.OK

    elif request.method == "PUT":
        forename = data.get("username")
        surname = data.get("surname")
        title = data.get("title")
        username = data.get("username")
        await db.execute("UPDATE teacher SET forname = $1, surname = $2, title = $3, username = $4 WHERE id = $5", forename, surname, title, username, id)
        return '', HTTPCode.OK

    elif request.method == "PATCH":
        if data.get('password'):
            salt, hashed = hash_func(form.get('password')) # Password has been given, now update the salt and password fields
            await db.execute("UPDATE student SET salt = $1, password = $2 WHERE id = $3", salt, hashed, id)
        
        if data.get("username"):
            await db.execute("UPDATE teacher SET username = $1 WHERE id = $2", data.get("username"), id)

        if data.get("forename"):
            await db.execute("UPDATE teacher SET forename = $1 WHERE id = $2", data.get("forename"), id)

        if data.get("surname"):
            await db.execute("UPDATE teacher SET surname = $1 WHERE id = $2", data.get("surname"), id)

        if data.get("title"):
            await db.execute("UPDATE teacer SET title = $1 WHERE id = $2")

        return '', HTTPCode.OK
