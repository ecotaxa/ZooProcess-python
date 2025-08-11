"""
User Management CLI

This module provides a command-line interface for managing users in the ZooProcess application.
It allows adding, updating, and removing users from the database.

Usage:
    python -m commands.user_cli --help
    python -m commands.user_cli add --name "John Doe" --email "john@example.com" --password "secure_password"
    python -m commands.user_cli update --id "user_id" --name "New Name"
    python -m commands.user_cli remove --id "user_id"
    python -m commands.user_cli list

"""

import click
import uuid
from rich.console import Console
from rich.table import Table
from sqlalchemy.exc import IntegrityError

from src.local_DB.models import User
from src.local_DB.sqlite_db import SQLAlchemyDB

console = Console()


@click.group(help="Manage users in the ZooProcess application")
def app():
    """Manage users in the ZooProcess application."""
    pass


@app.command()
@click.option("--name", required=True, help="User's full name")
@click.option("--email", required=True, help="User's email address")
@click.option(
    "--password", required=True, help="User's password", prompt=True, hide_input=True
)
@click.option(
    "--confirm-password",
    required=True,
    help="Confirm password",
    prompt=True,
    hide_input=True,
)
def add(name, email, password, confirm_password) -> None:
    """
    Add a new user to the database.
    """
    if password != confirm_password:
        console.print("[bold red]Passwords do not match![/bold red]")
        click.exit(1)

    # Generate a unique ID for the user
    user_id = str(uuid.uuid4())

    # Create a new user
    user = User(
        id=user_id,
        name=name,
        email=email,
        password=password,  # In a real application, this should be hashed
    )

    # Add the user to the database
    with SQLAlchemyDB() as db:
        try:
            db.session.add(user)
            db.session.commit()
            console.print(
                f"[bold green]User added successfully with ID: {user_id}[/bold green]"
            )
        except IntegrityError:
            console.print("[bold red]Error: Email already exists![/bold red]")
            click.exit(1)


@app.command()
@click.option("--id", required=True, help="User ID")
@click.option("--name", help="User's new name")
@click.option("--email", help="User's new email address")
@click.option("--password", help="User's new password", hide_input=True)
def update(id, name, email, password) -> None:
    """
    Update an existing user in the database.
    """
    with SQLAlchemyDB() as db:
        user = db.session.query(User).filter(User.id == id).first()

        if not user:
            console.print(f"[bold red]User with ID {id} not found![/bold red]")
            click.exit(1)

        if name:
            user.name = name

        if email:
            user.email = email

        if password:
            confirm_password = click.prompt("Confirm password", hide_input=True)
            if password != confirm_password:
                console.print("[bold red]Passwords do not match![/bold red]")
                click.exit(1)
            user.password = password  # In a real application, this should be hashed

        try:
            db.session.commit()
            console.print(f"[bold green]User {id} updated successfully![/bold green]")
        except IntegrityError:
            console.print("[bold red]Error: Email already exists![/bold red]")
            click.exit(1)


@app.command()
@click.option("--id", required=True, help="User ID")
@click.option("--force", "-f", is_flag=True, help="Force removal without confirmation")
def remove(id, force) -> None:
    """
    Remove a user from the database.
    """
    with SQLAlchemyDB() as db:
        user = db.session.query(User).filter(User.id == id).first()

        if not user:
            console.print(f"[bold red]User with ID {id} not found![/bold red]")
            click.exit(1)

        if not force:
            confirm = click.confirm(
                f"Are you sure you want to remove user {user.name} ({user.email})?"
            )
            if not confirm:
                console.print("[bold yellow]Operation cancelled![/bold yellow]")
                click.exit(0)

        db.session.delete(user)
        db.session.commit()
        console.print(f"[bold green]User {id} removed successfully![/bold green]")


@app.command()
def list() -> None:
    """
    List all users in the database.
    """
    with SQLAlchemyDB() as db:
        users = db.session.query(User).all()

        if not users:
            console.print("[yellow]No users found in the database.[/yellow]")
            return

        table = Table(title="Users")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="green")
        table.add_column("Email", style="blue")

        for user in users:
            table.add_row(user.id, user.name, user.email)

        console.print(table)


if __name__ == "__main__":
    app()
