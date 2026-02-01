# DBMS Project

A simple SQL parser and DBMS implementation.

## Installation

To install the dependencies, run:

```bash
pip install -r requirements.txt
```

## Running the CLI

The project provides a CLI with several commands. Use the `run.sh` script from the project root:

```bash
./run.sh [COMMAND] [OPTIONS]
```

### Available Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize the database metadata file |
| `lekser` | Run the lexer to tokenize an SQL query |
| `input` | Parse a SQL query and print the Abstract Syntax Tree (AST) |
| `gramatical` | Analyze grammar from a token stream |

### Examples

**Initialize the database:**

```bash
./run.sh init
```

**Run Lexer on a command:**

```bash
./run.sh lekser -c "SELECT * FROM users;"
```

**Parse a SQL command and see the AST:**

```bash
./run.sh input -c "INSERT INTO users (id, name) VALUES (1, 'Alice');"
./run.sh input -c "INSERT INTO products (id, title) VALUES (1, 'Book');"
./run.sh input -c "INSERT INTO coords (x, y, z) VALUES (10, 20, 30);"
```

**View help:**

```bash
./run.sh --help
```

## Running Tests

To run the tests, make sure you have `pytest` installed:

```bash
# Run all tests
PYTHONPATH=. pytest -vv src/test/

# Run specific test modules
PYTHONPATH=. pytest -vv src/test/storage/
PYTHONPATH=. pytest -vv src/test/parser/
```

## Running with Docker

You can also run the project using Docker.

### Build the Image

```bash
docker build -t dbms .
```

### Run CLI Commands

```bash
docker run -it dbms python main.py input -c "SELECT * FROM users WHERE id = 1;"
```

### Run Tests

```bash
docker run -it dbms pytest test/
```
