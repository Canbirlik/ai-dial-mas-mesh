# Multi-Agent System (MAS) Mesh with DIAL

A multi-agent application exploring how specialised agents can collaborate through a mesh-style architecture using the [DIAL platform](https://github.com/epam/ai-dial).

The workshop project brings together three specialised agents:

- **Calculations Agent** – performs calculations and creates charts using a calculator and Python code interpreter
- **Content Management Agent** – extracts content from uploaded files and performs RAG search
- **Web Search Agent** – searches the web and retrieves page content

The agents can call one another, allowing a request to be routed through multiple capabilities rather than handled by a single monolithic agent.

## Architecture

![MAS Mesh flow](flow.png)

## Learning context and attribution

This repository is my personal fork of the upstream workshop project: [khshanovskyi/ai-dial-mas-mesh](https://github.com/khshanovskyi/ai-dial-mas-mesh).

I used the workshop material to practise multi-agent orchestration, agent-to-agent tool integration, MCP-based services, document processing and RAG. This fork is maintained as a learning and portfolio project; the upstream repository remains the source for the original workshop structure and instructions. The fork's Git history shows changes made here.

## Technology

- Python
- EPAM DIAL / DIAL Core
- Docker Compose
- Multi-agent systems and agent-to-agent tool calls
- Model Context Protocol (MCP)
- Python code execution, web search and RAG

## Running locally

1. Install Docker and Docker Compose, and prepare a DIAL environment with model deployments you are authorised to use.
2. Create an untracked local `.env` file (it is ignored by Git) and set `NEXTAUTH_SECRET` and `DIAL_API_KEY` to values from your own environment. Never commit this file.
3. Review [core/config.json](core/config.json) and replace every `YOUR_DIAL_API_ENDPOINT`, `YOUR_DIAL_API_KEY` and `YOUR_PROJECT` placeholder with values from your own DIAL environment.
4. Review [settings/settings.json](settings/settings.json). Set strong, unique encryption values and configure authentication for your environment. Do not use the sample values in production.
5. Start the supporting services with `docker compose up`.
5. Implement or start the agent applications listed under `task/` according to the workshop exercises, then open the local DIAL Chat instance configured for your environment.

The application and model endpoints in the sample configuration are illustrative. Adapt ports, deployment names and service URLs to match your local setup.

## Security notes

- Never commit API keys, access tokens, passwords, private endpoints or production configuration.
- The configuration files contain placeholders; supply credentials locally and keep them out of Git.
- The `test` identity-provider configuration is for local experimentation only. Configure proper JWT verification and an appropriate identity provider before exposing the service.
- Use unique secrets for DIAL encryption and authentication. Do not reuse the example values.
- Review Docker port exposure and network access before running the stack on a shared or public network.

## Repository layout

- `core/` – DIAL Core application and model configuration
- `settings/` – DIAL Core settings
- `task/` – specialised agents, tools and application entry points
- `tests/` – sample files used to exercise agent workflows

## License and upstream

Please refer to the [upstream repository](https://github.com/khshanovskyi/ai-dial-mas-mesh) for the original workshop context and licensing information. This fork does not claim ownership of upstream material.
