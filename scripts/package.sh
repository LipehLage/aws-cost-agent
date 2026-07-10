#!/usr/bin/env bash
# Empacota o código + dependências em build/lambda.zip para o Terraform.
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf build
mkdir -p build/staging

pip install -r requirements.txt --target build/staging --quiet
cp -r cost_agent lambda_handler.py build/staging/

cd build/staging
zip -rq ../lambda.zip .
cd ../..
echo "Pacote gerado em build/lambda.zip"
