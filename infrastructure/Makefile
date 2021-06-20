environment := dev
project := $(shell gcloud config get-value project)
auto-approve := false
debug := false

ENVIRONMENTS := $(shell find ./vars -type f -name '*.tfvars' | cut -c 8- | rev | cut -c 8- | rev | paste -sd " " - | xargs)

define GET_TFVAR
$(shell sed -n 's/$(1) *= *"\(.*\)"$$/\1/p' vars/$(environment).tfvars)
endef

.PHONY: help
help:
	@echo "Usage: make <plan|apply|destroy> environment=<string> project=<string> auto-approve=<true|false> debug=<true|false>"
	@echo " "
	@echo "Options:"
	@echo "  environment      The terraform input variables file name (Supported values: [$(ENVIRONMENTS)])."
	@echo "  project          Use a specific project to manage resource in (Default: '$(project)')."
	@echo "  auto-approve     Skip interactive approval of plan before applying (Default: '$(auto-approve)')."
	@echo "  debug            Enable debugging mode (Default '$(debug)')."
	@echo " "

configure:
    ifeq ($(filter $(environment),$(ENVIRONMENTS)),)
		$(error Environment '$(environment)' is not supported)
    endif
    TF_ENV_VARS := TF_DATA_DIR="$(CURDIR)/.terraform/$(environment)/"
    ifeq ($(debug),true)
        TF_ENV_VARS := $(TF_ENV_VARS) TF_LOG=DEBUG
    endif
    TF_OPTIONS := $(TF_OPTIONS) -var="environment=$(environment)"
    TF_OPTIONS := $(TF_OPTIONS) -var="project=$(project)"
    TF_INIT_CONF := $(TF_INIT_CONF) -backend-config="bucket=$(call GET_TFVAR,'backend_bucket')"
    TF_INIT_CONF := $(TF_INIT_CONF) -backend-config="prefix=state/$(environment)/$(call GET_TFVAR,'name')"
    TF_INIT_CONF := $(TF_INIT_CONF) -var-file="$(CURDIR)/vars/$(environment).tfvars"
    TF_RUN_CONF := $(TF_RUN_CONF) -var-file="$(CURDIR)/vars/$(environment).tfvars"
    ifeq ($(auto-approve),true)
        TF_RUN_CONF := $(TF_RUN_CONF) -auto-approve
    endif

.PHONY: init
init: configure
	$(TF_ENV_VARS) terraform init $(TF_OPTIONS) $(TF_INIT_CONF)

.PHONY: plan
plan: init
	$(TF_ENV_VARS) terraform plan $(TF_OPTIONS) $(TF_RUN_CONF)

.PHONY: apply
apply: init
	$(TF_ENV_VARS) terraform apply $(TF_OPTIONS) $(TF_RUN_CONF)

.PHONY: destroy
destroy: init
	$(TF_ENV_VARS) terraform destroy $(TF_OPTIONS) $(TF_RUN_CONF)
