"""
Contextual Insights API for BibleScholarProject

This API provides an endpoint to generate rich contextual insights for Bible verses, topics, or text snippets.
Features:
- Summaries
- Cross-references
- Theological term explanations
- Historical context
- Original language notes
- Related entities (people, places)

Version: 1.0.0
"""
from flask import Flask, Blueprint, request, jsonify
import logging
import json
import datetime
from src.dspy_programs.contextual_insights_program import generate_insights

app = Flask(__name__)
api_blueprint = Blueprint("contextual_insights", __name__, url_prefix="/api/contextual_insights")

logging.basicConfig(level=logging.INFO, handlers=[
    logging.FileHandler("logs/contextual_insights_api.log", encoding="utf-8"),
    logging.StreamHandler()
])
logger = logging.getLogger(__name__)

@api_blueprint.route("/insights", methods=["POST"])
def get_contextual_insights():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        input_type = data.get("type")
        if input_type not in ["verse", "topic", "text_snippet"]:
            return jsonify({"error": "Invalid input type: must be 'verse', 'topic', or 'text_snippet'"}), 400

        raw_reference = data.get("reference")
        translation = data.get("translation", "KJV")
        if not raw_reference:
            return jsonify({"error": "Missing required field: 'reference'"}), 400

        # Normalize reference only for verse type
        if input_type == "verse":
            from src.dspy_programs.contextual_insights_program import normalize_reference
            reference = normalize_reference(raw_reference)
        else:
            reference = raw_reference

        logger.info(f"Generating insights for {input_type}: {reference}")
        start_time = datetime.datetime.now()

        try:
            insights_result = generate_insights(input_type, reference, translation)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        # Ensure 'theological_terms' is a dict, even if empty
        if isinstance(insights_result, dict) and "theological_terms" in insights_result and isinstance(insights_result["theological_terms"], list):
            logger.warning("Correcting 'theological_terms' from list to dict.")
            insights_result["theological_terms"] = {}

        end_time = datetime.datetime.now()
        response = {
            "input": {
                "type": input_type,
                "reference": reference,
                "translation": translation
            },
            "insights": insights_result,
            "processing_time_seconds": (end_time - start_time).total_seconds()
        }
        logger.info("Response JSON:\n%s", json.dumps(response, indent=2, ensure_ascii=False))
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

@api_blueprint.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})

app.register_blueprint(api_blueprint)

if __name__ == "__main__":
    # Run on port 5002 by default to avoid conflicts with other servers
    app.run(host="0.0.0.0", port=5002, debug=True) 