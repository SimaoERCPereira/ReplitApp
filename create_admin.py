import os
import sys
from app_production import app, db, User
from werkzeug.security import generate_password_hash

# Run this script to initialize the database and create an admin user
# Usage: python create_admin.py <admin_email> <admin_password>


def create_admin_user(email, username, password):
    with app.app_context():
        # Check if the admin user already exists
        admin = User.query.filter_by(email=email).first()

        if admin:
            print(f"Admin user with email {email} already exists.")
            return

        # Create the admin user
        admin = User(email=email, username=username, is_admin=True)
        admin.set_password(password)

        # Add to database
        db.session.add(admin)
        db.session.commit()

        print(f"Admin user '{username}' created successfully!")


if __name__ == "__main__":
    # Check if we have the right number of arguments
    if len(sys.argv) != 4:
        print(
            "Usage: python create_admin.py <admin_email> <admin_username> <admin_password>"
        )
        sys.exit(1)

    email = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]

    print(f"Creating admin user with email: {email} and username: {username}")
    create_admin_user(email, username, password)
