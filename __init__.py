﻿from quart import Quart
import student
import asyncpg
import asyncio
from csv import reader
import os
from utils import DatabaseHandler

# TODO: Get student methods - perhaps a studentmanager class
# TODO: Validate inputs for students
# TODO: Try and except for database inputs - move try and except into DatabaseHandler methods

try:
    with open("credentials.csv", 'r') as f:
        read = reader(f)
        for vars in read:
            os.environ[vars[0]] = vars[1]
except FileNotFoundError:
    pass

def create_app():
    '''This subroutine creates the Quart app and returns it. The DB is also connected in this step.'''
    app = Quart(__name__)
    app.register_blueprint(student.bp)

    @app.before_serving
    async def on_startup():
        app.config['db_handler'] = await DatabaseHandler.create()

    return app

app = create_app()
if __name__ == "__main__":
    app.run(debug = True, port = os.environ['PORT'], host="0.0.0.0")