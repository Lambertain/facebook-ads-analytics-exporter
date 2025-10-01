# Contributing to eCademy

Thank you for your interest in contributing to eCademy! This document provides guidelines and instructions for contributing to the project.

## 🤝 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## 🚀 How to Contribute

### Reporting Bugs

Before creating a bug report, please check existing issues to avoid duplicates.

**When reporting a bug, include:**
- Clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or error messages
- Screenshots if applicable

### Suggesting Features

Feature suggestions are welcome! Please:
- Check existing feature requests first
- Provide clear use cases
- Explain why this feature would benefit users
- Consider implementation complexity

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/ecademy.git
   cd ecademy
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set up development environment**
   ```bash
   # Backend
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pre-commit install

   # Frontend
   cd web
   npm install
   ```

4. **Make your changes**
   - Follow the code style guidelines (see below)
   - Add tests for new functionality
   - Update documentation as needed
   - Keep commits atomic and well-described

5. **Test your changes**
   ```bash
   # Backend tests
   pytest
   pytest --cov=app --cov-report=html

   # Frontend tests
   cd web
   npm test
   npm run lint
   ```

6. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

   Use conventional commit messages:
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation changes
   - `style:` formatting, missing semicolons, etc.
   - `refactor:` code restructuring
   - `test:` adding tests
   - `chore:` maintenance tasks

7. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub with:
   - Clear description of changes
   - Related issue numbers (if any)
   - Screenshots/GIFs for UI changes
   - Test results

## 📝 Code Style Guidelines

### Python (Backend)

- **PEP 8** compliance
- **Type hints** for all functions
- **Docstrings** (Google style) for classes and functions
- Maximum line length: 88 characters (Black default)

```python
def fetch_leads(
    start_date: str,
    end_date: str,
    campaign_id: str | None = None
) -> list[dict]:
    """
    Fetch leads from Meta API for the specified period.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        campaign_id: Optional campaign ID filter

    Returns:
        List of lead dictionaries with contact information

    Raises:
        MetaAPIError: If API request fails
    """
    # Implementation
```

**Formatting:**
```bash
black app/ tests/
flake8 app/ tests/
mypy app/
```

### TypeScript/React (Frontend)

- **ESLint** and **Prettier** configuration
- **Functional components** with hooks
- **TypeScript** strict mode
- Meaningful component and variable names

```typescript
interface StudentData {
  id: string;
  name: string;
  email: string;
  enrollmentDate: Date;
}

const StudentTable: React.FC<{ data: StudentData[] }> = ({ data }) => {
  // Implementation
};
```

**Formatting:**
```bash
cd web
npm run format
npm run lint
npm run type-check
```

## 🧪 Testing Standards

### Backend Tests

- **Unit tests** for business logic
- **Integration tests** for API endpoints
- **Mocked external services** (Meta API, Google Sheets, CRM)
- Minimum **70% code coverage**

```python
def test_fetch_leads_success(mocker):
    """Test successful lead fetching from Meta API."""
    mock_response = {"data": [{"id": "123", "email": "test@example.com"}]}
    mocker.patch("app.connectors.meta.requests.get", return_value=mock_response)

    result = fetch_leads("2025-01-01", "2025-01-31")

    assert len(result) == 1
    assert result[0]["id"] == "123"
```

### Frontend Tests

- **Component tests** with React Testing Library
- **User interaction tests**
- **Snapshot tests** for UI consistency

```typescript
test('renders student table with data', () => {
  const students = [{ id: '1', name: 'John Doe', email: 'john@example.com' }];
  render(<StudentTable data={students} />);

  expect(screen.getByText('John Doe')).toBeInTheDocument();
  expect(screen.getByText('john@example.com')).toBeInTheDocument();
});
```

## 📁 Project Structure

```
ecademy/
├── app/                    # Backend (FastAPI)
│   ├── connectors/         # External API integrations
│   ├── middleware/         # Authentication, CORS
│   ├── models.py           # Data models
│   ├── database.py         # Database connection
│   └── main.py             # FastAPI application
├── web/                    # Frontend (React + TypeScript)
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── api.ts          # API client
│   │   └── App.tsx         # Main application
│   └── public/
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── config/                 # Configuration files
└── docs/                   # Additional documentation
```

## 🔐 Security Guidelines

- **Never commit credentials** or API keys
- Use `.env` for sensitive configuration
- Validate all user inputs
- Sanitize data before database operations
- Follow OWASP security best practices
- Report security vulnerabilities privately

## 📚 Documentation

When adding new features:
- Update `README.md` if needed
- Add docstrings to new functions/classes
- Update API documentation in `/docs` endpoint
- Add examples for complex functionality

## 🎯 Review Process

Pull requests will be reviewed for:
1. **Code quality** - follows style guidelines
2. **Tests** - adequate test coverage
3. **Documentation** - clear and complete
4. **Functionality** - works as intended
5. **Performance** - no unnecessary overhead
6. **Security** - no vulnerabilities introduced

## 💬 Getting Help

- **Questions?** Open a discussion on GitHub
- **Need clarification?** Comment on relevant issues
- **Found a problem?** Open an issue with details

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Every contribution helps make eCademy better. We appreciate your time and effort!

---

**Happy Coding! 🚀**
