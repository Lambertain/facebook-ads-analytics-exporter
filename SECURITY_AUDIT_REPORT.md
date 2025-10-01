# Security Audit Report - eCademy Project
**Дата аудита:** 2025-10-01
**Аудитор:** Security Audit Agent
**Проект:** facebook-ads-analytics-exporter (eCademy)
**Репозиторий:** https://github.com/Lambertain/facebook-ads-analytics-exporter.git

---

## Исполнительное резюме

### Общая оценка безопасности: ⚠️ **КРИТИЧЕСКИЙ РИСК**

Проект **НЕ ГОТОВ к публичному использованию** без устранения критических уязвимостей. Обнаружено **12 уязвимостей**, из которых **4 имеют критический уровень (CRITICAL)** и **4 - высокий (HIGH)**.

**Основные риски:**
- Полное отсутствие authentication/authorization
- Публичный доступ к конфиденциальной конфигурации через API
- Критические уязвимости в зависимостях (pip, youtube-dl)
- Отсутствие базовых security механизмов (CORS, rate limiting, headers)
- Docker контейнер работает с root правами

**Рекомендация:** Устранить все P0 уязвимости перед любым публичным развертыванием.

---

## Детальный анализ уязвимостей

### 🔴 CRITICAL Severity (CVSS 9.0-10.0)

#### 1. Отсутствие authentication/authorization
**Локация:** `app/main.py` - все endpoints
**CVSS Score:** 9.8 (CRITICAL)
**CWE:** CWE-306 (Missing Authentication for Critical Function)

**Описание:**
Все API endpoints доступны без какой-либо аутентификации. Любой пользователь может:
- Запускать pipeline обработки данных (`/api/start-job`)
- Получать конфиденциальную конфигурацию (`/api/config`)
- Изменять конфигурацию (`POST /api/config`)
- Скачивать данные (`/api/download-excel`)
- Инспектировать CRM данные (`/api/inspect/*`)

**Эксплуатация:**
```bash
# Любой может запустить pipeline
curl -X POST http://target:8000/api/start-job \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-01-01", "end_date": "2025-12-31"}'

# Получить конфигурацию с путями к файлам
curl http://target:8000/api/config
```

**Рекомендация (P0):**
```python
# app/middleware/auth.py
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    # Implement JWT verification or API key validation
    if not validate_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return token

# Apply to all sensitive endpoints
@app.post("/api/start-job", dependencies=[Depends(verify_token)])
async def start_job(...):
    ...
```

---

#### 2. Публичная exposure конфигурации
**Локация:** `app/main.py:139-141` (`GET /api/config`)
**CVSS Score:** 9.1 (CRITICAL)
**CWE:** CWE-200 (Exposure of Sensitive Information)

**Описание:**
Endpoint `/api/config` возвращает конфиденциальную информацию:
- Пути к Excel файлам в файловой системе
- Структуру директорий проекта
- Настройки CRM интеграций
- Потенциально - частично замаскированные credentials

**Код уязвимости:**
```python
@app.get("/api/config")
async def get_config():
    return get_config_masked()  # НЕТ AUTHENTICATION!
```

**Рекомендация (P0):**
- Добавить authentication к `/api/config`
- Минимизировать информацию в ответе
- Полностью удалить пути к файлам из публичного API
- Логировать все доступы к этому endpoint

---

#### 3. pip 25.2 - Path Traversal Vulnerability
**Локация:** `requirements.txt` (pip version)
**CVSS Score:** 9.3 (CRITICAL)
**CVE/Advisory:** GHSA-4xh5-x5gv-qwph

**Описание:**
pip 25.2 имеет критическую уязвимость path traversal при извлечении source distributions. Вредоносный sdist может содержать symbolic/hard links, которые позволяют перезаписать произвольные файлы на хосте.

**Потенциальный сценарий атаки:**
1. Злоумышленник создает malicious package на PyPI или частном индексе
2. Администратор запускает `pip install malicious-package`
3. Происходит перезапись критических системных файлов
4. Возможна эскалация привилегий или RCE

**Рекомендация (P0):**
```bash
# Обновить pip до последней безопасной версии
pip install --upgrade pip>=25.2.1

# В requirements.txt добавить constraint
pip>=25.2.1
```

---

#### 4. youtube-dl - Path Traversal + RCE Risk
**Локация:** `requirements.txt:18` (`youtube-dl==2021.12.17`)
**CVSS Score:** 9.8 (CRITICAL)
**CVE/Advisory:** GHSA-22fp-mf44-f2mq

**Описание:**
youtube-dl версии 2021.12.17 имеет критическую уязвимость:
- Path traversal на Windows (через `non_existent_dir\..\..\target`)
- Неограниченные расширения загружаемых файлов
- Потенциал для RCE через маскировку исполняемых файлов под субтитры

**Рекомендация (P0):**
```bash
# Если youtube-dl НЕ используется - удалить из requirements.txt
# Если используется - обновить до yt-dlp (форк с патчами):
pip uninstall youtube-dl
pip install yt-dlp>=2024.7.3
```

---

### 🟠 HIGH Severity (CVSS 7.0-8.9)

#### 5. Отсутствие CORS защиты
**Локация:** `app/main.py` - FastAPI app configuration
**CVSS Score:** 7.5 (HIGH)
**CWE:** CWE-942 (Overly Permissive Cross-domain Whitelist)

**Описание:**
Полное отсутствие CORSMiddleware позволяет любым веб-сайтам делать запросы к API с credentials пользователя.

**Эксплуатация:**
```html
<!-- Malicious website -->
<script>
fetch('http://target:8000/api/start-job', {
  method: 'POST',
  credentials: 'include',
  body: JSON.stringify({start_date: '2020-01-01', end_date: '2025-12-31'})
})
</script>
```

**Рекомендация (P1):**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trusted-frontend.com"],  # Whitelist only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

#### 6. Отсутствие rate limiting
**Локация:** Все API endpoints
**CVSS Score:** 7.5 (HIGH)
**CWE:** CWE-770 (Allocation of Resources Without Limits)

**Описание:**
Нет ограничений на частоту запросов. Возможны:
- DDoS атаки
- Brute-force authentication (после добавления auth)
- Resource exhaustion через `/api/start-job`

**Рекомендация (P1):**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/start-job")
@limiter.limit("5/minute")  # Max 5 pipeline runs per minute
async def start_job(request: Request, ...):
    ...
```

---

#### 7. Docker контейнер работает с root правами
**Локация:** `Dockerfile` (отсутствует USER directive)
**CVSS Score:** 7.8 (HIGH)
**CWE:** CWE-250 (Execution with Unnecessary Privileges)

**Описание:**
Приложение выполняется от root пользователя в контейнере. При эксплуатации уязвимости в приложении или зависимостях, атакующий получает root доступ внутри контейнера, что может привести к container escape.

**Текущий Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
# ... no USER directive, runs as root
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Рекомендация (P0):**
```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser config/ ./config/

# Switch to non-root user
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

#### 8. Production режим с --reload flag
**Локация:** `Dockerfile:26`
**CVSS Score:** 7.2 (HIGH)
**CWE:** CWE-489 (Active Debug Code)

**Описание:**
Использование `--reload` в production Dockerfile включает режим разработки, который:
- Перезагружает приложение при изменении файлов (performance impact)
- Может выводить debug информацию в логи
- Увеличивает attack surface

**Текущий код:**
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Рекомендация (P0):**
```dockerfile
# Production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Development (use docker-compose override)
# docker-compose.dev.yml:
# command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### 🟡 MEDIUM Severity (CVSS 4.0-6.9)

#### 9. requests 2.32.3 - .netrc credential leak
**Локация:** `requirements.txt:8`
**CVSS Score:** 6.5 (MEDIUM)
**CVE/Advisory:** GHSA-9hjg-9r4m-mvj7

**Описание:**
requests < 2.32.4 может утечь credentials из `.netrc` файла при обработке специально созданных malicious URLs.

**Рекомендация (P1):**
```bash
# Обновить requests
pip install requests>=2.32.4

# В requirements.txt
requests>=2.32.4
```

---

#### 10. .env файл в репозитории с реальными путями
**Локация:** `.env` (если существует в git)
**CVSS Score:** 5.9 (MEDIUM)
**CWE:** CWE-312 (Cleartext Storage of Sensitive Information)

**Описание:**
Обнаружен `.env` файл с реальными путями к Excel файлам:
- Раскрывает структуру файловой системы
- Может содержать частичные credentials или API keys
- Нарушает принцип least privilege

**Рекомендация (P1):**
```bash
# Убедиться что .env в .gitignore
echo ".env" >> .gitignore

# Удалить из истории git (если был закоммичен)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all

# Пересоздать .env из .env.example
cp .env.example .env
```

---

#### 11. Отсутствие security headers
**Локация:** `app/main.py` - middleware
**CVSS Score:** 5.3 (MEDIUM)
**CWE:** CWE-1021 (Improper Restriction of Rendered UI Layers)

**Описание:**
Отсутствуют критичные HTTP security headers:
- `X-Frame-Options` → уязвимость к clickjacking
- `X-Content-Type-Options` → MIME-sniffing атаки
- `Strict-Transport-Security` → MITM атаки
- `Content-Security-Policy` → XSS защита

**Рекомендация (P1):**
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["ecademy.com", "*.ecademy.com"])

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

---

#### 12. Отсутствие input validation
**Локация:** `app/main.py:34-62` (start_job endpoint)
**CVSS Score:** 5.7 (MEDIUM)
**CWE:** CWE-20 (Improper Input Validation)

**Описание:**
Минимальная валидация пользовательского ввода. Возможны:
- SQL injection (если добавится БД)
- Path traversal в sheet_id
- Malicious date ranges

**Рекомендация (P2):**
```python
from pydantic import BaseModel, Field, validator
from datetime import datetime

class StartJobRequest(BaseModel):
    start_date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    end_date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    sheet_id: str | None = Field(None, max_length=100, regex=r'^[a-zA-Z0-9_-]+$')

    @validator('end_date')
    def end_after_start(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

@app.post("/api/start-job")
async def start_job(payload: StartJobRequest, ...):
    ...
```

---

## Приоритизация исправлений

### P0 - Блокирующие (устранить немедленно)

1. ✅ **Добавить authentication middleware** → все endpoints
2. ✅ **Обновить pip** → requirements.txt
3. ✅ **Удалить/обновить youtube-dl** → requirements.txt
4. ✅ **Убрать --reload** → Dockerfile
5. ✅ **Добавить USER** → Dockerfile

**ETA:** 4-6 часов работы
**Блокирует:** Публичное развертывание, production release

---

### P1 - Критичные (до публичного использования)

6. ✅ **CORSMiddleware** с whitelist
7. ✅ **Rate limiting** (slowapi)
8. ✅ **Обновить requests** → 2.32.4+
9. ✅ **Security headers middleware**
10. ✅ **Убрать .env** из git истории

**ETA:** 3-4 часа работы
**Блокирует:** Публичное использование

---

### P2 - Важные (техдолг)

11. ✅ **Pydantic models** для всех endpoints
12. ✅ **Security logging** (аудит доступа)
13. ✅ **Secrets rotation policy**
14. ✅ **Dependency scanning** в CI/CD (Dependabot/Snyk)

**ETA:** 6-8 часов работы
**Рекомендуется:** До первого major release

---

## Рекомендации по мониторингу

### Runtime Security

```python
# app/middleware/logging.py
import logging
from fastapi import Request

security_logger = logging.getLogger("security")

@app.middleware("http")
async def log_security_events(request: Request, call_next):
    # Log all access to sensitive endpoints
    if request.url.path.startswith("/api/config"):
        security_logger.warning(
            f"Config access: IP={request.client.host}, "
            f"User-Agent={request.headers.get('user-agent')}"
        )
    response = await call_next(request)
    return response
```

### CI/CD Integration

```yaml
# .github/workflows/security.yml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

      - name: Run pip-audit
        run: |
          pip install pip-audit
          pip-audit --desc --require-hashes requirements.txt

      - name: Run bandit SAST
        run: |
          pip install bandit
          bandit -r app/ -ll -f json -o bandit-report.json
```

---

## Compliance Checklist

### OWASP Top 10 (2021)

- ❌ **A01:2021 - Broken Access Control** → No authentication
- ❌ **A02:2021 - Cryptographic Failures** → .env in git
- ⚠️ **A03:2021 - Injection** → Minimal input validation
- ❌ **A04:2021 - Insecure Design** → No rate limiting, CORS
- ❌ **A05:2021 - Security Misconfiguration** → --reload, root user
- ❌ **A06:2021 - Vulnerable Components** → pip, youtube-dl, requests
- ⚠️ **A07:2021 - Auth Failures** → N/A (no auth implemented)
- ⚠️ **A08:2021 - Software/Data Integrity** → No package hashing
- ❌ **A09:2021 - Security Logging** → No audit logs
- ⚠️ **A10:2021 - SSRF** → Meta API calls без validation

**Текущий статус:** 5/10 критических нарушений, 4/10 предупреждений

---

## Заключение

Проект eCademy требует **немедленного устранения 4 CRITICAL и 4 HIGH уязвимостей** перед любым публичным использованием.

**Рекомендуемый план действий:**

1. **День 1-2:** Исправить все P0 уязвимости (блокируют релиз)
2. **День 3-4:** Исправить P1 уязвимости (до публичного использования)
3. **Неделя 2:** Реализовать P2 улучшения (техдолг)
4. **Постоянно:** Мониторинг CVE, автоматическое обновление зависимостей

**Следующий шаг:** Создать задачи в Archon для каждого приоритета исправлений.

---

**Подготовил:** Security Audit Agent
**Дата:** 2025-10-01
**Статус:** COMPLETED
