#! /bin/env bash

cd ../backend
source ./.venv/bin/activate
python -c "import main; import json; print(json.dumps(main.app.openapi()))" > ../frontend/openapi.json
cd ../frontend
npx openapi-ts
rm openapi.json
