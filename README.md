# Windows 98 Icons Search & Download 🖼️

A nostalgic Windows 95-styled React web application for searching and downloading Windows 98 icons with AI-powered semantic search using transformers.js running entirely in the browser.

## ✨ Features

- 🎨 **Authentic Windows 95 UI** - Built with react95 for pixel-perfect nostalgia
- 🧠 **AI-Powered Search** - Semantic vector search using transformers.js (runs entirely in browser!)
- 📦 **1700+ Icons** - Comprehensive collection of Windows 98 icons
- 💾 **Easy Downloads** - Download individual icons or select multiple
- 🚀 **Static Site** - No backend required, deploy anywhere
- 🔍 **Smart Search** - Find icons by describing what you're looking for
- ⚡ **Fast Performance** - ~4.5 embeddings/second processing speed

## 🚀 Quick Start

### Option 1: Master Build Script (Recommended)

```bash
# Clone and enter the project
git clone <your-repo>
cd windows_98_icons

# Run the complete build pipeline
uv run python build_complete_project.py
```

The script will guide you through building everything from scratch!

### Option 2: Manual Setup

**Prerequisites:**
- Python 3.8+ with uv package manager
- Node.js 18+ with bun package manager
- SQLite3 (usually pre-installed)
- OpenAI API Key (only for processing step)

```bash
# Install package managers
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -fsSL https://bun.sh/install | bash

# Set OpenAI API key for processing
export OPENAI_API_KEY="your-api-key-here"

# Run the complete pipeline
uv run python scraper.py                    # Scrape icons (~10 min)
uv run python process_icons.py              # Generate descriptions (requires OpenAI)
uv run python embed_single_process.py       # Create embeddings (~7 min)
bun install && bun run build                # Build React frontend

# Serve locally
bun run preview
```

## 🛠️ Project Architecture

```
windows_98_icons/
├── scraper.py                    # Scrapes icons from online sources
├── process_icons.py              # Generates AI descriptions with OpenAI
├── embed_single_process.py       # Creates vector embeddings with transformers.js
├── build_db.py                   # Builds SQLite database
├── build_complete_project.py     # Master build script
├── src/                          # React frontend source
│   ├── App.jsx                   # Main application
│   ├── components/               # React95 UI components
│   └── services/                 # Database and embedding services
├── static/                       # Static assets
│   ├── icons/                    # Downloaded icon files (.ico)
│   ├── icons.db                  # SQLite database with embeddings
│   └── icons_metadata.json       # Scraped metadata
└── dist/                         # Built frontend (deploy this)
```

### Pipeline Overview

1. **Icon Scraping** (`scraper.py`) - Downloads ~1700 Windows 98 icons
2. **AI Processing** (`process_icons.py`) - Generates descriptions using OpenAI Vision
3. **Embedding Generation** (`embed_single_process.py`) - Creates vectors using transformers.js
4. **Database Building** (`build_db.py`) - Combines everything into SQLite
5. **Frontend Build** (`bun run build`) - Compiles React app to static files

### Tech Stack

- **Frontend**: React + react95 + styled-components + Vite
- **AI**: transformers.js (Xenova/all-MiniLM-L6-v2) running in browser
- **Database**: SQLite with sql.js for browser loading
- **Styling**: Windows 95 authentic UI with pixel-perfect components

## Database Schema

```sql
-- Main icons table
CREATE TABLE icons (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    filename TEXT NOT NULL,
    description TEXT NOT NULL,
    width INTEGER,
    height INTEGER
);

-- Vector embeddings for semantic search
CREATE VIRTUAL TABLE icon_embeddings USING vec0(
    icon_id INTEGER PRIMARY KEY,
    embedding FLOAT[1536]
);

-- Full-text search for exact matches
CREATE VIRTUAL TABLE icons_fts USING fts5(
    name, description, searchable_text
);
```

## Search Types

1. **Semantic Search** - Vector similarity using OpenAI embeddings
2. **Text Search** - Full-text search on names and descriptions  
3. **Browse All** - Grid view of all icons with infinite scroll

## Development

### File Structure

```
windows_98_icons/
├── PRD.md                      # Product requirements
├── README.md                   # This file
├── pyproject.toml              # Python dependencies
├── scraper.py                  # Icon scraper script
├── process_icons.py            # AI description generator
├── build_db.py                 # Database builder
├── icons_metadata.json         # Scraped icon metadata
├── icons_processed.json        # AI-processed icons
└── static/                     # Deployable static site
    ├── index.html              # Main interface
    ├── app.js                  # Search logic
    ├── style.css               # Windows 98 theme
    ├── icons.db                # SQLite database
    └── icons/                  # Icon image files
```

### Adding New Icons

1. Add icon files to `static/icons/`
2. Update `icons_metadata.json` with new entries
3. Re-run `process_icons.py` and `build_db.py`

### Customizing the Interface

- Edit `static/style.css` for styling changes
- Modify `static/app.js` for search behavior
- Update `static/index.html` for layout changes

## Deployment

### Static Hosting

The `static/` directory can be deployed to any static hosting service:

- **GitHub Pages** - Enable GitHub Pages for the repository
- **Netlify** - Drag and drop the static folder
- **Vercel** - Connect repository and deploy
- **Nginx** - Copy static files to web root

## Performance

- **Database Size**: ~10-15MB total (includes all icons + embeddings)
- **Load Time**: < 3 seconds on Raspberry Pi
- **Search Speed**: < 100ms for most queries
- **Browser Support**: Modern browsers with WebAssembly support

## API Costs

Building the database requires OpenAI API calls:

- **Vision API**: ~$0.50 for 1700 icon descriptions
- **Embeddings API**: ~$0.10 for 1700 embeddings
- **Total**: ~$0.60 for complete database build

The database only needs to be built once and can be reused.

## Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY not set"**
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

2. **"sqlite-vec not found"**
   ```bash
   uv sync  # Reinstall dependencies
   ```

3. **"No icons found"**
   - Check that `scraper.py` completed successfully
   - Verify `static/icons/` directory has image files

4. **Database won't load in browser**
   - Serve files via HTTP (not file:// protocol)
   - Check browser console for errors
   - Ensure all static files are present

### Performance Issues

- Reduce database size by processing fewer icons
- Use smaller embedding model (text-embedding-3-small)
- Optimize images before processing

## License

MIT License - Feel free to use and modify!

## Contributing

1. Fork the repository
2. Make your changes
3. Test the complete pipeline
4. Submit a pull request

## Credits

- Icons from [Windows 98 UI](https://windows98-ui.netlify.app/)
- Vector search via [sqlite-vec](https://github.com/asg017/sqlite-vec)
- AI processing via OpenAI APIs