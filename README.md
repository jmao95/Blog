# Multi User Blog

The website is located at: https://multi-user-blog-165210.appspot.com/blog

To use the website, first create an account by clicking "Signup" in the upper
right-hand corner. An account requires at minimum a username and a password.
Once you have created an account, you have full access to the website and may
create posts, like other users' posts, and create comments. You may browse
existing content without logging in, but features that allow you to create or
change content will not be available. Click on "Multi User Blog" at any time
to return to the main blog page.

-------------------------------------------------------------------------------

In order to run the website locally you will need to install the Google Cloud
SDK and then initialize the gcloud tool. The Google Cloud SDK may be downloaded
from the following link:

https://cloud.google.com/appengine/docs/standard/python/download

Test the application using the local development server (dev_appserver.py),
which is included with the SDK.

From within the 'Project 3' directory where the app's app.yaml configuration
file is located, start the local development server with the following command:

dev_appserver.py app.yaml

The local development server is now running and listening for requests on
port 8080.

Visit http://localhost:8080/ in your web browser to view the app.