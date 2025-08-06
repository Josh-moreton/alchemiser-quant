# direnv Setup Guide

## What is direnv?

direnv automatically loads and unloads environment variables when you enter/exit the project directory. No more remembering to activate your virtual environment!

## Installation

### macOS (using Homebrew)
```bash
brew install direnv
```

### Ubuntu/Debian
```bash
apt install direnv
```

### Other systems
See: https://direnv.net/docs/installation.html

## Shell Configuration

Add this line to your shell configuration file:

### For zsh (~/.zshrc)
```bash
eval "$(direnv hook zsh)"
```

### For bash (~/.bashrc or ~/.bash_profile)
```bash
eval "$(direnv hook bash)"
```

### For fish (~/.config/fish/config.fish)
```bash
direnv hook fish | source
```

## Project Setup

1. **Copy the template**:
   ```bash
   cp .envrc.template .envrc
   ```

2. **Allow direnv to use the configuration**:
   ```bash
   direnv allow
   ```

3. **Test it works**:
   ```bash
   cd .. && cd the-alchemiser
   # You should see: "🔧 Environment activated for The Alchemiser"
   ```

## What it does

When you `cd` into the project directory, direnv will automatically:

- ✅ Activate the Python virtual environment (`.venv`)
- ✅ Set `PYTHONPATH` to include the project directories
- ✅ Configure testing environment variables
- ✅ Set up AWS credentials for testing (localstack/moto)
- ✅ Configure Poetry and development tools

## Customization

Edit `.envrc` to customize:

- Trading environment (`development`, `testing`, `staging`, `production`)
- Log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- API keys and credentials (for real trading environments)
- Custom Python paths
- Additional environment variables

## Security

- `.envrc` is git-ignored to prevent accidental credential commits
- Use `.envrc.template` for sharing configuration templates
- Never commit real API keys or secrets

## Troubleshooting

### direnv not working
```bash
# Check if direnv is installed
which direnv

# Check if shell hook is configured
grep "direnv hook" ~/.zshrc  # or ~/.bashrc

# Reload configuration
direnv reload
```

### Permission denied
```bash
# Allow the .envrc file
direnv allow
```

### Environment variables not loading
```bash
# Check direnv status
direnv status

# Check if .envrc has correct syntax
cat .envrc
```

## Testing the Setup

```bash
# Check environment is activated
echo $TRADING_ENV
which python
python -c "import sys; print('Project in path:', any('alchemiser' in p for p in sys.path))"

# Run tests to verify everything works
pytest tests/unit/ -v
```

## Benefits

- 🚀 **No more forgetting to activate virtualenv**
- 🔧 **Consistent development environment**
- 🧪 **Automatic testing configuration**
- 🔒 **Environment-specific settings**
- 👥 **Team-friendly with template**

Now you can focus on coding instead of environment management! 🎉
