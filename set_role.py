import sys
from app import create_app, db
from app.models import User

ROLES = ("customer", "staff", "driver")

app = create_app()

if len(sys.argv) != 3 or sys.argv[2] not in ROLES:
    print("Usage: python set_role.py user@example.com customer|staff|driver")
    sys.exit(1)

with app.app_context():
    user = User.query.filter_by(email=sys.argv[1].strip().lower()).first()
    if not user:
        print("No user with that email. Register first.")
    else:
        user.role = sys.argv[2]
        db.session.commit()
        print(f"{user.name} is now {user.role}.")