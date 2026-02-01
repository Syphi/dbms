import click

from pprint import pprint

from src.parser.lekser import read_string, read_from_file
from src.parser.gramatical import parse_sql
from src.storage.metadata import MetadataController

@click.group()
def cli_dbms(): ...


@cli_dbms.command("init")
def _init_db():
    MetadataController.init_file()


@cli_dbms.command("create_table")
@click.option(
    "-n",
    "--name",
    "table_name",
    default=None,
    type=str,
    help="Name of the table",
)
def _init_db(table_name: str):
    MetadataController().write_tables_to_metadata_file(table_name)


@cli_dbms.command("lekser")
@click.option(
    "-p",
    "--path",
    "path",
    default=None,
    type=click.Path(),
    help="The file with sql to open.",
)
@click.option(
    "-c", "--command", "command", default=None, type=str, help="The string with a SQL."
)
def _perform_lekser(path, command):
    if not path and not command:
        click.secho("Must contain a path or command!", fg="red")
        return None

    _input = command
    if path:
        _input = read_from_file(path)

    if not _input or _input == "":
        click.secho("Empty input!", fg="red")
        return None

    return read_string(_input)


@cli_dbms.command("gramatical")
@click.option(
    "-s",
    "--stream",
    "stream",
    type=list,
    help="Stream from lerser to analyze gramatic.",
)
def _perform_gramatical(stream):
    stream = " ".join(stream)
    return parse_sql(stream)


@cli_dbms.command("input")
@click.option(
    "-p",
    "--path",
    "path",
    default=None,
    type=click.Path(),
    help="The file with sql to open.",
)
@click.option(
    "-c", "--command", "command", default=None, type=str, help="The string with a SQL."
)
def _parse_query(path, command):
    if not path and not command:
        click.secho("Must contain a path or command!", fg="red")
        return None

    _input = command
    if path:
        _input = read_from_file(path)

    if not _input or _input == "":
        click.secho("Empty input!", fg="red")
        return None

    _stream = read_string(_input)
    _stream = parse_sql(" ".join(_stream))

    if _stream.error:
        click.secho(f"Error on parse a command {_stream.error.msg}!", fg="red")
        return None

    pprint(_stream.result)
