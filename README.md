# ☀️ sunny-2

**Solar Generation Estimator** - Powered by Copernicus satellite data and Gemini 2.0 AI

> Estimate solar panel generation potential for any location worldwide using real satellite radiation data.

## 🌟 Features

- 🛰️ **Real satellite data** from Copernicus CAMS and PVGIS
- 🤖 **AI-powered insights** with Gemini 2.0 (climate, geography, recommendations)
- 🗺️ **Interactive map** with location search
- 📊 **Monthly breakdown** with seasonal analysis
- 💰 **Economic savings** with country-specific regulations
- 🌍 **CO₂ impact** environmental metrics
- ⏰ **Solar Clock** - Real-time orientation optimization

## 🏗️ Architecture

```
sunny-2/
├── apps/
│   ├── api/          # FastAPI backend (Python 3.12)
│   └── web/          # Next.js 14 frontend (TypeScript)
├── packages/         # Shared packages
└── _bmad/            # Project documentation
```

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development servers
npm run dev
```

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📡 Data Sources

| Source | Type | Coverage |
|--------|------|----------|
| PVGIS (JRC) | Historical TMY | Global |
| CAMS (Copernicus) | Real-time radiation | Global |
| ERA5-Land | Climate reanalysis | Global |

## 🔒 License

This project is licensed under the **Business Source License 1.1** (BSL-1.1).

- ✅ **Permitted**: Internal evaluation, testing, research, education, personal use
- ❌ **Restricted**: Commercial Solar Generation Estimation Services
- 📅 **Change Date**: December 30, 2028 → Apache 2.0

See [LICENSE](./LICENSE) for full terms.

© 2024-2025 Apply Digital. All Rights Reserved.

---

Built with ❤️ by Apply Digital

