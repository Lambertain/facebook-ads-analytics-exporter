# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Funnel path tracking for lead journey through sales pipeline
- NetHunt CRM integration with status/stage mapping
- AlfaCRM integration with comprehensive status mapping
- CRM enrichment endpoints for leads data
- Real diagnostic scripts for CRM status verification

### Changed
- Updated .env.example with all required environment variables
- Enhanced README.md with detailed API documentation
- Improved security documentation and guidelines

## [1.0.0] - 2025-10-10

### Added
- Meta (Facebook) Marketing API integration
- Automated lead collection from Facebook lead forms
- Google Sheets export with formatting
- Excel export with 33 fields for student data
- SQLite database for run history tracking
- Real-time progress via Server-Sent Events
- API Key authentication for production security
- React frontend with Material-UI dark theme
- Campaign classification (teachers vs students)
- CRM integrations (NetHunt for teachers, AlfaCRM for students)
- Funnel path reconstruction from current CRM status
- Docker and Docker Compose support
- CI/CD configuration for Railway deployment
- Pre-commit hooks for code quality

### Security
- API Key authentication middleware
- CORS configuration for production
- Secure credential management via .env
- Git history verified clean (no token leaks)

### Documentation
- Comprehensive README with Quick Start guide
- API documentation with Swagger UI
- CONTRIBUTING.md for contributors
- MIT License
- Architecture diagrams
- Troubleshooting guide

## [0.9.0] - 2025-09-15

### Added
- Initial project setup
- Basic FastAPI backend structure
- React frontend scaffolding
- Meta API connector prototype
- Google Sheets integration POC

---

For detailed commit history, see [GitHub Commits](https://github.com/yourusername/ecademy/commits/main)
