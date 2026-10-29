from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user

def role_required(*allowed_roles):
    """
    Decorator to restrict view access to specific user roles.
    Super Admin always has universal access.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            
            if not current_user.has_role(*allowed_roles):
                flash('Access denied. You do not have permission to view this resource.', 'danger')
                return abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permission_required(perm_code):
    """
    Decorator to restrict access based on granular permission code.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            
            if not current_user.has_permission(perm_code):
                flash('Access denied. Missing required permission.', 'danger')
                return abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
