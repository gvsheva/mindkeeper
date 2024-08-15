from mindkeeper.controller import Controller, command


class ContactsController(Controller):
    """A set of commands to manage contacts."""

    @command
    def add(self, repl, *args):
        """Add a contact."""
        print(f"Adding contact: {args}")

    @command
    def delete(self, repl, *args):
        """Delete a contact."""
        print(f"Deleting contact: {args}")

    @command
    def list(self, repl, *args):
        """List contacts."""
        print(f"Listing contacts: {args}")
