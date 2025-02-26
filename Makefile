# Makefile for managing AWS Lambda layers and CloudFormation stack

FUNCTIONS_DIR := functions
STACK_NAME := DynamoNextGen

LAYER_DIRS := $(wildcard lambda-layers/*)

.PHONY: build-layers clear-layers delete-stack deploy-functions re-build-layers

build-layers:
	@for dir in ./lambda-layers/*; do \
		if [ -d "$$dir" ]; then \
			echo "Processing $$dir"; \
			pip3 install \
				--platform manylinux2014_aarch64 \
				-r "$$dir/requirements.txt" \
				-t "$$dir/python/lib/python3.9/site-packages" \
				--python-version 3.9 \
				--only-binary=:all:; \
		fi; \
	done
	@echo "✅ Built all layers successfully."

clear-layers:
	@for dir in $(LAYER_DIRS); do \
		rm -rf $$dir/python; \
	done
	@echo "Cleared all Python dependencies from layers."

re-build-layers: clear-layers build-layers

delete-stack:
	@read -p "Are you sure you want to delete $(STACK_NAME)? [Y/n]: " confirm; \
	if [ "$$confirm" = "Y" ] || [ "$$confirm" = "y" ] || [ -z "$$confirm" ]; then \
		echo "Deleting CloudFormation stack $(STACK_NAME)..."; \
		aws cloudformation delete-stack --stack-name $(STACK_NAME); \
	else \
		echo "Aborted."; \
	fi

deploy-functions:
	sam build --template-file templates/functions_template.yaml
	sam deploy --template-file templates/functions_template.yaml