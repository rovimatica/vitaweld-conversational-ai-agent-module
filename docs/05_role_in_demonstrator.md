# Role in the TRL6-7 Demonstrator

This document connects the open **VITAWELD Conversational AI Agent** with the
TRL6 demonstrator from which it was extracted: what was demonstrated, which part
became reusable, and what remains demonstrator-specific.

## 1. Demonstrator overview

| Item | Description |
|---|---|
| Demonstrator name | VITAWELD — HRI-enabled robotic welding demonstrator (Stage 3 / D3) |
| Environment | Industrial robotic welding cell at IDONIAL's facilities (industrial pilot environment) |
| Robot / platform | Robot KUKA cell: welding robot (with welding gun) + KUKA workpiece positioner; a camera focused on the weld; a second camera for safety and gesture detection (ROS4HRI); ROS 2 / Vulcanexus (Jazzy + Fast DDS) backbone and a FIWARE context broker |
| End user / scenario | Welding operators performing robotic welding of metal parts (e.g., a T-shaped workpiece) at IDONIAL |
| Problem addressed | Operators depend on several fragmented, expert-oriented tools and teach-pendant programming, with high training effort and specialisation. The demonstrator unified and simplified the workflow through natural-language HRI. |
| Video link | _[URL — see [`../media/video_link.md`](../media/video_link.md)]_ |

## 2. Module role in the demonstrator

In the demonstrator, the agent acted as the **mission controller**: the
conversational layer through which the operator drove the entire welding
workflow — part selection, weld definition, workpiece positioning, parameter
configuration, trajectory generation and execution, and process monitoring.

The agent never controlled the robot or spoke any middleware directly. It
invoked the operational tasks through a single ROS 2 service, `PlanWeldPro.srv`,
exposed to it as a tool. Everything below that service (trajectory generation,
execution, perception, monitoring) lived in the ROS 2 / Vulcanexus + Fast DDS +
FIWARE layer, outside the agent (see [`02_interfaces.md`](02_interfaces.md)).

## 3. What became reusable and what remains demonstrator-specific

| Demonstrator component | Reusable module extraction | What remains demonstrator-specific |
|---|---|---|
| Conversational mission controller | The framework-agnostic LLM orchestration core (agent, tool registration and parallel execution, conversation memory, configuration) — i.e. **this open module** | The welding-specific system prompt and tool set, and the graphical web front-end (the open module is console-only) |
| Welding task / skill layer | Only the orchestration pattern (how operational tasks are exposed to the agent as tools) | All welding logic: MoveIt/`LIN` trajectory planning, weld-candidate selection, workpiece positioning and weld-quality vision — remain proprietary |
| ARISE middleware integration | None bundled; the reusable element is the **tool interface** through which such integrations can be bridged | ROS 2/Vulcanexus nodes and services, Fast DDS transport, the DDS Router allow-list, the FIWARE/Orion-LD context model and the ROS4HRI perception pipeline |
| Web application (operator UI) | None | The entire web front-end (3D viewer, camera views, graphical task tools, process monitoring) |

## 4. Summary

The demonstrator validated the agent as a natural-language mission controller in
a real industrial welding cell. What was extracted as open and reusable is the
**orchestration core**; the welding tasks, the ARISE middleware integration and
the graphical interface remain demonstrator-specific or proprietary.
