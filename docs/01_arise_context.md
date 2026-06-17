# ARISE Context

This document explains how the **VITAWELD Conversational AI Agent** fits within
the ARISE initiative and its reusable-module philosophy.

## 1. ARISE and the reusable-module concept

ARISE promotes **human-centric Human-Robot Interaction (HRI)** built on a common,
open middleware stack (ROS 2 / Vulcanexus, FIWARE / NGSI-LD, DDS and ROS4HRI).
A core goal of the initiative is **reusability**: each experiment, after
validating its solution in a TRL6-7 demonstrator, extracts a self-contained,
reusable capability and releases it openly so that other developers, integrators
and platforms can adopt or adapt it.

This repository is the open, reusable capability extracted from the **VITAWELD**
experiment.

## 2. The VITAWELD experiment

VITAWELD ("Vision & Human-Robot Teaming for Enhanced Welding") demonstrated a
robotic welding cell that an operator can drive through **natural language**,
removing the need to juggle several specialised tools and teach-pendant
programming. The solution was validated at TRL6 in a real industrial welding
cell at IDONIAL (see [`05_role_in_demonstrator.md`](05_role_in_demonstrator.md)).

## 3. Where this module sits (PAL architecture)

The VITAWELD solution follows the ARISE/PAL layered model:

```
Application  →  Mission controller  →  Intents  →  Tasks  →  Skills
```

This module implements the **mission controller and intent layer**: it receives
the operator's natural-language input, interprets the intent, and orchestrates
the appropriate **tasks** by invoking them as tools. The tasks and skills
themselves (in VITAWELD: trajectory generation, workpiece positioning,
weld-quality, etc.) are the operational units the controller drives — they are
**not** part of the open module and remain demonstrator-specific.

In other words, what is open here is the **orchestration brain**, not the
welding-specific tasks or the middleware integration.

## 4. ARISE contribution

The module contributes a **reusable HRI capability**: a framework-agnostic
conversational mission controller (LLM + ReAct + non-blocking tool execution)
that any ARISE partner can place in front of their own tools or skills to add
natural-language operator interaction, independently of the robot, the task
domain or the middleware.

Its relationship with the ARISE middleware interfaces (and why they are not
bundled) is detailed in [`02_interfaces.md`](02_interfaces.md).

## 5. Document map

- [`02_interfaces.md`](02_interfaces.md) — ARISE interfaces and integration contract
- [`03_installation_and_hello_world.md`](03_installation_and_hello_world.md) — install and run
- [`04_basic_demo_how_to_use.md`](04_basic_demo_how_to_use.md) — basic demo
- [`05_role_in_demonstrator.md`](05_role_in_demonstrator.md) — role in the TRL6 demonstrator
