#!/usr/bin/env bash
set -euo pipefail

require() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required env var: ${name}" >&2
    exit 1
  fi
}

require DOCR_NAME
require DO_API_TOKEN

IMAGE_NAME="${IMAGE_NAME:-letraz-server}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DOCTL_VERSION="${DOCTL_VERSION:-1.146.0}"

REGISTRY="registry.digitalocean.com/${DOCR_NAME}"
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "[ci] Installing doctl v${DOCTL_VERSION}"
curl -fsSL "https://github.com/digitalocean/doctl/releases/download/v${DOCTL_VERSION}/doctl-${DOCTL_VERSION}-linux-amd64.tar.gz" -o /tmp/doctl.tgz
tar -C /tmp -xzf /tmp/doctl.tgz
sudo mv /tmp/doctl /usr/local/bin/doctl

echo "[ci] Authenticating doctl"
doctl auth init -t "${DO_API_TOKEN}"

echo "[ci] Logging in to DO Container Registry"
doctl registry login --expiry-seconds 600

echo "[ci] Building amd64 base image with Chromium deps"
docker build --platform linux/amd64 -f Dockerfile.encore-base -t "${IMAGE_NAME}-encore-base:amd64" .

echo "[ci] Building Encore image (amd64): ${FULL_IMAGE}"
encore build docker "${FULL_IMAGE}" \
  --config infra-config.json \
  --arch amd64 \
  --base "${IMAGE_NAME}-encore-base:amd64" \
  -v

echo "[ci] Pushing image: ${FULL_IMAGE}"
docker push "${FULL_IMAGE}"

echo "[ci] Done"

