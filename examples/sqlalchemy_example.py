"""
Example script demonstrating how to use SQLAlchemy in the ZooProcess project.

This script shows how to:
1. Connect to the database using SQLAlchemyDB
2. Create, read, update, and delete records using SQLAlchemy ORM
3. Perform queries using SQLAlchemy's query API
"""

from src.sqlite_db import SQLAlchemyDB
from src.db_models import Example


def main():
    """
    Main function demonstrating SQLAlchemy usage.
    """
    print("SQLAlchemy Example")
    print("-----------------")

    # Connect to the database using the context manager
    with SQLAlchemyDB() as db:
        # Create a new record
        print("\nCreating a new record...")
        example = Example(name="example_record", value="This is an example value")
        db.session.add(example)
        db.session.commit()
        print(f"Created record: {example}")

        # Read records
        print("\nReading all records...")
        records = db.session.query(Example).all()
        for record in records:
            print(f"Record: {record}")

        # Read a specific record
        print("\nReading a specific record...")
        record = db.session.query(Example).filter_by(name="example_record").first()
        print(f"Found record: {record}")

        # Update a record
        print("\nUpdating a record...")
        record.value = "Updated value"
        db.session.commit()
        print(f"Updated record: {record}")

        # Delete a record
        print("\nDeleting a record...")
        db.session.delete(record)
        db.session.commit()
        print("Record deleted")

        # Verify deletion
        print("\nVerifying deletion...")
        record = db.session.query(Example).filter_by(name="example_record").first()
        if record is None:
            print("Record was successfully deleted")
        else:
            print(f"Record still exists: {record}")


if __name__ == "__main__":
    main()
