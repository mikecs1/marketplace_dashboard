#!/usr/bin/env python3
"""
Create an admin user manually.
Usage: python3 create_admin.py <username> <email> <password>
Example: python3 create_admin.py admin admin@example.com mypassword123
"""

import sys
from app import app, db, bcrypt
from models import User

def create_admin(username, email, password):
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"Error: Username '{username}' already exists.")
            return False
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            print(f"Error: Email '{email}' already registered.")
            return False
        
        # Create admin user
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        admin = User(username=username, email=email, password=hashed_pw, role='admin')
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"✓ Admin user '{username}' created successfully!")
        print(f"  Email: {email}")
        print(f"  Role: admin")
        return True

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python3 create_admin.py <username> <email> <password>")
        print("Example: python3 create_admin.py admin admin@example.com mypassword123")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    success = create_admin(username, email, password)
    sys.exit(0 if success else 1)
