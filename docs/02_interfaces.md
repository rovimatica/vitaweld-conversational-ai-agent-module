# Interfaces

This document describes how the **VITAWELD Conversational AI Agent** relates to
the ARISE middleware interfaces (ROS 2 / Vulcanexus, FIWARE / NGSI-LD, the DDS
enabler and ROS4HRI).

## 1. Design principle

The module is a **framework-agnostic conversational orchestrator**. It does not
bundle any ARISE middleware interface. In the VITAWELD demonstrator, every
middleware interaction was implemented in the **external tools** registered into
the agent, keeping a clean separation between:

- **Orchestration (open, this module):** natural-language understanding,
  reasoning, tool selection and invocation, conversation memory.
- **System integration (demonstrator-specific):** ROS 2 communication, context
  management, persistence, perception.

The agent's **tool interface** is the single integration point through which any
of the interfaces below can be connected.

## 2. ARISE interface status

| ARISE interface | Implemented in module? | Justification | How it was realised in the TRL6 demonstrator |
|---|---|---|---|
| ROS 2 / Vulcanexus | No (N/A) | The module is not a ROS 2 package and performs no ROS 2 communication. It is intentionally middleware-neutral; a ROS 2 client is plugged in as a registered tool. | ROS 2 (Vulcanexus, Jazzy + FastDDS) carried all robot/cell communication. The agent invoked ROS 2 services/actions (e.g. trajectory planning and execution) through tools wrapping the corresponding clients. |
| FIWARE / NGSI-LD | No (N/A) | The agent neither publishes nor consumes NGSI-LD entities. Context management is out of the orchestration scope. | A dedicated demonstrator component handled the Orion-LD context broker and data persistence; the agent only triggered or queried it via tools. |
| DDS enabler | No (N/A) | The module performs no DDS communication and defines no DDS topics or QoS profiles. | DDS (FastDDS) was the underlying transport of the ROS 2 layer, and a DDS Router governed the FIWARE allow-list — both external to the agent. |
| ROS4HRI | No (N/A) | The agent does not produce or consume ROS4HRI messages. **No extension to ROS4HRI is proposed and no non-aligned workaround is introduced at the agent level**: human-state information reaches the agent only as abstract tool inputs/events, leaving the ROS4HRI representation entirely in the perception layer. | Human perception (gesture-based stop, presence) was published on ROS4HRI-aligned topics by perception tools; the agent received only the resulting high-level event as a tool input. |

## 3. The module's actual interface (integration contract)

The single integration point is the **Python tool interface**:

- A tool is a Python function decorated with `@ray.remote`.
- It takes a single argument `input_dict` (a `dict`); the agent injects
  `tool_call_id` and `thread_id` into it.
- It returns a **JSON-serialisable** value (a `dict` or `str` is recommended).
- The agent discovers, selects and invokes tools through its ReAct loop, and
  dispatches them as parallel, non-blocking Ray tasks.

Any ARISE interface in the table above can therefore be bridged by wrapping its
client in such a tool, **without modifying the module**.

## 4. Example: bridging a ROS 2 action as a tool

The following sketch shows how a ROS 2 client would be exposed to the agent as a
tool (the ROS 2 dependency lives entirely in the tool, not in the module):

```python
import ray

@ray.remote
def execute_weld_trajectory(input_dict: dict = None) -> dict:
    """Plan and execute a welding trajectory on the cell.

    Expects a "trajectory_id" in the call arguments.
    """
    input_dict = input_dict or {}
    trajectory_id = input_dict.get("trajectory_id")

    # --- ROS 2 / Vulcanexus client code would go here ---
    # e.g. create a node, call an action server, wait for the result.
    # result = ros2_action_client.send_goal(trajectory_id)

    return {"status": "executed", "trajectory_id": trajectory_id}
```

Registering this tool (together with any perception, FIWARE or DDS bridges) is
all that is required to connect the open agent to a full ARISE-aligned system.

## 5. The VITAWELD case: how it was actually integrated

In the VITAWELD demonstrator the agent acted as the mission controller, connected to the rest of the system through a **single, pre-existing ROS 2 service**, `PlanWeldPro.srv`. This service receives a session identifier (`sid`) and a serialized task description (`task_json`) and returns a structured response (a success flag, a `result_json` payload and an error field). It is the controlled abstraction that translates chat- or web-triggered requests into executable actions, so the agent never invokes low-level functionality directly.
Everything below that service lived entirely in the ROS 2 / Vulcanexus + FastDDS layer, **outside the agent**:

- **Trajectory generation** through `LINpetition.srv`, which takes a `vitaweld_interfaces/LIN` request (a `LIN.msg` weld-segment description: `alpha`, `beta`, `distance`, `start_point`, `end_point`) and returns `moveit_msgs/RobotTrajectory` objects from the MoveIt-based planning skill.
- **Trajectory execution and runtime feedback** through `RobotStatus.msg` (robot state, execution progress, end-effector pose, TCP speed, distance to goal and safety fields).
- **Human perception** through ROS4HRI-compatible topics (the gesture-based stop) plus the safety and welding-monitoring topics.
- **External monitoring** through a Vulcanexus **DDS Router** that forwards an allowlisted subset of topics from the ROS 2 stack to the FIWARE DDS participant, where Orion-LD updates the `RobotKUKA` entity.

No intermediate Python bridge over these interfaces was built, and no ROS 2 / DDS / FIWARE logic was reimplemented. The existing `PlanWeldPro.srv` entry point was **simply exposed to the agent by registering one thin `@ray.remote` tool that calls it**. As a result:

- The agent discovers, selects and invokes that tool through its ReAct loop exactly like any other tool, **without knowing anything about ROS 2, Vulcanexus, FastDDS, DDS routing or FIWARE**.
- Because the tool is dispatched as an **asynchronous, non-blocking Ray task**, the (potentially long) planning-and-execution call runs in the background while the agent stays free to keep conversing or trigger other actions.

This records that interoperability in VITAWELD was achieved by **reusing the existing ROS 2 / Vulcanexus + FastDDS + FIWARE stack through its `PlanWeldPro.srv` service and exposing it to the agent as a single Ray tool** — confirming the design principle of Section 1: the open module remains a pure orchestrator, and all middleware lives in (or behind) the tool it invokes.