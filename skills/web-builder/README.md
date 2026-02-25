# Web Builder Skill Pack

This pack defines a full pipeline for planning, building, validating, securing,
and deploying a production-grade web application.

```text
web-stack-planner
  └─> web-ux-architect
        └─> web-frontend-designer
              └─> web-backend-builder
                    └─> web-auth-integrator
                          └─> web-database-validator
                                └─> web-api-tester
                                      └─> web-frontend-tester
                                            └─> web-security-auditor
                                                  └─> web-deploy-launcher
```

## Pipeline Inputs/Outputs

- `web-stack-planner` outputs `project-config.json`
- `web-ux-architect` outputs `sitemap.md`, `wireframes.md`, `ux-report.json`
- `web-frontend-designer` outputs frontend scaffold plan and `frontend-report.json`
- `web-backend-builder` outputs backend scaffold plan, `openapi.yaml`, `backend-report.json`
- `web-auth-integrator` outputs `auth-report.json`
- `web-database-validator` outputs `db-validation-report.json`
- `web-api-tester` outputs `api-test-report.json`
- `web-frontend-tester` outputs `frontend-test-report.json`
- `web-security-auditor` outputs `security-report.json`
- `web-deploy-launcher` outputs deploy config files, `DEPLOYMENT.md`, `deploy-report.json`

## Reference Catalog

- `references/tools.md`
