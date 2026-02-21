from app import create_app

app = create_app('development')

if __name__ == '__main__':
    print("\n🚀 Starting Flask...")
    print("📍 Visit: http://localhost:5000\n")
    app.run(debug=True, port=5000)