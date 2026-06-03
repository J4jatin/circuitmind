# ⚡ CircuitMind — AI-Powered EDA Design Automation

**🔗 Live API:** https://circuitmind.onrender.com/docs  
**🎛️ Dashboard:** https://circuitmind-eda.streamlit.app  
**📦 GitHub:** https://github.com/J4jatin/circuitmind

[![CI](https://github.com/jattinshah/circuitmind/actions/workflows/ci.yml/badge.svg)](https://github.com/jattinshah/circuitmind/actions)
[![Python](https://img.shields.io/badge/python-3.10%20|%203.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green)](https://fastapi.tiangolo.com)

An EDA (Electronic Design Automation) tool for analog circuit analysis, component generation, and AI-driven design optimization. Inspired by the **circuit generator** approach used in Fraunhofer IIS Mixed-Signal Automation research ([Intelligent IP](https://www.intelligent-ip.org)).

---

## 🎯 What It Does

| Feature                 | Description                                                                                                    |
| ----------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Circuit Analyzer**    | Computes cutoff frequency, time constant, impedance, phase shift, Q-factor, bandwidth for 6 circuit topologies |
| **Component Generator** | Given a target frequency spec, generates optimal **E24 standard** R/L/C values                                 |
| **AI Design Advisor**   | Claude API integration for natural-language design guidance; offline rule-based fallback                       |
| **Streamlit GUI**       | Interactive Bode plot visualization and design wizard                                                          |
| **FastAPI REST API**    | Production-ready API with Pydantic validation and OpenAPI docs                                                 |
| **CI/CD**               | GitHub Actions pipeline on Python 3.10 and 3.11                                                                |

---

## 🔌 Supported Circuit Topologies

- `rc_low_pass` — RC Low-Pass Filter
- `rc_high_pass` — RC High-Pass Filter
- `rl_low_pass` — RL Low-Pass Filter
- `rl_high_pass` — RL High-Pass Filter
- `rlc_band_pass` — RLC Band-Pass Filter
- `rlc_band_stop` — RLC Band-Stop (Notch) Filter

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the FastAPI backend
uvicorn app.main:app --reload
# → API docs at http://localhost:8000/docs

# Run the Streamlit GUI
streamlit run gui/dashboard.py
# → Dashboard at http://localhost:8501

# Run tests
pytest tests/ -v --cov=app
```

---

## 📡 API Endpoints

| Method | Endpoint         | Description                                    |
| ------ | ---------------- | ---------------------------------------------- |
| `GET`  | `/health`        | Health check                                   |
| `GET`  | `/circuit-types` | List all supported topologies                  |
| `POST` | `/analyze`       | Analyze circuit → cutoff freq, impedance, gain |
| `POST` | `/generate`      | Generate E24 component values from spec        |
| `POST` | `/advise`        | Get AI-powered design recommendations          |

### Example: Analyze a 1kHz RC Low-Pass Filter

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "circuit_type": "rc_low_pass",
    "resistance": 1000,
    "capacitance": 1e-6,
    "frequency": 1000
  }'
```

Response:

```json
{
  "circuit_type": "RC Low-Pass Filter",
  "cutoff_frequency_hz": 159.1549,
  "time_constant_s": 0.001,
  "gain_db": -15.9,
  "phase_shift_deg": -80.96,
  "summary": "RC Low-Pass: fc=159.15 Hz, τ=1.0000 ms. ..."
}
```

### Example: Generate Component Values

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "circuit_type": "rc_low_pass",
    "target_cutoff_frequency": 1000,
    "preferred_resistance": 10000
  }'
```

---

## 🧪 Test Suite

**29 tests** across 3 test files:

```
tests/
├── test_analyzer.py   # Mathematical correctness of all 6 topologies
├── test_generator.py  # E24 value selection, design accuracy
└── test_api.py        # FastAPI endpoint integration tests
```

Run:

```bash
pytest tests/ -v --tb=short --cov=app --cov-report=term-missing
```

---

## 🏗️ Project Structure

```
circuitmind/
├── app/
│   ├── main.py          # FastAPI app + route handlers
│   ├── models.py        # Pydantic schemas (CircuitParameters, AnalysisResult, ...)
│   ├── analyzer.py      # Circuit analysis algorithms (6 topologies)
│   ├── generator.py     # E24-standard component value generator
│   └── ai_advisor.py    # Claude API + rule-based design advisor
├── gui/
│   └── dashboard.py     # Streamlit interactive dashboard + Bode plots
├── tests/
│   ├── test_analyzer.py
│   ├── test_generator.py
│   └── test_api.py
├── .github/
│   └── workflows/ci.yml # CI on Python 3.10 + 3.11
└── requirements.txt
```

---

## 🤖 AI Advisor

Set your Anthropic API key to enable Claude-powered advice:

```bash
export ANTHROPIC_API_KEY=your_key_here
```

Without the key, the rule-based advisor activates automatically — covering tolerance warnings, parasitic effects, PCB layout tips, and component selection guidance.

---

## 🔗 Relevance to EDA Research

This project demonstrates core concepts from EDA automation research:

- **Circuit generators**: parameterized design templates that produce valid component values for given specs (analogous to Fraunhofer IIS Intelligent IP)
- **Design space exploration**: E24 value snapping simulates real-world component sourcing constraints
- **AI-assisted design**: LLM integration for natural-language diagnosis mirrors emerging AI-EDA workflows
- **API-first architecture**: clean REST interface enables integration with external CAD tools

---

## 👤 Author

**Jattin Shah** · MSc Applied Artificial Intelligence, TU Dresden  
jattinshahgli@gmail.com · [LinkedIn](https://linkedin.com) · [GitHub](https://github.com)
