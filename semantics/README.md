# Semantics

This directory contains the semantic resources used to validate CPS models in the **MDD4CPS** process.  
It is organized into three subdirectories, each serving a specific role in the validation workflow.

## Structure

- **`draw.io_models/`**  
  Contains the original CIM and PIM models created with [diagrams.net](https://www.diagrams.net/), using the custom libraries developed for MDD4CPS.  
  - `*_eng.drawio` / `*_eng.xml` → Canonical reference models (correct).  
  - `*_err*.drawio` / `*_err*.xml` → Models with deliberately introduced errors (structural cases 1, 2, and 3).  
  These serve as the basis for transformations and subsequent validations.

- **`structural_validations/`**  
  Includes the **PIM DSL ontology** and **structural validation test cases**.  
  - Ontology in RDF/XML (`dsl_pim_mdd4cps.rdf`) and configuration (`*.properties`).  
  - Test datasets in Turtle (`owl_*.ttl`) introducing structural inconsistencies, validated with Protégé + HermiT reasoner.  
  Focus: logical contradictions (e.g., disjointness, multiple containment).

- **`semantic_validations/`**  
  Includes datasets, SHACL shapes, and scripts for **semantic validation**.  
  - `data_case*.ttl` → Model instances (with and without errors).  
  - `shapes_case*.ttl` → SHACL constraints for each case.  
  - `validation_command` → Example command using [pySHACL](https://github.com/RDFLib/pySHACL).  
  - `report_case.ttl` → Sample validation report.  
  Focus: completeness and pragmatic constraints (e.g., missing messaging links, top interval actions, invalid timing).

## Purpose

The resources in this directory support the **reproducible validation experiments** described in the chapter:  
- **Structural validation** with OWL (open-world reasoning).  
- **Semantic validation** with SHACL (closed-world constraints).  

Together, these artifacts demonstrate how semantic technologies can strengthen the MDD4CPS workflow by detecting inconsistencies early and preventing their propagation into later stages.

---

🔗 For more details, see the [project repository root](..).

