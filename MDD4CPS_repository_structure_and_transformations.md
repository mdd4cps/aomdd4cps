# MDD4CPS Repository Structure and Transformations

## Purpose of this document

This document describes how the transformations of the MDD4CPS process are implemented within the repository.

A conceptual description of the complete MDD4CPS workflow, including its modelling phases, artefacts, transformations, and supporting tools, is available in the document [MDD4CPS_process_overview.md](MDD4CPS_process_overview.md).

The purpose of the present document is to identify the repository artefacts involved in each transformation stage and explain their role within the implementation.

## Relationship with the MDD4CPS Process

The MDD4CPS process is organised around four main phases:

```text
CIM → PIM → PSM → Code
```

Within the repository, these transformations are implemented through a combination of:

- JSON rule definitions used to interact with the designer;
- XSLT model transformation scripts;
- Python-based code generation scripts;
- technology-specific code generation mechanisms.

The following sections describe how these artefacts are organised and how they participate in each transformation stage.

## Repository Structure

The repository artefacts directly involved in the transformation workflow are organised as follows:

```text
src/
├── frontend/
│   └── static/
│       └── input/
│           ├── json/
│           │   ├── CIM-PIM-Rules.json
│           │   └── PIM-PSM-Rules.json
│           └── xsl/
│               ├── CIM-PIM.xsl
│               ├── CIM-PIM-Aux.xsl
│               └── PIM-PSM.xsl
│
└── backend/
    └── psm_to_code-arduinomkr1010.py
```

The `json/` directory contains rule definitions used to collect additional information from the designer during the transformation process.

The `xsl/` directory contains the XSLT transformations that implement the CIM-to-PIM and PIM-to-PSM model transformations.

The backend script `psm_to_code-arduinomkr1010.py` implements the generation of Arduino MKR1010 source code from the PSM representation produced by the previous transformation stages.


## CIM-to-PIM Transformation

### Purpose

The CIM-to-PIM transformation converts CIM models into the intermediate DSL used by MDD4CPS. This stage preserves relevant modelling information and incorporates additional design decisions required to obtain a complete PIM representation.

Some information cannot be inferred directly from the CIM model and therefore must be provided by the designer during the transformation process.

### Repository Artefacts

| Artefact | Role |
|-----------|--------|
| `CIM-PIM-Rules.json` | Defines the information requested from the designer during the transformation process. |
| `CIM-PIM.xsl` | Main XSLT transformation implementing the CIM-to-PIM mapping. |
| `CIM-PIM-Aux.xsl` | Auxiliary templates and functions used by the main transformation. |

### Implementation Notes

During this stage, additional information may be requested from the designer through the rule definitions contained in `CIM-PIM-Rules.json`. Once collected, the CIM model is processed by the XSLT transformations to generate the corresponding PIM representation.

The transformation logic is implemented in the XSLT files located under:

```text
src/frontend/static/input/xsl/
```

while the interaction rules are located under:

```text
src/frontend/static/input/json/
```

---

## PIM-to-PSM Transformation

### Purpose

The PIM-to-PSM transformation restructures and enriches the intermediate DSL representation in preparation for automatic source-code generation.

This stage organises the model according to the requirements of the target implementation technology and produces a representation intended to support subsequent code generation activities.

### Repository Artefacts

| Artefact | Role |
|-----------|--------|
| `PIM-PSM-Rules.json` | Defines the information requested from the designer during the transformation process. |
| `PIM-PSM.xsl` | XSLT transformation that restructures and preprocesses the PIM model into a code-generation-oriented representation. |

### Implementation Notes

As in the previous stage, additional information may be requested from the designer through the rule definitions contained in `PIM-PSM-Rules.json`.

The transformation logic is implemented in:

```text
src/frontend/static/input/xsl/PIM-PSM.xsl
```

while the interaction rules are located in:

```text
src/frontend/static/input/json/
```

Unlike the CIM-to-PIM stage, the resulting representation is primarily intended to support the subsequent source-code generation process rather than to serve as a standalone modelling notation.

---

## PSM-to-Code Transformation

### Purpose

The PSM-to-Code transformation generates deployable source code from the PSM representation.

In the current proof-of-concept implementation, the target platform is Arduino MKR1010. This stage automates the generation of technology-specific infrastructure and repetitive implementation elements while preserving extension points for manual customisation.

### Repository Artefacts

| Artefact | Role |
|-----------|--------|
| `psm_to_code-arduinomkr1010.py` | Generates Arduino MKR1010 source code from the PSM representation. |

### Implementation Notes

The code generator processes the PSM representation produced by the previous transformation stages and systematically generates the source files required for deployment on Arduino MKR1010 devices.

The generator is implemented in:

```text
src/backend/psm_to_code-arduinomkr1010.py
```

The generated code includes technology-specific infrastructure such as communication support, task structures, data definitions, configuration elements, and other boilerplate code required by the target platform.

---

## Summary of Transformation Artefacts

| Transformation | Artefacts | Technology |
|----------------|-----------|------------|
| CIM-to-PIM | `CIM-PIM-Rules.json`, `CIM-PIM.xsl`, `CIM-PIM-Aux.xsl` | JSON, XSLT |
| PIM-to-PSM | `PIM-PSM-Rules.json`, `PIM-PSM.xsl` | JSON, XSLT |
| PSM-to-Code | `psm_to_code-arduinomkr1010.py` | Python |
