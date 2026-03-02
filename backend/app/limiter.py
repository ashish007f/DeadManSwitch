from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize Limiter in a separate file to avoid circular dependencies
# between main.py and routes.py
limiter = Limiter(key_func=get_remote_address)
