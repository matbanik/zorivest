# **Architectural Validation Report: Service Layer Design for Desktop Trading Analytics**

## **1\. Architecture Pattern Validation**

The architectural foundation of the Zorivest application currently relies on a Service Layer combined with a Unit of Work (UoW) and Repository pattern, inspired by the *Cosmic Python* methodology. This paradigm was originally conceived for distributed, multi-user web applications interfacing with high-concurrency databases like PostgreSQL. Validating this approach for a single-user, desktop-bound Python application using SQLite requires analyzing the fundamental impedance mismatch between web-first patterns and local desktop environments.

The unique constraints of Zorivest include the absence of network latency between the application and the database, the presence of a persistent stateful GUI (PySide6) whose event loop must not be blocked, and an external integration boundary defined by a TypeScript Model Context Protocol (MCP) server.

### **Comparative Architectural Analysis**

To determine the optimal foundation, the current approach is evaluated against five alternative architectural paradigms, specifically through the lens of a single-user SQLite desktop application versus a multi-user web service.

| Architecture Paradigm | Core Mechanism | Desktop (SQLite) vs. Web Service Trade-offs | Suitability for Zorivest |
| :---- | :---- | :---- | :---- |
| **Service Layer \+ UoW \+ Repo** | Orchestrates domain models and abstracts transaction boundaries and database queries. | **Web:** Essential for connection pooling and distributed transaction safety. **Desktop:** Mitigates SQLite's strict single-writer lock limitations, but risks over-abstracting simple local file I/O operations.1 | **High.** Provides necessary transaction boundaries for complex trading operations. |
| **Clean / Hexagonal** | Strict dependency inversion; domain is entirely isolated from UI and database via Ports and Adapters. | **Web:** Allows swapping databases (e.g., PostgreSQL to MongoDB) and scaling teams. **Desktop:** Introduces severe "lasagna architecture" boilerplate for a database that will never be swapped.3 | **Low.** Over-engineered for an app permanently bound to local SQLite. |
| **Vertical Slice (VSA)** | Organizes code by discrete features from the entry point down to the data access, minimizing shared layers. | **Web:** Facilitates microservice decomposition. **Desktop:** Maximizes cohesion. A single feature folder contains the PySide6 UI binding, the logic, and the SQLite query, making modification trivial.5 | **High.** Prevents file-jumping and layer bloat in standalone applications. |
| **CQRS** | Segregates read operations (Queries) from write operations (Commands) into distinct models. | **Web:** Allows independent scaling of read/write databases. **Desktop:** Offers no scaling benefits, but provides vast performance improvements for complex portfolio analytics via optimized read-only SQL views.7 | **Medium.** Useful only for heavy analytical dashboards. |
| **Transaction Script** | Procedural logic handling the request, business rules, and database calls in a single routine. | **Web:** Inadequate for complex domains; leads to duplicated logic. **Desktop:** Fast for prototyping, but becomes unmaintainable as trading analytics formulas grow in complexity.8 | **Low.** Fails to support complex mathematical portfolio operations safely. |

### **The SQLite Concurrency Constraint**

The most critical architectural differentiator between a web service and a Zorivest-style desktop app is the database engine. While web services utilize connection pooling to handle thousands of concurrent transactions, SQLite operates fundamentally differently. Even when configured with Write-Ahead Logging (WAL) mode, which allows concurrent readers, SQLite strictly enforces a single-writer lock at the database level.1

If the background TypeScript MCP server attempts to ingest a broker CSV while the user simultaneously updates a trade tag in the PySide6 GUI, a database is locked operational error will occur without proper transaction management. The Unit of Work pattern is therefore not merely a theoretical abstraction for this application; it is a mechanical necessity to serialize writes and ensure atomic commits, preventing database corruption during concurrent boundary access.

### **Recommendations and Output**

1. **Your Recommendation:** Transition from a strict horizontal Layered Architecture to a Hybrid Vertical Slice Architecture, retaining the Unit of Work for SQLite write-serialization (Confidence: High).  
2. **Supporting Evidence:** Architectural consensus indicates that strict Clean/Hexagonal architectures scatter cohesive feature logic across multiple arbitrary directories, slowing development.4 Vertical Slice Architecture (VSA) groups all artifacts that change together—such as the trade entry schema, the validation logic, and the database persistence—into a single location, which is highly advantageous for distinct use cases like trading applications.5 Furthermore, retaining the UoW is validated by SQLite's concurrency limitations, which require explicit transaction boundaries to prevent lock contention.9  
3. **Specific Code Example:** Instead of scattering logic across controllers.py, services.py, and repositories.py, a Vertical Slice encapsulates the entire operation:  
   Python  
   \# features/record\_trade/slice.py  
   from dataclasses import dataclass  
   from domain.models import Trade  
   from infrastructure.uow import SqlAlchemyUnitOfWork

   @dataclass  
   class RecordTradeCommand:  
       ticker: str  
       quantity: int  
       execution\_price: float

   class RecordTradeHandler:  
       def \_\_init\_\_(self, uow: SqlAlchemyUnitOfWork):  
           self.uow \= uow

       def execute(self, command: RecordTradeCommand) \-\> int:  
           \# Business logic and data access co-located for the slice  
           trade \= Trade(  
               ticker=command.ticker,   
               quantity=command.quantity,   
               price=command.execution\_price  
           )

           with self.uow:  
               self.uow.session.add(trade)  
               self.uow.commit()  
               return trade.id

4. **Risks or Trade-offs:** The primary risk of Vertical Slice Architecture is code duplication. Because slices are discouraged from sharing logic, developers may inadvertently copy-paste common validation or calculation routines across different features.6 This must be mitigated by aggressively pushing core business rules (like calculating trade commissions) down into pure Python domain entities that multiple slices can invoke.

## **2\. Service Granularity Analysis**

The current design features over 25 distinct service classes. In a single-user desktop application managed via a manual composition root, an abundance of fine-grained services creates severe wiring complexity and initialization overhead. This section analyzes the optimal granularity for specific service clusters.

### **Single Responsibility in TaxService**

The TaxService currently contains 8 distinct methods. Evaluating whether this violates the Single Responsibility Principle (SRP) requires understanding the definition of a "responsibility." The SRP does not mandate that a class perform only one action; rather, it dictates that a class should have only one reason to change.12

If the 8 methods in TaxService encompass operations such as FIFO cost basis matching, wash sale rule identification, and short-term versus long-term capital gains classification, they all share a singular axis of change: modifications to federal tax codes. Splitting these methods into an AmortizationService and a WashSaleService would artificially fracture highly cohesive logic, requiring simultaneous updates across multiple files whenever tax reporting requirements evolve.

### **Grouping Analytics Services**

The architecture currently isolates quantitative metrics into separate services (ExpectancyService, DrawdownService, SQNService, ExcursionService). This fragmentation is detrimental to the desktop UI, which typically requires all of these metrics simultaneously to render a unified portfolio dashboard. Furthermore, mathematical calculations do not inherently require orchestration, repository access, or state management, which are the primary mandates of an application service.

These calculations should be demoted to pure domain functions, and their orchestration should be handled by a singular facade. The Facade pattern provides a simplified, unified interface to a complex subsystem, vastly reducing the dependencies that must be injected into the PySide6 ViewModels.

### **Unifying Import Services**

The existence of a BrokerImportService and a PDFImportService suggests a procedural design that violates the Open/Closed Principle. As the trading journal expands to support multiple brokerages (e.g., Interactive Brokers, Schwab, TD Ameritrade), creating a new dedicated service for each broker will lead to infinite horizontal scaling of the composition root.

Because importing trades requires executing a family of interchangeable algorithms that yield the identical output (a normalized list of Trade entities), this subsystem is the perfect candidate for the Strategy Design Pattern.14

### **Recommendations and Output**

1. **Your Recommendation:** Retain TaxService as a unified class, refactor analytics into pure functions orchestrated by a single AnalyticsFacadeService, and unify file parsers under a TradeImportService utilizing the Strategy pattern (Confidence: High).  
2. **Supporting Evidence:** The definition of SRP supports keeping functionally cohesive rules (like tax laws) bound to a single module.12 For file importing, the Strategy pattern eliminates extensive branching logic and allows dynamic injection of parser behaviors without modifying the core service layer, adhering to the Open/Closed Principle.15 Managing 25+ services via manual dependency injection generates significant boilerplate; consolidating these through Facades and Strategies drastically reduces the instantiation payload in the composition root.16  
3. **Specific Code Example:** Unifying the import services via the Strategy Pattern:  
   Python  
   from abc import ABC, abstractmethod  
   from typing import List  
   from domain.models import Trade  
   from infrastructure.uow import AbstractUnitOfWork

   \# The Strategy Interface  
   class AbstractImportStrategy(ABC):  
       @abstractmethod  
       def extract\_trades(self, file\_path: str) \-\> List:  
           pass

   \# Concrete Strategies  
   class SchwabPDFStrategy(AbstractImportStrategy):  
       def extract\_trades(self, file\_path: str) \-\> List:  
           \# Complex PDF OCR and regex logic here  
           return

   class InteractiveBrokersCSVStrategy(AbstractImportStrategy):  
       def extract\_trades(self, file\_path: str) \-\> List:  
           \# Standard CSV parsing logic here  
           return

   \# The Unified Context/Service  
   class TradeImportService:  
       def \_\_init\_\_(self, uow: AbstractUnitOfWork):  
           self.uow \= uow

       def execute\_import(self, file\_path: str, strategy: AbstractImportStrategy) \-\> int:  
           trades \= strategy.extract\_trades(file\_path)  
           with self.uow:  
               for trade in trades:  
                   self.uow.trades.add(trade)  
               self.uow.commit()  
           return len(trades)

4. **Risks or Trade-offs:** Consolidating analytics into a single AnalyticsFacadeService means that loading the dashboard will compute all metrics simultaneously. If calculating Monte Carlo drawdowns takes several seconds, it will block the return of simpler metrics like Expectancy. This trade-off requires that the Facade service support asynchronous execution or granular querying parameters so the PySide6 UI does not freeze during calculation.

## **3\. Testing Strategy Validation**

The current exit criteria relies entirely on service-layer unit tests passing against a unittest.mock implementation of the Unit of Work, completely avoiding the database or network. While testing in isolation is a staple of theoretical software engineering, over-reliance on database mocking in SQLAlchemy environments is a recognized anti-pattern that yields fragile, low-confidence test suites.

### **Mock-Based UoW vs. In-Memory Integration Testing**

Mocking the SQLAlchemy Unit of Work requires mocking the underlying session, queries, and returned model objects. This approach fundamentally fails to verify the Object-Relational Mapping (ORM). If a SQLAlchemy model is missing a column, if a foreign key constraint is violated, or if an eager-loading configuration is incorrect, a mock-based test will pass successfully, but the application will immediately crash in production.17

Because the target architecture relies on SQLite, the traditional arguments against database integration tests (e.g., slow execution, complex container orchestration) are invalidated. SQLite can operate entirely in memory (sqlite:///:memory:). These in-memory integration tests execute in milliseconds, providing the speed of a unit test with the absolute confidence of a full stack execution.17

### **Missing Test Categories**

The proposed strategy is missing critical validation categories necessary for a desktop application integrating with an external MCP server:

1. **Contract Testing:** The MCP server operates as an external TypeScript client calling the Python application. Contract testing is required to ensure that the JSON schemas defined in the TypeScript tools precisely match the Pydantic/dataclass serialization models returned by the Python Service Layer.20  
2. **Property-Based Testing (PBT):** For quantitative trading metrics, example-based testing is mathematically insufficient. Defining a test that asserts Expectancy(\[100, \-50\]) \== 25 does not prove the algorithm handles extreme volatility, zero-division scenarios, or massive arrays without memory leaks.

### **Property-Based Testing for Math-Heavy Services**

Financial math invariants must be validated against thousands of randomized inputs. The Hypothesis library in Python is the industry standard for this.22 By declaring properties that must always hold true, the testing framework can identify edge cases that humans routinely overlook.

For example, the mathematical property of Maximum Drawdown (MDD) dictates that it represents a loss from a peak. Therefore, MDD must always be ![][image1]. Furthermore, the Kelly Criterion fraction (![][image2]) representing optimal bet sizing based on probability and win/loss ratios must remain mathematically bounded.24

### **Recommendations and Output**

1. **Your Recommendation:** Abandon unittest.mock for the UoW in favor of in-memory SQLite integration tests. Implement Property-Based Testing via Hypothesis for all analytics, and organize test files by feature/use-case rather than mapping 1:1 to service files (Confidence: High).  
2. **Supporting Evidence:** Experienced test automation architects heavily discourage mocking the database layer when the correctness of the query is relevant to the system's behavior.19 Leveraging SQLite's in-memory mode provides true integration testing without the I/O overhead.17 Furthermore, the application of Property-Based Testing using Hypothesis is widely adopted in financial technology to verify that risk calculations do not fail under unpredictable data conditions.26  
3. **Specific Code Example:** Replacing example-based unit tests with Hypothesis Property-Based Testing for the Kelly Criterion:  
   Python  
   from hypothesis import given, strategies as st  
   from domain.analytics import calculate\_kelly\_fraction

   \# Generate lists of random floats representing trade return percentages  
   @given(st.lists(st.floats(min\_value=-1.0, max\_value=5.0), min\_size=5))  
   def test\_kelly\_criterion\_invariants(returns):  
       kelly\_fraction \= calculate\_kelly\_fraction(returns)

       \# Invariant 1: Kelly fraction should never suggest leveraging beyond mathematical limits  
       \# Assuming our system caps leverage at 1.0 (100% of account)  
       assert kelly\_fraction \<= 1.0

       \# Invariant 2: If the sum of returns is negative, Kelly should never suggest allocating capital  
       if sum(returns) \<= 0:  
           assert kelly\_fraction \<= 0.0

4. **Risks or Trade-offs:** Transitioning to in-memory SQLite tests requires careful teardown procedures. If tests run concurrently via pytest-xdist, they must each provision their own isolated database memory space, otherwise state pollution will cause flaky test failures.18 Additionally, Hypothesis tests consume more CPU time than standard unit tests, which may slightly increase the CI pipeline duration.

## **4\. Domain Events Gap**

The architecture currently lacks a domain event system. When a new trade is registered via the Service Layer, secondary processes such as deduplication algorithms, round-trip matching (pairing entries and exits), and excursion enrichment (calculating Maximum Adverse Excursion) must be invoked explicitly in sequence. This procedural coupling violates the Open/Closed Principle and results in bloated service handlers.

### **Viability of an In-Process Event Bus**

Implementing a domain event bus is highly advantageous, even in a single-user desktop application. While enterprise web applications rely on heavy, distributed asynchronous message brokers (like RabbitMQ or Kafka) to achieve eventual consistency across microservices 27, a desktop app only requires an *in-process, synchronous* event dispatcher.28

The primary value of this pattern in Zorivest is decoupling the core TradeService from the various downstream analytics engines. If a user subsequently installs a plugin to calculate "Time in Trade," the new handler simply subscribes to the TradeCreated event without modifying the original service.

### **Interaction with the UoW Commit Lifecycle**

In Domain-Driven Design (DDD), an aggregate forms a strict consistency boundary. A domain event should only trigger side effects if the original state mutation is successfully persisted to the database. If the UoW rolls back due to a SQLite constraint violation, no downstream events should fire.

Therefore, the simplest and most robust implementation utilizes the "Internal Event Collection" pattern.29 The domain entities internally queue events during business operations. The Unit of Work is then modified to act as the publisher. Upon a successful commit(), the UoW sweeps the repositories for any queued events and dispatches them synchronously to registered handlers.

### **Recommendations and Output**

1. **Your Recommendation:** Implement a lightweight, synchronous, in-process event bus triggered directly by the Unit of Work's post-commit lifecycle phase (Confidence: High).  
2. **Supporting Evidence:** The internal event collection strategy is a documented best practice for achieving decoupling without introducing external message brokers.29 By having the UoW orchestrate the dispatch after persistence, the system guarantees that side effects only process valid, committed data, maintaining aggregate consistency boundaries.27  
3. **Specific Code Example:** Implementing the UoW commit hook and a simple dispatcher:  
   Python  
   from typing import Callable, Dict, List, Type  
   from dataclasses import dataclass

   @dataclass  
   class Event:  
       pass

   @dataclass  
   class TradeCreatedEvent(Event):  
       trade\_id: int

   class EventBus:  
       \_subscribers: Dict, List\[Callable\]\] \= {}

       @classmethod  
       def subscribe(cls, event\_type: Type\[Event\], handler: Callable):  
           if event\_type not in cls.\_subscribers:  
               cls.\_subscribers\[event\_type\] \=  
           cls.\_subscribers\[event\_type\].append(handler)

       @classmethod  
       def publish(cls, event: Event):  
           for handler in cls.\_subscribers.get(type(event),):  
               handler(event)  \# Executed synchronously

   class SqlAlchemyUnitOfWork:  
       \#... standard enter/exit methods...

       def commit(self):  
           self.session.commit()  
           self.\_publish\_events()

       def \_publish\_events(self):  
           \# Sweep all tracked entities in the session  
           for entity in self.session.identity\_map.values():  
               if hasattr(entity, 'events'):  
                   while entity.events:  
                       event \= entity.events.pop(0)  
                       EventBus.publish(event)

4. **Risks or Trade-offs:** Because the event bus is synchronous, if an event handler (such as a complex MFE/MAE excursion calculation) takes five seconds to execute, the original thread calling the UoW commit() will block for those five seconds.30 In a PySide6 application, if this occurs on the main thread, the GUI will freeze. Developers must ensure that computationally heavy event handlers are dispatched to background worker threads.

## **5\. Error Handling**

The existing Service Layer mixes implicit None returns, standard Python exceptions, and dictionary structures. This inconsistent contract creates immense friction at the application's external boundaries—specifically, the PySide6 UI layer and the TypeScript MCP server.

### **Exceptions vs. The Result Pattern**

While the Python ecosystem heavily leans toward "Easier to Ask for Forgiveness than Permission" (EAFP)—utilizing exceptions for control flow—this paradigm degrades rapidly at system boundaries.31 Exceptions mask the alternate execution paths of a function, forcing the consumer to guess which errors might propagate upward.32

In modern software architecture, the consensus is shifting toward the Result (or Either) pattern for predictable, expected domain failures (e.g., TradeNotFound, InsufficientDataForAnalytics), reserving native exceptions strictly for fatal, unforeseeable anomalies (e.g., DatabaseConnectionLost).32

### **Implications for the Desktop App and MCP Server**

**Context 1: PySide6 GUI Event Loop** In a Qt application, if an unhandled exception propagates through a Slot (the function connected to a UI action like a button click), it can destabilize or crash the C++ event loop, causing the application to terminate silently.34 If the Service Layer returns a Result object, the PySide6 presentation layer is forced to explicitly evaluate the is\_success property and safely render a QMessageBox to the user, ensuring GUI stability.

**Context 2: TypeScript MCP Server Serialization** The Model Context Protocol communicates via JSON-RPC. A core best practice for building MCP servers is that tools must return structured content, and expected errors should return a well-formatted schema with isError: true, rather than corrupting the standard output stream with Python traceback strings.20 If the Python Service Layer natively returns a Result dataclass, it serializes perfectly into the required MCP JSON payload, creating seamless interop with the TypeScript client.21

### **Recommendations and Output**

1. **Your Recommendation:** Standardize all Service Layer return types using a generic Result dataclass pattern for expected domain logic outcomes, reserving Python Exceptions for catastrophic infrastructure failures (Confidence: High).  
2. **Supporting Evidence:** The Result pattern explicitly declares failure modes in the function signature, eliminating the unpredictability of nested exception handling.32 Furthermore, handling known application states via Result objects avoids the performance overhead of call-stack traversal associated with throwing exceptions.36 Crucially, standardizing on a structured object maps directly to the required error-handling specifications for MCP server implementations.20  
3. **Specific Code Example:** Implementing a generic Result type that serializes easily for the MCP boundary and PySide6:  
   Python  
   from dataclasses import dataclass  
   from typing import Generic, TypeVar, Optional

   T \= TypeVar('T')

   @dataclass  
   class Result(Generic):  
       is\_success: bool  
       value: Optional \= None  
       error\_message: Optional\[str\] \= None

       @classmethod  
       def ok(cls, value: T) \-\> 'Result':  
           return cls(is\_success=True, value=value)

       @classmethod  
       def fail(cls, error\_message: str) \-\> 'Result':  
           return cls(is\_success=False, error\_message=error\_message)

       def to\_mcp\_payload(self) \-\> dict:  
           """Serializes cleanly for the TypeScript MCP Client"""  
           if not self.is\_success:  
               return {  
                   "isError": True,  
                   "content": \[{"type": "text", "text": f"Error: {self.error\_message}"}\]  
               }  
           return {  
               "isError": False,  
               "content": \[{"type": "text", "text": str(self.value)}\]  
           }

   \# Usage in a PySide6 View  
   def on\_calculate\_clicked(self):  
       result \= analytics\_service.get\_expectancy()  
       if not result.is\_success:  
           QMessageBox.warning(self, "Calculation Failed", result.error\_message)  
           return  
       self.expectancy\_label.setText(str(result.value))

4. **Risks or Trade-offs:** The primary trade-off of the Result pattern is the introduction of a slight "success tax".36 Every successful operation must instantiate and return an wrapper object, marginally increasing memory allocations compared to returning raw primitives. Furthermore, developers accustomed to standard Pythonic EAFP paradigms may find the constant checking of if not result.is\_success: verbose and repetitive, requiring disciplined code review to enforce the standard.

#### **Works cited**

1. Abusing SQLite to Handle Concurrency \- SkyPilot Blog, accessed February 27, 2026, [https://blog.skypilot.co/abusing-sqlite-to-handle-concurrency/](https://blog.skypilot.co/abusing-sqlite-to-handle-concurrency/)  
2. How to Implement the Repository Pattern in Python \- OneUptime, accessed February 27, 2026, [https://oneuptime.com/blog/post/2026-02-03-python-repository-pattern/view](https://oneuptime.com/blog/post/2026-02-03-python-repository-pattern/view)  
3. Hexagonal vs. Clean Architecture: Same Thing Different Name? : r/programming \- Reddit, accessed February 27, 2026, [https://www.reddit.com/r/programming/comments/1l7vun6/hexagonal\_vs\_clean\_architecture\_same\_thing/](https://www.reddit.com/r/programming/comments/1l7vun6/hexagonal_vs_clean_architecture_same_thing/)  
4. Understanding Hexagonal, Clean, Onion, and Traditional Layered Architectures: A Deep Dive | by Roman Glushach, accessed February 27, 2026, [https://romanglushach.medium.com/understanding-hexagonal-clean-onion-and-traditional-layered-architectures-a-deep-dive-c0f93b8a1b96](https://romanglushach.medium.com/understanding-hexagonal-clean-onion-and-traditional-layered-architectures-a-deep-dive-c0f93b8a1b96)  
5. Vertical Slice vs Clean Architecture: A Practical Comparison (2025) \- Nadir Badnjevic, accessed February 27, 2026, [https://nadirbad.dev/vertical-slice-vs-clean-architecture](https://nadirbad.dev/vertical-slice-vs-clean-architecture)  
6. Vertical Slice Architecture in .NET — From N‑Tier Layers to Feature Slices \- DEV Community, accessed February 27, 2026, [https://dev.to/cristiansifuentes/vertical-slice-architecture-in-net-from-n-tier-layers-to-feature-slices-4iha](https://dev.to/cristiansifuentes/vertical-slice-architecture-in-net-from-n-tier-layers-to-feature-slices-4iha)  
7. Best practices repository and service layer \- Software Engineering Stack Exchange, accessed February 27, 2026, [https://softwareengineering.stackexchange.com/questions/442728/best-practices-repository-and-service-layer](https://softwareengineering.stackexchange.com/questions/442728/best-practices-repository-and-service-layer)  
8. When to use Vertical Slice or Clean Architecture when developing a REST API?, accessed February 27, 2026, [https://stackoverflow.com/questions/69273524/when-to-use-vertical-slice-or-clean-architecture-when-developing-a-rest-api](https://stackoverflow.com/questions/69273524/when-to-use-vertical-slice-or-clean-architecture-when-developing-a-rest-api)  
9. Write-Ahead Logging \- SQLite, accessed February 27, 2026, [https://sqlite.org/wal.html](https://sqlite.org/wal.html)  
10. Why Vertical Slices Won't Evolve from Clean Architecture \- Rico Fritzsche, accessed February 27, 2026, [https://ricofritzsche.me/why-vertical-slices-wont-evolve-from-clean-architecture/](https://ricofritzsche.me/why-vertical-slices-wont-evolve-from-clean-architecture/)  
11. Stop Writing try/except Hell: Clean Database Transactions with SQLAlchemy with the Unit Of Work \- Dev.to, accessed February 27, 2026, [https://dev.to/dentedlogic/stop-writing-tryexcept-hell-clean-database-transactions-with-sqlalchemy-with-the-unit-of-work-hjk](https://dev.to/dentedlogic/stop-writing-tryexcept-hell-clean-database-transactions-with-sqlalchemy-with-the-unit-of-work-hjk)  
12. Does Single Responsibility Principle mean that each class should only have one method?, accessed February 27, 2026, [https://www.reddit.com/r/learnprogramming/comments/15opwvp/does\_single\_responsibility\_principle\_mean\_that/](https://www.reddit.com/r/learnprogramming/comments/15opwvp/does_single_responsibility_principle_mean_that/)  
13. A question about Single Responsibility Principle : r/learnprogramming \- Reddit, accessed February 27, 2026, [https://www.reddit.com/r/learnprogramming/comments/1kigcr1/a\_question\_about\_single\_responsibility\_principle/](https://www.reddit.com/r/learnprogramming/comments/1kigcr1/a_question_about_single_responsibility_principle/)  
14. Strategy in Python / Design Patterns \- Refactoring.Guru, accessed February 27, 2026, [https://refactoring.guru/design-patterns/strategy/python/example](https://refactoring.guru/design-patterns/strategy/python/example)  
15. Strategy Pattern in Python: Write Flexible, Clean Code | by Jan Walczak | Medium, accessed February 27, 2026, [https://medium.com/@walczak.coding/strategy-pattern-in-python-write-flexible-clean-code-98992568f84a](https://medium.com/@walczak.coding/strategy-pattern-in-python-write-flexible-clean-code-98992568f84a)  
16. 13\. Dependency Injection (and Bootstrapping) \- Cosmic Python, accessed February 27, 2026, [https://www.cosmicpython.com/book/chapter\_13\_dependency\_injection.html](https://www.cosmicpython.com/book/chapter_13_dependency_injection.html)  
17. True sqlalchemy unit testing \- Frank-Mich's Blog, accessed February 27, 2026, [https://blog.frank-mich.com/true-sqlalchemy-unit-testing/](https://blog.frank-mich.com/true-sqlalchemy-unit-testing/)  
18. Integration Testing in Depth : Test components working together (and not hate it) \- Part 3, accessed February 27, 2026, [https://billyokeyo.dev/posts/integration-testing/](https://billyokeyo.dev/posts/integration-testing/)  
19. You Probably Shouldn't Mock the Database : r/programming \- Reddit, accessed February 27, 2026, [https://www.reddit.com/r/programming/comments/11my2km/you\_probably\_shouldnt\_mock\_the\_database/](https://www.reddit.com/r/programming/comments/11my2km/you_probably_shouldnt_mock_the_database/)  
20. Building MCP servers the right way: a production-ready guide in TypeScript \- Mauro Canuto, accessed February 27, 2026, [https://maurocanuto.medium.com/building-mcp-servers-the-right-way-a-production-ready-guide-in-typescript-8ceb9eae9c7f](https://maurocanuto.medium.com/building-mcp-servers-the-right-way-a-production-ready-guide-in-typescript-8ceb9eae9c7f)  
21. modelcontextprotocol/python-sdk: The official Python SDK ... \- GitHub, accessed February 27, 2026, [https://github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)  
22. Hypothesis 6.151.8 documentation, accessed February 27, 2026, [https://hypothesis.readthedocs.io/](https://hypothesis.readthedocs.io/)  
23. Property-Based Testing in Financial Microservices with Python | by Shantanu Vashishtha, accessed February 27, 2026, [https://medium.com/@vashishthashantanu3/property-based-testing-in-financial-microservices-with-python-afa63a02d929](https://medium.com/@vashishthashantanu3/property-based-testing-in-financial-microservices-with-python-afa63a02d929)  
24. Drawdown (economics) \- Wikipedia, accessed February 27, 2026, [https://en.wikipedia.org/wiki/Drawdown\_(economics)](https://en.wikipedia.org/wiki/Drawdown_\(economics\))  
25. Kelly criterion \- Wikipedia, accessed February 27, 2026, [https://en.wikipedia.org/wiki/Kelly\_criterion](https://en.wikipedia.org/wiki/Kelly_criterion)  
26. Introduction to Property-Based Testing | by Tushar\_Trivedi \- Medium, accessed February 27, 2026, [https://medium.com/@tt3043701/introduction-to-property-based-testing-55a27aec1346](https://medium.com/@tt3043701/introduction-to-property-based-testing-55a27aec1346)  
27. Achieve domain consistency in event-driven architectures | AWS Cloud Operations Blog, accessed February 27, 2026, [https://aws.amazon.com/blogs/mt/achieve-domain-consistency-in-event-driven-architectures/](https://aws.amazon.com/blogs/mt/achieve-domain-consistency-in-event-driven-architectures/)  
28. Domain events: simple and reliable solution \- Enterprise Craftsmanship, accessed February 27, 2026, [https://enterprisecraftsmanship.com/posts/domain-events-simple-reliable-solution/](https://enterprisecraftsmanship.com/posts/domain-events-simple-reliable-solution/)  
29. Events in Domain-Driven Design: Event Propagation Strategies | by Dawid Kraczkowski, accessed February 27, 2026, [https://medium.com/@dkraczkowski/events-in-domain-driven-design-event-propagation-strategies-b30d8df046e2](https://medium.com/@dkraczkowski/events-in-domain-driven-design-event-propagation-strategies-b30d8df046e2)  
30. Domain Events in DDD — System Architecture, accessed February 27, 2026, [https://dckms.github.io/system-architecture/emacsway/it/ddd/tactical-design/domain-model/domain-events/domain-events-in-ddd.html](https://dckms.github.io/system-architecture/emacsway/it/ddd/tactical-design/domain-model/domain-events/domain-events-in-ddd.html)  
31. Built-in Exceptions — Python 3.14.3 documentation, accessed February 27, 2026, [https://docs.python.org/3/library/exceptions.html](https://docs.python.org/3/library/exceptions.html)  
32. Result pattern \- An exceptional way to handle errors — blog \- Graham Knapp, accessed February 27, 2026, [https://grahamknapp.com/blog/result-pattern-an-exceptional-way-to-handle-errors/](https://grahamknapp.com/blog/result-pattern-an-exceptional-way-to-handle-errors/)  
33. .NET Error Handling: Balancing Exceptions and the Result Pattern \- DEV Community, accessed February 27, 2026, [https://dev.to/k\_ribaric/net-error-handling-balancing-exceptions-and-the-result-pattern-ljo](https://dev.to/k_ribaric/net-error-handling-balancing-exceptions-and-the-result-pattern-ljo)  
34. Strategy for handling exceptions in property accessors | Qt Forum, accessed February 27, 2026, [https://forum.qt.io/topic/161477/strategy-for-handling-exceptions-in-property-accessors](https://forum.qt.io/topic/161477/strategy-for-handling-exceptions-in-property-accessors)  
35. Recommended error handling (try/catch or exceptions) using Pyside/Qt \- Stack Overflow, accessed February 27, 2026, [https://stackoverflow.com/questions/9607421/recommended-error-handling-try-catch-or-exceptions-using-pyside-qt](https://stackoverflow.com/questions/9607421/recommended-error-handling-try-catch-or-exceptions-using-pyside-qt)  
36. NET: Exceptions vs Result Pattern \- Performance Benchmark \- DEV Community, accessed February 27, 2026, [https://dev.to/gramli/net-throwing-exceptions-vs-result-pattern-benchmark-4a62](https://dev.to/gramli/net-throwing-exceptions-vs-result-pattern-benchmark-4a62)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAXCAYAAAAcP/9qAAABIElEQVR4XmNgGAWjgMbAHIjL0QWpAN4CcTMQewLxCSBegCILBcxAfBmIfwOxJpocqYATiDcB8VQ08RdA7IYmhgIsgPgPEJ9hgDiIVDAZiP8DsSma+FIgvo0mhgH0gXgbAyQUSLV8NwN2ixcB8Q80MbxgGhA/AeIUdAkc4DUDxGIpNHFYSJAMBBkgGrnRJdAAKFFhs7gCKk4SiATiOww4UiYaoIrFBUD8CYiF0SXwALItBmn4ygCJV1DWIBVcZIBYYIgmDkpcWC1exwDJxy7oEiQCmM/Q8+w+Boij4IARiHcC8REGSB6mFOgyQAqLTDTxmwxohQrIYmoDBQZIIQQrA1ShfFrYhQFYGSBlwEogTkWTG1ggA8R3ScAcEG2jYAgAADi1RC3fqgvwAAAAAElFTkSuQmCC>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAZCAYAAADTyxWqAAAA+0lEQVR4Xu2Tuw4BURCGRyGRiMIlcQki3kCl0krEC2hE7R20au/gKSQqUWkRCiqVhoKGRMI/mSN2J7uxFt1+yZc9mTmZPWdmlygATOEdnmBI5RIOMVdKcA9r8ALLtizRFuZUzJUN7MEmyeliJj6EdTiCaZIXvYULVHTQUIRXONAJJyIkxTI6AZLwCOdwBVv29Au+CveBr8HFeM1ycese5tkzHoQjKZINfXg2azZs3WTwPM0ZnOigX3YkU/sJ3C/u29dESYrFdcIPeZJinpr7jja86aAf+Ipj+tEkqyRfd0MnPqEDl7BL7r+RZw5wAdfm+RVZkpMVdCLgvzwAT20pH67/xzsAAAAASUVORK5CYII=>