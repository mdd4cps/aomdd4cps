# Semantics

This directory contains the semantic resources used to validate MDD4CPS models.  
It is organized into three subdirectories, each serving a specific role in the validation workflow.

## Structure

- **`draw.io_models/`**  
  Contains CIM and PIM models created with [diagrams.net](https://www.diagrams.net/) using the custom libraries developed for MDD4CPS.
  - `*_eng.drawio` / `*_eng.xml` → Reference models.
  - `*_err*.drawio` / `*_err*.xml` → Models with deliberately introduced inconsistencies used as validation cases.

  These models serve as the basis for transformations and validation activities.

- **`structural_validations/`**  
  Includes the **PIM DSL ontology** and datasets used for **structural validation**.
  - Ontology in RDF/XML (`dsl_pim_mdd4cps.rdf`) and configuration (`*.properties`).
  - Test datasets in Turtle (`owl_*.ttl`) containing structural inconsistencies, validated with Protégé and the HermiT reasoner.

  Focus: logical contradictions such as multiple refinement operators, invalid containment relationships, and violations of class disjointness.

- **`semantic_validations/`**  
  Includes datasets, SHACL shapes, and scripts used for **semantic validation**.
  - `data_case*.ttl` → Model instances (with and without errors).
  - `shapes_case*.ttl` → SHACL constraints for each validation case.
  - `validation_command` → Example command using [pySHACL](https://github.com/RDFLib/pySHACL).
  - `report_case.ttl` → Sample validation report.

  Focus: completeness and pragmatic constraints such as missing messaging structures, missing top interval actions, invalid timing definitions, and incomplete operation-mode specifications.

## Purpose

This directory contains the semantic resources used to validate the structural and semantic consistency of MDD4CPS models.

The included validation cases cover:

- **Structural validation with OWL and HermiT**, including:
  - actions associated with multiple refinement operators;
  - internal elements assigned to multiple cyber-physical components;
  - resources simultaneously typed as hardware and software resources.

- **Semantic validation with SHACL and pySHACL**, including:
  - missing messaging structures between components;
  - absence of a top `OnIntervalAction` within a component;
  - missing operation mode descriptions when operation modes are enabled;
  - invalid `interval_in_milliseconds` values;
  - incomplete messaging structures, payload definitions, and conditional communication links.

Together, these artifacts illustrate how OWL- and SHACL-based validation can help detect modelling inconsistencies and completeness violations before model transformations and code generation take place.
