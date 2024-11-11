import docker
import os
import tempfile
from app.exceptions.judge_exceptions import UnsupportedLanguageError

class CodeExecutor:
    def __init__(self, language, source_code, time_limit, memory_limit):
        self.language = language
        self.source_code = source_code
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.docker_client = docker.from_env()

        self.configure_language()

    def configure_language(self):
        self.language_config = app.config['DOCKER_IMAGE_MAPPING'].get(self.language)
        if not self.language_config:
            raise UnsupportedLanguageError(f"Unsupported language: {self.language}")

        self.image = self.language_config['image']
        self.extension = self.language_config['extension']
        self.compile_cmd = self.language_config['compile_cmd']
        self.run_cmd = self.language_config['run_cmd']

    def execute(self, test_input):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write source code to file
            source_file = f"main{self.extension}"
            source_path = os.path.join(temp_dir, source_file)
            with open(source_path, 'w') as f:
                f.write(self.source_code)

            # Write input to file
            input_path = os.path.join(temp_dir, 'input.txt')
            with open(input_path, 'w') as f:
                f.write(test_input)

            # Compile if needed
            if self.compile_cmd:
                compile_result = self.docker_client.containers.run(
                    self.image,
                    self.compile_cmd.format(filename=source_file),
                    volumes={temp_dir: {'bind': '/workspace', 'mode': 'rw'}},
                    working_dir='/workspace',
                    remove=True
                )

            # Run the code
            try:
                container = self.docker_client.containers.run(
                    self.image,
                    self.run_cmd.format(filename=source_file),
                    volumes={temp_dir: {'bind': '/workspace', 'mode': 'rw'}},
                    working_dir='/workspace',
                    mem_limit=f'{self.memory_limit}m',
                    cpus=1,
                    detach=True
                )

                result = container.wait(timeout=self.time_limit)
                logs = container.logs().decode()
                container.remove()

                return {
                    'output': logs,
                    'exit_code': result['StatusCode'],
                    'error': result.get('Error')
                }

            except docker.errors.ContainerError as e:
                return {
                    'output': None,
                    'exit_code': 1,
                    'error': str(e)
                }