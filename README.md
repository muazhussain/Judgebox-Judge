# JudgeBox Judge Service

A secure and efficient code execution service built with Flask and Docker, designed to run user-submitted code in isolated containers. This service is part of the JudgeBox (online judge).

## Features

- 🔒 Secure code execution in isolated Docker containers
- ⚡ Support for multiple programming languages
- ⏱️ Time and memory limit enforcement
- 🛡️ Network access restriction
- 🚀 Scalable architecture
- 📊 Detailed execution feedback

## Supported Languages

Currently supports:
- Python (3.9)
- C++ (Latest GCC)

## Tech Stack

- **Framework**: Flask
- **Containerization**: Docker
- **CI/CD**: GitHub Actions
- **Deployment**: Docker Hub

## Prerequisites

- Python 3.9+
- Docker
- pip

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/judgebox-judge.git
cd judgebox-judge
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the service:
```bash
flask run
```

## API Endpoints

### Judge Endpoint
`POST /judge`

Executes code and evaluates against test cases.

Request Body:
```json
{
    "submissionId": "string",
    "problemId": "string",
    "language": "python|cpp",
    "sourceCode": "string"
}
```

Response:
```json
{
    "submissionId": "string",
    "result": "ACCEPTED|WRONG_ANSWER|RUNTIME_ERROR",
    "testResults": [
        {
            "testCaseId": "string",
            "status": "ACCEPTED|WRONG_ANSWER|RUNTIME_ERROR",
            "executionTime": number,
            "memoryUsed": number
        }
    ]
}
```

## Code Execution Flow

1. **Request Validation**
   - Verify submission details
   - Check language support
   - Validate source code

2. **Problem & Test Case Retrieval**
   - Fetch problem details
   - Get associated test cases

3. **Code Execution**
   - Create isolated Docker container
   - Set resource limits (time, memory)
   - Execute code with test input
   - Collect execution results

4. **Result Evaluation**
   - Compare output with expected output
   - Calculate final verdict
   - Return detailed results

## Security Measures

1. **Docker Isolation**
   - Each submission runs in a separate container
   - Network access disabled
   - Memory limits enforced
   - CPU usage restricted

2. **Resource Management**
   - Time limit enforcement
   - Memory limit enforcement
   - Process count restriction

3. **Error Handling**
   - Graceful handling of runtime errors
   - Container cleanup after execution
   - Resource cleanup on failures

## Development

### Project Structure
```
judgebox-judge/
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── services/
│   │   ├── code_executor.py
│   │   └── judge_service.py
│   └── exceptions/
│       └── judge_exceptions.py
├── app.py
├── config.py
├── Dockerfile
├── requirements.txt
└── README.md
```

### Adding New Language Support

1. Add language configuration in `code_executor.py`:
```python
LANGUAGE_CONFIGS = {
    'new_language': {
        'image': 'docker_image:tag',
        'extension': '.ext',
        'compile_cmd': 'compile command',
        'run_cmd': 'run command'
    }
}
```

2. Update the Docker image to include the new language's dependencies

## Deployment

The service uses GitHub Actions for CI/CD:

1. Automated testing
2. Docker image building
3. Push to Docker Hub
4. Deployment triggers

## Error Handling

The service handles various error cases:
- Compilation errors
- Runtime errors
- Timeout errors
- Memory limit exceeded
- Docker connection issues

## License

This project is licensed under the MIT License - see the LICENSE file for details.