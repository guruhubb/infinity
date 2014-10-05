from flask.ext.script import Command
from infinity import userDatastore
import models

# Seed initial users and roles

class SeedUsersAndRoles(Command):
    def run(self):
        models.Role.drop_collection()
        models.User.drop_collection()

        level0 = userDatastore.create_role(name='Level0', description='Lowest Level Clearance')
        level1 = userDatastore.create_role(name='Level1', description='Level 1 Clearance')
        level2 = userDatastore.create_role(name='Level2', description='Level 2 Clearance')
        level3 = userDatastore.create_role(name='Level3', description='Level 3 Clearance')

        admin = userDatastore.create_role(name='Root',description='All Access')

        # userDatastore.create_user(email='saswata_basu@yahoo.com',name='Saswata', role=admin)
        userDatastore.create_user(email='saswata_basu@yahoo.com',name='Saswata', roles=[admin])

