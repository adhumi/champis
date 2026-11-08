# Référentiel Champis (adhumi/champis). `make` ou `make help` liste les cibles.
# Le pipeline et l'API sont dans adhumi/champis-api, le site dans adhumi/champis-web : ils ont ce
# dépôt en sous-module champis/ (découpage des dépôts, spec › Produit › Étape C, lot C7).

.DEFAULT_GOAL := help

.PHONY: help
help: ## Cette aide
	@awk 'BEGIN { FS = ":.*## " } /^[a-zA-Z_-]+:.*## / { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

.PHONY: species
species: ## Fichiers espèces et table BD Forêt (species/validate.py)
	python3 species/validate.py

.PHONY: shared
shared: ## JSON lisibles, index des textes du Guide, vecteurs de parité, illustrations à jour (scripts/check_shared.py, draw_illustrations.py --check)
	python3 scripts/check_shared.py
	python3 scripts/draw_illustrations.py --check

.PHONY: illustrations
illustrations: ## Redessine shared/illustrations/ (scripts/draw_illustrations.py)
	python3 scripts/draw_illustrations.py

.PHONY: check
check: species shared ## Exactement la CI
