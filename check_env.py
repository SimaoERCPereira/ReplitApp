import os

# Check if required environment variables are set
required_vars = ["SECRET_KEY", "FLASK_ENV", "DATABASE_URL"]

# Optional but recommended variables
recommended_vars = ["CRON_API_KEY", "APP_URL"]

print("Environment Variable Check:")
print("-" * 40)

missing_required = []
for var in required_vars:
    value = os.getenv(var)
    if value:
        # Don't print the actual secret key value
        if var == "SECRET_KEY":
            print(f"✅ {var}: [HIDDEN - VALUE SET]")
        else:
            print(f"✅ {var}: {value}")
    else:
        missing_required.append(var)
        print(f"❌ {var}: NOT SET (REQUIRED)")

print("\nRecommended Variables:")
for var in recommended_vars:
    value = os.getenv(var)
    if value:
        print(f"✅ {var}: {value}")
    else:
        print(f"⚠️ {var}: NOT SET (RECOMMENDED)")

print("\nDatabase URL Check:")
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Check if using proper postgresql:// prefix
    if database_url.startswith("postgres://"):
        print(
            "⚠️ DATABASE_URL uses 'postgres://' prefix. It should be automatically converted to 'postgresql://'"
        )
    elif database_url.startswith("postgresql://"):
        print("✅ DATABASE_URL uses correct 'postgresql://' prefix")
    else:
        print(
            f"⚠️ DATABASE_URL uses an unexpected protocol: {database_url.split('://')[0]}"
        )
else:
    print("❌ DATABASE_URL is not set")

if missing_required:
    print("\n❌ ERROR: Missing required environment variables!")
    print("The application may not function correctly without these variables.")
else:
    print("\n✅ All required environment variables are set!")
