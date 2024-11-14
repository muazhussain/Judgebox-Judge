import docker
import os
import tempfile
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

from app.exceptions.judge_exceptions import UnsupportedLanguageError

class ExecutionError(Exception):
    """Base exception for code execution errors"""
    pass

class DockerConnectionError(ExecutionError):
    """Raised when unable to connect to Docker daemon"""
    pass

class CompilationError(ExecutionError):
    """Raised when code compilation fails"""
    pass

class ExecutionTimeoutError(ExecutionError):
    """Raised when code execution exceeds time limit"""
    pass

class CodeExecutor:
    def __init__(self, language: str, source_code: str, time_limit: int, memory_limit: int):
        """
        Initialize the code executor.
        
        Args:
            language: Programming language of the source code
            source_code: Source code to execute
            time_limit: Maximum execution time in seconds
            memory_limit: Maximum memory usage in MB
        """
        self.language = language
        self.source_code = source_code
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.docker_client = None
        self.logger = logging.getLogger(__name__)
        
        self._initialize_docker()
        self.configure_language()

    def _initialize_docker(self) -> None:
        """Initialize Docker client with error handling."""
        try:
            # Try to initialize Docker client without specifying a URL
            self.docker_client = docker.from_env()
            
            # Test the connection
            self.docker_client.ping()
            self.logger.info("Successfully connected to Docker daemon")
        
        except docker.errors.DockerException as e:
            self.logger.error(f"Failed to connect to Docker daemon: {str(e)}")
            
            # Try to initialize Docker client with a specific URL
            try:
                self.docker_client = docker.DockerClient(base_url="unix://var/run/docker.sock")
                self.docker_client.ping()
                self.logger.info("Successfully connected to Docker daemon using Unix socket")
            except docker.errors.DockerException as e:
                raise DockerConnectionError(f"Failed to connect to Docker daemon: {str(e)}")

    def configure_language(self) -> None:
        """Configure language-specific settings."""
        LANGUAGE_CONFIGS = {
            'python': {
                'image': 'python:3.9-slim',
                'extension': '.py',
                'compile_cmd': None,
                'run_cmd': 'python {filename}'
            },
            'cpp': {
                'image': 'gcc:latest',
                'extension': '.cpp',
                'compile_cmd': 'g++ {filename} -o program',
                'run_cmd': './program'
            },
            # Add more languages as needed
        }

        self.language_config = LANGUAGE_CONFIGS.get(self.language)
        if not self.language_config:
            raise UnsupportedLanguageError(f"Unsupported language: {self.language}")

        self.image = self.language_config['image']
        self.extension = self.language_config['extension']
        self.compile_cmd = self.language_config['compile_cmd']
        self.run_cmd = self.language_config['run_cmd']

    @contextmanager
    def _prepare_workspace(self, test_input: str) -> str: # type: ignore
        """
        Prepare temporary workspace with source code and input files.
        
        Args:
            test_input: Input data for the program
            
        Yields:
            Path to temporary directory
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write source code
            source_file = f"main{self.extension}"
            source_path = os.path.join(temp_dir, source_file)
            with open(source_path, 'w') as f:
                f.write(self.source_code)

            # Write input
            input_path = os.path.join(temp_dir, 'input.txt')
            with open(input_path, 'w') as f:
                f.write(test_input)

            yield temp_dir

    def _compile_code(self, workspace_dir: str) -> None:
        """
        Compile the code if needed.
        
        Args:
            workspace_dir: Path to temporary workspace
        """
        if not self.compile_cmd:
            return

        try:
            result = self.docker_client.containers.run(
                self.image,
                self.compile_cmd.format(filename=f"main{self.extension}"),
                volumes={workspace_dir: {'bind': '/workspace', 'mode': 'rw'}},
                working_dir='/workspace',
                remove=True,
                network_mode='none'  # Disable network access
            )
            self.logger.debug(f"Compilation result: {result}")
        except docker.errors.ContainerError as e:
            raise CompilationError(f"Compilation failed: {str(e)}")

    def execute(self, test_input: str) -> Dict[str, Any]:
        """
        Execute the code with the given input.
        
        Args:
            test_input: Input data for the program
            
        Returns:
            Dictionary containing execution results
        """
        try:
            with self._prepare_workspace(test_input) as workspace_dir:
                if self.compile_cmd:
                    self._compile_code(workspace_dir)

                container = None
                try:
                    # Run the code
                    container = self.docker_client.containers.run(
                        self.image,
                        self.run_cmd.format(filename=f"main{self.extension}"),
                        volumes={workspace_dir: {'bind': '/workspace', 'mode': 'rw'}},
                        working_dir='/workspace',
                        mem_limit=f'{self.memory_limit}m',
                        cpus=1,
                        detach=True,
                        network_mode='none',  # Disable network access
                        stdin_open=True,
                        tty=True
                    )

                    try:
                        result = container.wait(timeout=self.time_limit)
                        logs = container.logs().decode('utf-8', errors='replace')
                        
                        return {
                            'output': logs,
                            'exit_code': result['StatusCode'],
                            'error': result.get('Error'),
                            'status': 'success'
                        }

                    except docker.errors.NotFound:
                        return {
                            'output': None,
                            'exit_code': 1,
                            'error': 'Container was removed unexpectedly',
                            'status': 'error'
                        }

                except docker.errors.ContainerError as e:
                    return {
                        'output': None,
                        'exit_code': 1,
                        'error': str(e),
                        'status': 'error'
                    }
                
                finally:
                    if container:
                        try:
                            container.remove(force=True)
                        except docker.errors.APIError:
                            pass  # Ignore errors during cleanup

        except Exception as e:
            self.logger.exception("Execution failed")
            return {
                'output': None,
                'exit_code': 1,
                'error': str(e),
                'status': 'error'
            }

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.docker_client:
            try:
                self.docker_client.close()
            except Exception as e:
                self.logger.error(f"Error during cleanup: {str(e)}")