def validate_role(role):
    return role in ["tenant", "landlord", "admin"]

def validate_email(email):
    return email and "@" in email

def validate_password(password):
    return password and len(password) >= 6
