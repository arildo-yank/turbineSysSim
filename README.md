This separation mirrors how real industrial systems are engineered:
- Physics is independent of UI
- Maintenance logic is explicit
- Diagnostics are first-class features

---

## User Interface

The application includes a **PyQt6-based industrial interface** with:
- Operator view (real-time parameters)
- Engineering view (performance curves)
- Maintenance view (degradation & recovery)
- Scenario simulation via sliders and presets

The UI is designed to resemble **control-room and engineering tools**, not academic demos.

---

## Intended Use

This simulator is intended for:
- Engineering reasoning and decision support
- Training and conceptual validation
- Demonstrating systems understanding
- Discussing operational trade-offs in interviews or technical reviews

It is **not intended for plant design, safety-critical decisions, or production control**.

---

## Technical Stack

- Python 3.10+
- NumPy / SciPy
- Pandas
- PyQt6
- Matplotlib / PyQtGraph

---

## Disclaimer

This project is:
- Independently developed
- Based solely on public-domain engineering principles
- Not affiliated with any manufacturer or OEM
- Not derived from proprietary documentation or models

All simulations are **educational and conceptual**.

---

## Author

Developed by an experienced industrial engineer with a background in:
- Power and energy systems
- Industrial machinery
- Field engineering and diagnostics
- Systems-level problem solving

---

## Future Roadmap

- Expanded fault-diagnosis logic
- Multi-stage turbine modeling
- Data-driven degradation fitting
- Scenario playback and reporting
- Exportable engineering reports

---

## License

This project is released for educational and professional demonstration purposes.