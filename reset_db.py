from app.database import engine, Base
from app import models
from sqlalchemy import text



with engine.connect() as connection:
    print("Dropping old tables...")
    connection.execute(text("DROP TABLE IF EXISTS payment_attempts CASCADE;"))
    connection.execute(text("DROP TABLE IF EXISTS refunds CASCADE;"))
    connection.execute(text("DROP TABLE IF EXISTS transactions CASCADE;"))
    connection.execute(text("DROP TABLE IF EXISTS idempotency_keys CASCADE;"))
    connection.execute(text("DROP TYPE IF EXISTS transactionstatus CASCADE;"))
    connection.execute(text("DROP TYPE IF EXISTS attemptstatus CASCADE;"))
    connection.commit()

print("Old tables dropped.")

print("Creating new tables...")
Base.metadata.create_all(bind=engine)
print("New tables created successfully!")