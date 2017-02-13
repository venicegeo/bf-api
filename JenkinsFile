node ('python35') {
    git url: 'https://github.com/venicegeo/bf-api.git', branch: 'master'
    withCredentials([[$class: 'StringBinding', credentialsId: '978C467A-2B26-47AE-AD2F-4AFD5A4AF695', variable: 'THREADFIXKEY']]) {
        stage 'OWASP Dependency Check'
        sh """
            . /opt/rh/rh-python35/enable
            python -m venv .env
            . .env/bin/activate
            pip install -r requirements.txt
        """
        sh '/opt/dependency-check/bin/dependency-check.sh --project "bf-api" --scan ".env" --format "XML" --enableExperimental'
        sh 'cat dependency-check-report.xml'
        sh "/bin/curl -v --insecure -H 'Accept: application/json' -X POST --form file=@dependency-check-report.xml https://threadfix.devops.geointservices.io/rest/applications/57/upload?apiKey=$THREADFIXKEY"
        archive 'dependency-check-report.xml'
    }
}
