# Agent Rules

## Coding Principles

### 1. 주석 사용 금지

- **인라인 주석(`#`) 사용 금지**: 모든 인라인 주석은 제거
- **Docstring만 사용**: 로직 설명이 필요하면 함수/클래스 Docstring에 작성
- **예외**: Shebang 및 encoding 선언만 허용

### 2. 함수 길이 제한

- **15줄 제한**: 한 함수는 15줄을 초과하지 않음
- **분리 원칙**: 15줄 초과 시 helper 함수로 분리

## Execution Rules

1. **Execution**: Always use `uv run` for running Python scripts (e.g., `uv run script.py`).
2. **Language**: Always answer in Korean.
3. **Commit Convention**: Follow the specified commit emojis and format.
