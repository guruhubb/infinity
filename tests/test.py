#__author__ = 'saswata_basu'

# global variable used in all files
# @app.context_processor
# def inject_webcontext():
#     return dict(STATIC_URL="/static/", VER=VER, NMS_VER=VER)

# Flask views
# @app.route('/')
# def index():
#     return '<a href="/admin/">Click me to get to Admin!</a>'

# Create a user to test with
# @app.before_first_request
# def create_user():
#     user_datastore.create_user(email='matt@nobien.net', password='password')
# cache = Cache()

#from flask.ext.admin import Admin, BaseView, expose
# class MyView(BaseView):
#     @expose('/')
#     def index(self):
#         # return "Hello World!"
#         return self.render('admin.html')
#
# admin = Admin(app, name="Infinity")
# admin.add_view(MyView(name='Hello 1', endpoint='test1', category='Test'))
# admin.add_view(MyView(name='Hello 2', endpoint='test2', category='Test'))
# admin.add_view(MyView(name='Hello 3', endpoint='test3', category='Test'))
# # Add administrative views here

# Create application
# app = Flask(__name__)

# # Create dummy secret key so we can use sessions
# app.config['SECRET_KEY'] = '123456790'  #need this to delete a record
# app.config['MONGODB_SETTINGS'] = {'DB': 'testing'}  #need this to save
#
# # Create models
# from flask.ext.mail import Message
# from nmsapp import mail, app

# Define mongoengine documents

# class Role(db.Document, RoleMixin):
#     name = db.StringField(max_length=80, unique=True)
#     description = db.StringField(max_length=255)
#
#     # def __unicode__(self):
#     #     return self.name
#
#
# class User(db.Document, UserMixin):
#     name = db.StringField(max_length=64)
#     email = db.StringField(max_length=255)
#     password = db.StringField(max_length=255, default="infinity")
#     active = db.BooleanField(default=True)
#     confirmed_at = db.DateTimeField()
#     roles = db.ListField(db.ReferenceField(Role), default=[])
#
#     # def __unicode__(self):
#     #     return self.name
#
# class User(db.Document):
#     name = db.StringField(max_length=40)
#     tags = db.ListField(db.ReferenceField('Tag'))
#     password = db.StringField(max_length=40)
#
#     def __unicode__(self):
#         return self.name
#
# class Todo(db.Document):
#     title = db.StringField(max_length=60)
#     text = db.StringField()
#     done = db.BooleanField(default=False)
#     pub_date = db.DateTimeField(default=datetime.datetime.now)
#     user = db.ReferenceField(User, required=False)
#
#     # Required for administrative interface
#     def __unicode__(self):
#         return self.title
#
# class Tag(db.Document):
#     name = db.StringField(max_length=10)
#
#     def __unicode__(self):
#         return self.name
#
# class Comment(db.EmbeddedDocument):
#     name = db.StringField(max_length=20, required=True)
#     value = db.StringField(max_length=20)
#     tag = db.ReferenceField(Tag)
#
#
# class Post(db.Document):
#     name = db.StringField(max_length=20, required=True)
#     value = db.StringField(max_length=20)
#     inner = db.ListField(db.EmbeddedDocumentField(Comment))
#     lols = db.ListField(db.StringField(max_length=20))
#
#
# class File(db.Document):
#     name = db.StringField(max_length=20)
#     data = db.FileField()
#
#
# class Image(db.Document):
#     name = db.StringField(max_length=20)
#     image = db.ImageField(thumbnail_size=(100, 100, True))
#
#
#
# # Customized admin views
#
# class UserView(ModelView):
#     column_filters = ['name']
#     column_searchable_list = ('name')
#     column_exclude_list = ('password')
#     form_excluded_columns = ('password')
#     form_ajax_refs = {
#         'tags': {
#             'fields': ('name',)
#         }
#     }
#     def is_accessible(self):
#         return current_user.is_authenticated() and current_user.has_role('Administrator')
#
# class TodoView(ModelView):
#     column_filters = ['done']
#
#     form_ajax_refs = {
#         'user': {
#             'fields': ['name']  # search field with a character
#         }
#     }
#
#
# class PostView(ModelView):
#     # pass
#     form_subdocuments = {
#         'inner': {
#             'form_subdocuments': {
#                 None: {
#                     # Add <hr> at the end of the form
#                     'form_rules': ('name', 'tag', 'value', rules.HTML('<hr>')),
#                     'form_widget_args': {
#                         'name': {
#                             'style': 'color: red'  # apply red color name field
#                         }
#                     }
#                 }
#             }
#         }
#     }
#     def is_accessible(self):
#         return current_user.is_authenticated() and (current_user.has_role('Root') or current_user.has_role('Administrator'))

# def log_exception(sender, exception, **extra):
#     sender.logger.debug('Got exception during processing: %s', exception)
#
# from flask import got_request_exception
# got_request_exception.connect(log_exception, app)
#
#
# def log_request(sender, **extra):
#     a = flask.request
#     #sender.logger.debug('Request context is set up')
#
# from flask import request_started
# request_started.connect(log_request, app)
#
#
# @app.context_processor
# def inject_webcontext():
#     return dict(STATIC_URL="/static/", VER=VER, NMS_VER=VER)

# Tried plot.ly.  Does not work responsively.  Hard to correlated two plots.  Hard to take out merit line

# import plotly.plotly as py
# from plotly.graph_objs import *
# py.sign_in("saswata", "mret9csgsi")

#    timeStamp = time.strftime("%Y-%m-%d %H:%M:%S")
#     time.sleep(1)
#     timeStamp1 = time.strftime("%Y-%m-%d %H:%M:%S")
#     time.sleep(1)
#     timeStamp2 = time.strftime("%Y-%m-%d %H:%M:%S")
#
#     trace1 = Scatter(
#         x=[
#                 timeStamp,
#                 timeStamp1,
#                 timeStamp2,],
#         y=[40, 50, 60],
#         name='Capacity'
#     )
#     trace2 = Scatter(
#         x=[
#                 timeStamp2,
#                 timeStamp1,
#                 timeStamp,],
#         y=[4, 5, 6],
#         name='Traffic',
#         yaxis='y2'
#     )
#     data = Data([trace1, trace2])
#     layout = Layout(
#         title='Capacity and Traffic',
#         yaxis=YAxis(
#             title='Capacity'
#         ),
#         yaxis2=YAxis(
#             title='Traffic',
#             titlefont=Font(
#                 color='rgb(148, 103, 189)'
#             ),
#             tickfont=Font(
#                 color='rgb(148, 103, 189)'
#             ),
#             overlaying='y',
#             side='right'
#         ),
#         xaxis=XAxis(
#             title='AXIS TITLE',
#             titlefont=Font(
#                 family='Arial, sans-serif',
#                 size=18,
#                 color='grey'
#             )
#         )
#     )
#     fig = Figure(data=data, layout=layout)
#     plot_url = py.plot(fig, filename='multiple-axes-double', auto_open=False)
#     # figure = py.get_figure(plot_url)
#     # py.image.save_as(figure, 'plot.png')
#     # plot_url = py.plot(fig, filename='multiple-axes-double', auto_open=False)
#     # plot_url = py.plot(fig, filename='multiple-axes-double')
#
#
#     ctx['plot']=plot_url
#
#     return render_template('index.html', **ctx)