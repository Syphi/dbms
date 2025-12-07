import click

from src import lekser


@click.group()
def cli_dbms():
    ...


@cli_dbms.command("lekser")
@click.option("-p", "--path", "path", default=None, type=click.Path(), help="The file with sql to open.")
@click.option("-c", "--command", "command", default=None, type=str, help="The string with a SQL.")
def lekser_analyzer(path, command):
    if not path and not command:
        click.secho("Must contain a path or command!", fg="red")
        return

    _input = command
    if path:
        _input = lekser.read_from_file(path)

    if not _input or _input == "":
        click.secho("Empty input!", fg="red")
        return

    _tokenize_stream = lekser.read_string(_input)


@cli_dbms.command()
def gramatic_analyzer():
    ...