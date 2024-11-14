from flask import Blueprint, request, jsonify
from app.services.code_executor import CodeExecutor
from app.exceptions.judge_exceptions import UnsupportedLanguageError
from app.services.judge_service import get_problem, get_test_cases

blueprint = Blueprint('api', __name__)

@blueprint.route('/judge', methods=['POST'])
def judge():
    data = request.get_json()
    submission_id = data['submissionId']
    problem_id = data['problemId']
    language = data['language']
    source_code = data['sourceCode']
    # Get problem details and test cases from database
    problem = get_problem(problem_id)
    problem = problem['data']
    test_cases = get_test_cases(problem_id)
    test_cases = test_cases['data']

    try:
        executor = CodeExecutor(
            language,
            source_code,
            problem['timeLimit'],
            problem['memoryLimit']
        )
    except UnsupportedLanguageError as e:
        return jsonify({'error': str(e)}), 400

    results = []
    for test_case in test_cases:
        result = executor.execute(test_case['input'])
        
        if result['exit_code'] != 0:
            status = 'RUNTIME_ERROR'
        elif result['output'].strip() != test_case['output'].strip():
            status = 'WRONG_ANSWER'
        else:
            status = 'ACCEPTED'

        results.append({
            'testCaseId': test_case['id'],
            'status': status,
            'executionTime': result['execution_time'],
            'memoryUsed': result['memory_used']
        })

    # Calculate final result
    final_result = 'ACCEPTED' if all(r['status'] == 'ACCEPTED' for r in results) else 'WRONG_ANSWER'

    return jsonify({
        'submissionId': submission_id,
        'result': final_result,
        'testResults': results
    })