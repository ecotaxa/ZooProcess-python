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

import typer
import uuid
from typing import Optional
from rich.console import Console
from rich.table import Table
from sqlalchemy.exc import IntegrityError

from src.db_models import User
from src.sqlite_db import SQLAlchemyDB

app = typer.Typer(help="Manage users in the ZooProcess application")
console = Console()


@app.command()
def add(
    name: str = typer.Option(..., help="User's full name"),
    email: str = typer.Option(..., help="User's email address"),
    password: str = typer.Option(
        ..., help="User's password", prompt=True, hide_input=True
    ),
    confirm_password: str = typer.Option(
        ..., help="Confirm password", prompt=True, hide_input=True
    ),
) -> None:
    """
    Add a new user to the database.
    """
    if password != confirm_password:
        console.print("[bold red]Passwords do not match![/bold red]")
        raise typer.Exit(code=1)

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
            raise typer.Exit(code=1)


@app.command()
def update(
    id: str = typer.Option(..., help="User ID"),
    name: Optional[str] = typer.Option(None, help="User's new name"),
    email: Optional[str] = typer.Option(None, help="User's new email address"),
    password: Optional[str] = typer.Option(
        None, help="User's new password", prompt=False, hide_input=True
    ),
) -> None:
    """
    Update an existing user in the database.
    """
    with SQLAlchemyDB() as db:
        user = db.session.query(User).filter(User.id == id).first()

        if not user:
            console.print(f"[bold red]User with ID {id} not found![/bold red]")
            raise typer.Exit(code=1)

        if name:
            user.name = name

        if email:
            user.email = email

        if password:
            confirm_password = typer.prompt("Confirm password", hide_input=True)
            if password != confirm_password:
                console.print("[bold red]Passwords do not match![/bold red]")
                raise typer.Exit(code=1)
            user.password = password  # In a real application, this should be hashed

        try:
            db.session.commit()
            console.print(f"[bold green]User {id} updated successfully![/bold green]")
        except IntegrityError:
            console.print("[bold red]Error: Email already exists![/bold red]")
            raise typer.Exit(code=1)


@app.command()
def remove(
    id: str = typer.Option(..., help="User ID"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force removal without confirmation"
    ),
) -> None:
    """
    Remove a user from the database.
    """
    with SQLAlchemyDB() as db:
        user = db.session.query(User).filter(User.id == id).first()

        if not user:
            console.print(f"[bold red]User with ID {id} not found![/bold red]")
            raise typer.Exit(code=1)

        if not force:
            confirm = typer.confirm(
                f"Are you sure you want to remove user {user.name} ({user.email})?"
            )
            if not confirm:
                console.print("[bold yellow]Operation cancelled![/bold yellow]")
                raise typer.Exit()

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
