# Contributing to OpenClaw Dashboard

Thanks for your interest in contributing! 🦞

OpenClaw Dashboard is built to be **simple, fast, and useful** for personal AI agent observability. Contributions that align with these principles are always welcome.

---

## 🚀 Quick Start (Development)

### 1. **Clone & Setup**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry
pip install -r requirements.txt
```

### 2. **Run Locally**
```bash
python3 dashboard.py --port 8900
# Opens at http://localhost:8900
```

### 3. **Test Console Entry Point**
```bash
pip install -e .
clawmetry --help
```

### 4. **Make Changes & Test**
- Edit `dashboard.py` (single file architecture)
- Restart dashboard to see changes
- Test auto-detection: `cd /tmp && python3 /path/to/dashboard.py`

---

## 📁 Project Structure

```
clawmetry/
├── dashboard.py          # 🎯 Main application (single file)
├── README.md             # 📖 Documentation
├── setup.py              # 📦 Package configuration
├── requirements.txt      # 🔧 Dependencies
├── screenshots/          # 🖼️  UI screenshots
├── LICENSE               # ⚖️  MIT license
└── CONTRIBUTING.md       # 📝 This file
```

**Philosophy**: Keep it simple. The entire dashboard is one Python file (`dashboard.py`) with minimal dependencies. This makes it easy to understand, modify, and deploy.

---

## 🎯 Contribution Guidelines

### **What We're Looking For**
- 🐛 **Bug fixes** - especially around auto-detection, log parsing, or UI edge cases
- ✨ **Small features** - new visualizations, better error handling, performance improvements  
- 📖 **Documentation** - clearer setup instructions, troubleshooting guides
- 🎨 **UI polish** - better mobile support, dark theme, accessibility improvements
- 🧪 **Testing** - help us test on different OpenClaw setups

### **What to Avoid**
- ❌ **Complex dependencies** - no heavy frameworks, ML libraries, or databases
- ❌ **Breaking the single-file architecture** - keep everything in `dashboard.py`
- ❌ **Enterprise features** - this is for personal AI agents, not teams
- ❌ **Major architectural changes** - discuss large changes in Issues first

---

## 🛠️ Development Guidelines

### **Code Style**
- **Python 3.8+** compatible
- **PEP 8** formatting (but don't obsess)
- **Clear variable names** - readability over brevity
- **Comments for complex logic** - especially auto-detection and log parsing
- **No external formatting tools required** - just make it readable

### **Testing Your Changes**
Before submitting, test these scenarios:

1. **Auto-detection works**:
   ```bash
   cd /tmp
   python3 /path/to/dashboard.py --port 9999
   # Should find your OpenClaw workspace automatically
   ```

2. **CLI arguments work**:
   ```bash
   python3 dashboard.py --help
   python3 dashboard.py --workspace ~/myagent --port 8901
   ```

3. **Console entry point works** (after `pip install -e .`):
   ```bash
   clawmetry --version
   clawmetry --port 8902
   ```

4. **UI loads without errors**:
   - Visit all tabs (Overview, Usage, Sessions, etc.)
   - Check browser console for JS errors
   - Test with/without OpenClaw running

### **Adding New Features**

If you want to add a new tab or major feature:

1. **Open an Issue first** - describe what you want to build and why
2. **Keep it lightweight** - remember this is a single-file app
3. **Follow the existing pattern** - look at how other tabs are implemented
4. **Update the README** - document your new feature in the features table

---

## 📝 Pull Request Process

### **Before You Submit**
- [ ] Test auto-detection from different directories
- [ ] Verify console entry point still works
- [ ] Check that all tabs load without errors  
- [ ] Run dashboard with real OpenClaw logs
- [ ] Update README if you added features

### **PR Description Template**
```markdown
## What This PR Does
Brief description of the change.

## Testing
- [ ] Tested auto-detection: `cd /tmp && python3 dashboard.py`
- [ ] Tested console entry point: `clawmetry --help`
- [ ] Tested new feature with real OpenClaw data
- [ ] All tabs load without browser console errors

## Screenshots (if UI changes)
![Before/After or Demo GIF]
```

### **Review Process**
- PRs are usually reviewed within 48 hours
- Small fixes may be merged quickly  
- New features will get more thorough review
- We may ask for changes to keep things simple

---

## 🐛 Bug Reports

### **Good Bug Report Template**
```markdown
**What happened?**
Brief description.

**Steps to reproduce:**
1. Start dashboard with `clawmetry`
2. Click on Sessions tab
3. Error appears in browser console

**Environment:**
- OS: Linux/macOS/Windows
- Python version: `python3 --version` 
- OpenClaw version: X.X.X
- Dashboard version: `clawmetry --version`

**Logs/Screenshots:**
Paste relevant error messages or attach screenshots.
```

### **Where to Find Logs**
- **Dashboard errors**: Check terminal where you ran `dashboard.py`
- **Browser errors**: Check browser Developer Tools → Console  
- **OpenClaw logs**: Usually in `/tmp/moltbot/` or `/tmp/openclaw/`

---

## 💡 Feature Requests

Have an idea? Great! But first:

1. **Check existing Issues** - someone might have already suggested it
2. **Consider the scope** - would this benefit most personal AI agent users?
3. **Think about complexity** - can it be done without adding dependencies?

### **Good Feature Request Template**
```markdown
**Problem:**
What pain point does this solve?

**Proposed Solution:**
Brief description of what you want.

**Alternatives:**
Other ways this could be solved.

**Use Case:**
How would you personally use this feature?
```

---

## 📞 Questions?

- **General questions**: Open a GitHub Discussion
- **Bug reports**: Open a GitHub Issue  
- **Feature requests**: Open a GitHub Issue
- **Quick questions**: Find @vivekchand on Twitter/LinkedIn

---

## 🏆 Recognition

Contributors who help improve OpenClaw Dashboard will be:
- Added to a CONTRIBUTORS section in the README
- Mentioned in release notes for significant contributions
- Given credit in any blog posts or talks about the project

---

## 📄 License

By contributing to OpenClaw Dashboard, you agree that your contributions will be licensed under the same MIT License that covers the project.

---

**Thanks for making OpenClaw Dashboard better! 🦞**