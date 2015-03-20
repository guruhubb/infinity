from flask.ext.script import Manager, Server
from infinity import app
# from dataController import dataLayer
import commands

manager = Manager(app)

# Turn on debugger by default and reloader
# Run local app with Edit Configuration "runserver" script
# For server app use runfcgi.py

manager.add_command("runserver", Server(
    threaded=True,
    use_debugger=True,
    use_reloader=False,
    host='127.0.0.1',
    port = 5000),
    # host='192.168.55.84', port=5000)
    # host='104.131.101.197',port=5000)
)
# Turn on debugger by default and reloader

manager.add_command("seedusers", commands.SeedUsersAndRoles())

if __name__ == "__main__":
    # dataLayer()
    manager.run()
