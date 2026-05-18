from app import create_app
from database.db import init_db
from database.seed_data import seed

app = create_app()

if __name__ == "__main__":
    init_db()
    seed()
    app.run(debug=True, host="0.0.0.0", port=5000)
