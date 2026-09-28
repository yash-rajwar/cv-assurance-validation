# CV Assurance Validation Project

## Purpose

This repository is an independent validation environment for:

Trustworthy Computer Vision Integrity Assurance System.

This repository does NOT contain the production application.

Its purpose is:

- dataset preparation
- attack simulation
- evaluation
- validation evidence generation


## Current Objective

Build:

CV-Assurance-Dataset-v1


## Dataset Strategy

Primary dataset:

COCO 2017 Object Detection Dataset


Initial scope:

1000 images


Split:

800 development

200 frozen holdout


## Important Rules

1. Never modify holdout data after creation.
2. Never generate fake metrics.
3. Never claim security without evidence.
4. Every generated artifact must be reproducible.
5. All scripts must be saved.
6. All random operations must use fixed seeds.
7. Maintain complete documentation.
