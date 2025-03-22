# General Logic Module with Input/Output Logic Formalism - Product Requirements Document

## 1. Overview

This project involves implementing the General Logic Module, which encapsulates Kant's table of judgments through Evans' input/output logic formalism. This module provides the foundational logical structures that govern valid inference independent of content within the KantAI system. Rather than using traditional truth-functional logic, this module implements judgment forms as conditional imperatives and permissives that guide cognitive operations. In accordance with Kant's epistemology, this module focuses strictly on the formal structure of thought, distinct from both the categories of the Understanding Module and the empirical concepts derived from experience.

## 2. Problem Statement

The KantAI backend requires a logical foundation that properly captures Kant's general logic—the formal structure of thought independent of content. Traditional truth-functional logic is inadequate for representing Kant's system, which involves rules that guide mental operations rather than simply establish truth values. Following Evans' (2017) groundbreaking formalization, we need to implement an input/output logic system where rules are represented as ordered pairs with context-sensitive application. Without this module, the system would lack the formal logical infrastructure needed to properly implement Kantian judgment forms and reasoning patterns.

## 3. Goals & Objectives

- Implement the 12 forms of judgment from Kant's table using Evans' input/output logic formalism
- Create a clear distinction between imperative rules (mandatory operations) and permissive rules (optional operations)
- Establish clear boundaries between General Logic (formal structures), Categories (Understanding), and Empirical Concepts
- Develop representation of formal judgment forms in Neo4j as a foundation for future inference capabilities
- Integrate the logical formalism with the Neo4j knowledge graph
- Implement all four judgment groups: Quantity, Quality, Relation, and Modality
- Support the transformation from traditional logic to operation-guiding imperatives
- Create structural foundations for future rule conflict resolution and inference capabilities

## 4. User Stories

- As a knowledge engineer, I want to represent Kantian judgment forms in the system so that reasoning follows proper logical forms
- As a developer, I want to understand the distinct roles of General Logic and the Understanding Module when modeling concepts
- As a system architect, I want the logical formalism to integrate with Neo4j so that rules can be stored and retrieved from the graph database
- As an AI researcher, I want to see how traditional logic is transformed into operation-guiding imperatives
- As a domain expert, I want to see how formal judgment structures will eventually support context-sensitive rule application
- As a frontend developer, I want to visualize and explain judgment forms through the chat interface

## 5. Functional Requirements

### 5.1 Kantian Epistemological Distinctions

- Implement clear separation between:
  - General Logic: Content-neutral formal structures (judgment forms)
  - Categories: Concepts of Understanding that structure experience
  - Empirical Concepts: Specific concepts derived from experience
- Create explicit relationships between these layers that respect Kantian epistemology
- Support visualization and explanation of these distinctions
- Enable proper attribution of which layer a particular element belongs to
- Implement validation to ensure elements are not misclassified across layers

### 5.2 Input/Output Logic Representation (Phase 1)

- Implement rule representation as ordered pairs (A,B) where A is input condition and B is output obligation/permission
- Create distinct classes for imperative rules and permissive rules
- Develop rule templates for all 12 judgment forms
- Create metadata structures for rules (domain, judgment form, derivation type)
- Implement rule serialization for storage in the knowledge graph
- Create validation mechanisms for well-formed rules

### 5.3 Judgment Form Implementation (Phase 1)

- Implement representation of all judgment forms in Neo4j:
  - Quantity: Universal, Particular, Singular
  - Quality: Affirmative, Negative, Infinite
  - Relation: Categorical, Hypothetical, Disjunctive
  - Modality: Problematic, Assertoric, Apodictic
- Create validation mechanisms for well-formed judgment structures
- Develop graph patterns for each judgment form
- Implement example rules for each form
- Support visual representation of judgment forms

### 5.4 Neo4j Integration (Phase 1)

- Create graph patterns for storing input/output rules
- Implement rule retrieval mechanisms from the knowledge graph
- Develop metadata models for rule context and domains
- Support metadata querying for rule information
- Implement efficient indexing for rule patterns
- Create visualization mechanisms for rule structures

### 5.5 Rule Application Mechanisms (Future Phase)

- Develop rule application mechanisms that transform content into properly formatted rules
- Implement contextual relevance evaluation for rules
- Create mechanisms for functional differentiation of rule types
- Develop rule conflict resolution based on context and evidential support
- Implement non-monotonicity handling for belief revision
- Create decision rationale recording for explanatory purposes
- Support prioritization based on rule types and domains
- Implement rule selection strategies for different reasoning tasks

## 6. Technical Considerations

### 6.1 Implementation Approach

- Adopt a phased approach with initial focus on representation in Neo4j
- Design a modular class structure for the General Logic Module
- Create clear separation between rule representation and rule application
- Develop solid foundations for future inference capabilities
- Consider performance implications for large rule sets
- Support both synchronous and asynchronous rule application in future phases
- Create comprehensive testing frameworks for logical correctness

### 6.2 Neo4j Integration Specifics

- Design an efficient graph pattern for representing rules
- Consider property structure for rule components
- Implement appropriate indices for rule retrieval
- Develop Cypher queries for rule retrieval and visualization
- Create specialized procedures for future rule operations
- Support transaction management for rule updates
- Implement backup mechanisms for rule sets

### 6.3 Frontend and Chat Integration

- Design visualization-friendly representations of judgment forms
- Create explanatory templates for describing logical structures
- Develop query mechanisms for frontend exploration of rules
- Implement examples for each judgment form that can be visualized
- Support hierarchical display of rule structures
- Create documentation accessible through the chat interface
- Implement basic response templates for logical form questions

### 6.4 Integration with Other Modules

- Design clear interfaces with the Understanding Module (categories)
- Create distinction between formal logic and categorical application
- Establish patterns for how empirical concepts relate to both formal logic and categories
- Develop documentation explaining the roles of each module
- Plan connections to future Judgment Module functionalities
- Create example flows demonstrating inter-module boundaries

## 7. Acceptance Criteria

- All 12 judgment forms from Kant's table are correctly represented in Neo4j using Evans' formalism
- The system properly distinguishes between General Logic, Categories, and Empirical Concepts
- The system maintains clear boundaries between formal structures and content
- Rules can be stored in and retrieved from the Neo4j knowledge graph
- Validation mechanisms ensure rule correctness
- Documentation clearly explains the distinction between General Logic and other modules
- Chat interface can explain and visualize judgment forms
- The foundation for future inference capabilities is established

## 8. Future Considerations (v2)

- Implementation of the active inference engine for rule application
- Context-sensitive rule application mechanisms
- Rule conflict resolution strategies
- Non-monotonic reasoning capabilities
- Advanced non-classical logic extensions beyond Evans' formalism
- Learning mechanisms for rule prioritization based on outcomes
- Domain-specific judgment form specializations
- Probabilistic extensions to the input/output logic framework
- Integration with external logic systems and ontologies

## 9. Implementation Plan

We'll split the implementation into smaller, manageable tasks, with a focus on representation first and inference later:

### Task 1: Kantian Epistemological Distinction Implementation
- [ ] Create clear model separating General Logic, Categories, and Empirical Concepts
- [ ] Implement boundary validation between these domains
- [ ] Create documentation explaining these distinctions
- [ ] Develop visualization of the three-layer model
- [ ] **Steps to Test**: Verify correct classification of elements across layers

### Task 2: Core Input/Output Logic Representation
- [ ] Design and implement the basic rule representation classes
- [ ] Create the distinction between imperative and permissive rules
- [ ] Develop rule metadata structures
- [ ] Create serialization formats for rules
- [ ] **Steps to Test**: Verify rule representation and serialization with simple examples

### Task 3: Judgment Form Implementation
- [ ] Implement Neo4j representations for Quantity judgment forms (Universal, Particular, Singular)
- [ ] Create Neo4j patterns for Quality judgment forms (Affirmative, Negative, Infinite)
- [ ] Develop Neo4j patterns for Relation judgment forms (Categorical, Hypothetical, Disjunctive)
- [ ] Implement Neo4j patterns for Modality judgment forms (Problematic, Assertoric, Apodictic)
- [ ] Create validation mechanisms for each judgment form
- [ ] **Steps to Test**: Create examples of each judgment form and verify correct structure

### Task 4: Neo4j Storage and Retrieval
- [ ] Design graph patterns for rule storage
- [ ] Implement rule persistence mechanisms
- [ ] Create rule retrieval functions
- [ ] Implement metadata querying
- [ ] Develop visualization-friendly query patterns
- [ ] **Steps to Test**: Store rules in the graph database and verify correct retrieval

### Task 5: Frontend and Chat Support
- [ ] Create visualization templates for judgment forms
- [ ] Implement explanatory descriptions of logical structures
- [ ] Develop query mechanisms for frontend exploration
- [ ] Create example data for frontend demonstration
- [ ] Implement chat response templates for logical questions
- [ ] **Steps to Test**: Verify visualization and explanation of judgment forms through the chat interface

## 10. Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| Current Date | 1.0 | Initial PRD | AI Assistant |
| Current Date | 1.1 | Updated to clarify Kantian distinctions and implement phased approach | AI Assistant | 