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

### Principal Construct Mappings

| CIM Construct | PIM Construct / Representation |
|--------------|--------------------------------|
| Actor / Agent / Role marked as CPC | `cps_component` |
| Goal | `operational_goal` |
| Task | `action` |
| Resource | `hw_resource` or `sw_resource` |
| Needed-by relationship | `relation_from_to` |
| Refinement relationship | `relation_from_to` plus refinement operator |
| Dependency | `listener_thread`, `comm_thread`, `comm_relation`, `mail_symbol` |
| Softgoal | Qualification and contribution metadata attached to generated elements |

### Implementation Notes

The CIM-to-PIM transformation is implemented mainly in:

```text
src/frontend/static/input/xsl/CIM-PIM.xsl
```

with an auxiliary post-processing step in:

```text
src/frontend/static/input/xsl/CIM-PIM-Aux.xsl
```

The auxiliary XSLT removes duplicated objects generated during the transformation, preserving a valid draw.io model.

---

## PIM-to-PSM Transformation

### Purpose

The PIM-to-PSM stage prepares the enriched PIM model for source-code generation. Rather than defining a completely new modelling notation, this transformation restructures the PIM elements into an XML representation that can be processed directly by the code generator.

### PIM Elements Processed

| PIM Element | PSM Representation |
|------------|--------------------|
| `cps_component` | `cpc` |
| `sw_resource` | `sw_resource` |
| `hw_resource` | `hw_resource` |
| `action` | `function` |
| `operational_goal` | `thread` |
| `relation_from_to` | `relation` |
| `comm_thread` | `commThread` |
| `listener_thread` | `listenerThread` |
| `comm_relation` | `commRelation` |

### Implementation Notes

The transformation is implemented in:

```text
src/frontend/static/input/xsl/PIM-PSM.xsl
```

This XSLT groups the model by `cps_component` and creates one `cpc` element for each cyber-physical component. Inside each `cpc`, it collects the related resources, actions, operational goals, relations, communication threads, listener threads, and communication relations.

The technological enrichment required for code generation is guided by:

```text
src/frontend/static/input/json/PIM-PSM-Rules.json
```

This JSON file requests information such as parameter types, operation modes, hardware integration descriptions, and data structures. The XSLT then propagates this information into the intermediate PSM representation.

Therefore, the PIM-to-PSM stage should be understood mainly as a preprocessing and structuring stage for code generation.

---

## PSM-to-Code Transformation

### Purpose

The PSM-to-Code stage generates Arduino MKR1010 source code from the intermediate PSM XML representation.

### Implementation Notes

The generator is implemented in:

```text
src/backend/psm_to_code-arduinomkr1010.py
```

The script processes each `cpc` element and generates the corresponding source-code artefacts. In particular, it uses:

| PSM Element | Code Generation Role |
|------------|----------------------|
| `cpc` | Generates one Arduino project directory per component |
| `function` | Generates C/C++ functions |
| `thread` | Generates FreeRTOS task functions for operational goals |
| `commThread` | Generates MQTT publishing tasks |
| `listenerThread` | Generates MQTT receiving tasks and callbacks |
| `sw_resource` | Generates data structures used by functions |
| `hw_resource` | Generates contextual comments for hardware integration |
| `relation` | Generates dependency logic between functions, threads, and resources |
| `commRelation` | Links communication senders and receivers |

The generated artefacts include `.ino` files, `secrets.h`, `comm_utils.h`, FreeRTOS task creation code, MQTT connectivity code, data structures, callback functions, and boilerplate required for Arduino MKR1010 deployment.

---

## Summary of Transformation Artefacts

| Stage | Main Role | Artefacts |
|------|-----------|-----------|
| CIM-to-PIM | Converts CIM constructs into PIM DSL constructs | `CIM-PIM-Rules.json`, `CIM-PIM.xsl`, `CIM-PIM-Aux.xsl` |
| PIM-to-PSM | Enriches and restructures the PIM model into a code-generation-oriented XML representation | `PIM-PSM-Rules.json`, `PIM-PSM.xsl` |
| PSM-to-Code | Generates Arduino MKR1010 source code from the PSM representation | `psm_to_code-arduinomkr1010.py` |

