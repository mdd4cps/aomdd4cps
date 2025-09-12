# Semantic Validations

This directory contains the **semantic validation artifacts** used in the MDD4CPS process.  
It includes datasets with and without errors, SHACL shapes for each validation case, and example commands to reproduce the validation procedure.

## Contents

### Data Graphs (`data_case*.ttl`)
Each case has **two versions**:
- `*_no_errors.ttl` → Correct dataset (conformant to ontology + SHACL constraints).  
- `*_missing_*` or similar → Faulty dataset where a deliberate error was introduced.  

Cases correspond to those described in the chapter:
1. **Missing messaging structures**  
   - `data_case1_no_errors.ttl`  
   - `data_case1_missing_messaging.ttl`
2. **Missing top OnIntervalAction**  
   - `data_case2_no_errors.ttl`  
   - `data_case2_missing_top_onintervalaction.ttl`
3. **Missing operation modes description**  
   - `data_case3_no_errors.ttl`  
   - `data_case3_missing_operations_modes_description.ttl`
4. **Invalid timing intervals**  
   - `data_case4_no_errors.ttl`  
   - `data_case4_missing_timing_interval.ttl`
5. **Missing messaging data structures and links (CIM-driven)**  
   - `data_case5_no_errors.ttl`  
   - `data_case5_missing_messaging_structures.ttl`

### Shapes Graphs (`shapes_case*.ttl`)
Each file defines the SHACL constraints that must be satisfied for its corresponding dataset:
- `shapes_case1_missing_messaging.ttl`  
- `shapes_case2_top_onintervalaction.ttl`  
- `shapes_case3_operation_modes.ttl`  
- `shapes_case4_timing_interval.ttl`  
- `shapes_case5_messaging_structures.ttl`

### Ontology
- `dsl_pim_mdd4cps.ttl` → OWL ontology of the PIM DSL (in Turtle format).  
- `dsl_pim_mdd4cps.properties` → Ontology metadata.

### Validation Command
- `validation_command` → Example command used to run validation.  

```bash
$ pyshacl -s shapes.ttl -d <(cat ontology.ttl data_case.ttl) -i owlrl -o report_case.ttl

