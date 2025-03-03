# Define the Python files to check
PYTHON_FILES=$(shell find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*")
NOTEBOOK_FILES=$(shell find . -name "*.ipynb" -not -path "./venv/*" -not -path "./.venv/*")

# Run Black formatting
black:
	@echo "Running Black on Python files..."
	@if [ -z "$(PYTHON_FILES)" ]; then \
		echo "No Python files found to check with Black."; \
	else \
		black .;\ 
		black --check $(PYTHON_FILES) --verbose; \
	fi
	@echo "Running Black-NB on Jupyter notebooks..."
	@if [ -z "$(NOTEBOOK_FILES)" ]; then \
		echo "No Jupyter notebooks found to check with Black"; \
	else \
		nbqa black .; \
		nbqa black --check $(NOTEBOOK_FILES) --verbose; \
	fi

# Run Radon maintainability check
radon:
	@echo "Running Radon Maintainability Check..."
	@if [ -z "$(PYTHON_FILES)" ]; then \
		echo "No Python files found to check with Radon."; \
	else \
		radon mi $(PYTHON_FILES); \
	fi
	@echo "Running Radon Maintainability Check for Jupyter Notebooks..."
	@if [ -z "$(NOTEBOOK_FILES)" ]; then \
		echo "No No Jupyter notebooks found to check with Radon."; \
	else \
		radon mi --include-ipynb $(NOTEBOOK_FILES); \
	fi

# Run Pylint
pylint:
	@echo "Running Pylint..."
	@if [ -z "$(PYTHON_FILES)" ]; then \
		echo "No Python files found to check with Pylint."; \
	else \
		pylint $(PYTHON_FILES) --output-format=colorized --score=y || true; \
		echo "Pylint completed. Check the output above for details."; \
	fi
	@echo "Running nbQA Pylint for Jupyter Notebooks..."
	@if [ -z "$(NOTEBOOK_FILES)" ]; then \
		echo "No Jupyter notebooks found to check with nbQA."; \
	else \
		nbqa pylint $(NOTEBOOK_FILES) --output-format=colorized --score=y || true; \
		echo "nbQA Pylint completed. Check the output above for details."; \
	fi

# Run all checks
check: black radon pylint
	@echo "All checks passed!"

# Help command
help:
	@echo "Makefile commands:"
	@echo "  make black   - Run Black and Black-NB to format the code"
	@echo "  make radon   - Run Radon maintainability check"
	@echo "  make pylint  - Run Pylint for code linting"
	@echo "  make check   - Run all checks (Black, Radon, and Pylint)"