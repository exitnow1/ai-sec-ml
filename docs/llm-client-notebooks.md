# 노트북 LLM 클라이언트 공통화 및 타입 오류 수정

## 목적

실습 노트북마다 반복되던 MonoRouter/Ollama 클라이언트 설정을 공통 모듈로
옮겼다. API 키 관리, 노트북의 모듈 검색 경로, OpenAI SDK 호출 타입을 한
곳에서 일관되게 관리하고, 노트북 실행과 정적 타입 검사 모두에서 같은
설정을 사용하도록 한다.

## 공통 클라이언트

저장소 루트의 `llm_client.py`가 `create_llm_client`를 제공한다.

```python
from llm_client import create_llm_client

PROVIDER = "mono"  # 또는 "ollama"
client, MODEL = create_llm_client(
    provider=PROVIDER,
    api_key_env="MY_API_KEY",
)
```

`provider`는 `mono` 또는 `ollama`이며, 함수는 OpenAI 호환 클라이언트와
해당 provider의 기본 모델명을 반환한다.

| Provider | API URL | 기본 모델 | 인증 |
| --- | --- | --- | --- |
| `mono` | MonoRouter OpenAI 호환 URL | `gpt-5.5` | `api_key_env`가 지정한 환경 변수 |
| `ollama` | `http://localhost:11434/v1` | `llama3.2:3b` | 로컬 Ollama용 `ollama` 값 |

`api_key_env`의 기본값은 `"MY_API_KEY"`다. MonoRouter 사용 시 `load_dotenv()`
로 프로젝트 `.env`의 변수를 읽은 다음 그 변수명으로 키를 조회한다. 키가
없으면 성공처럼 진행하지 않고, 어떤 환경 변수를 설정해야 하는지 알려주는
`ValueError`를 발생시킨다. Ollama는 로컬 엔드포인트를 사용하므로 이 키를
읽지 않는다. 지원하지 않는 provider도 `ValueError`로 명시적으로 거부한다.

프로젝트 루트의 `.env`에는 다음 형식으로 키를 둔다.

```dotenv
MY_API_KEY=발급받은_API_키
```

`.env`는 로컬 개발용이며 Git에 포함하지 않는다. 키를 노트북 셀이나 출력에
넣지 않는다. 키가 저장소에 노출된 적이 있다면 파일에서 지우는 것만으로
충분하지 않으므로 키를 폐기하고 새 값을 발급한다. 배포 환경에서는
환경 변수나 Secret Manager를 사용한다.

## 노트북의 모듈 검색 경로

Jupyter 커널의 현재 작업 디렉터리는 노트북 파일의 위치와 항상 같지는 않다.
따라서 `from llm_client import ...`만 두면 커널이 저장소 루트가 아닌
디렉터리에서 시작할 때 모듈을 찾지 못할 수 있다.

LLM 설정을 사용하는 노트북은 `llm_client.py`가 있는 디렉터리를 현재
작업 디렉터리와 그 상위에서 탐색해 `sys.path`에 추가한다. 탐색에 실패하면
`FileNotFoundError`를 발생시킨다. `os.chdir()`로 작업 디렉터리를 바꾸지는
않으므로 `../data`와 같은 기존 노트북 상대경로의 의미는 유지된다.

## OpenAI SDK 호출의 Pylance 오류

### 관찰한 진단

채팅 요청은 다음 형태로 작성되어 있었다.

```python
messages = [{"role": "user", "content": prompt}]
if system:
    messages.insert(0, {"role": "system", "content": system})

limit = {"max_tokens": 500} if PROVIDER == "ollama" else {}
client.chat.completions.create(
    model=MODEL,
    messages=messages,
    temperature=temperature,
    stream=True,
    **limit,
)
```

같은 문제를 Python 파일에서 Pylance로 재현했다. 진단은
`reportCallIssue`였고, 구체적인 `reportArgumentType`은 `messages`에 대해
다음 불일치를 지적했다.

```text
list[dict[str, Unknown]]
Iterable[ChatCompletionMessageParam]
```

즉, 메시지 딕셔너리의 `role`/`content` 형태를 Python SDK가 요구하는 채팅
메시지 타입으로 추론하지 못한 것이 확인된 원인이다. 진단에 함께 표시된
`temperature` 타입 설명은 SDK의 파라미터 타입 정보이며, 이 사례에서
`temperature`가 잘못된 인자라는 증거는 아니었다.

또한 `**limit`은 동적으로 만든 일반 딕셔너리를 키워드 인자로 확장한다.
이 방식은 Pylance가 각 키를 SDK의 개별 파라미터와 대조하는 데 방해가 될
수 있다. 그러므로 오류 원인을 `temperature`로 돌리거나, `**limit`만
제거하는 것으로 충분하다고 가정하지 않았다.

### 적용한 수정

메시지 목록에 SDK가 제공하는 `ChatCompletionMessageParam` 타입을 지정했다.
`ask`의 입력 인자와 반환 타입도 명시했다. 최대 토큰 수는 Ollama 분기에서만
`max_tokens=500`으로 직접 전달하고, MonoRouter 분기에서는 그 인자를
전달하지 않는다.

```python
from openai.types.chat import ChatCompletionMessageParam

messages: list[ChatCompletionMessageParam] = [
    {"role": "user", "content": prompt}
]
if system:
    messages.insert(0, {"role": "system", "content": system})

if PROVIDER == "ollama":
    stream = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        stream=True,
        max_tokens=500,
    )
else:
    stream = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        stream=True,
    )
```

이 수정은 SDK에 맞는 메시지 타입을 정적으로 확인할 수 있게 하며, 두
provider의 요청 파라미터 차이를 코드에서 명시한다. 두 분기 모두 기존
`temperature`와 스트리밍 동작을 유지한다.

## 검증

- `tests/test_llm_client.py`: provider 선택, 키 환경 변수 기본값 및 사용자
  지정, 키 누락, 미지원 provider를 포함한 테스트 5개가 통과했다.
- 노트북 17개의 JSON을 읽고 IPython 변환 후 각 코드 셀의 Python 문법을
  검사했다.
- 타입 재현 코드를 별도 Python 파일로 만들어 Pylance 진단을 확인했다.
  `ChatCompletionMessageParam` 타입 지정과 명시적인 provider별 호출로
  재현 파일의 진단이 사라졌다.
- 노트북 작업 디렉터리를 `notebook/`으로 설정한 상태에서 프로젝트 루트의
  `llm_client.py` import 및 Ollama 설정 생성을 실행으로 확인했다.
