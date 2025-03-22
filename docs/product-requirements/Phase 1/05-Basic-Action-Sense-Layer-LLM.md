# Basic Action/Sense Layer with LLM Integration - Product Requirements Document

## 1. Overview

This project involves implementing the initial version of the Action/Sense Layer, which serves as the interface between external unstructured data and the Understanding Module's structured knowledge graph. Leveraging Large Language Models (LLMs), this layer will ingest textual data from various sources, extract relevant entities, relationships, and concepts, and transform them into structured representations compatible with the Kantian categorical framework. Additionally, this layer will support interactive chat functionality for frontend users to query and update the ontology.

## 2. Problem Statement

The KantAI backend requires a mechanism to process raw, unstructured data from external sources (e.g., text documents, web content) and convert it into structured knowledge that aligns with the Kantian categorical framework. Without this capability, the system would remain isolated from real-world information and unable to grow its knowledge base organically. Additionally, users need an intuitive way to interact with the ontology through natural language, enabling them to query, explore, and update the knowledge graph without requiring expertise in graph query languages or understanding the underlying Kantian structure. We need a robust Action/Sense Layer that uses LLMs to intelligently parse, extract, and structure information while minimizing hallucinations, maintaining conceptual integrity, and providing an engaging chat interface for users.

## 3. Goals & Objectives

- Create an Action/Sense Layer that processes unstructured textual data using LLMs
- Implement data ingestion mechanisms for various text formats (documents, web pages, etc.)
- Extract entities, relationships, and concepts that align with the Kantian categorical framework
- Develop hallucination detection and mitigation mechanisms
- Connect the LLM outputs to the Understanding Module's knowledge graph via its API
- Support confidence scoring and uncertainty representation for extracted knowledge
- Enable basic processing of causal relationships, substance-accident relationships, and other Kantian categories
- Implement an interactive chat interface for frontend users to query and update the ontology
- Provide natural language explanations of ontology structures and relationships
- Support early demonstrations of the system's capabilities for investors
- Enable progressive refinement of the ontology through conversational interactions

## 4. User Stories

- As a knowledge engineer, I want to ingest textual documents and have relevant concepts automatically extracted and added to the knowledge graph
- As a system administrator, I want to configure which external data sources the system can access
- As a data curator, I want to review and validate LLM-extracted concepts before they are permanently added to the knowledge graph
- As a developer, I want to trace how external information was processed from raw text to structured concepts
- As a researcher, I want confidence scores attached to extracted relationships to understand their reliability
- As a system integrator, I want clear interfaces between the Action/Sense Layer and the Understanding Module
- As a frontend user, I want to ask questions about the ontology and receive natural language explanations
- As a knowledge editor, I want to add new concepts and relationships through conversational interactions
- As a domain expert, I want to refine the ontology through natural language feedback
- As an investor, I want to see a compelling demonstration of the system's capabilities through an intuitive interface
- As a project stakeholder, I want to understand how the system reasons about concepts without needing to understand the underlying Kantian framework

## 5. Functional Requirements

### 5.1 Data Ingestion

- Implement a text document ingestion system that supports common formats (TXT, PDF, HTML, etc.)
- Create a web content scraper for extracting information from specified URLs
- Develop a batching system for processing large volumes of text
- Support prioritization of data sources based on reliability and relevance
- Enable filtering of content based on topic, domain, or other criteria

### 5.2 LLM-Based Parsing

- Integrate with one or more LLM providers (e.g., OpenAI, HuggingFace, self-hosted models)
- Create prompt templates optimized for extracting Kantian categories
- Implement specialized prompts for different relationship types:
  - Causal relationships (CAUSES)
  - Substance-accident relationships (HAS_PROPERTY)
  - Community relationships (INTERACTS_WITH)
  - Hierarchical relationships (CONTAINS, IS_PART_OF)
- Support both zero-shot and few-shot learning approaches with examples
- Enable context window management for processing longer texts

### 5.3 Structured Output Generation

- Define JSON schemas for LLM outputs that align with the Knowledge Graph structure
- Implement templates that correspond to the Kantian categories
- Create validators for LLM outputs to ensure compliance with expected formats
- Support structured representation of uncertainty and confidence
- Enable extraction of multiple relationships from a single text passage

### 5.4 Hallucination Mitigation

- Implement multi-stage verification for LLM outputs
- Create confidence scoring mechanisms based on source reliability and LLM certainty
- Develop pattern-based validation rules for common relationship types
- Support manual review workflows for low-confidence extractions
- Implement citation tracking to link concepts back to their source material

### 5.5 Knowledge Graph Integration

- Create an integration layer with the Understanding Module's API
- Implement mappings between LLM outputs and API requests
- Develop error handling for constraint violations
- Support both synchronous and asynchronous processing modes
- Enable feedback loops where existing knowledge contextualizes new extractions

### 5.6 Interactive Chat Interface

- Implement a conversational API endpoint for the frontend chat interface
- Create context management to maintain conversation history and state
- Develop intent recognition for different types of user queries:
  - Knowledge retrieval queries ("What is X?", "How does X relate to Y?")
  - Knowledge creation requests ("Add a new concept", "Create a relationship")
  - Knowledge modification requests ("Update this concept", "Change this relationship")
  - Meta-queries about the ontology structure ("Show me all concepts related to X")
  - Explanatory queries ("Why is X classified this way?", "Explain this relationship")
- Support natural language generation for explanations of ontological structures
- Implement prompt templates for different conversation scenarios
- Enable visualization requests through natural language

### 5.7 Frontend Integration

- Create WebSocket support for real-time chat interactions
- Implement streaming responses for improved user experience
- Develop frontend-friendly JSON response formats
- Support authentication and session management
- Provide user-specific conversation history
- Enable chat interface customization (system prompts, persona, etc.)
- Implement typing indicators and other chat UI enhancements

### 5.8 Early Demonstration Capabilities

- Create a set of pre-configured demo scenarios highlighting key capabilities
- Implement guided exploration paths through the ontology
- Support simplified ontology creation for demo purposes
- Develop visually compelling examples of ontology reasoning
- Enable investor-friendly explanations of the system's capabilities
- Create a "showcase mode" with predefined examples and responses

## 6. Technical Considerations

### 6.1 LLM Selection and Configuration

- Evaluate and select appropriate LLM(s) based on performance, cost, and integration ease
- Consider fine-tuning approaches for domain-specific knowledge extraction
- Implement prompt engineering best practices
- Support model versioning and performance tracking
- Consider token usage optimization strategies
- Evaluate streaming capabilities for real-time chat responses

### 6.2 Performance and Scalability

- Design for asynchronous processing of large document batches
- Implement queuing mechanisms for high-volume processing
- Consider distributed processing for horizontal scaling
- Optimize token usage to minimize operational costs
- Define appropriate timeouts and retry mechanisms
- Implement caching for common chat queries

### 6.3 Security and Privacy

- Implement content filtering to prevent processing of inappropriate material
- Create mechanisms to respect copyright and usage rights
- Support source material anonymization where appropriate
- Implement secure API key management for LLM providers
- Enable audit logging of all processing activities
- Protect conversation history and user data
- Implement rate limiting to prevent abuse

### 6.4 Integration Requirements

- Ensure compatibility with the Understanding Module API
- Design for future integration with the Judgment Module for validation
- Consider integration points with the Imagination Module
- Support the Concept Transition Pipeline's requirements
- Plan for eventual connection to the Reason Module for coherence checking
- Create seamless integration with the Chat Ontology Builder frontend
- Support WebSocket connections for real-time communication

### 6.5 Chat Functionality Considerations

- Implement context window management to maintain relevant conversation history
- Develop strategies for graceful handling of out-of-scope queries
- Create fallback mechanisms for unanswerable questions
- Support conversational repair when misunderstandings occur
- Enable explicit and implicit disambiguation of user queries
- Implement conversation state tracking
- Support multi-turn interactions for complex ontology operations

## 7. Acceptance Criteria

- The Action/Sense Layer successfully ingests textual content from multiple sources
- LLMs correctly extract entities and relationships aligned with Kantian categories
- Structured outputs comply with Knowledge Graph requirements
- Hallucination detection mechanisms successfully identify and mitigate false information
- Confidence scoring accurately reflects the reliability of extracted knowledge
- Integration with the Understanding Module API works seamlessly
- Performance meets specified requirements for throughput and latency
- Documentation clearly explains the system's capabilities and limitations
- The chat interface correctly interprets user intents and provides appropriate responses
- Users can successfully query and update the ontology through natural language
- The system provides clear explanations of ontological structures and relationships
- Investor demonstrations effectively showcase the system's capabilities
- The interface supports both technical and non-technical users

## 8. Future Considerations (v2)

- Support for multi-modal inputs (images, audio, video)
- Specialized fine-tuning of LLMs on the Kantian framework
- Advanced hallucination detection using contradictory information checks
- Integration with external knowledge bases for verification
- Real-time processing of streaming data sources
- Enhanced domain-specific extraction capabilities
- Implementation of active learning to improve extraction quality over time
- Advanced conversational capabilities with multi-step reasoning
- Voice interface for ontology interaction
- Personalized interaction styles based on user preferences
- Advanced visualization guidance through natural language
- Collaborative ontology editing through conversation

## 9. Implementation Plan

We'll split the implementation into smaller, manageable tasks:

### Task 1: Data Ingestion Framework
- [ ] Set up document processing pipeline
- [ ] Implement web content scraping capabilities
- [ ] Create batching and prioritization mechanisms
- [ ] Develop content filtering and source validation
- [ ] **Steps to Test**: Ingest various document types and verify correct extraction of raw text

### Task 2: LLM Integration
- [ ] Select and integrate LLM provider(s)
- [ ] Develop prompt engineering framework
- [ ] Create category-specific prompt templates
- [ ] Implement context window management
- [ ] Evaluate and implement streaming capabilities for chat
- [ ] **Steps to Test**: Process sample texts and evaluate extraction quality for different relationship types

### Task 3: Structured Output Generation
- [ ] Define JSON schemas for all categorical relationships
- [ ] Implement output validators and formatters
- [ ] Create confidence scoring mechanisms
- [ ] Develop citation and source tracking
- [ ] **Steps to Test**: Verify that outputs conform to expected schemas and include appropriate metadata

### Task 4: Basic Chat Functionality (Priority for Early Demos)
- [ ] Implement conversational API endpoint
- [ ] Create context management for conversation history
- [ ] Develop basic intent recognition for queries
- [ ] Implement response generation for knowledge retrieval
- [ ] Create WebSocket support for real-time interaction
- [ ] Develop frontend-friendly response formats
- [ ] **Steps to Test**: Conduct basic conversations about the ontology and verify appropriate responses

### Task 5: Hallucination Mitigation
- [ ] Implement multi-stage verification
- [ ] Create validation rules for common relationship types
- [ ] Develop review workflow for uncertain extractions
- [ ] Set up basic fact-checking mechanisms
- [ ] **Steps to Test**: Introduce deliberate hallucinations and verify detection rates

### Task 6: Advanced Chat Capabilities
- [ ] Implement knowledge creation through conversation
- [ ] Develop knowledge modification capabilities
- [ ] Create explanation generation for ontological structures
- [ ] Implement meta-queries about the ontology
- [ ] Add visualization request handling
- [ ] **Steps to Test**: Use natural language to create, modify, and query the ontology

### Task 7: Integration and Demonstration
- [ ] Implement client for the Understanding Module API
- [ ] Create mappings between LLM outputs and API requests
- [ ] Develop error handling and retry mechanisms
- [ ] Implement feedback loops with existing knowledge
- [ ] Create demonstration scenarios and guided paths
- [ ] Develop investor-friendly explanations and examples
- [ ] **Steps to Test**: Run through demonstration scenarios and verify system performance

## 10. Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| Current Date | 1.0 | Initial PRD | AI Assistant |
| Current Date | 1.1 | Added chat functionality and frontend integration | AI Assistant |
| Current Date | 1.2 | Updated numbering from #04 to #05 due to addition of General Logic Module | AI Assistant | 