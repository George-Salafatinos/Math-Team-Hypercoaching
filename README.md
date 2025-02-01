# Math Team Analytics Dashboard

![Chart](images/chart_example.png)

This project is a web-based analytics dashboard for tracking the performance of a high school Math Team. The application processes data from various math competitions, including individual and team events, to provide detailed insights into topic mastery, participant performance, and overall team strengths. Specifically designed for WSML in Illinois.

## Features

1. **Meet and Event Management**
   - Create meets and add events (fixed types such as "Individual Algebra," "Frosh-Soph 2-Person," etc.)
   - Upload exam questions to parse topics using GPT
   - Add participant data manually or via GPT-parsed scores

2. **Individual and Team Events**
   - Handle individual events with participant-specific scores and topic tagging
   - Handle team events with a single set of scores for the team and participant rosters

3. **Dashboard Insights**
   - Main Chart: Topic accuracy across all meets and events
   - Event summaries (total correct answers, questions, participants)
   - Participant breakdowns with individual performance

4. **Event-Level Analytics**
   - Charts for topic accuracy specific to each event
   - Exam questions with parsed topics displayed clearly

5. **Modern UI**
   - Built with Flask, Bootstrap, and Chart.js for a clean and modern interface
   - Responsive design for usability across devices

## Cost Estimate

The GPT-powered parsing features use the OpenAI API, with an estimated cost of approximately $0.10 (10 cents) per meet.

## Setup Instructions

### Requirements
- Python 3.8 or higher
- Flask
- OpenAI API Key (for GPT-powered parsing)
- Node.js (optional for advanced frontend customization)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/math-team-dashboard.git
   cd math-team-dashboard
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file for your OpenAI API Key:
   ```bash
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

5. Run the app:
   ```bash
   flask run
   ```

6. Visit the app in your browser at [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Usage

### Workflow Overview

1. **Create Meets**  
   - Navigate to the home page and click "Add Meet"
   - Enter a title for the meet (e.g., "Fall Competition 2023")

2. **Add Events**  
   - Inside a meet, click "Add Event" and select from fixed event types:
     - Individual events: Algebra, Geometry, etc.
     - Team events: Frosh-Soph 2-Person, Calculator Team, etc.

3. **Upload Exam Questions**  
   - Upload photos of exam questions for GPT parsing
   - Topics are tagged to each question and stored for event analytics

4. **Add Participant Scores**  
   - For individual events, add participant names, grades, and correct/incorrect questions
   - For team events, enter a single set of team scores and add participants by name

5. **View Insights**  
   - Dashboard: View charts and tables summarizing topic accuracy, event performance, and participant breakdowns across all meets
   - Event Pages: View event-specific analytics, including topic charts and participant performance

## Data Structure

The application uses a nested data structure for local JSON storage:

```plaintext
store.json
└── meets
    ├── events
    │   ├── participants
    │   │   ├── studentName
    │   │   ├── gradeLevel
    │   │   ├── correctQuestions
    │   │   └── incorrectQuestions
    │   ├── teamCorrectQuestions (for team events)
    │   ├── teamIncorrectQuestions (for team events)
    │   └── examTopics
    └── topicList
```

## Key Features in Detail

### Exam Parsing
- Upload images of exam questions
- GPT parses questions into tagged topics, e.g.:
  ```json
  [
    {"questionNumber": 1, "topics": ["Geometry - Area of Rectangles", "Geometry - Volume"]},
    {"questionNumber": 2, "topics": ["Algebra - Factoring"]}
  ]
  ```

### Topic Accuracy
- Tracks correct and attempted answers for each topic across all events and participants
- Dashboard includes a main chart summarizing topic performance

### Team Event Support
- Single set of team scores per event
- Topic accuracy includes team data properly weighted

## Technology Stack

### Backend
- Flask (Python)
- OpenAI API for GPT-based parsing
- JSON-based local storage (no database required)

### Frontend
- Bootstrap for styling
- Chart.js for visualizations
- Responsive and modern UI

### APIs
- OpenAI GPT (4-mini) for:
  - Parsing exam topics
  - Scoring participant answers

## Future Enhancements
- Add user authentication for secure data management
- Export analytics as CSV or PDF
- Support custom event types or flexible topic lists

## Contributing
1. Fork the repository
2. Create a new branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit changes:
   ```bash
   git commit -m "Add new feature"
   ```
4. Push to the branch:
   ```bash
   git push origin feature-name
   ```
5. Open a pull request

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.