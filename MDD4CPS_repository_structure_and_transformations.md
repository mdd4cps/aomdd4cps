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
