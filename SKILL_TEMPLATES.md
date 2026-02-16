# Skill Templates Library

## Overview

Reusable skill templates for OpenClaw agents. These templates capture proven automation patterns from real-world implementations. Choose a template, customize for your needs, and deploy quickly.

## Template Categories

### 🌐 API & CLI Integration
- **[Simple API Wrapper](skill-templates/simple-api-wrapper.md)** - Wrap external APIs (weather, news, status checks)
- **[CLI Tool Wrapper](skill-templates/cli-tool-wrapper.md)** - Automate command-line tools (gh, docker, kubectl)

### 🎥 Content & Media Creation
- **[Media Pipeline](skill-templates/media-pipeline.md)** - Multi-step content generation (video, audio, images)

### 📊 Dashboards & Visualization
- **[Dashboard Component](skill-templates/dashboard-component.md)** - Interactive dashboards with real-time data

### 🔄 Coming Soon
- **Social Media Automation** - Platform-specific content creation and posting
- **Data Collection Engine** - Web scraping, API monitoring, data aggregation  
- **Notification System** - Multi-channel alerts and messaging
- **Code Generation** - Template-based code and project scaffolding
- **Authentication Service** - OAuth, API key management, secure integrations

## Quick Start

1. **Choose a template** that matches your automation pattern
2. **Copy the template** to your skills directory
3. **Customize** the SKILL.md and scripts for your use case  
4. **Test locally** before integrating
5. **Document** any customizations for future reference

## Template Structure

All templates follow this standard structure:

```
skill-name/
├── SKILL.md           # Main documentation and usage
├── scripts/           # Executable automation scripts
│   ├── main.sh       # Primary entry point
│   └── helpers/      # Utility scripts
├── templates/        # Configuration/content templates
├── examples/         # Usage examples
└── README.md        # Quick reference for maintainers
```

## Best Practices

### Documentation
- ✅ Clear description in SKILL.md header
- ✅ Required dependencies and installation steps
- ✅ Working examples for all major use cases
- ✅ Troubleshooting section for common issues

### Implementation
- ✅ Idempotent operations (safe to run multiple times)
- ✅ Error handling with meaningful messages
- ✅ Configurable via environment variables
- ✅ Logging for debugging and audit trails

### Testing
- ✅ Dry-run mode for destructive operations
- ✅ Input validation before processing
- ✅ Fallback strategies for external dependencies
- ✅ Health checks for long-running processes

---

## Quick Template Selection

**I want to...**

- **Call an external API** → [Simple API Wrapper](skill-templates/simple-api-wrapper.md)
- **Automate a CLI tool** → [CLI Tool Wrapper](skill-templates/cli-tool-wrapper.md)
- **Generate videos/audio/images** → [Media Pipeline](skill-templates/media-pipeline.md)
- **Build a monitoring dashboard** → [Dashboard Component](skill-templates/dashboard-component.md)

## Real-World Examples

These templates are based on proven patterns from our production skills:

| Template | Real Implementation | Description |
|----------|-------------------|-------------|
| [Simple API Wrapper](skill-templates/simple-api-wrapper.md) | `weather`, `news-headlines` | Free APIs, JSON processing, error handling |
| [CLI Tool Wrapper](skill-templates/cli-tool-wrapper.md) | `github`, `docker-ops` | Command automation, JSON output parsing |
| [Media Pipeline](skill-templates/media-pipeline.md) | `video-reels`, `vedicvoice-instagram` | TTS, video assembly, quality validation |
| [Dashboard Component](skill-templates/dashboard-component.md) | `weather-dashboard`, `clawmetry` | Real-time monitoring, interactive charts |

## Template Usage

1. **Browse** available templates above
2. **Choose** the template that matches your automation pattern
3. **Copy** template to your skills directory: `cp skill-templates/TEMPLATE.md my-skills/my-service/SKILL.md`
4. **Follow** the customization checklist in the template
5. **Test** locally before deploying to production

Each template includes:
- ✅ Complete SKILL.md with working examples
- ✅ Production-ready script templates
- ✅ Configuration file templates (JSON, env vars)
- ✅ Step-by-step customization checklist
- ✅ Dependencies and installation guide
- ✅ Error handling and troubleshooting guide

---

## Contributing New Templates

Found a pattern worth sharing? Create a new template:

1. **Analyze** the automation pattern and identify reusable components
2. **Document** the SKILL.md with real working examples (not pseudocode)
3. **Include** configuration templates and helper scripts
4. **Add** comprehensive customization checklist
5. **Test** the template by building a new skill from it
6. **Submit** via pull request with examples

Focus on patterns that solve common automation challenges across multiple projects.
