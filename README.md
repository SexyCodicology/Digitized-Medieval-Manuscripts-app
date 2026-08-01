# 📚 Digitized Medieval Manuscripts App

> A curated, interactive directory of digitized medieval manuscript libraries worldwide with support for standardized image formats and open access resources.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Pages](https://img.shields.io/badge/Hosted%20on-GitHub%20Pages-green)](https://sexycodicology.github.io/Digitized-Medieval-Manuscripts-app/)
[![Build Status](https://github.com/SexyCodicology/Digitized-Medieval-Manuscripts-app/actions/workflows/deploy.yml/badge.svg)](https://github.com/SexyCodicology/Digitized-Medieval-Manuscripts-app/actions/workflows/deploy.yml)
[![JSON Schema Validation](https://img.shields.io/badge/Data%20Format-JSON%20Schema-blue)](./schema.json)

## What you can do

Use DMMapp (Digitized Medieval Manuscripts Application) to discover and access digitized medieval manuscript collections from around the world. Instead of visiting dozens of institutional websites, you can search a single directory that gives you:

- 🔍 Advanced filtering and search capabilities
- 🌍 Global coverage with location-based discovery
- 📋 Real-time statistics and insights
- ♿ Full accessibility support
- 🚀 Lightning-fast performance with no external dependencies

## Features

### Interactive dashboard
- **Real-time search**: Filter libraries instantly by name or city
- **Advanced filters**:
  - Filter by nation or country
  - Filter by standardized image format support (lets you access images the same way across different libraries)
  - Filter by open license (find freely reusable materials)
- **Live statistics**:
  - Total libraries in the database
  - Number of participating nations
  - Collections with standardized image format support
- **Responsive design**: Works on desktop, tablet, and mobile devices

### Detailed library information
Each library entry includes:
- **Library name and location**: Official institution name, city, and country
- **Website link**: Direct access to the digitized collection
- **Standardized image format support**: Badge indicating compatibility (lets you view and compare manuscripts consistently across libraries)
- **Open license**: Badge for freely reusable collections
- **Manuscript quantity**: Approximate number of digitized manuscripts (Few, Dozens, Hundreds, Thousands)

### Comprehensive documentation
- Getting started guide
- About the project and technology stack
- Contributing guidelines
- Information about standardized image formats

## Quick start

### For researchers
Visit the live dashboard to browse and search:
👉 [Digitized Medieval Manuscripts App](https://sexycodicology.github.io/Digitized-Medieval-Manuscripts-app/)

No installation required. Everything runs in your browser.

### For contributors
Clone the repository and set up your local environment:

```bash
git clone https://github.com/SexyCodicology/Digitized-Medieval-Manuscripts-app.git
cd Digitized-Medieval-Manuscripts-app
```

The dashboard is a MkDocs Material page, so you preview it the same way as the rest of the documentation. Install the dependencies from `requirements.txt`, then start the MkDocs development server:

```bash
pip install -r requirements.txt
mkdocs serve
```

Open `http://localhost:8000` in your browser to see the full dashboard.

## Project structure

```
Digitized-Medieval-Manuscripts-app/
├── mkdocs.yml              # Documentation and dashboard build settings
├── requirements.txt        # Python dependencies for MkDocs
├── schema.json             # Data format definition
├── overrides/
│   └── home.html           # Dashboard template (extends Material's main.html)
│
├── docs/                   # Documentation and dashboard source
│   ├── index.md            # Dashboard home page (uses the home.html template)
│   ├── about.md            # About the project
│   ├── getting-started.md  # How to use the dashboard
│   ├── schema.md            # Data structure guide
│   ├── update-data.md       # How to add or edit library entries
│   ├── contributing.md      # How to contribute code or docs
│   ├── setup.md             # Local development setup
│   └── assets/
│       ├── dashboard.js     # Dashboard interactivity
│       ├── dashboard.css    # Dashboard styling
│       └── data.json        # Library database
│
├── README.md               # This file
├── CONTRIBUTING.md         # Contribution guide
└── LICENSE                 # MIT License
```

## Technology stack

### Frontend dashboard
- **HTML5**: Semantic markup
- **CSS3**: Custom Material Design styling
- **Vanilla JavaScript**: No frameworks, pure web standards
- **Bootstrap Icons**: Accessible icons
- **Google Fonts (Roboto)**: Professional typography

### Documentation
- **MkDocs**: Static site generator
- **Material for MkDocs**: Responsive theme

### Data and validation
- **Data format**: Simple, portable database (uses a text-based format for easy editing)
- **Data validation**: Automated checks to ensure data quality
- **GitHub Actions**: Automatic testing and deployment

### Hosting and deployment
- **GitHub Pages**: Free, reliable hosting
- **GitHub Actions**: Automatic updates when you make changes

## Data schema

Each library entry in [docs/assets/data.json](./docs/assets/data.json) follows this structure:

```json
{
  "id": "Unique record identifier",
  "library": "Official institution name",
  "nation": "Country name",
  "city": "City name",
  "website": "URL to digitized collection",
  "copyright": "Copyright or license information",
  "quantity": "Few | Dozens | Hundreds | Thousands | Unknown",
  "iiif": "Supports standardized image format",
  "is_free_cultural_works_license": "Has open license",
  "is_part_of": "Whether the library is part of a larger project"
}
```

See [schema.json](./schema.json) for the complete definition.

## Contributing

You can help in several ways:

### Add libraries
1. **Search first**: Make sure the library isn't already listed in [docs/assets/data.json](./docs/assets/data.json)
2. **Edit the file**: Add your entry following the data format
3. **Submit a pull request**: Send it to the `master` branch

[See detailed contributing guide →](./CONTRIBUTING.md)

### Report issues
Found an error or have a suggestion?
[Open an issue](https://github.com/SexyCodicology/Digitized-Medieval-Manuscripts-app/issues)

### Improve the codebase
- Enhance the dashboard
- Improve documentation
- Suggest features
- Fix bugs

## About standardized image formats

Libraries that support standardized image formats (like IIIF) let you:
- **Search across multiple collections** simultaneously
- **View and compare manuscripts** side-by-side
- **Zoom, rotate, and annotate** images
- **Reuse collections** freely in your own projects

## Design principles

1. **Simplicity**: Clean, maintainable code and design
2. **Performance**: Fast loading with minimal dependencies
3. **Accessibility**: Works for all users, including those using assistive technology
4. **Consistency**: Unified design across all components
5. **Open source**: Transparent development, community-driven

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.

You're free to use, modify, and distribute this project with proper attribution.

## Support and questions

- **Documentation**: See the [docs/](./docs/) folder
- **Issues and discussions**: [GitHub Issues](https://github.com/SexyCodicology/Digitized-Medieval-Manuscripts-app/issues)
- **Contributing**: See [CONTRIBUTING.md](./CONTRIBUTING.md)
- **Code of Conduct**: See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)

## Related resources

- [Standardized image format information](https://iiif.io/)
- [MkDocs documentation](https://www.mkdocs.org/)
- [Data schema resources](https://json-schema.org/)
- [Material Design](https://material.io/)
- [GitHub Pages](https://pages.github.com/)

## Project statistics

- **Total libraries**: Check the dashboard for current count
- **Countries represented**: Explore the directory to discover
- **Collections with standardized image format support**: Use the filter to see available options
- **Last updated**: Check the GitHub commit history

## Roadmap

Future enhancements you might see:
- Geographic map view of libraries
- Advanced search with manuscript details
- Collections comparison tool
- User submissions and voting
- API for other applications
- Multi-language support

## Author

Created with ❤️ in the Netherlands

Want recognition? [Contribute today!](./CONTRIBUTING.md)

---

**Made with ❤️ for researchers, historians, and manuscript enthusiasts everywhere.**

[Visit the live dashboard](https://sexycodicology.github.io/Digitized-Medieval-Manuscripts-app/) | [View documentation](./docs/) | [Contribute](./CONTRIBUTING.md)
