# Math Team Dashboard

This is a small web application for a high-school math team to track meet events, upload exam images, parse them with GPT for topics and scoring, and view overall dashboards. Specifically designed for WSML in Illinois.

## Features

- **Add Meets** and a **Topic List** (parsed by GPT)
- **Add Events** with a *fixed set* of event names
- **Upload** exam images and store them locally
- **Upload** single student score sheets, parse them via GPT to see which questions are correct/incorrect
- **Dashboard** with aggregated stats: topic accuracy, event summaries, participant breakdowns

## Quick Start

1. **Clone** the repo or copy these files

2. **Install** dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create** a `.env` file with your GPT/OpenAI key:
   ```
   OPENAI_API_KEY=sk-123yourKeyHere
   ```

4. Ensure you have a `data` folder with a `store.json`:
   ```json
   {
     "meets": []
   }
   ```

5. **Run** the app:
   ```bash
   python src/app.py
   ```

6. **Open** http://127.0.0.1:5000/ in your browser

## Project Structure

```
.
├── src/
│   ├── app.py
│   ├── data_manager.py
│   ├── gpt_services.py
│   ├── dashboard_logic.py
│   └── ...
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── add_meet.html
│   ├── create_event.html
│   ├── meet.html
│   ├── event.html
│   └── dashboard.html
├── static/
│   ├── styles.css
│   └── ...
├── data/
│   └── store.json
├── uploads/
│   ├── topic_list/
│   ├── exams/
│   └── scores/
├── requirements.txt
└── README.md
```

## Common Issues

- **GPT parse failures**: If the image is unclear or GPT times out, you might see partial results. We recommend re-uploading or improving prompt instructions.
- **Permissions**: Ensure your `uploads/` and `data/` folders are writable.
- **Large images**: If your images are huge, consider resizing before upload.

## Estimated Costs

This application uses the OpenAI API for parsing exams and score sheets. Based on typical usage:
- Approximately $0.10 per event (including exam and score sheet parsing)

For more details, see the inline docstrings in each file.