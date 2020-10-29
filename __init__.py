from quart import Quart
import student
import asyncpg
import asyncio
from csv import reader
import os

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
        app.config['pool'] = await asyncpg.create_pool(os.environ['GCSE_DATABASE_URL'] + "?sslmode=require", max_size=20)

    return app

app = create_app()
if __name__ == "__main__":
    app.run(debug = True)