import sys
from app import create_app, db
from app.models import User

app = create_app()

if len(sys.argv) != 2:
    print("Usage: python make_staff.py user@example.com")
    sys.exit(1)

with app.app_context():
    user = User.query.filter_by(email=sys.argv[1].strip().lower()).first()
    if not user:
        print("No user with that email. Register first.")
    else:
        user.role = "staff"
        db.session.commit()
        print(f"{user.name} is now staff.")