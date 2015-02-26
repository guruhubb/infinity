from flask.ext.script import Command
from infinity import userDatastore
import infinity
import models

# Seed initial users and roles

class SeedUsersAndRoles(Command):
    def run(self):
        infinity.Role.drop_collection()
        infinity.User.drop_collection()

        level0 = userDatastore.create_role(name='Level0', description='Lowest Level Clearance')
        level1 = userDatastore.create_role(name='Level1', description='Level 1 Clearance')
        level2 = userDatastore.create_role(name='Level2', description='Level 2 Clearance')
        level3 = userDatastore.create_role(name='Level3', description='Level 3 Clearance')

        admin = userDatastore.create_role(name='Root',description='All Access')

        # userDatastore.create_user(email='saswata_basu@yahoo.com',name='Saswata', role=admin)
        # userDatastore.create_user(email='saswata_basu@yahoo.com',name='Saswata', roles=[admin])
        userDatastore.create_user(email='saswata_basu@yahoo.com',name='Saswata', password='123', roles=[admin], active=True,
                                   confirmed_at='02/25/2015')
        userDatastore.create_user(email='admin',name='admin', password='admin', roles=[admin], active=True,
                                   confirmed_at='02/25/2015')
