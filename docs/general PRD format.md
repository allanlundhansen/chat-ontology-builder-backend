# Collapse/Expand Parent Concepts - Product Requirements Document

## 1. Overview

## 2. Problem Statement

## 3. Goals & Objectives

## 4. User Stories

## 5. Functional Requirements

Below are ONLY examples for sub-points and ONLY if required
### 5.1 Data Structure

### 5.2 Relationship Establishment

### 5.3 Collapse/Expand Behavior

### 5.4 Interaction Requirements

## 6. UI/UX Requirements (only for frontend)

Again below are ONLY example and ONLY if required
### 6.1 Visual Indicators

### 6.2 Collapse/Expand Controls

### 6.3 Animation & Transitions

## 7. Technical Considerations

Again below are ONLY example and ONLY if required
### 7.1 Performance

### 7.2 State Management

### 7.3 Layout Implications

## 8. Acceptance Criteria

## 9. Future Considerations (v2)

## 10. Implementation Plan

We'll split the implementation into smaller, manageable tasks:

(amount of tasks required depends on project, below filled in tasks are ONLY examples)
### Task 1: Data Structure Updates
- [x] Update Node interface to include parentId and isCollapsed properties
- [x] Update Connection interface to handle visibility
- [x] Add basic type definitions for parent-child relationships
- [x] **Steps to Test**: Create unit tests for the updated interfaces using Jest/React Testing Library. Verify that nodes can have parent IDs and collapse states, and that these properties are properly tracked.
  - **Note**: Successfully tested the Node and Connection interfaces with proper tests

### Task 2: Core Parent-Child Relationship Functions
- [x] Implement getChildNodes function to find children of a node
- [x] Implement getAllDescendantIds to find all descendants recursively
- [x] Implement function to detect circular references
- [x] Implement setParentChild function for establishing relationships
- [x] **Steps to Test**: Create unit tests for each function with various test cases including:
  - Test getChildNodes with nodes having multiple children
  - Test getAllDescendantIds with multi-level hierarchies
  - Test circular reference detection with different circular scenarios
  - Test setParentChild with both valid and invalid parent assignments
### Task 3: Collapse/Expand Core Functionality
- [x] Implement toggleCollapseNode function
- [x] Add logic to determine node visibility based on parent collapse state
- [x] Create functions to filter visible nodes and connections
- [x] **Steps to Test**: Create unit tests that verify:
  - toggleCollapseNode correctly changes the node's collapse state
  - Node visibility is correctly calculated based on ancestors' collapse states
  - The filtering functions correctly identify which nodes and connections should be visible
  - **Additional Tests**:
    - Test deep hierarchies (4+ levels) with various collapse states at different levels
    - Test edge cases where nodes have multiple connections to hidden and visible nodes
    - Test visibility of nodes that are both children and parents
    - Test scenarios where a child node is visible but a grandchild is not
    - Test that expanding a node doesn't affect its children's own collapse states
    - Test that collapsing a node hides all its descendants regardless of their collapse states
    - Test that connections between a visible and a hidden node are not displayed
  - **Notes**: The collapse-expand and parent-child tests pass successfully, confirming the core functionality works. The visibility-specific tests need further refinement in a future PR.

### Task 4: UI Updates for Node Visualization
- [ ] Add visual indicators for parent nodes (P badge)
- [ ] Add visual indicators for child nodes (C badge)
- [ ] Implement the collapse/expand button for parent nodes
- [ ] Update node styling based on relationship status
- [ ] **Steps to Test**: Manually verify in the UI:
  - Create a parent node with child nodes and verify badges appear correctly
  - Verify that a node that is both parent and child shows both indicators
  - Check that the collapse/expand button only appears on parent nodes
  - Verify UI styling matches design for all node states

We should begin with Task 1 (Data Structure Updates) as it forms the foundation for all other tasks.

## 11. Revision History

(should be updated as well as the tasks are)
| Date | Version | Changes | Author |
|------|---------|---------|--------|
| Current Date | 1.0 | Initial PRD | AI Assistant |
