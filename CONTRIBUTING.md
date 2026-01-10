# Contributing to Dev Orchestrator MCP

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/chaos-consultant/dev-orchestrator-mcp.git
   cd dev-orchestrator-mcp
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   pip install -e .
   pip install pytest pytest-asyncio  # For testing
   ```

3. **Set up dashboard**
   ```bash
   cd dashboard
   npm install
   cd ..
   ```

## Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow existing code style
   - Add tests for new features
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run Python tests
   pytest

   # Test server imports
   python -c "from src.server import server; print('OK')"

   # Build dashboard
   cd dashboard && npm run build
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

5. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

- **Python**: Follow PEP 8 guidelines
- **TypeScript/React**: Use consistent naming and structure
- **Commit messages**: Use clear, descriptive messages

## Testing

- Add tests for new features in the `tests/` directory
- Ensure existing tests pass before submitting PR
- Test MCP tools manually with Claude Code

## Questions?

Feel free to open an issue for any questions or concerns.
