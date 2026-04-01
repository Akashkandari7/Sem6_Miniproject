import sys
import os
sys.path.insert(0, '/Users/niteshsharma/Desktop/minor-project-app/backend')
from app import create_app

print("Testing app creation with default development config...")
# Development config uses sqlite in the local instance folder,
# so create_app WILL auto-seed during app_context, because db_uri starts with sqlite://
app = create_app('development')
print("App created successfully (auto-seed ran because local sqlite)")

# Now let's test POST /api/setup endpoint
with app.test_client() as client:
    # 1. No key
    resp = client.post('/api/setup')
    print("Without key:", resp.status_code, resp.json)
    
    # 2. Wrong key
    resp = client.post('/api/setup?key=wrong')
    print("Wrong key:", resp.status_code, resp.json)
    
    # 3. Correct key
    secret = app.config['SECRET_KEY']
    resp = client.post(f'/api/setup?key={secret}')
    print("Correct key:", resp.status_code, resp.json)
