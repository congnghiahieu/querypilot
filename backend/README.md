# QueryPilot

## Dựng môi trường dev tạm thời

- Tạo file `.env` với nội dung tối thiểu

```bash
STAGE=dev
ENV=local
DEEPSEEK_API_KEY=<api_key>
SECRET_KEY=KtKKEojaAvRWStFaEXtIg6fZ3lqQui2P
CLIENT_URL=http://localhost:3000
DATABASE_URL=postgresql+psycopg2://querypilot:querypilot@localhost:5432/querypilot
```

- Chạy service `db` với `postgres:15` như trong file `docker-compose.dev.yml`

```

```

- Cài dependencies và chạy

```bash
uv sync # nhớ tải uv
source ./.venv/bin/activate
make dev # Port 8080
```

- Sang folder `frontend` chạy:

```bash
npm install
npm run dev # Port 3000
```

## Requirements

- Python >= 3.10
- Backend project use Makefile so need `make`
- Backend use [uv](https://docs.astral.sh/uv/) package manager. Install via `pipx install uv` or `pip install uv`. Please use `uv` instead of `pip`

- Some `uv` usage example:

```bash
uv add numpy # add a new dependency, equals to `pip install`
uv add ruff --dev # add a new dev dependency, equals to `pip install`
uv venv # create new venv, equals to `python -m venv .venv`
uv sync # dowload all dependencies listed in pyproject.toml, equals to `pip install -r requirements`
```

## Set up environment

- Run `make generate_dot_env` if file `.env` doesn't exists, see below example

```bash
# .env

ENV=local # local | aws
STAGE=dev # dev | prod
DEEPSEEK_API_KEY=<real_api_key>
SECRET_KEY=<real_secret_string>
CLIENT_URL=http://localhost:3000 # Frontend address for CORS settings
DATABASE_URL=postgresql+psycopg2://querypilot:querypilot@localhost:5432/querypilot # Recommend run postgreSQL locally using `docker-compose.yml`, run before backend

# AWS S3 Configuration (only required when ENV=aws)
AWS_ACCESS_KEY_ID=<your_aws_access_key>
AWS_SECRET_ACCESS_KEY=<your_aws_secret_key>
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=<your_s3_bucket_name>
AWS_S3_BUCKET_URL=<optional_custom_s3_url>

# AWS Athena Configuration (only required when ENV=aws)
AWS_ATHENA_DATABASE=<your_athena_database>
AWS_ATHENA_WORKGROUP=primary
AWS_ATHENA_OUTPUT_LOCATION=s3://<your-athena-results-bucket>/query-results/
AWS_ATHENA_TIMEOUT=300

# AWS Cognito Configuration (only required when ENV=aws)
AWS_COGNITO_USER_POOL_ID=<your_cognito_user_pool_id>
AWS_COGNITO_CLIENT_ID=<your_cognito_client_id>
AWS_COGNITO_CLIENT_SECRET=<your_cognito_client_secret>
AWS_COGNITO_REGION=<your_cognito_region>
AWS_COGNITO_DOMAIN=<your_cognito_domain>

# AWS IAM Configuration (only required when ENV=aws)
AWS_IAM_ROLE_PREFIX=QueryPilot-User-
AWS_IAM_POLICY_ARN_BASE=arn:aws:iam::<account-id>:policy/QueryPilot-Base-Policy

# AWS RDS Configuration (only required when ENV=aws)
AWS_RDS_HOST=<your_rds_host>
AWS_RDS_PORT=5432
AWS_RDS_DB_NAME=<your_rds_database>
AWS_RDS_USERNAME=<your_rds_username>
AWS_RDS_PASSWORD=<your_rds_password>
```

## Install dependencies

- Create virtual env, install dependencies and activate:

```bash
uv sync
source ./.venv/bin/activate
```

- Run backend:

```bash
make dev # for dev environment
make run # for prod environment
```

## AWS Cognito Setup

When using AWS environment (ENV=aws), you need to set up AWS Cognito:

1. **Create a Cognito User Pool**:

   - Go to AWS Cognito Console
   - Create a new User Pool
   - Configure sign-in options (username, email)
   - Set password policy
   - Enable email verification
   - Note down the User Pool ID

2. **Create App Client**:

   - In your User Pool, create an App Client
   - Enable "Generate client secret"
   - Configure app client settings
   - Note down Client ID and Client Secret

3. **Configure Domain** (Optional):

   - Set up a custom domain for hosted UI
   - Note down the domain name

4. **IAM Permissions**:
   - Ensure your AWS credentials have permissions for:
     - Cognito User Pool operations
     - IAM role creation and management
     - S3 and Athena access
     - Lake Formation permissions

## Authentication Flow

### Local Environment (ENV=local)

- Uses JWT tokens with local password hashing
- User data stored in local PostgreSQL database

### AWS Environment (ENV=aws)

- Uses AWS Cognito for authentication
- Automatically creates IAM roles for new users
- Integrates with Lake Formation for row-level security
- User permissions managed through IAM policies

## API Endpoints

### Authentication (AWS Cognito)

- `POST /auth/register` - Register new user
- `POST /auth/confirm-signup` - Confirm user registration
- `POST /auth/login` - Login user
- `POST /auth/logout` - Logout user
- `POST /auth/refresh` - Refresh access token
- `POST /auth/forgot-password` - Initiate password reset
- `POST /auth/reset-password` - Reset password with code

### User Management

- `GET /user/settings` - Get user settings
- `POST /user/settings` - Update user settings (auto-updates IAM permissions)
- `GET /user/iam-role-info` - Get IAM role information (AWS only)
