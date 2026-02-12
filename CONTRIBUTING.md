# Contributing to CACM

Thank you for your interest in contributing to CACM (CIP Asset Configuration Manager). This guide outlines the contribution process, workflow requirements, and quality standards for the project.

By participating, you agree to abide by our Code of Conduct (see `CODE_OF_CONDUCT.md`).

---

## Ways to Contribute

- Report bugs and propose enhancements via GitHub Issues
- Improve documentation, examples, and diagrams
- Fix bugs or implement features
- Add tests and improve reliability and security

If you are unsure where to start, open an issue describing what you would like to do and we will help you scope it.

---

## Development Workflow

### 1. Fork and Branch

Fork the repository and create a feature branch following our conventional branching strategy:

- `feat/<short-description>` — new features
- `fix/<short-description>` — bug fixes
- `docs/<short-description>` — documentation-only changes
- `chore/<short-description>` — maintenance, dependencies, tooling, refactors
- `test/<short-description>` — test-only changes

Examples:
- `feat/baseline-collector-linux`
- `fix/api-auth-middleware`
- `docs/cip-010-baseline-evidence`

### 2. Make Changes

Implement your changes following these guidelines:
- Write clear, maintainable code
- Add or update tests for new functionality or bug fixes
- Update documentation when behavior changes
- Keep changes focused and reasonably scoped

### 3. Run Required Tools

Before committing, you must run both `prek` and `ruff`. These are not optional.

#### prek (Pre-commit Hooks)

Install prek hooks once:
```bash
prek install
```

Run hooks on staged or changed files:
```bash
prek run
```

Run hooks on the entire repository (recommended before opening a PR):
```bash
prek run --all-files
```

Documentation: https://prek.j178.dev/

If a hook fails, fix the issue and re-run prek before committing.

#### ruff (Linting)

Run ruff to check for linting issues:
```bash
ruff check .
```

If the repository uses ruff formatting, also run:
```bash
ruff format .
```

Fix any reported issues before committing. If you believe an exception is warranted, discuss it in your pull request.

### 4. Test Locally

Run the test suite locally and ensure all tests pass:
```bash
pytest -q
```

New features must include appropriate tests. Bug fixes should include regression tests when feasible.

### 5. Commit Using Conventional Commits

All commits must follow the Conventional Commits specification.

Format:
```
<type>(optional-scope): <description>

[optional body]

[optional footer(s)]
```

Common types:
- `feat:` a new feature
- `fix:` a bug fix
- `docs:` documentation changes
- `chore:` tooling, maintenance, or dependency updates
- `refactor:` code refactoring without behavior changes
- `test:` adding or fixing tests
- `ci:` CI configuration changes

Examples:
- `feat(api): add baseline snapshot endpoint`
- `fix(collector): handle firmware-only assets`
- `docs: clarify CIP-010 evidence mapping`

For breaking changes:
- Add `!` after the type or scope: `feat!: change API response format`
- Include a `BREAKING CHANGE:` footer in the commit body

### 6. Open a Pull Request

Include the following in your pull request description:
- What changed and why
- Related issue(s), if applicable (e.g., "Closes #123")
- How you tested the changes (commands and results)
- Screenshots or logs if the change impacts user experience or outputs

---

## Testing Requirements

All pull requests must meet the following testing criteria:
- All CI checks pass
- New features include unit or integration tests as appropriate
- Bug fixes include regression tests when feasible
- You have run the test suite locally and confirmed all tests pass

Testing guidelines:
- For parsing or collector changes, include representative samples and edge case tests
- For detection or scoring logic changes, include tests demonstrating expected severity and outputs
- For API contract changes, update OpenAPI documentation and add contract tests where possible

---

## Pull Request Review and Merge Criteria

A pull request is ready to merge when:
- The change aligns with project scope and CIP-010/CACM goals
- Code is readable and maintainable
- Pre-commit hooks (prek) pass
- Linting (ruff) passes with no unresolved issues
- All tests pass with appropriate coverage
- A maintainer approves the pull request

Maintainers may request changes, additional tests, or restructuring to maintain project consistency and quality.

---

## Reporting Security Issues

Do not file public issues for security vulnerabilities. See `SECURITY.md` for responsible disclosure procedures.

---

## License

By contributing, you agree that your contributions will be licensed under the project's license. See `LICENSE` for details.

---

Thank you for helping improve CACM.
