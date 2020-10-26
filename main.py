import logging
import os

import webapp2
import jinja2

from google.appengine.ext import db
from google.appengine.ext import ndb

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

class Handler(webapp2.RequestHandler):
    """
    Utility functions to handle rendering templates
    """
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class Poem(db.Model):
    """
    DB model class for an individual poetry post
    """
    #uploaded_by_user_id = ndb.StringProperty()
    title = db.TextProperty(default="Untitled")
    poet = db.StringProperty(default="Unknown")
    poem = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    #image = ndb.BlobProperty()

class PoemPage(Handler):
    """
    Display and delete a single poem entry
    """
    def get(self, poem_id):
        logging.info("Entering function get request for id %s, PoemPage Handler" % poem_id)
        key = db.Key.from_path('Poem', int(poem_id))
        poem = db.get(key)

        if not poem:
            logging.error("No poem found for id %s" % poem_id)
            self.error(404)
            return

        self.render("poem_page.html", poem=poem)
        logging.info("Displayed poem id %s. Exiting function" % poem_id)
    
    def post(self, poem_id):
        logging.info("Entering post function PoemPage Handler to delete poem id %s" % poem_id)
        key = db.Key.from_path('Poem', int(poem_id))
        db.delete(key)
        logging.info("Exiting post function PoemPage Handler; delete poem id %s" % poem_id)

class MainPage(Handler):
    """
    Home Feed Handler
    """
    def get(self):
        """
        Display 5 poems in the datastore, most recent poem on top
        TODO: Add pagination for more poems
        """
        poems = db.GqlQuery("SELECT * FROM Poem ORDER BY created DESC LIMIT 5")
        self.render("home.html", poems=poems)

class NewPoem(Handler):
    """
    Create new poem post and edit/update existing poem 
    """
    def render_poem_form(self, title="", poet="", poem="", error=""):
        self.render("poem_form.html", title=title, poet=poet, poem=poem, error=error)

    def get(self, poem_id=''):
        # Poem ID exists when we receive edit request
        if poem_id:
            # edit request: fetch the current poem and show form with current poem
            poem = db.get(db.Key.from_path('Poem', int(poem_id)))
            self.render("poem_update.html", title=poem.title,
                                            poet=poem.poet,
                                            poem=poem.poem)
        else:
            # new form request
            self.render_poem_form()

    def post(self, poem_id=''):
        # Poem ID exists when we receive edit request
        # First get the form values from post          
        title = self.request.get('poemTitle')
        poem = self.request.get('poemContent')
        poet = self.request.get('poetName')

        #if the poem body is not empty
        if poem:
            # and if it is an edit request
            if poem_id:
                #fetch the existing poem entity and update its values
                p = db.get(db.Key.from_path('Poem', int(poem_id)))
                p.title = title
                p.poem = poem
                p.poet = poet
            #if it is a new poem, create a new entity
            else: 
                p = Poem(title=title, poet=poet, poem=poem)
            #save the entity values on the datastore
            p.put()
            #redirect to the individual poem page of the new/updated poem
            self.redirect("/poems/%s" % str(p.key().id()))

        #if the poem body is empty, show error    
        else:
            self.render_poem_form(title, poet, poem, 
                                  error="Oops, you kinda gotta write a poem before posting!")

class PoemsHandler(Handler):
    """
    My poems Handler
    TODO: Once there is signup, poems uploaded by the user to be handled here.
    """
    def get(self):
        self.render("home.html")

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/new', NewPoem),
                               ('/update', NewPoem),
                               ('/myPoems', PoemsHandler),
                               ('/poems/([0-9]+)', PoemPage),
                               ('/poems/([0-9]+)/delete', PoemPage),
                               ('/poems/([0-9]+)/edit', NewPoem)
                              ], debug=True)
