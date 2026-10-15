# AI 보안 실습

## LLM 설정

LLM API 클라이언트 설정은 프로젝트 루트의 [`llm_client.py`](./llm_client.py)에 모아 두었습니다. 노트북은 `notebook/` 폴더를 작업 경로로 실행해도 프로젝트 루트를 찾아 공통 모듈을 불러옵니다. MonoRouter 키는 프로젝트 루트의 `.env` 파일에 설정합니다.

클라이언트 생성과 provider별 설정을 공통 모듈로 분리하는 방식은 실무에서도 흔합니다. `.env`는 로컬 개발용이며, 배포 환경에서는 키를 소스에 두지 않고 환경 변수나 클라우드 Secret Manager를 통해 주입하세요.

```dotenv
MY_API_KEY=발급받은_API_키
```

`.env`는 Git에 커밋하지 마세요. 키가 노트북, 출력 결과, 저장소 이력에 한 번이라도 포함됐다면 해당 키를 폐기하고 새 키를 발급받으세요.

MonoRouter 사용:

```python
from llm_client import create_llm_client

PROVIDER = "mono"
client, MODEL = create_llm_client(
    provider=PROVIDER,
    api_key_env="MY_API_KEY",
)
```

Ollama 사용:

```python
PROVIDER = "ollama"
client, MODEL = create_llm_client(provider=PROVIDER)
```

MonoRouter 키는 `MY_API_KEY` 환경 변수 또는 `.env`에서 읽고, Ollama는 `http://localhost:11434/v1`의 `llama3.2:3b` 모델을 사용합니다. API 키를 코드나 노트북 출력에 표시하지 마세요.
