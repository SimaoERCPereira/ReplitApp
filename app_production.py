
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Configure for production use
    app.config['DEBUG'] = False
    app.config['ENV'] = 'production'
    app.run(host='0.0.0.0', port=3000)
