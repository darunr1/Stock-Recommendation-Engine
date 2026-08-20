.PHONY: bootstrap dev down format lint typecheck test-unit test-integration test-e2e test build seed smoke email-preview lighthouse deploy-check post-deploy-smoke

bootstrap:
	pnpm bootstrap
dev:
	pnpm dev
down:
	docker compose down
format:
	pnpm format
lint:
	pnpm lint
typecheck:
	pnpm typecheck
test-unit:
	pnpm test:unit
test-integration:
	pnpm test:integration
test-e2e:
	pnpm test:e2e
test:
	pnpm test
build:
	pnpm build
seed:
	pnpm seed
smoke:
	pnpm smoke
email-preview:
	pnpm email-preview
lighthouse:
	pnpm lighthouse
deploy-check:
	pnpm deploy-check
post-deploy-smoke:
	pnpm post-deploy-smoke -- $(BASE_URL)
