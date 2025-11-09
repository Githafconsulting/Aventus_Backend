# Contractor Unit Tests

This directory contains unit tests for the contractor module, including tests for both the SQLAlchemy models and Pydantic schemas.

## Test Files

- `test_contractor_model.py` - Tests for the Contractor SQLAlchemy model
- `test_contractor_schema.py` - Tests for the Contractor Pydantic schemas

## Running Tests

### Install Testing Dependencies

First, make sure you have pytest installed:

```bash
pip install pytest pytest-cov
```

Or install from requirements.txt (if pytest is added there).

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_contractor_model.py
pytest tests/test_contractor_schema.py
```

### Run with Coverage

```bash
pytest --cov=app.models.contractor --cov=app.schemas.contractor tests/
```

### Run Specific Test Class

```bash
pytest tests/test_contractor_model.py::TestContractorModel
pytest tests/test_contractor_schema.py::TestContractorCreate
```

### Run Specific Test Method

```bash
pytest tests/test_contractor_model.py::TestContractorModel::test_create_contractor_minimal
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Debug Output

```bash
pytest -s
```

## Test Coverage

The tests cover:

### Model Tests (`test_contractor_model.py`)
- Contractor model creation with minimal and full fields
- Default values (status, currency)
- Unique constraints (email, contract_token)
- Status transitions
- Timestamp handling
- JSON field storage (cds_form_data)
- Text field storage (long content)
- Nullable fields
- Enum values

### Schema Tests (`test_contractor_schema.py`)
- ContractorCreate validation
- ContractorUpdate partial updates
- SignatureSubmission validation
- CDSFormData flexible structure
- ContractorResponse serialization
- ContractorDetailResponse with all fields
- Email validation
- Required vs optional fields
- Default values

## Writing New Tests

When adding new tests:

1. Follow the existing naming conventions
2. Group related tests in classes (e.g., `TestContractorModel`)
3. Use descriptive test method names (e.g., `test_create_contractor_minimal`)
4. Add docstrings to explain what each test does
5. Use fixtures from `conftest.py` for common setup

## Test Database

The model tests use an in-memory SQLite database for fast, isolated testing. Each test function gets a fresh database session via the `test_db` fixture.
