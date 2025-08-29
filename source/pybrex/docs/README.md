# PyBrex

PyBrex is a Python library for creating custom LibreOffice based applications using frames and dialogs.

## Requirements

1. **LibreOffice**
   - Download and install from [LibreOffice.org](https://www.libreoffice.org/download/)

2. **LibrePy**
   - A LibreOffice-based IDE for Python development
   - Contact Timothy Hoover (tim@timtech.io) to obtain the latest version of LibrePy

## Getting Started

The recommended way to develop PyBrex applications is using LibrePy IDE. After installing the prerequisites above:

1. **Get PyBrex**
   - Create a dedicated directory for PyBrex source code
   - Clone the repository: `git clone ssh://git@168.73.52.35:587/home/git/pybrex.git`
   - Always run `git pull` before starting a new project

2. **Create a LibrePy Project**
   - Create a new project in LibrePy IDE
   - Use 'Embedded project' option
   - Enable "Use the LibrePy executable"
   - Configure LibreOffice instance settings

3. **Copy PyBrex Files**
   ```bash
   # Replace {workspace} and {project} with your paths
   cp -r ~/Documents/pybrex_source/pybrex/source/* ~/{workspace}/{project}/source/
   ```

4. **Start Development**
   - Check the `examples` directory for implementation patterns
   - Follow the getting started guide in the `docs` directory

## Documentation

For detailed information, please refer to:
- Getting Started Guide: `docs/getting_started.md`
- Example Applications: `examples/`
- More Documentation: `docs/`

## License

[Insert your license information here]