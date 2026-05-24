.PHONY: start docker-build package deploy deploy-observability

APP_NAME ?= ddia-ch02
IMAGE_TAG ?= latest
IMAGE ?= $(APP_NAME):$(IMAGE_TAG)
PORT ?= 8000
KUBECTL ?= kubectl
HELM ?= helm
NAMESPACE ?= cobrakai
KPS_RELEASE ?= kube-prometheus-stack

start:
	uv run main.py

docker-build:
	docker build --build-arg PORT=$(PORT) -t $(IMAGE) .

package: docker-build

deploy-observability:
	$(KUBECTL) apply -f k8s/namespace.yaml
	$(HELM) repo add prometheus-community https://prometheus-community.github.io/helm-charts
	$(HELM) repo update
	$(HELM) upgrade --install $(KPS_RELEASE) prometheus-community/kube-prometheus-stack --namespace $(NAMESPACE) --values k8s/helm/kube-prometheus-stack-values.yaml --set grafana.adminPassword=admin --set prometheus.prometheusSpec.scrapeInterval=5s
	$(KUBECTL) apply -f k8s/jaeger.yaml

deploy:
	$(MAKE) deploy-observability
	$(KUBECTL) apply -f k8s/deployment.yaml
	$(KUBECTL) apply -f k8s/service.yaml
