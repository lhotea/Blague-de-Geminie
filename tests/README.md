# Test Suite for Blague-de-Geminie

## Overview

This directory contains the test suite for the Blague-de-Geminie application, focusing on parser functions and data analysis logic.

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run with verbose output
```bash
pytest tests/ -v
```

### Run with coverage report
```bash
pytest tests/ --cov=analyse_strava --cov-report=term-missing
```

### Run specific test file
```bash
pytest tests/test_analyse_strava.py -v
```

### Run specific test class
```bash
pytest tests/test_analyse_strava.py::TestParserFormatTabule -v
```

### Run specific test
```bash
pytest tests/test_analyse_strava.py::TestParserFormatTabule::test_valid_nordic_ski -v
```

## Test Structure

```
tests/
├── __init__.py                    # Package initialization
├── README.md                      # This file
├── test_analyse_strava.py         # Parser function tests (54 tests)
└── fixtures/                      # Test data fixtures
    ├── sample_tabule.txt          # Tab-separated format examples
    ├── sample_strava_export.txt   # Strava export format examples
    └── sample_simple.txt          # Simple CSV format examples
```

## Test Coverage

Current coverage: **58%** on `analyse_strava.py`

### Covered Functions (100% or near-complete)
- ✅ `parser_duree_strava()` - Duration parsing (H:MM:SS, MM:SS)
- ✅ `parser_duree()` - Duration parsing (1h30, 45min, decimal)
- ✅ `parser_distance()` - Distance parsing with units
- ✅ `parser_format_tabule()` - Tab-separated format parsing
- ✅ `parser_format_strava_export()` - Strava export format parsing
- ✅ `parser_format_simple()` - Simple CSV format parsing
- ✅ `parser_donnees_strava()` - Main parser entry point
- ✅ `calculer_temps_par_semaine()` - Weekly time calculation
- ✅ `comparer_activites()` - Activity comparison

### Not Yet Covered
- ⚠️ `generer_feedback_coach()` - OpenAI API integration (needs mocks)
- ⚠️ `analyser_donnees_strava()` - CLI main function
- ⚠️ Edge cases in exception handling

## Test Classes

### `TestParserDureeStrava` (4 tests)
Tests for Strava duration format parser (H:MM:SS, MM:SS)

### `TestParserDuree` (6 tests)
Tests for flexible duration parser (1h30, 45min, decimal)

### `TestParserDistance` (4 tests)
Tests for distance parsing with various formats

### `TestParserFormatTabule` (10 tests)
Tests for tab-separated format including:
- Valid entries (Nordic Ski, Run, Ride, Weight Training)
- Distance in km and meters
- Date parsing edge cases
- Activity name normalization
- Invalid inputs

### `TestParserFormatStravaExport` (8 tests)
Tests for Strava export format including:
- French day abbreviations
- Distance in km and meters
- Missing fields
- Invalid inputs

### `TestParserFormatSimple` (7 tests)
Tests for simple CSV format including:
- With and without distance
- Multiple duration formats
- Missing fields
- Invalid dates

### `TestParserDonneesStrava` (7 tests)
Tests for main parser including:
- Empty inputs
- Mixed format handling
- Invalid line filtering
- Whitespace handling

### `TestCalculerTempsSemaine` (3 tests)
Tests for weekly time calculation

### `TestComparerActivites` (5 tests)
Tests for activity comparison logic

## Writing New Tests

### Example test structure
```python
def test_something(self):
    """Clear description of what's being tested"""
    # Arrange
    input_data = "some data"

    # Act
    result = function_to_test(input_data)

    # Assert
    assert result == expected_value
```

### Using pytest.approx for float comparisons
```python
assert result == pytest.approx(1.5125)
assert result == pytest.approx(0.0844, rel=1e-3)
```

### Testing for NaN values
```python
assert pd.isna(result['Distance (km)'])
```

## Known Issues

1. **Distance parsing in Strava export format**: When multiple meter values appear (distance and elevation), the regex may match the elevation instead of distance.

2. **Invalid date handling**: Pandas may parse some invalid dates as NaT instead of raising exceptions.

## Future Improvements

- [ ] Add tests for `generer_feedback_coach()` with OpenAI API mocks
- [ ] Add integration tests for full analysis pipeline
- [ ] Add tests for weather API integration
- [ ] Add tests for Streamlit app utility functions
- [ ] Increase coverage to 80%+
- [ ] Add performance tests for large datasets
