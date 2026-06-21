TOOL (تول) - Architecture Document
==================================

Architecture Principles
-----------------------

1.  Local First
    
2.  Modular Design
    
3.  Feature Flags
    
4.  Memory-Centric Architecture
    
5.  Planner-Driven Workflows
    
6.  Extensible Provider Layer
    

Layer 1: Core Layer
===================

These components are mandatory and always enabled.

Planner
-------

Responsible for:

*   Intent understanding
    
*   Task decomposition
    
*   Workflow planning
    
*   Provider selection
    

Workflow Engine
---------------

Responsible for:

*   Progress tracking
    
*   Execution stages
    
*   Status updates
    
*   Approval checkpoints
    

Memory Graph
------------

Main memory system.

Contains:

*   Global Memory
    
*   Brand Memory
    
*   Study Memory
    
*   Project Memory
    

Provider Layer
--------------

Provider abstraction layer.

Supported modes:

### Native

Examples:

*   OpenCode
    
*   OpenDesign
    

### API

Examples:

*   OpenAI
    
*   Claude
    
*   Gemini
    

### Browser

Examples:

*   Services without APIs
    

Storage Manager
---------------

Responsible for:

*   File organization
    
*   Folder structure
    
*   Retention policies
    
*   Archive management
    

Settings System
---------------

Centralized configuration management.

Layer 2: Dormant Features
=========================

Implemented but disabled by default.

Preference Memory
-----------------

Learns user preferences over time.

Feature Flag:

preference\_memory=false

Knowledge Vault
---------------

Stores long-term structured knowledge.

Feature Flag:

knowledge\_vault=false

Artifact System
---------------

Stores generated outputs.

Examples:

*   Reports
    
*   Presentations
    
*   Carousels
    
*   Designs
    
*   Code
    

Feature Flag:

artifact\_system=false

Google Drive Sync
-----------------

Backup and archive system.

Feature Flag:

google\_drive\_sync=false

Telegram Integration
--------------------

Optional communication channel.

Feature Flag:

telegram\_enabled=false

Task Journal
------------

Execution history and analytics.

Feature Flag:

task\_journal=false

Health Dashboard
----------------

System monitoring.

Feature Flag:

health\_dashboard=false

Self Improvement Queue
----------------------

Stores system improvement suggestions.

Feature Flag:

self\_improvement=false

User System
-----------

Future-ready user architecture.

Feature Flag:

users\_enabled=false

Layer 3: Future Layer
=====================

Not implemented in V1.

*   Teams
    
*   Billing
    
*   Marketplace
    
*   MCP
    
*   Cloud Sync
    
*   Multi-Tenant SaaS
    

Data Structure
==============

Memory Graph

Global Memory├── Preferences├── Brands├── University├── Projects└── Knowledge Vault

File Structure
==============

Data/

Brands/University/Projects/Artifacts/Archive/

Retention Policy
================

Supported modes:

*   Never Delete
    
*   30 Days
    
*   60 Days
    
*   90 Days
    
*   180 Days
    

Archive before deletion.

Approval Workflow
=================

Discuss→ Plan→ Approve→ Execute→ Learn

This workflow is mandatory for major tasks.

Development Rule
================

OpenCode must never implement features outside the approved sprint plan.

All development must follow:

Architecture → TODO → Sprint → Implementation