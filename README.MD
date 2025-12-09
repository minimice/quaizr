# 🎯 Problem Statement
Professional certification preparation, particularly for complex platforms like Google Cloud, faces a critical gap: learners need more than just practice questions as they need intelligent, contextual support during their learning journey.

Current quiz platforms fall short in three key ways:

- No adaptive assistance: When learners get stuck, they're left without guidance.  Hints can help in this case.
- Missing explanations: Wrong answers aren't learning opportunities.  Explanations can help to reinforce learning.
- One-size-fits-all feedback: No mechanism to understand why certain hints help.  Getting feedback on why hints work can be useful.

To address these shortcomings, I built **QuAIzR**, an app that transforms passive quiz-taking into active, guided learning through specialised AI agents.

# 💡 Solution Architecture
## Multi-Agent Design Philosophy
I architected QuAIzR using two specialised AI agents, each optimised for distinct cognitive tasks:

### Agent 1: Hint Agent (Gemini 2.5 Flash Lite)

- Purpose: Guidance without revealing answers
- Design rationale: Hints must nudge learners toward the concept without spoiling the learning moment
- Constraints: 15-word maximum to prevent information overload, No tools (prioritizing speed and cost-efficiency), Concept-focused rather than answer-focused

### Agent 2: Explanation Agent (Gemini 2.5 Flash Lite)

- Purpose: Referenced explanations for both correct and incorrect choices
- Design rationale: Learning happens when understanding why an answer is right or wrong
- Capabilities: Google Search tool for real-time documentation lookup, Provides official GCP documentation URLs, Adapts explanation based on whether answer was correct or incorrect

## Why This Agent Architecture Matters
Rather than using a single generalist agent, I separated concerns based on cognitive load and response characteristics:

- Hints require constraint: A lightweight agent without tools delivers faster responses and prevents over-explanation

- Explanations require verification: The search-enabled agent can validate claims against current documentation, reducing hallucinations

This separation also enables independent optimisation allowing me to tune each agent's performance metrics separately.

# 🔬 Innovation Highlights
## Human-in-the-Loop Quality Assurance
Every AI-generated hint includes a feedback mechanism (👍/👎). This creates a continuous improvement dataset stored in hint_feedback.csv that can provide the following benefits:
- Train evaluation rubrics for hint quality
- Identify patterns in unhelpful hints
- Enable LLM-as-judge evaluations for agent performance
- Build a foundation for supervised fine-tuning

## Observability-First Design
Integrated ADK's LoggingPlugin from the start, providing:
- Full traceability of agent decisions
- Performance metrics for each agent type
- Debugging capability for prompt engineering iterations

## Production-Ready Deployment Strategy

- Dockerized architecture: Built once, deployed anywhere
- Cloud Run deployment: Serverless scaling for variable quiz traffic
- State management: URL query parameters enable shareable quiz progress
- Retry logic: Configured exponential backoff for API resilience

## Contextual Explanation Adaptation
The explanation agent provides different educational value based on performance:

- Correct answers: Reinforces understanding with documentation references
- Incorrect answers: First shows human-written explanation, then AI provides additional context on why the wrong choice is tempting

This dual-layer approach combines curated content quality with AI flexibility.

# 🛠️ Technical Implementation

## Technology Stack

- Framework: Google ADK (Agent Development Kit)
- AI Agents: Gemini 2.5 Flash Lite (chosen for speed and cost-efficiency)
- Frontend: Streamlit (rapid prototyping with professional UI)
- Language: Python 3.11
- Deployment: Docker to Cloud Run (serverless, scalable)
- Data Storage: CSV (v1), designed for easy migration to Cloud SQL/Firestore

## Key Design Decisions
### Question Curation Over Generation
I used human-verified GCP questions rather than AI-generated content to ensure:

- Zero hallucination risk in question quality
- Consistent difficulty progression
- Accurate answer validation

### Asynchronous Agent Execution
I used `asyncio` with ADK's `run_debug` for non-blocking AI calls, maintaining responsive UX.

### Session State Management
I combined Streamlit session state and URL parameters enable:

- Resume-able quizzes
- Shareable progress links
- Browser refresh tolerance

# 📊 Demonstration of Capabilities
The live application showcases:

- Real-time hint generation with sub-3-second response times
- Context-aware explanations that cite official documentation
- Feedback loop closure with persistent hint quality tracking
- Graceful error handling with user-friendly fallback messages
- Progressive disclosure of assistance (hints optional, explanations configurable)  

You can easily deploy the application locally as well by following the instructions at the botton of this writeup, or to Cloud Run.

# 🚀 Future Enhancements
The following are considerations for the immediate roadmap.
## Agent Evaluation Pipeline
- Use collected hint feedback to build LLM-as-judge evaluation
- Establish baseline metrics for hint usefulness to be used as a rubric
- A/B test different hint generation strategies

## Database Migration
- Move from CSV to Cloud Firestore for real-time sync
- Enable multi-user progress tracking
- Build analytics dashboard for learning patterns

## Production Hardening
- Replace `run_debug` with production runners
- Implement rate limiting and quota management
- Add comprehensive error telemetry

## Advanced Capabilities
- Adaptive Difficulty: Agent analyzes performance to suggest focus areas
- Personalized Learning Paths: Multi-agent coordination to create custom study plans
- Collaborative Learning: Shared sessions with peer hint generation
- Multi-modal Hints: Architecture diagrams generated for visual learners

# 🎓 Why This Matters for AI Agents
QuAIzR demonstrates practical AI agent orchestration for education:  
✅ Specialised agents outperform generalists for cognitive tasks with different requirements  
✅ Human feedback loops are essential for quality assurance in educational AI  
✅ Tool selection matters: Search-enabled agents for factual accuracy, tool-free agents for speed  
✅ State management enables complex multi-turn interactions in stateless environments  
This is a starting blueprint for AI-assisted learning that respects pedagogical principles while leveraging LLM capabilities.

# 📦 Project Resources
Source Code: [GitHub Repository](https://github.com/minimice/quaizr)  
Docker Image: minimice/quaizr:0.0.1  
YouTube: [YouTube demo](https://www.youtube.com/watch?v=eq2Bi1C6Hno)  
Built by: Lim, Chooi Guan ([LinkedIn](https://linkedin.com/in/cgl88))


## Local deployment instructions

### Pre-requisites
You will require Docker to run the application as well as a Google API key.  

1. Clone the repository and change directory to `quaizr`.
2. Run `docker build -t local/quaizr-app:0.0.1 .` to build the image.
3. Run `docker run -p 80:80 -e GOOGLE_API_KEY="YOUR-GOOGLE-API-KEY" local/quaizr-app:0.0.1` to run the image.
4. Open your browser and navigate to [http://localhost](http://localhost)

## Cloud Run deployment instructions

### Pre-requisites
You will require Docker, a Docker hub user ID to push to Docker Hub, Google API key and a Google Cloud Platform account.  

1. Clone the repository and change directory to `quaizr`.
2. Run `docker build -t YOUR-DOCKER-USERID/quaizr-app:0.0.1 .` to build the image.
3. Run `docker push YOUR-DOCKER-USERID/quaizr-app:0.0.1` to push the image to Docker hub.
4. You can now deploy the image to Cloud Run by following [these instructions](https://docs.cloud.google.com/run/docs/deploying#gcloud_1).  Remember to set the GOOGLE_API_KEY environment variable!

## Making code changes
With your favourite code editor!

### Pre-requisites
You will require Python 3.11.14 (tested) and a code editor.

1. Clone the repository and change directory to `quaizr`.
2. Run `python -m nvenv venv` to create the virtual env.
3. Run `source ./venv/bin/activate` to activate the virtual env.
4. Run `pip install -r requirements.txt` to install the application requirements.
5. Make your code changes.
6. Run `streamlit run app.py` and browse to [localhost:8501](http://localhost:8501).
7. Test your changes, press Ctrl+C to stop the app.
8. Run `deactivate` to deactivate the virtual env.
9. Done!
