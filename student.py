from quart import Blueprint, request, abort, current_app
import asyncpg

bp = Blueprint("student", __name__, url_prefix = "/student")

@bp.route('/<id>', methods = ['GET'])
async def student_function(id):
    to_return = None
    async with current_app.config['pool'].acquire() as connection:
        async with connection.transaction():
            data = await connection.fetch("SELECT * FROM qotd WHERE id = $1", int(id))
            to_return = data[0][1]

    return to_return

@bp.route('/error', methods = ['GET'])
async def error():
    abort(401)
