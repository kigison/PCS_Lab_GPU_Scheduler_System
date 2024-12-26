from app import app
from models import db, User

username = input("Enter admin username: ")
name = input("Enter admin's name: ")
email = input("Enter admin email: ")
phone = input("Enter admin phone: ")
password = input("Enter admin password: ")

with app.app_context():
    # Check if the username or email is already registered.
    if User.query.filter_by(username=username).first():
        print("User {} is already registered!")
    elif User.query.filter_by(email=email).first():
        print("This email has already be used for registeration!")
    elif User.query.filter_by(phone=phone).first():
        print("This phone has already be used for registeration!")
    else:
        admin_user = User(
            username=username,
            name=name,
            email=email,
            phone=phone,
            lab='PCS Lab',
            priority=1,
            authentication=True,
            is_admin=True,
        )
        admin_user.set_password(password)

        db.session.add(admin_user)
        db.session.commit()

        print("Admin user created successfully!")
