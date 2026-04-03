import os
from app import create_app

# Get config name from environment (default to 'development' for local dev)
config_name = os.getenv('APP_CONFIG', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # Use PORT from environment variable (standard for Railway/Render)
    port = int(os.getenv('PORT', 5000))
    print(f"\n🚀 Starting Flask in {config_name} mode...")
    print(f"📍 Visit: http://localhost:{port}\n")
    
    # Run server with 0.0.0.0 to allow external access in production
    app.run(debug=(config_name == 'development'), host='0.0.0.0', port=port)