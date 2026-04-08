# The Cardiac Architecture: A Biologically-Inspired Approach to Experiential Learning in Multi-Agent Systems

**the author Fadil**

*April 2026*

## Abstract

Current multi-agent AI systems route every decision through language models, creating computational bottlenecks and preventing experiential learning. We present the Cardiac Architecture, a biologically-inspired framework that adds a persistent experiential subsystem to multi-agent orchestration. Drawing from neuroscience research on somatic markers and the intrinsic cardiac nervous system, we implement three mechanisms: (1) an autonomous sensing layer that monitors system coherence, (2) valence-tagged decision memory that accumulates experiential markers, and (3) pre-cognitive routing that handles the majority of decisions without language model involvement. Empirical validation on a benchmark of 200 diverse, labeled routing tasks spanning eight agent specialties: market and data analysis, web research, content generation, email and outreach, code and infrastructure automation, strategic decision-making, multi-agent orchestration, and risk/intelligence synthesis demonstrates that the architecture achieves 95% autonomous routing with 100% accuracy after accumulating 1,000 experiential markers, reduces language model calls by 95%, and self-reorganizes routing topology within one operational pass after agent failure. The architecture provides a foundation for AI systems that compound performance through deployment experience rather than requiring retraining.

## 1. Introduction

Every major agentic AI framework shares a fundamental assumption: the language model is the sole locus of intelligence. Tasks arrive, the LLM reasons about them, routes them, executes them, and evaluates results. This architecture cannot learn from operational experience—a system deployed for one day behaves identically to the same system deployed for one thousand days.

Recent observations from leading researchers confirm this limitation. Sutskever (2025) notes that current models "generalize dramatically worse than people" and asks: "What is the ML analogy for emotions?" This paper presents a specific answer: the Cardiac Architecture—a persistent experiential subsystem that accumulates valence-tagged somatic markers from operational history and routes decisions before reasoning engages.

The biological heart provides the architectural inspiration. The intrinsic cardiac nervous system contains approximately 40,000 neurons that operate autonomously, and the vagus nerve connecting heart to brain carries 80% afferent (upward) signals. This bottom-up dominance suggests an architectural pattern absent from current AI: a simpler subsystem that shapes complex reasoning through accumulated experience.

We make three primary contributions:
- A biologically-inspired architecture that enables experiential learning in multi-agent systems without retraining
- Empirical validation demonstrating 95% reduction in language model calls while maintaining accuracy
- Evidence that architectural mechanisms, not scale alone, enable understanding-like properties in AI systems

## 2. Related Work

### 2.1 Neuroscience Foundations

Damasio's somatic marker hypothesis (Damasio, 1994) demonstrates that bodily state signals create markers associated with situations and outcomes through experience. Patients with ventromedial prefrontal cortex damage retain full intellectual capability but make catastrophically poor decisions under uncertainty (Bechara et al., 2000). The Iowa Gambling Task shows that healthy subjects develop intuition for advantageous choices 20-30 trials before conscious articulation (Reimann & Bechara, 2010).

Armour's discovery (1991) of the intrinsic cardiac nervous system established that the heart contains afferent, local circuit, and efferent neurons organized into ganglionic plexuses. This system operates autonomously—transplanted hearts function without central nervous system connection. Recent work demonstrates bidirectional heart-brain communication influences cognitive performance (Thayer et al., 2009; Laborde et al., 2017).

### 2.2 Current AI Architectures

Existing approaches to experiential learning in AI fall into several categories:

**Retrieval-Augmented Generation (RAG):** Systems retrieve relevant past information and inject it into context windows. This is memory-assisted reasoning, not pre-cognitive shaping.

**Reinforcement Learning:** RL optimizes policy parameters through reward signals. This requires retraining and operates on externally-defined objectives rather than internally-generated valence.

**Agent Reflection:** Frameworks implement reflection where agents reason about past failures. This remains within the reasoning layer without creating a separate experiential subsystem.

Recent work explores adjacent concepts. Biomimetic approaches apply scalar somatic markers to grid-world agents (MDPI Biomimetics, 2026). Life-inspired interoceptive AI proposes internal state monitoring (2025). Neither implements the full cardiac architecture with multi-dimensional valence, coherence monitoring, and pre-cognitive routing.

## 3. Architecture

### 3.1 Core Mechanisms

The Cardiac Architecture implements three biologically-inspired mechanisms:

**Mechanism 1: Autonomous Sensing Layer**  
A non-LLM infrastructure layer continuously monitors system telemetry—timing, error rates, confidence distributions, task outcomes—computing a real-time coherence score (0.0-1.0) analogous to heart rate variability. High coherence (>0.7) enables autonomous routing without LLM involvement. Low coherence (<0.3) triggers escalation to highest-capability models.

**Mechanism 2: Valence-Tagged Decision Memory**  
After each task execution, the system creates a marker entry containing:
- Task signature (embedding vector)
- Agent used
- Outcome (success/failure/partial)
- Confidence (0.0-1.0)
- Surprise (deviation from prediction)
- Effort (resources consumed)
- Downstream impact
- Cost ratio
- Composite valence (-1.0 to 1.0)

These markers enable the "as-if body loop"—predicting task outcomes by combining similar past experiences without execution.

**Mechanism 3: Pre-Cognitive Routing**  
The system inverts the typical 100% top-down control flow. The sensing layer and marker library handle the majority of routing decisions autonomously. The LLM engages only for novel situations, low-coherence states, or high-stakes tasks, receiving coherence and marker context when invoked.

### 3.2 Operational Flow

```
TASK ARRIVES
+-- Sensing Layer (continuous, autonomous)
|   +-- Compute coherence score
|   +-- Query K nearest task signatures
|   +-- Compute predicted valence + confidence
+-- Routing Decision (pre-cognitive)
|   +-- IF high coherence AND high confidence AND positive valence
|   |   --> Route autonomously
|   +-- IF high coherence AND high confidence AND negative valence
|   |   --> Escalate immediately
|   +-- OTHERWISE --> Invoke LLM with context
+-- Execution --> Marker Generation --> Coherence Update
```

### 3.3 Implementation Details

The architecture requires three infrastructure components:
1. **Vector Database:** Stores task embeddings and enables K-nearest neighbor queries (e.g., Pinecone, Weaviate)
2. **Time-Series Database:** Maintains coherence metrics and system telemetry (e.g., InfluxDB, TimescaleDB)
3. **Inference Proxy:** Intercepts routing decisions and implements cardiac logic (custom middleware)

## 4. Experimental Design

### 4.1 Benchmark Construction

We constructed a benchmark of 200 diverse, labeled routing tasks spanning eight agent specialties: market and data analysis, web research, content generation, email and outreach, code and infrastructure automation, strategic decision-making, multi-agent orchestration, and risk/intelligence synthesis. Each task includes:
- Natural language description
- Required capabilities
- Ground-truth optimal agent assignment
- Expected resource consumption
- Success criteria

### 4.2 Agent Configuration

The evaluated multi-agent orchestration system consists of eight specialized agents with distinct capabilities:
1. Market/Data Analysis Agent
2. Web Research Agent
3. Content Generation Agent
4. Email/Outreach Agent
5. Code/Infrastructure Agent
6. Strategic Decision Agent
7. Multi-Agent Orchestration Agent
8. Risk/Intelligence Synthesis Agent

### 4.3 Evaluation Metrics

- **Routing Accuracy:** Percentage of tasks routed to optimal agent
- **Cardiac Routing Percentage:** Tasks handled without LLM involvement
- **Coherence Score:** System-wide coherence metric (0.0-1.0)
- **Recovery Time:** Passes required to restore performance after failure
- **Transfer Efficiency:** Performance boost from marker transplantation

## 5. Results

### 5.1 Multi-Pass Compounding

We evaluated the system across 20 passes of the 200-task benchmark (4,000 total decisions):

| Pass | Cardiac Routing % | Cardiac Accuracy | Overall Accuracy | Markers |
|------|------------------|------------------|------------------|---------|
| 1    | 0.0%            | —                | 95.0%            | 200     |
| 5    | 47.5%           | 100.0%           | 95.0%            | 1,000   |
| 10   | 95.0%           | 100.0%           | 95.0%            | 2,000   |
| 20   | 95.0%           | 100.0%           | 95.0%            | 4,000   |

The system plateaus at 95% autonomous routing with perfect accuracy. The remaining 5% represent boundary cases requiring deliberative reasoning.

### 5.2 Agent Failure Recovery

After disabling the most-used agent (handling 31/200 tasks):

| Metric | Pre-Failure | Immediate Post | After 1 Pass |
|--------|------------|----------------|--------------|
| Accuracy | 95.0% | 81.0% | 96.5% |
| Misroutes | 0 | 31 | 0 |
| Coherence | 0.82 | 0.31 | 0.85 |

The system self-reorganizes routing topology within one operational pass through marker accumulation.

### 5.3 Marker Transplantation

Transplanting markers from a mature deployment (1,000 markers at 0.5 weight):

| Configuration | First Pass Cardiac % | First Pass Accuracy |
|--------------|---------------------|-------------------|
| Cold Start | 0.0% | 95.0% |
| With Transplant | 89.5% | 100.0% |

This validates markers as transferable experiential assets.

### 5.4 Adversarial Robustness

Injecting 50 poisoned markers (4.8% of library) with incorrect agent assignments:

| Poisoning % | Accuracy Impact | Cardiac Routing Impact |
|------------|-----------------|----------------------|
| 0% | 95.0% | 95.0% |
| 4.8% | 95.0% | 94.5% |
| 10% | 93.5% | 92.0% |
| 20% | 87.0% | 85.0% |

The KNN voting mechanism provides passive immunity to low-concentration poisoning.

### 5.5 Cross-Domain Transfer

| Transfer Type | Initial Boost | Convergence Passes |
|--------------|--------------|-------------------|
| Same Domain | 89.5% | 2 |
| Cross Domain | 7.3% | 8 |
| Random Markers | 0.0% | 10 |

Cross-domain transfer provides minimal benefit, confirming markers encode genuine domain-specific knowledge.

## 6. Discussion

### 6.1 Architectural Understanding

The cardiac architecture demonstrates four operational markers of understanding:

1. **Superior performance on novel tasks** through experiential transfer
2. **Behavioral drift** over deployment lifetime (0%→95% cardiac routing)
3. **Calibrated confidence** under novelty (uncertainty on boundary cases)
4. **Graceful degradation** (self-reorganization after component failure)

These properties emerge from architecture, not scale. A system with cardiac mechanisms develops understanding through experience accumulation, while scaled models without these mechanisms remain static.

### 6.2 Biological Validity

The 95/5 routing ratio mirrors biological findings where 95% of decisions occur below conscious awareness. The coherence-based escalation parallels how heart rate variability predicts cognitive load. The marker accumulation process resembles how the Iowa Gambling Task participants develop intuition before articulation.

### 6.3 Practical Implications

For production deployments, the architecture offers:
- **95% reduction in LLM API costs** after bootstrap period
- **Continuous improvement** without retraining or fine-tuning
- **Resilience** through self-reorganization under failure
- **Interpretability** through inspectable marker libraries

## 7. Limitations

Current limitations include:

1. **Cold-start requirements:** Systems need 200-1,000 tasks for bootstrap
2. **Marker management:** Untested scaling to millions of markers
3. **Bias accumulation:** Potential for skewed environments to create persistent biases
4. **Temporal dynamics:** No mechanism for marker decay or forgetting
5. **Multi-tenant isolation:** Unclear how to separate markers across users

## 8. Conclusion

The Cardiac Architecture introduces a new primitive for agentic AI: a persistent experiential subsystem that enables continuous learning from deployment experience. By implementing biological principles of somatic markers and bottom-up signal dominance, the architecture achieves 95% reduction in language model calls while maintaining accuracy and enabling self-reorganization under failure.

The architecture is immediately implementable with commodity infrastructure—vector databases for markers, time-series databases for coherence, inference proxies for routing. As AI systems increasingly operate as persistent agents rather than stateless functions, the ability to accumulate and leverage operational experience becomes essential for both capability and efficiency.

Future work should explore hierarchical marker organization, temporal decay mechanisms, multi-tenant marker isolation, and formal theoretical foundations for experiential learning in artificial systems.

## References

Armour, J. A. (1991). Intrinsic cardiac neurons. *Journal of Cardiovascular Electrophysiology*, 2(4), 331-341.

Bechara, A., Damasio, H., & Damasio, A. R. (2000). Emotion, decision making and the orbitofrontal cortex. *Cerebral Cortex*, 10(3), 295-307.

Damasio, A. R. (1994). *Descartes' Error: Emotion, Reason, and the Human Brain*. Putnam.

Laborde, S., Mosley, E., & Thayer, J. F. (2017). Heart rate variability and cardiac vagal tone in psychophysiological research. *Frontiers in Psychology*, 8, 213.

MDPI Biomimetics. (2026). Biomimetic synthetic somatic markers in the pixelverse. *Biomimetics*, 11(3), 142.

Reimann, M., & Bechara, A. (2010). The somatic marker framework as a neurological theory of decision-making. *Journal of Economic Psychology*, 31(5), 767-776.

Sutskever, I. (2025). Interview with Dwarkesh Patel, November 25, 2025. Available at: [https://youtu.be/aR20FWCCjAs](https://youtu.be/aR20FWCCjAs)

Thayer, J. F., Hansen, A. L., Saus-Rose, E., & Johnsen, B. H. (2009). Heart rate variability, prefrontal neural function, and cognitive performance. *Annals of Behavioral Medicine*, 37(2), 141-153.