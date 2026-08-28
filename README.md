# Cryptova 설치 및 실행 설명서

Cryptova는 AI 기반 암호화폐 자동매매 어시스턴트 시스템입니다.

본 프로젝트는 React 프론트엔드, FastAPI 백엔드, AI 추론 서버, MySQL 데이터베이스로 구성됩니다.  
사용자는 회원가입 및 로그인 후 전략 설정을 저장하고, AI가 생성한 LONG / SHORT / HOLD 신호를 기반으로 Paper Trading 방식의 자동매매 흐름을 검증할 수 있습니다.

---

## 1. 실행 환경

본 프로젝트는 로컬 개발 환경 실행을 기준으로 합니다.

| 구분 | 사용 기술 |
|---|---|
| Frontend | React, Vite, JavaScript |
| Backend | Python, FastAPI, SQLAlchemy |
| AI Server | Python, FastAPI |
| Database | MySQL |
| External API | Bybit Public API, Gemini API |
| Package Manager | npm, pip |

권장 실행 환경은 다음과 같습니다.

```text
Python 3.10 이상
Node.js 18 이상
npm
MySQL 8.x
Git
VSCode 또는 PowerShell
```

---

## 2. 프로젝트 폴더 구조

```text
Cryptova/
├─ cryptova-back/      # FastAPI 백엔드 서버
├─ cryptova-ui/        # React 프론트엔드
└─ cryptova-ai/        # AI 추론 서버
```

| 폴더 | 설명 |
|---|---|
| cryptova-back | 인증, 전략 설정, 자동매매 실행, 포지션 관리, 백테스트 API 제공 |
| cryptova-ui | 사용자 화면 제공, Trading / History / Backtest UI |
| cryptova-ai | `/predict/latest` API를 통해 AI 신호 반환 |

---

## 3. 사전 준비 사항

프로젝트 실행 전 다음 항목이 준비되어 있어야 합니다.

1. MySQL 서버 실행
2. 백엔드 `.env` 파일 설정
3. Python 패키지 설치
4. npm 패키지 설치
5. AI 서버 실행 가능 상태 확인

---

## 4. 데이터베이스 설정

MySQL에 접속한 뒤 프로젝트에서 사용할 데이터베이스를 생성합니다.

```sql
CREATE DATABASE cryptova_db;
```

이미 데이터베이스가 존재한다면 생략할 수 있습니다.

백엔드는 SQLAlchemy의 `Base.metadata.create_all()`을 사용하여 서버 실행 시 필요한 테이블을 자동 생성합니다.

서버 실행 시 생성되는 주요 테이블은 다음과 같습니다.

```text
users
strategy_settings
ai_signals
orders
trading_positions
trading_runs
api_keys
backtest_results
```

---

## 5. 백엔드 환경 변수 설정

`cryptova-back` 폴더에 `.env` 파일을 생성합니다.

```env
APP_NAME=Cryptova
APP_ENV=local

DATABASE_URL=mysql+pymysql://root:비밀번호@localhost:3306/cryptova_db

JWT_SECRET_KEY=change-this-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

AUTO_TRADING_INTERVAL_MINUTES=60

GEMINI_API_KEY=본인_GEMINI_API_KEY
BYBIT_PUBLIC_BASE=https://api.bybit.com
```

주의사항은 다음과 같습니다.

- `DATABASE_URL`의 MySQL 비밀번호는 본인 환경에 맞게 수정해야 합니다.
- `GEMINI_API_KEY`가 없으면 Gemini Explanation 대신 fallback 설명을 사용할 수 있습니다.
- `AUTO_TRADING_INTERVAL_MINUTES`는 자동매매 실행 주기입니다.
- 테스트용으로는 1분, 일반 실행용으로는 60분을 권장합니다.

---

## 6. 백엔드 설치 및 실행

PowerShell에서 백엔드 폴더로 이동합니다.

```powershell
cd C:\Users\User\Desktop\Cryptova\cryptova-back
```

가상환경을 생성합니다.

```powershell
python -m venv venv
```

가상환경을 실행합니다.

```powershell
.\venv\Scripts\activate
```

필요 패키지를 설치합니다.

```powershell
pip install -r requirements.txt
```

만약 `requirements.txt`가 없다면 아래 주요 패키지를 직접 설치합니다.

```powershell
pip install fastapi uvicorn sqlalchemy pymysql python-dotenv python-jose passlib[bcrypt] apscheduler httpx requests google-generativeai
```

백엔드 서버를 실행합니다.

```powershell
python -m uvicorn app.main:app --reload
```

정상 실행 주소는 다음과 같습니다.

```text
http://127.0.0.1:8000
```

API 문서 주소는 다음과 같습니다.

```text
http://127.0.0.1:8000/docs
```

---

## 7. AI 서버 설치 및 실행

AI 서버 폴더로 이동합니다.

```powershell
cd C:\Users\User\Desktop\Cryptova\cryptova-ai
```

가상환경을 생성하고 실행합니다.

```powershell
python -m venv venv
.\venv\Scripts\activate
```

필요 패키지를 설치합니다.

```powershell
pip install -r requirements.txt
```

만약 `requirements.txt`가 없다면 아래 주요 패키지를 직접 설치합니다.

```powershell
pip install fastapi uvicorn pandas numpy torch scikit-learn
```

AI 서버를 실행합니다.

```powershell
python -m uvicorn main:app --port 8001 --reload
```

정상 실행 주소는 다음과 같습니다.

```text
http://127.0.0.1:8001
```

백엔드는 AI 서버의 다음 API를 호출합니다.

```text
POST http://127.0.0.1:8001/predict/latest
```

---

## 8. 프론트엔드 설치 및 실행

프론트엔드 폴더로 이동합니다.

```powershell
cd C:\Users\User\Desktop\Cryptova\cryptova-ui
```

npm 패키지를 설치합니다.

```powershell
npm install
```

프론트엔드 개발 서버를 실행합니다.

```powershell
npm run dev
```

브라우저에서 다음 주소로 접속합니다.

```text
http://localhost:5173
```

또는

```text
http://127.0.0.1:5173
```

---

## 9. 전체 실행 순서 요약

프로젝트 실행 순서는 다음과 같습니다.

1. MySQL 실행
2. `cryptova-back`의 `.env` 설정 확인
3. 백엔드 서버 실행
4. AI 서버 실행
5. 프론트엔드 실행
6. 브라우저에서 `http://localhost:5173` 접속
7. 회원가입 또는 로그인
8. Trading 화면에서 전략 설정 저장
9. Run Once 실행
10. History / Backtest 화면 확인

각 서버 실행 명령어는 다음과 같습니다.

### 백엔드 실행

```powershell
cd C:\Users\User\Desktop\Cryptova\cryptova-back
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

### AI 서버 실행

```powershell
cd C:\Users\User\Desktop\Cryptova\cryptova-ai
.\venv\Scripts\activate
python -m uvicorn app:app --port 8001 --reload
```

### 프론트엔드 실행

```powershell
cd C:\Users\User\Desktop\Cryptova\cryptova-ui
npm run dev
```

---

## 10. 기능 테스트 방법

### 10.1 회원가입 및 로그인

브라우저에서 프론트엔드에 접속합니다.

```text
http://localhost:5173
```

회원가입 또는 로그인 성공 시 Trading 화면으로 이동하면 정상입니다.

---

### 10.2 전략 설정 저장

Trading 화면 왼쪽 Strategy Settings에서 값을 설정합니다.

| 항목 | 테스트 값 |
|---|---|
| Confidence Threshold | 46 |
| Position Size | 1 |
| Leverage | 1 |
| Max Drawdown Stop | -10 |
| Holding Strategy | 24h Fixed |

`Save Settings` 버튼을 클릭합니다.

정상 동작 시 백엔드 로그에 다음과 유사한 요청이 출력됩니다.

```text
POST /strategy/settings 200 OK
GET /strategy/settings 200 OK
```

---

### 10.3 Run Once 실행

Trading 화면에서 `Run Once` 버튼을 클릭합니다.

정상 동작 시 다음 흐름이 수행됩니다.

1. AI Signal 생성
2. Risk Filter 적용
3. Paper Entry 생성 또는 HOLD 처리
4. Trading Runs 저장
5. History 화면 반영

백엔드 로그 예시는 다음과 같습니다.

```text
POST /trading/run-once 200 OK
GET /signals 200 OK
GET /positions/open/pnl?symbol=BTCUSDT 200 OK
GET /trading/runs?limit=10 200 OK
```

---

### 10.4 Paper Position 확인

Run Once 실행 후 Trading 화면에서 `Current Paper Position` 또는 `Recent Runs` 영역을 확인합니다.

정상 결과 예시는 다음과 같습니다.

```text
Action: SHORT Entry
Order Status: OPEN
Position Status: OPEN
```

AI 결과에 따라 LONG Entry가 나올 수도 있습니다.

---

### 10.5 History 확인

History 화면으로 이동하여 자동매매 실행 이력을 확인합니다.

확인할 항목은 다음과 같습니다.

- Signal
- Action
- Order Status
- Position Status
- PnL
- Execution Summary
- System Decision

---

### 10.6 Backtest 실행

Backtest 화면에서 다음 값으로 실행합니다.

| 항목 | 테스트 값 |
|---|---|
| Symbol | BTCUSDT |
| Start Date | 2026-01-03 |
| End Date | 2026-03-30 |
| Confidence Threshold | 46 |
| Position Size | 1 |
| Max Drawdown Stop | -10 |

정상 실행 시 다음 성과 지표가 표시됩니다.

- Total Return
- CAGR
- Sharpe
- MDD
- Win Rate
- Trade Count
- Equity Curve
- Drawdown

---

## 11. 자주 발생하는 오류와 해결 방법

### 11.1 `/auth/me 401 Unauthorized`

#### 원인

로그인 token이 없거나 localStorage에 저장된 token이 만료된 경우입니다.

#### 해결 방법

1. 로그아웃 후 다시 로그인합니다.
2. 브라우저 개발자 도구에서 localStorage의 `access_token`을 확인합니다.
3. `access_token`이 없으면 로그인 로직을 확인합니다.

---

### 11.2 `/exchange/balance 404 Not Found`

#### 원인

Bybit API key가 등록되지 않은 경우입니다.

#### 해결 방법

본 프로젝트는 Paper Trading 중심으로 동작하므로, API key가 없어도 Paper Asset은 정상 표시됩니다.

해당 오류는 Exchange Balance 조회 실패이며, Paper Portfolio 기능과는 별개입니다.

---

### 11.3 `Bybit API key is not registered`

#### 원인

사용자의 거래소 API key가 DB에 등록되지 않은 경우입니다.

#### 해결 방법

실제 주문이 아닌 Paper Trading으로 검증하면 됩니다.

Run Once 실행 시 실제 주문 대신 Paper Execution이 기록됩니다.

---

### 11.4 `Too many visits. Exceeded the API Rate Limit`

#### 원인

Bybit Public API를 짧은 시간에 너무 자주 호출한 경우입니다.

#### 해결 방법

1. 페이지 새로고침을 반복하지 않습니다.
2. 차트 timeframe 변경을 너무 빠르게 반복하지 않습니다.
3. 백엔드 캐시 또는 DB 저장 구조를 활용하도록 개선할 수 있습니다.

---

### 11.5 `GEMINI_EXPLANATION_ERROR`

#### 원인

Gemini API quota 제한, 모델명 오류, 응답 지연, API key 문제로 발생할 수 있습니다.

#### 해결 방법

1. `GEMINI_API_KEY`가 `.env`에 설정되어 있는지 확인합니다.
2. Gemini quota 제한 여부를 확인합니다.
3. Gemini 호출 실패 시 시스템은 fallback 설명을 생성하므로 전체 실행은 중단되지 않습니다.

---

### 11.6 AI 서버 연결 실패

#### 원인

AI 서버가 실행 중이지 않거나 포트가 다를 경우 발생합니다.

#### 해결 방법

AI 서버를 다시 실행합니다.

```powershell
cd C:\Users\User\Desktop\Cryptova\cryptova-ai
python -m uvicorn app:app --port 8001 --reload
```

백엔드에서 AI 서버 주소가 다음과 맞는지 확인합니다.

```text
http://127.0.0.1:8001
```

---

## 12. 종료 방법

각 서버가 실행 중인 PowerShell 창에서 다음 키를 입력합니다.

```text
Ctrl + C
```

백엔드 종료 시 Scheduler도 함께 종료됩니다.

---

## 13. 실행 확인 체크리스트

최종적으로 다음 항목이 확인되면 정상 실행된 것입니다.

- [ ] MySQL 서버 실행
- [ ] 백엔드 서버 8000번 포트 실행
- [ ] AI 서버 8001번 포트 실행
- [ ] 프론트엔드 5173번 포트 실행
- [ ] 회원가입 또는 로그인 성공
- [ ] Strategy Settings 저장 성공
- [ ] Paper Asset 표시
- [ ] Run Once 실행 성공
- [ ] History 실행 이력 표시
- [ ] Backtest 결과 표시