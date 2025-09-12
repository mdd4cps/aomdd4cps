# Structural Validations

This directory contains the artifacts used to perform **structural validations** of the PIM DSL in the MDD4CPS process.  
Structural validations focus on detecting **logical inconsistencies** in models, as verified with **Protégé** and the **HermiT reasoner**.

## Contents

- **`dsl_pim_mdd4cps.rdf`**  
  The ontology of the PIM DSL expressed in **RDF/XML** format.  
  This ontology formalizes the main constructs of the PIM stage, including classes, properties, disjointness axioms, and cardinality restrictions.

- **`dsl_pim_mdd4cps.properties`**  
  Protégé configuration file used to facilitate loading the ontology and running consistency checks with the HermiT reasoner.

- **`owl_01_two_ops_in_action.ttl`**  
  Faulty dataset (Turtle format).  
  Demonstrates a structural violation where a single action is associated with two different refinement operators, breaking exclusivity constraints.

- **`owl_02_element_in_two_components.ttl`**  
  Faulty dataset (Turtle format).  
  Demonstrates a structural violation where the same internal element is assigned to two different `CPComponent`s, violating uniqueness.

- **`owl_03_hw_and_sw_resource.ttl`**  
  Faulty dataset (Turtle format).  
  Demonstrates a structural violation where the same resource is typed both as `HWResource` and `SWResource`, which are disjoint classes.

## Usage

1. Open the ontology (`dsl_pim_mdd4cps.rdf`) in **Protégé**.  
2. Load any of the faulty datasets (`.ttl`) as individuals of the ontology.  
3. Run the **HermiT reasoner** to check for consistency.  
4. Observe how the reasoner correctly detects the structural violations introduced in each dataset.

## Purpose

These artifacts serve as **controlled experiments** to illustrate how structural constraints in the PIM DSL ontology can be enforced.  
They show that inconsistencies such as multiple refinement operators, duplicate containment, or conflicting resource typing are systematically detected before models proceed to subsequent transformations.

