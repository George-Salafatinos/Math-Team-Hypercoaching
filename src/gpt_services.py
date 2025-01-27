# src/gpt_services.py

def parse_topic_list_images(file_paths):
    """
    Stub function to parse the topic list images.
    file_paths: list of strings (paths to uploaded images)
    Returns a dict that categorizes topics by grade/subject.
    """
    # In reality, you'd call an OCR + GPT pipeline here and interpret the results.
    # For now, just return a fake dictionary with some sample topics.
    return {
        "Algebra": ["Factoring", "Linear Equations", "Inequalities"],
        "Geometry": ["Angles", "Triangles", "Circles"],
        "Algebra II": ["Quadratic Equations", "Polynomials", "Logarithms"],
        "Precalculus": ["Trigonometry", "Sequences and Series"]
    }


def parse_exam_images(file_paths, known_topic_list):
    """
    Stub function to parse exam questions from images, returning question->topic mapping.
    known_topic_list: the meet's existing topic list, if you want to reference it.
    """
    # For now, just return a fixed set of "exam questions" with topic tags.
    # The real version would analyze the images and figure out which topics apply.
    return [
        {"questionNumber": 1, "topics": ["Algebra - Factoring"]},
        {"questionNumber": 2, "topics": ["Algebra - Linear Equations"]},
        {"questionNumber": 3, "topics": ["Geometry - Triangles"]},
    ]


def parse_student_scores_images(file_paths, known_exam_data):
    """
    Stub function to parse student score sheets, returning participant info.
    known_exam_data: list of question->topic mappings from parse_exam_images.
    """
    # For now, just return some sample participants with points per topic
    return [
        {
            "studentName": "Alice",
            "gradeLevel": "freshman",
            "pointsPerTopic": {
                "Algebra - Factoring": 10,
                "Algebra - Linear Equations": 5,
                "Geometry - Triangles": 0
            }
        },
        {
            "studentName": "Bob",
            "gradeLevel": "sophomore",
            "pointsPerTopic": {
                "Algebra - Factoring": 8,
                "Algebra - Linear Equations": 10,
                "Geometry - Triangles": 10
            }
        }
    ]
