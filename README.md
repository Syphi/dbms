# DBMS Project

A simple SQL parser and DBMS implementation.

## Installation

To install the dependencies, run:

```bash
pip install -r requirements.txt
```

## Running the CLI

The project provides a CLI with several commands. You can run it using:

```bash
python src/main.py [COMMAND] [OPTIONS]
```

### Commands

- `lekser`: Run the lexer to tokenize an SQL query.
- `input`: Parse a SQL query and print the Abstract Syntax Tree (AST).

### Examples

**Run Lexer on a command:**

```bash
python src/main.py lekser -c "SELECT * FROM users;"
```

**Parse a SQL command and see the AST:**

```bash
python src/main.py input -c "INSERT INTO users (id, name) VALUES (1, 'Alice');"
```

## Running Tests

To run the tests, make sure you have `pytest` installed and use the following command:

```bash
PYTHONPATH=. pytest src/test/test_gramatical_coverage.py
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
docker run -it dbms pytest test/test_gramatical_coverage.py
```
