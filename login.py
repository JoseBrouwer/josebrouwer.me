from functools import wraps
from flask import session, redirect, url_for

def login_required(view_func):
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            # Redirect to the homepage if the user is not logged in
            return redirect("/new_user")
        return view_func(*args, **kwargs)
    return decorated_function

