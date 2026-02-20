# **Architectural Design for a Local-First Agentic Investment Platform**

## **1\. Introduction: The Convergence of Local-First Software and Agentic AI**

The contemporary landscape of personal finance software is characterized by a dichotomy between secure, offline spreadsheet-based methods and cloud-native, automated SaaS platforms. The former offers privacy and control but lacks automation; the latter offers convenience but introduces latency, vendor lock-in, and significant privacy exposure. A third paradigm is emerging: **Local-First Agentic Architecture**. This approach leverages the increasing computational power of edge devices to run sophisticated AI agents locally, granting them autonomous control over sensitive data without that data ever leaving the user's machine.

This document details the technical architecture for a desktop-based personal investment management system built on the Electron and Python/FastAPI stack. The core differentiator of this system is its **Scheduling & Pipeline System**, designed to be authored and managed by an Artificial Intelligence (AI) agent via the Model Context Protocol (MCP). Unlike traditional systems where workflows are hard-coded by developers, this architecture treats the workflow policy as a dynamic asset—a JSON document authored by the AI, stored in a local SQLite database, and executed by a deterministic engine.

The design philosophy prioritizes **determinism**, **persistence**, and **safety**. By treating the AI as an untrusted author of executable logic, the system requires a rigorous validation layer, a robust state machine for execution, and a sandboxed environment for side effects. This report explores the implementation of these components, drawing on established patterns such as the Amazon States Language (ASL) for schema definition 1, the Saga pattern for transactional integrity 2, and SQLite's advanced concurrency features for state persistence.3

## **2\. JSON Policy Schema Design**

The JSON Policy Schema serves as the contract between the probabilistic reasoning of the Large Language Model (LLM) and the deterministic execution environment of the Python backend. This schema must be expressive enough to capture complex investment logic—such as conditional rebalancing, iterative trade execution, and error handling—while remaining rigid enough to ensure validation and safe execution.

### **2.1. Schema Philosophy and Structural Foundations**

The schema design creates a Domain-Specific Language (DSL) tailored for investment workflows. It adopts a declarative approach, specifying *what* state transitions should occur rather than *how* they are implemented. This separation of concerns is critical for AI-authored workflows, as it prevents the agent from needing to understand the underlying Python implementation details.

The structure is modeled after a Directed Acyclic Graph (DAG), although controlled cycles are permitted for retries and iteration. The schema borrows heavily from the **Amazon States Language (ASL)** and **Windmill OpenFlow** specifications, optimizing them for a local, single-process environment. ASL’s rigorous definition of state transitions and data passing provides a battle-tested framework for defining robust state machines.1 Similarly, concepts from Windmill’s OpenFlow, such as input transforms and suspendable steps, are integrated to support human-in-the-loop interactions, which are essential for sensitive financial operations.6

#### **2.1.1. The Root Definition**

The policy document is a JSON object that encapsulates metadata, trigger definitions, and the state machine definition.

| Field | Type | Description |
| :---- | :---- | :---- |
| policy\_id | String (UUID) | Unique identifier for the policy. |
| version | String (SemVer) | The version of the policy logic, facilitating migration and rollback. |
| schema\_version | String (URI) | The version of the underlying JSON schema used for validation (e.g., v1.2). |
| triggers | Array\[Object\] | Defines the temporal or event-based conditions that initiate execution. |
| context\_defaults | Object | Default values for the global execution context. |
| start\_at | String | The name of the initial state to execute. |
| states | Object | A dictionary mapping state names to state definitions. |
| timeout\_seconds | Integer | Global timeout for the entire workflow execution. |

The triggers array allows the agent to define multiple entry points for a single policy. For example, a "Portfolio Rebalance" policy might be triggered by a Cron schedule (e.g., "Every Friday at 4 PM") or by a webhook event (e.g., "When cash deposit \> $1000").7

### **2.2. State Definitions and Polymorphism**

The core logic resides within the states object. Each key represents a unique state name, and the value is an object defining the state's behavior. The schema utilizes a polymorphic type field to distinguish between different state behaviors.

#### **2.2.1. Task State (type: "Task")**

The Task state represents a unit of work performed by the system. It maps directly to a registered function in the backend.

JSON

"FetchMarketData": {  
  "type": "Task",  
  "resource": "market.fetch\_prices",  
  "input\_path": "$.target\_tickers",  
  "parameters": {  
    "provider": "yfinance",  
    "interval": "1d",  
    "symbols.$": "$$.execution.input"  
  },  
  "result\_path": "$.market\_data",  
  "retry": \[ { "error\_equals": \["NetworkError"\], "max\_attempts": 3 } \],  
  "next": "CalculateDrift"  
}

* **resource**: Identifies the specific tool or function to execute. This string corresponds to a key in the Step Type Registry.  
* **parameters**: Defines the arguments passed to the function. The schema supports strict typing here, distinguishing between static values and dynamic reference paths (denoted by the .$ suffix convention from ASL).8  
* **retry**: Defines declarative error handling policies, allowing the workflow to recover from transient failures (e.g., API rate limits) without failing the entire execution.5

#### **2.2.2. Choice State (type: "Choice")**

The Choice state introduces branching logic. It evaluates the workflow's data context against a set of boolean expressions.

JSON

"CheckDrift": {  
  "type": "Choice",  
  "choices":,  
  "default": "NoActionRequired"  
}

This state is crucial for AI agents, as it allows them to encode decision trees directly into the workflow. The variable field uses JSONPath to reference data from previous steps.1

#### **2.2.3. Map State (type: "Map")**

The Map state allows for concurrent or sequential processing of a list of items. In a local investment app, this is typically used to iterate over a list of orders to execute them one by one.

* **items\_path**: JSONPath pointing to the array to iterate over.  
* **iterator**: A sub-workflow definition applied to each item.  
* **max\_concurrency**: Controls how many iterations run in parallel. In a single-process Python app, this manages the size of the asyncio task group.10

### **2.3. Data Flow and Context Management**

A critical aspect of the schema is managing how data flows between steps. The execution engine maintains a JSON object representing the **Execution Context**.

* **InputPath**: Filters the global context to pass only relevant data to a specific step. This reduces the risk of leaking sensitive information (e.g., API keys) into steps that don't need them.5  
* **ResultSelector**: Allows transformation of a step's raw output before it is merged into the context. This is useful for normalizing data from different API providers.  
* **ResultPath**: Specifies where in the global context the step's output should be written. This essentially appends data to the state, building up a comprehensive record of the execution.4

### **2.4. JSON Schema for Validation**

To ensure that the AI generates valid policies, the application utilizes a rigorous meta-schema (Draft 2020-12). This schema is used both for runtime validation and to provide context to the LLM.

**Validation Strategy:**

1. **Structural Validation**: Ensures required fields (type, next) are present and valid types.  
2. **Referential Integrity**: Custom validators check that every state referenced in next or default fields actually exists within the states object.  
3. **Cyclic Dependency Checks**: While loops are permitted via specific constructs, unintended infinite loops in the graph structure are detected using topological sorting algorithms (e.g., Kahn's algorithm or DFS-based cycle detection) during the validation phase.11

By enforcing these constraints at the schema level, the system minimizes runtime errors and "hallucinations" where the AI invents non-existent step types or invalid transitions.13

## **3\. Step Type Registry & Extensibility**

The Step Type Registry acts as the interface between the abstract JSON definitions and the concrete Python implementation. It serves as a dynamic catalog of capabilities that the AI agent can discover and utilize.

### **3.1. The Registry Pattern and Decorators**

The registry is implemented as a singleton utilizing the **Registry Pattern**. Python's decorator syntax provides an elegant mechanism for registering functions.

Python

class StepRegistry:  
    \_registry \= {}

    @classmethod  
    def register(cls, name: str, description: str, side\_effect: bool \= False):  
        def decorator(func):  
            \# Introspection and validation logic here  
            cls.\_registry\[name\] \= ToolDefinition(  
                func=func,  
                name=name,  
                description=description,  
                schema=cls.\_generate\_schema(func),  
                side\_effect=side\_effect  
            )  
            return func  
        return decorator

This approach allows developers to define steps as standard Python functions. The @register decorator handles the metadata extraction, ensuring that the function is indexed by its unique name.15

### **3.2. Automated Schema Generation with Pydantic**

To enable the AI agent to use these tools effectively, strict input and output schemas are required. We utilize **Pydantic v2** to automate this process. By annotating function arguments with Pydantic models, we can generate compliant JSON Schemas on the fly.

Python

from pydantic import BaseModel, Field

class OrderParams(BaseModel):  
    ticker: str \= Field(..., description="The stock symbol to trade")  
    quantity: int \= Field(..., gt=0, description="Number of shares")  
    side: Literal

@StepRegistry.register("trade.execute", "Executes a market order")  
async def execute\_trade(params: OrderParams) \-\> TradeResult:  
    \# Implementation  
    pass

The StepRegistry inspects execute\_trade, extracts OrderParams, and converts it into a JSON Schema. This schema is then exposed to the MCP server, allowing the AI to understand exactly what parameters are required, their types, and constraints (e.g., quantity \> 0).17 This eliminates the need for manual documentation maintenance and ensures that the AI's understanding of the toolset is always synchronized with the code.

### **3.3. MCP Tool Discovery and Dynamic Registration**

The Model Context Protocol (MCP) requires a mechanism to list available tools. The Step Registry serves as the source of truth for this tools/list operation.

When the MCP client (the IDE or AI agent) connects:

1. The server queries the StepRegistry.  
2. It serializes each ToolDefinition into the MCP Tool format, including name, description, and inputSchema.  
3. The client receives this list and uses it to prompt the LLM.19

This dynamic registration is crucial for extensibility. If a user adds a new plugin (e.g., a "Crypto Wallet" integration), the plugin simply defines new functions decorated with @register. Upon application restart (or hot-reload), these new tools automatically appear in the registry and become available to the AI agent without any changes to the core MCP server code.19

### **3.4. Extensibility via typing.Protocol and Plugins**

To support a local-first ecosystem where users might share custom steps, the system implements a plugin architecture based on Python's importlib and typing.Protocol.

* **Plugin Discovery**: The application scans a user-writable plugins/ directory at startup.  
* **Protocol Enforcement**: A WorkflowStep Protocol defines the expected signature of valid steps. This ensures that third-party plugins adhere to the structural requirements of the execution engine (e.g., accepting a context object, returning a serializable result).15  
* **Safety**: Steps loaded from plugins are flagged. The Execution Engine can apply stricter timeouts or authorization scopes to these untrusted steps (discussed further in Section 5).

## **4\. Pipeline Execution Engine**

The Execution Engine is the runtime environment responsible for interpreting the JSON policy, managing state transitions, and executing the registered Python functions. In a single-process desktop application, efficient concurrency management is paramount to prevent blocking the UI thread.

### **4.1. Asyncio Event Loop Architecture**

The engine is built upon Python's asyncio library. Each running policy is encapsulated in a WorkflowExecution object, managed by a central Engine class.

* **Event Loop**: The engine runs on the main asyncio event loop. It polls the database for pending jobs and spawns asyncio.Task objects for execution.  
* **Non-Blocking I/O**: All network-bound steps (e.g., fetching market data, executing trades) are defined as async def functions. This allows the application to remain responsive while waiting for external API responses.10  
* **CPU-Bound Operations**: Heavy calculations (e.g., portfolio optimization algorithms) are offloaded to a ProcessPoolExecutor or ThreadPoolExecutor. This prevents the "Stop-the-World" effect where a heavy calculation freezes the GUI.24

### **4.2. State Machine Implementation**

The engine implements a Finite State Machine (FSM). It maintains a pointer to the current\_state\_name and the execution\_context.

1. **State Entry**: When entering a state (e.g., "FetchData"), the engine retrieves the definition from the policy.  
2. **Input Processing**: It applies the InputPath JSONPath query to extract the necessary data from the global context.9  
3. **Execution**: It resolves the resource string to a Python function via the Registry and awaits its execution.  
4. **Output Processing**: The result is filtered via ResultSelector and merged back into the context via ResultPath.  
5. **Transition**: The engine evaluates the next field (or Choice logic) to determine the subsequent state. If end: true is encountered, the execution terminates.6

### **4.3. Persistence with SQLite and WAL Mode**

Unlike cloud-based workflow engines that might use Redis or DynamoDB, this local-first app relies on SQLite. To achieve high throughput and concurrency without locking issues, the database is configured in **Write-Ahead Logging (WAL)** mode.

* **WAL Mode**: Enabling PRAGMA journal\_mode=WAL; allows simultaneous readers and writers. This is critical because the UI (reader) might be querying the portfolio status while the execution engine (writer) is updating the workflow state.3  
* **Checkpointing**: The state is persisted after *every* step transition. The workflow\_executions table stores the serialized context JSON and the current\_step. This ensures that if the application crashes or the user quits, the workflow can resume exactly where it left off (Durable Execution).27

**Table Structure:**

SQL

CREATE TABLE workflow\_executions (  
    id TEXT PRIMARY KEY,  
    policy\_id TEXT NOT NULL,  
    status TEXT CHECK(status IN ('PENDING', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED')),  
    current\_step TEXT,  
    context JSON,  
    created\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP,  
    updated\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP  
);

### **4.4. Sequential Pipeline Logic**

While asyncio allows for concurrency, the logical flow of a single investment pipeline is typically sequential (Fetch Data \-\> Analyze \-\> Trade). The engine enforces this sequence via await. However, for Map states (processing a list of stocks), the engine can dynamically create a TaskGroup to process items in parallel, up to a configurable max\_concurrency limit, effectively utilizing the machine's network bandwidth.10

## **5\. Edge Cases & Failure Modes**

Reliability in a local desktop environment is significantly more challenging than in a managed cloud environment. The system must contend with the computer going to sleep, the user quitting the app mid-execution, and network instability.

### **5.1. APScheduler and the "Lost Job" Problem**

A known issue with APScheduler using persistent job stores (like SQLAlchemyJobStore with SQLite) is the handling of missed jobs during downtime. If the application is closed when a scheduled job triggers, APScheduler's behavior depends on the misfire\_grace\_time and coalesce settings. Furthermore, using replace\_existing=True when adding jobs can inadvertently reset the next\_run\_time, causing the scheduler to "forget" the missed execution.29

**Mitigation Strategy:**

1. **Startup Audit**: Upon application startup, a specialized routine queries the apscheduler\_jobs table before the scheduler starts. It compares the stored next\_run\_time with the current wall-clock time.  
2. **Manual Catch-Up**: If a job is found to be in the past (beyond the grace period), the system manually creates an immediate, one-off trigger for that job. This ensures that a daily portfolio rebalance is not skipped just because the user opened their laptop at 10:00 AM instead of 9:00 AM.29  
3. **Configuration**: We enforce a strict policy of coalesce=True to prevent a flood of piled-up jobs (e.g., hourly checks running 20 times at once after a weekend) and set a generous misfire\_grace\_time (e.g., 1 hour).30

### **5.2. System Sleep and Time Drift**

asyncio.sleep() is relative and can be paused by system sleep/hibernate cycles. A 10-minute sleep might turn into 8 hours if the lid is closed.

* **Absolute Scheduling**: The engine avoids asyncio.sleep() for long durations. Instead, it relies on APScheduler (which calculates based on system clock time) or calculates the target resume time as a UTC timestamp.  
* **Wake Detection**: The Electron main process listens for system power events (suspend/resume) and notifies the Python backend via IPC. On resume, the backend immediately forces a "heartbeat" check of all pending workflows to correct any drift.31

### **5.3. Handling Zombie States**

If the process is killed (SIGKILL) or power is lost, a workflow might remain in the RUNNING state in the database forever.

**Recovery Mechanism:**

On startup, the engine scans for RUNNING executions. Since we are in a single-process environment, any "running" execution found at startup *must* be a zombie from a previous crash.

* **Idempotency Check**: The engine checks the saga\_log (see Section 6\) to see if the last step had side effects.  
* **Auto-Resume**: If the last step was read-only (e.g., "FetchData"), the engine rewinds the state to the beginning of that step and resumes.  
* **Safe-Fail**: If the last step was a side-effect (e.g., "SubmitOrder"), the workflow is transitioned to PAUSED/ERROR requiring user intervention to prevent duplicate orders.27

## **6\. Security & Guardrails**

Allowing an AI agent to author and execute code-equivalent policies on a user's machine introduces significant security risks. The architecture employs a "Defense in Depth" strategy.

### **6.1. SQLite Sandboxing via Authorizers**

The AI agent, or the policies it generates, should never have unfettered access to the database. We utilize SQLite's set\_authorizer hook to enforce fine-grained access control at the connection level.

Python

def strict\_authorizer(action, arg1, arg2, db\_name, source):  
    if action \== sqlite3.SQLITE\_DELETE and arg1 \== 'user\_portfolio':  
        return sqlite3.SQLITE\_DENY  \# Prevent deletion of critical data  
    if action \== sqlite3.SQLITE\_DROP\_TABLE:  
        return sqlite3.SQLITE\_DENY  \# Prevent schema destruction  
    return sqlite3.SQLITE\_OK

This authorizer is attached to the database connection used by the execution engine. It ensures that even if a malicious or hallucinating agent injects SQL logic (e.g., via a poorly sanitized parameter), the database engine itself rejects destructive operations like DROP TABLE or accessing internal system tables.32

### **6.2. MAPL-Inspired Policy Binding**

Drawing on the **Model-Agnostic Policy Language (MAPL)** concept, the system enforces "Intent Verification".34

* **Policy Attachment**: Every sensitive tool (e.g., trade.execute) is wrapped with a policy decorator. This policy defines limits (e.g., "Max trade value \< $5000").  
* **Cryptographic Binding**: When the agent authors a policy, the JSON document is hashed. This hash is signed (or effectively pinned) to the user's approval. The execution engine verifies this hash before running the policy, ensuring that the executed logic matches exactly what the user reviewed, mitigating "Time-of-Check to Time-of-Use" attacks.34

### **6.3. Step Registry Sandboxing**

The Registry acts as a whitelist. The policy document cannot execute arbitrary Python code; it can *only* call functions explicitly registered in the StepRegistry.

* **No Eval**: The system strictly forbids eval() or exec() usage within the engine.  
* **Type Guardrails**: Pydantic validation ensures that a string passed to a quantity parameter is rejected if it doesn't parse to a positive integer, preventing type-confusion attacks.21

## **7\. Saga Pattern Adaptation**

In a distributed system, the Saga pattern manages long-running transactions across microservices. In our monolithic desktop app, we adapt this pattern to handle "distributed" interactions with *external* APIs (brokerages, banks) which do not support ACID transactions.

### **7.1. Orchestration-Based Saga**

We utilize the **Orchestration** variant of the Saga pattern. The Pipeline Execution Engine acts as the Orchestrator.

* **Compensating Actions**: Every step definition in the registry that produces a side effect (e.g., buy\_stock) must define a corresponding compensating\_action (e.g., sell\_stock).  
* **Saga Log**: As the workflow executes, every successful side-effect step pushes an entry to a persistent saga\_log in the database. This log records the step ID, the action taken, and the input parameters required to reverse it.2

### **7.2. Failure Recovery and Compensation**

If a step fails (and retries are exhausted), the engine triggers the **Compensation Workflow**:

1. **Pivot Point**: The engine identifies the point of failure.  
2. **Reverse Iteration**: It reads the saga\_log in reverse order.  
3. **Execution**: It executes the registered compensating\_action for each entry.

For example, if a rebalancing policy successfully sells Apple stock but fails to buy Microsoft stock due to a network error, the Saga logic ensures the system doesn't leave the user with uninvested cash. It triggers the compensation (re-buying Apple stock) to restore the portfolio to its initial state, or, if configured, creates a "Manual Intervention" alert for the user.38

## **8\. Real-World Examples**

### **8.1. Example: Monthly Rebalancing with Volatility Guardrail**

This policy demonstrates the use of triggers, conditional logic (Choice), and external data fetching (Task).

JSON

{  
  "name": "Volatility-Aware Rebalance",  
  "triggers": \[{ "type": "cron", "expression": "0 9 1 \* \*" }\],  
  "start\_at": "GetVIX",  
  "states": {  
    "GetVIX": {  
      "type": "Task",  
      "resource": "market.get\_quote",  
      "parameters": { "symbol": "^VIX" },  
      "result\_path": "$.vix\_data",  
      "next": "CheckVolatility"  
    },  
    "CheckVolatility": {  
      "type": "Choice",  
      "choices": \[  
        {  
          "variable": "$.vix\_data.price",  
          "numeric\_greater\_than": 30,  
          "next": "NotifyHighVol"  
        }  
      \],  
      "default": "CalculateDrift"  
    },  
    "NotifyHighVol": {  
      "type": "Task",  
      "resource": "notify.user",  
      "parameters": { "msg": "Rebalance skipped: High Volatility" },  
      "end": true  
    },  
    "CalculateDrift": {  
      "type": "Task",  
      "resource": "portfolio.calc\_drift",  
      "next": "ExecuteRebalance"  
    },  
    "ExecuteRebalance": {  
      "type": "Task",  
      "resource": "portfolio.rebalance\_saga",  
      "end": true  
    }  
  }  
}

### **8.2. Example: Tax-Loss Harvesting Scanner**

This workflow iterates over all holdings (Map state) to find positions with significant unrealized losses.

JSON

{  
  "name": "Tax Loss Harvester",  
  "triggers": \[{ "type": "cron", "expression": "0 16 \* \* 5" }\],   
  "start\_at": "GetPositions",  
  "states": {  
    "GetPositions": {  
      "type": "Task",  
      "resource": "broker.get\_positions",  
      "result\_path": "$.positions",  
      "next": "ScanLosses"  
    },  
    "ScanLosses": {  
      "type": "Map",  
      "items\_path": "$.positions",  
      "iterator": {  
        "start\_at": "CheckLoss",  
        "states": {  
          "CheckLoss": {  
            "type": "Choice",  
            "choices": \[  
              {  
                "variable": "$.iterator.unrealized\_pl\_pct",  
                "numeric\_less\_than": \-0.10,  
                "next": "Harvest"  
              }  
            \],  
            "default": "Pass"  
          },  
          "Harvest": {  
            "type": "Task",  
            "resource": "trade.tax\_loss\_harvest",  
            "end": true  
          },  
          "Pass": {  
            "type": "Pass",  
            "end": true  
          }  
        }  
      },  
      "end": true  
    }  
  }  
}

## **Conclusion**

This architectural design provides a rigorous blueprint for a local-first, AI-driven investment application. By synthesizing the deterministic structure of **ASL-based JSON policies**, the extensibility of a **Python Step Registry**, and the transactional safety of **Sagas** and **SQLite WAL**, the system achieves a delicate balance. It grants AI agents the agency to author sophisticated financial workflows while imposing the hard constraints necessary to ensure user safety and data integrity. This approach represents a mature, professional-grade solution to the challenges of autonomous personal finance management.

### **References**

* **JSON Schema & Validation**: 13  
* **Workflow Standards (ASL/OpenFlow)**: 1  
* **Python Registry & Plugins**: 15  
* **SQLite Concurrency & Security**: 3  
* **APScheduler & Persistence**: 29  
* **Saga Pattern**: 2  
* **MCP Protocol**: 19  
* **MAPL & Security**: 34

#### **Works cited**

1. Using Amazon States Language to define Step Functions workflows, accessed February 18, 2026, [https://docs.aws.amazon.com/en\_us/step-functions/latest/dg/concepts-amazon-states-language.html](https://docs.aws.amazon.com/en_us/step-functions/latest/dg/concepts-amazon-states-language.html)  
2. Saga Design Pattern \- Azure Architecture Center | Microsoft Learn, accessed February 18, 2026, [https://learn.microsoft.com/en-us/azure/architecture/patterns/saga](https://learn.microsoft.com/en-us/azure/architecture/patterns/saga)  
3. Using SQLite and asyncio effectively — Piccolo 1.3.2 documentation, accessed February 18, 2026, [https://piccolo-orm.readthedocs.io/en/1.3.2/piccolo/tutorials/using\_sqlite\_and\_asyncio\_effectively.html](https://piccolo-orm.readthedocs.io/en/1.3.2/piccolo/tutorials/using_sqlite_and_asyncio_effectively.html)  
4. Using Amazon States Language to define Step Functions workflows, accessed February 18, 2026, [https://docs.aws.amazon.com/step-functions/latest/dg/concepts-amazon-states-language.html](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-amazon-states-language.html)  
5. Processing input and output in Step Functions \- AWS Documentation, accessed February 18, 2026, [https://docs.aws.amazon.com/step-functions/latest/dg/concepts-input-output-filtering.html](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-input-output-filtering.html)  
6. OpenFlow \- Windmill, accessed February 18, 2026, [https://www.windmill.dev/docs/openflow](https://www.windmill.dev/docs/openflow)  
7. Schema reference guide for trigger and action types in Azure Logic Apps, accessed February 18, 2026, [https://docs.azure.cn/en-us/logic-apps/logic-apps-workflow-actions-triggers](https://docs.azure.cn/en-us/logic-apps/logic-apps-workflow-actions-triggers)  
8. Intrinsic functions for JSONPath states in Step Functions \- AWS Documentation, accessed February 18, 2026, [https://docs.aws.amazon.com/step-functions/latest/dg/intrinsic-functions.html](https://docs.aws.amazon.com/step-functions/latest/dg/intrinsic-functions.html)  
9. Example: Manipulating state data with paths in Step Functions workflows, accessed February 18, 2026, [https://docs.aws.amazon.com/step-functions/latest/dg/input-output-example.html](https://docs.aws.amazon.com/step-functions/latest/dg/input-output-example.html)  
10. Async \- python-statemachine 2.6.0, accessed February 18, 2026, [https://python-statemachine.readthedocs.io/en/latest/async.html](https://python-statemachine.readthedocs.io/en/latest/async.html)  
11. NetworkX for Python — A Practical Guide to Cycle Detection and Connectivity Algorithms | by Sneha Jain | Jan, 2026 | Medium, accessed February 18, 2026, [https://medium.com/@jainsnehasj6/networkx-for-python-a-practical-guide-to-cycle-detection-and-connectivity-algorithms-f6025c73915d](https://medium.com/@jainsnehasj6/networkx-for-python-a-practical-guide-to-cycle-detection-and-connectivity-algorithms-f6025c73915d)  
12. Topological Sorting Algorithms \- Meegle, accessed February 18, 2026, [https://www.meegle.com/en\_us/topics/algorithm/topological-sorting-algorithms](https://www.meegle.com/en_us/topics/algorithm/topological-sorting-algorithms)  
13. How JSON Schema Works for LLM Data \- Latitude.so, accessed February 18, 2026, [https://latitude.so/blog/how-json-schema-works-for-llm-data](https://latitude.so/blog/how-json-schema-works-for-llm-data)  
14. Why structured outputs / strict JSON schema became non-negotiable in production agents, accessed February 18, 2026, [https://www.reddit.com/r/AI\_Agents/comments/1qeetme/why\_structured\_outputs\_strict\_json\_schema\_became/](https://www.reddit.com/r/AI_Agents/comments/1qeetme/why_structured_outputs_strict_json_schema_became/)  
15. How to Build Plugin Systems in Python \- OneUptime, accessed February 18, 2026, [https://oneuptime.com/blog/post/2026-01-30-python-plugin-systems/view](https://oneuptime.com/blog/post/2026-01-30-python-plugin-systems/view)  
16. Python Registry Pattern: A Clean Alternative to Factory Classes \- DEV Community, accessed February 18, 2026, [https://dev.to/dentedlogic/stop-writing-giant-if-else-chains-master-the-python-registry-pattern-ldm](https://dev.to/dentedlogic/stop-writing-giant-if-else-chains-master-the-python-registry-pattern-ldm)  
17. JSON Schema \- Pydantic Validation, accessed February 18, 2026, [https://docs.pydantic.dev/latest/concepts/json\_schema/](https://docs.pydantic.dev/latest/concepts/json_schema/)  
18. Schema Generation for LLM Function Calling | by Xiaojing \- Medium, accessed February 18, 2026, [https://medium.com/@wangxj03/schema-generation-for-llm-function-calling-5ab29cecbd49](https://medium.com/@wangxj03/schema-generation-for-llm-function-calling-5ab29cecbd49)  
19. Practical Guide to MCP (Model Context Protocol) in Python \- DEV Community, accessed February 18, 2026, [https://dev.to/m\_sea\_bass/practical-guide-to-mcp-model-context-protocol-in-python-ijd](https://dev.to/m_sea_bass/practical-guide-to-mcp-model-context-protocol-in-python-ijd)  
20. Architecture overview \- What is the Model Context Protocol (MCP)?, accessed February 18, 2026, [https://modelcontextprotocol.io/docs/learn/architecture](https://modelcontextprotocol.io/docs/learn/architecture)  
21. Tools \- FastMCP, accessed February 18, 2026, [https://gofastmcp.com/servers/tools](https://gofastmcp.com/servers/tools)  
22. Creating and discovering plugins \- Python Packaging User Guide, accessed February 18, 2026, [https://packaging.python.org/guides/creating-and-discovering-plugins/](https://packaging.python.org/guides/creating-and-discovering-plugins/)  
23. Coroutines and Tasks — Python 3.14.3 documentation, accessed February 18, 2026, [https://docs.python.org/3/library/asyncio-task.html](https://docs.python.org/3/library/asyncio-task.html)  
24. Writing async workflows | LlamaIndex Python Documentation, accessed February 18, 2026, [https://developers.llamaindex.ai/python/llamaagents/workflows/async\_workflows/](https://developers.llamaindex.ai/python/llamaagents/workflows/async_workflows/)  
25. Amazon States Language, accessed February 18, 2026, [https://states-language.net/](https://states-language.net/)  
26. Abusing SQLite to Handle Concurrency \- SkyPilot Blog, accessed February 18, 2026, [https://blog.skypilot.co/abusing-sqlite-to-handle-concurrency/](https://blog.skypilot.co/abusing-sqlite-to-handle-concurrency/)  
27. Building a Durable Execution Engine With SQLite \- Gunnar Morling, accessed February 18, 2026, [https://www.morling.dev/blog/building-durable-execution-engine-with-sqlite/](https://www.morling.dev/blog/building-durable-execution-engine-with-sqlite/)  
28. Asyncio Coroutine Chaining in Python: Building a Sequential Workflow Engine \- Medium, accessed February 18, 2026, [https://medium.com/@diwasb54/asyncio-coroutine-chaining-in-python-building-a-sequential-workflow-engine-07c29f718c6e](https://medium.com/@diwasb54/asyncio-coroutine-chaining-in-python-building-a-sequential-workflow-engine-07c29f718c6e)  
29. APScheduler misfire testing \- python \- Stack Overflow, accessed February 18, 2026, [https://stackoverflow.com/questions/58583955/apscheduler-misfire-testing](https://stackoverflow.com/questions/58583955/apscheduler-misfire-testing)  
30. User guide — APScheduler 3.11.2.post1 documentation \- Read the Docs, accessed February 18, 2026, [https://apscheduler.readthedocs.io/en/3.x/userguide.html](https://apscheduler.readthedocs.io/en/3.x/userguide.html)  
31. Apscheduler \- scheduler keeps getting shut down : Forums \- PythonAnywhere, accessed February 18, 2026, [https://www.pythonanywhere.com/forums/topic/12884/](https://www.pythonanywhere.com/forums/topic/12884/)  
32. sqlite3 — DB-API 2.0 interface for SQLite databases — Python 3.14.3 documentation, accessed February 18, 2026, [https://docs.python.org/3/library/sqlite3.html](https://docs.python.org/3/library/sqlite3.html)  
33. SQLite Database Authorization and Access Control with Python \- Charles Leifer, accessed February 18, 2026, [https://charlesleifer.com/blog/sqlite-database-authorization-and-access-control-with-python/](https://charlesleifer.com/blog/sqlite-database-authorization-and-access-control-with-python/)  
34. Authenticated Workflows: A Systems Approach to Protecting Agentic AI \- arXiv.org, accessed February 18, 2026, [https://arxiv.org/html/2602.10465v1](https://arxiv.org/html/2602.10465v1)  
35. \[2602.10465\] Authenticated Workflows: A Systems Approach to Protecting Agentic AI, accessed February 18, 2026, [https://arxiv.org/abs/2602.10465](https://arxiv.org/abs/2602.10465)  
36. The guide to structured outputs and function calling with LLMs \- Agenta, accessed February 18, 2026, [https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms](https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms)  
37. How to Implement Saga Pattern in Python \- OneUptime, accessed February 18, 2026, [https://oneuptime.com/blog/post/2026-01-23-saga-pattern-python/view](https://oneuptime.com/blog/post/2026-01-23-saga-pattern-python/view)  
38. Temporal Unscripted: Compensating Transactions (part of Saga Pattern) in Python, accessed February 18, 2026, [https://www.youtube.com/watch?v=EUAXkqQIPXY](https://www.youtube.com/watch?v=EUAXkqQIPXY)  
39. Saga Compensating Transactions \- Temporal, accessed February 18, 2026, [https://temporal.io/blog/compensating-actions-part-of-a-complete-breakfast-with-sagas](https://temporal.io/blog/compensating-actions-part-of-a-complete-breakfast-with-sagas)  
40. jsonschema 4.26.0 documentation, accessed February 18, 2026, [https://python-jsonschema.readthedocs.io/](https://python-jsonschema.readthedocs.io/)  
41. State machine structure in Amazon States Language for Step Functions workflows, accessed February 18, 2026, [https://docs.aws.amazon.com/step-functions/latest/dg/statemachine-structure.html](https://docs.aws.amazon.com/step-functions/latest/dg/statemachine-structure.html)  
42. Using Pydantic with typing.Protocol \- Stack Overflow, accessed February 18, 2026, [https://stackoverflow.com/questions/78379572/using-pydantic-with-typing-protocol](https://stackoverflow.com/questions/78379572/using-pydantic-with-typing-protocol)  
43. How can I open a database in read-only mode by sqlite3 in python? \- Stack Overflow, accessed February 18, 2026, [https://stackoverflow.com/questions/77641477/how-can-i-open-a-database-in-read-only-mode-by-sqlite3-in-python](https://stackoverflow.com/questions/77641477/how-can-i-open-a-database-in-read-only-mode-by-sqlite3-in-python)  
44. Python sqlite3.Connection.set\_authorizer method \- ZetCode, accessed February 18, 2026, [https://zetcode.com/python/sqlite3-connection-set-authorizer/](https://zetcode.com/python/sqlite3-connection-set-authorizer/)  
45. How to optimize performance when accessing SQLite concurrently? \- Tencent Cloud, accessed February 18, 2026, [https://www.tencentcloud.com/techpedia/138374](https://www.tencentcloud.com/techpedia/138374)  
46. modelcontextprotocol/python-sdk: The official Python SDK for Model Context Protocol servers and clients \- GitHub, accessed February 18, 2026, [https://github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)