# Running Tests

## Installation

1. Add variables .env in root folder:

```
TEST_TOKEN=Get a test token from authentication page
```

2. Install `pytest` library:

```
pip install pytest==8.3.5
```

3. Run the tests inside app/tests folder:

```
# Run all tests
pytest

# Run all test of file
pytest test_docs_tools.py

# Run specific test
pytest test_docs_tools.py::test_create_and_delete
```
