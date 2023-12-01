"""
Module: login.py

This module provides decorators for enforcing authentication and authorization 
in a Flask application.

It includes two main decorators: `login_required` and `admin_required`.

The `login_required` decorator ensures that a user is logged in before accessing certain routes. 
If a user is not logged in, they're redirected to a page for new or unauthenticated users.

The `admin_required` decorator ensures that a user has administrative privileges to 
access certain routes. 

It checks the user's admin status from the database and redirects 
non-admin users to a default display page if they attempt to access admin-only routes.

These decorators are essential for maintaining secure and proper access control within
the application.

Functions:
- login_required(view_func): Decorator to enforce user authentication for protected routes.
- admin_required(view_func): Decorator to enforce admin privileges for specific routes.

Usage:
Decorators can be applied to any Flask route handlers where user authentication or 
admin privileges are required.

Example:
@app.route('/some-protected-route')
@login_required
def protected_route():
# route logic here

@app.route('/admin-only-route')
@admin_required
def admin_route():
# route logic here

"""

from functools import wraps
import sqlite3
from flask import session, redirect, url_for

def login_required(view_func):
    """
    Decorator to enforce user login for protected routes.

    Wraps a view function to ensure the user is logged in. 
    If the user is not logged in, redirects them to the new user page.
    Can be applied to any route that requires the user to be authenticated before access.

    Parameters:
    - view_func (function): The view function that needs login protection.

    Returns:
    - function: The decorated view function which includes the login check.
    """
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            # Redirect to the homepage if the user is not logged in
            return redirect("/new_user")
        return view_func(*args, **kwargs)

    return decorated_function


def admin_required(view_func):
    """
    Decorator to enforce admin privileges for certain routes.

    Wraps a view function to ensure the user has admin privileges. 
    If the user is not an admin, redirects them to the main display page.
    Can be applied to any route that should be accessible only by users with admin status.
    Checks the user's admin status by querying the 'users' table in the database.

    Parameters:
    - view_func (function): The view function that requires admin access.

    Returns:
    - function: The decorated view function which includes the admin check.
    """
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
        user_info = session.get("user", {}).get("userinfo", {})
        user_email = user_info.get("email")

        # Connect to the database
        connection = sqlite3.connect("stories.db")
        cursor = connection.cursor()

        # Check if the user is an admin
        cursor.execute("SELECT admin FROM users WHERE email = ?", (user_email,))
        result = cursor.fetchone()

        if result is None or result[0] == 0:
            # Redirect non-admin users to a different page
            return redirect(url_for("display"))

        return view_func(*args, **kwargs)

    return decorated_function
