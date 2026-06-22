pipeline {
    agent any

    parameters {
        choice(
            name: 'AI_DEMO_SCENARIO',
            choices: ['ai-ok', 'ai-timeout', 'ai-invalid', 'ai-disabled', 'high-risk'],
            description: 'Escenario de IA a simular'
        )
        choice(
            name: 'AI_PROVIDER',
            choices: ['mock', 'ollama'],
            description: 'Proveedor de IA. mock es reproducible; ollama requiere un servidor Ollama accesible.'
        )
        string(
            name: 'OLLAMA_BASE_URL',
            defaultValue: 'http://localhost:11434',
            description: 'URL base de Ollama si AI_PROVIDER=ollama'
        )
        string(
            name: 'OLLAMA_MODEL',
            defaultValue: 'qwen2.5:1.5b',
            description: 'Modelo Ollama si AI_PROVIDER=ollama'
        )
    }

    environment {
        PYTHON = 'python3'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Unit tests') {
            steps {
                sh '${PYTHON} -m unittest discover -s tests'
            }
        }

        stage('AI continuity review') {
            steps {
                sh '''${PYTHON} scripts/run_ci_demo.py \
                    --scenario ${AI_DEMO_SCENARIO} \
                    --ai-provider ${AI_PROVIDER} \
                    --ollama-base-url ${OLLAMA_BASE_URL} \
                    --ollama-model ${OLLAMA_MODEL} \
                    --reports-dir reports'''
            }
        }

        stage('Deployment gate') {
            steps {
                sh '${PYTHON} scripts/deployment_gate.py --audit-report reports/audit-report.json'
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**/*', fingerprint: true, allowEmptyArchive: true
        }
    }
}
