import os
import re
import random
import hashlib
import hmac
from string import letters

import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret = 'h43gjfi#*F&ve#fs'

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())


def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val


class BlogHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))


class MainPage(BlogHandler):
  def get(self):
      self.redirect('/blog')


def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))


def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)


def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)


def users_key(group = 'default'):
    return db.Key.from_path('users', group)


class User(db.Model):

    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return cls.get_by_id(uid, parent = users_key())

    @classmethod
    def by_name(cls, name):
        u = cls.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return cls(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u


class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    user = db.StringProperty(required = True)
    likes = db.StringListProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self, show_comments):
        self._render_text = self.content.replace('\n', '<br>')
        if not self.user_comments:
            show_comments = False

        return render_str("post.html", p = self, show_comments = show_comments)


class Comment(db.Model):
    post = db.ReferenceProperty(Post, collection_name='user_comments')
    user = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    content = db.TextProperty(required = True)


class BlogFront(BlogHandler):

    def get(self):
        posts = db.GqlQuery("select * from Post order by created desc")
        self.render('front.html', posts = posts)


def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)


class PostPage(BlogHandler):

    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            return self.error(404)

        num_likes = len(post.likes)

        if not self.user:
            self.render("permalink.html", post = post, loggedin = False,
                        num_likes = num_likes)
        else:
            # user has not liked post, so "Like" is displayed
            if post.likes.count(self.user.name) == 0:
                self.render("permalink.html", post = post, loggedin = True,
                            num_likes = num_likes, liked = False)
            # user has liked post, so "Unlike" is displayed
            else:
                self.render("permalink.html", post = post, loggedin = True,
                            num_likes = num_likes, liked = True)

    def post(self, post_id):
        if not self.user:
            return self.redirect('/login')

        edit = self.request.get('edit')
        delete = self.request.get('delete')
        like = self.request.get('like')
        back = self.request.get('back')
        save = self.request.get('save')
        comment = self.request.get('comment')
        comment_edit = self.request.get('([0-9]{16})+(_edit)')
        comment_delete = self.request.get('([0-9]{16})+(_delete)')

        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            return self.error(404)

        num_likes = len(post.likes)

        if post.likes.count(self.user.name) == 0:
            liked = False
        else:
            liked = True

        if edit:
            if self.user.name == post.user:
                subject = post.subject
                content = post.content
                self.render("edit.html", subject = subject, content = content)
            else:
                error = "You can only edit your own posts"
                self.render("permalink.html", post = post, error = error,
                            loggedin = True, num_likes = num_likes, liked = liked)

        elif delete:
            if self.user.name == post.user:
                # Delete associated comments when deleting a post
                for comment in post.user_comments:
                    db.delete(comment.key())

                subject = post.subject
                db.delete(key)
                self.render("delete.html", subject = subject)
            else:
                error = "You can only delete your own posts"
                self.render("permalink.html", post = post, error = error,
                            loggedin = True, num_likes = num_likes, liked = liked)

        elif like:
            if self.user.name == post.user:
                error = "Sorry, you can't like your own posts!"
                self.render("permalink.html", post = post, error = error,
                            loggedin = True, num_likes = num_likes, liked = liked)
            # post has not been previously liked by user, so name is added to likes list
            elif post.likes.count(self.user.name) == 0:
                post.likes.append(self.user.name)
                post.put()
                self.redirect('/blog/%s' % str(post.key().id()))
            # post has been previously liked by user, so name is removed from likes list
            else:
                post.likes.remove(self.user.name)
                post.put()
                self.redirect('/blog/%s' % str(post.key().id()))

        elif save:
            if self.user.name != post.user:
                error = "You can only edit your own posts"
                self.render("edit.html", subject=subject, content=content,
                error=error)

            subject = self.request.get('subject')
            content = self.request.get('content')
            user = self.user.name

            if subject and content:
                post.subject = subject
                post.content = content
                post.put()
                self.redirect('/blog/%s' % str(post.key().id()))
            else:
                error = "subject and content, please!"
                self.render("edit.html", subject=subject, content=content,
                            error=error)

        elif back:
            self.render("permalink.html", post = post, loggedin = True,
                        num_likes = num_likes, liked = liked)

        elif comment:
            comment_content = self.request.get('comment_content')
            user = self.user.name

            if comment_content:
                new_comment = Comment(post=post, user=user,
                                      content=comment_content)
                new_comment.put()
                self.render("comment-added.html")
            else:
                error = "You cannot submit an empty comment"
                self.render("permalink.html", post = post, loggedin = True,
                            num_likes = num_likes, liked = liked, error=error)

        else:
            return self.error(404)


class NewPost(BlogHandler):

    def get(self):
        if self.user:
            self.render("newpost.html")
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            return self.redirect('/login')

        subject = self.request.get('subject')
        content = self.request.get('content')
        user = self.user.name
        likes = []

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content,
                     user = user, likes = likes)
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "Please include both a subject and content"
            self.render("newpost.html", subject=subject, content=content,
                        error=error)


class CommentPage(BlogHandler):

    def get(self, comment_id):
        key = db.Key.from_path('Comment', int(comment_id))
        comment = db.get(key)

        if not comment:
            return self.error(404)

        if not self.user:
            self.render("comment.html", comment=comment, loggedin = False)
        else:
            self.render("comment.html", comment=comment, loggedin = True)

    def post(self, comment_id):
        if not self.user:
            return self.redirect('/login')

        edit = self.request.get('edit')
        delete = self.request.get('delete')
        back = self.request.get('back')
        save = self.request.get('save')
        back_to_comment = self.request.get('back_to_comment')

        key = db.Key.from_path('Comment', int(comment_id))
        comment = db.get(key)

        if not comment:
            return self.error(404)

        post = comment.post

        if edit:
            if self.user.name == comment.user:
                content = comment.content
                self.render("comment-edit.html", content = content)
            else:
                error = "You can only edit your own comments"
                self.render("comment.html", comment = comment, error = error,
                            loggedin = True)

        elif delete:
            if self.user.name == comment.user:
                content = comment.content
                db.delete(key)
                self.render("comment-delete.html", content=content)
            else:
                error = "You can only delete your own comments"
                self.render("comment.html", comment = comment, error = error,
                            loggedin = True)

        elif back:
            self.redirect('/blog/%s' % str(post.key().id()))

        elif save:
            if self.user.name != comment.user:
                error = "You an only edit your own comments"
                self.render("comment.html", comment = comment, error = error,
                            loggedin = True)

            content = self.request.get('content')
            user = self.user.name

            if content:
                comment.content = content
                comment.put()
                self.redirect('/blog/comment/%s' % str(comment.key().id()))
            else:
                error = "Your comment must have content"
                self.render("comment-edit.html", content=content, error=error)

        # returns user to comment page from comment editing page
        elif back_to_comment:
            self.render("comment.html", comment = comment, loggedin = True)

        else:
            return self.error(404)


def valid_username(username):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return username and USER_RE.match(username)


def valid_password(password):
    PASS_RE = re.compile(r"^.{3,20}$")
    return password and PASS_RE.match(password)


def valid_email(email):
    EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
    return not email or EMAIL_RE.match(email)


class Signup(BlogHandler):

    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username = self.username,
                      email = self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That's not a valid password."
            have_error = True
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError


class Register(Signup):

    def done(self):
        # make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup-form.html', error_username = msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect('/welcome')


class Login(BlogHandler):

    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/welcome')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', error = msg)


class Logout(BlogHandler):

    def get(self):
        self.logout()
        self.redirect('/blog')


class Welcome(BlogHandler):

    def get(self):
        if self.user:
            self.render('welcome.html', username = self.user.name)
        else:
            self.redirect('/signup')


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/blog/newpost', NewPost),
                               ('/blog/comment/([0-9]+)', CommentPage),
                               ('/signup', Register),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/welcome', Welcome),
                               ],
                              debug=True)