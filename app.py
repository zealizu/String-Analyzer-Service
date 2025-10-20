from flask import Flask,request,jsonify, Response
import json
from flask_cors import CORS
import hashlib
from collections import Counter
from datetime import datetime, timezone
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()

apikey = os.environ["GEMINI_API_KEY"]

app= Flask(__name__)
CORS(app)

string_db=[]

import json
from flask import Response, jsonify

def filter_strings(string_db, filters):
    """
    Reusable filtering function for string data.

    Args:
        string_db (list): The list of string objects.
        filters (dict): A dictionary of filters that may include:
            {
                "is_palindrome": bool | str | None,
                "min_length": int | None,
                "max_length": int | None,
                "word_count": int | None,
                "contains_character": str | None
            }

    Returns:
        Flask Response: JSON response with filtered data and metadata.
    """
    try:
        is_palindrome = filters.get("is_palindrome")
        min_length = filters.get("min_length")
        max_length = filters.get("max_length")
        word_count = filters.get("word_count")
        contains_character = filters.get("contains_character")

        filtered = string_db

        # ✅ Validate and apply filters
        if is_palindrome is not None:
            # Convert string 'true'/'false' to actual booleans
            if isinstance(is_palindrome, str):
                if is_palindrome.lower() == "true":
                    is_palindrome = True
                elif is_palindrome.lower() == "false":
                    is_palindrome = False
                else:
                    raise ValueError("is_palindrome must be a boolean (true/false)")
            elif not isinstance(is_palindrome, bool):
                raise ValueError("is_palindrome must be a boolean (true/false)")

            filtered = [s for s in filtered if s["properties"]["is_palindrome"] == is_palindrome]

        if min_length is not None:
            try:
                min_length = int(min_length)
            except ValueError:
                raise ValueError("min_length must be an integer")
            filtered = [s for s in filtered if s["properties"]["length"] >= min_length]

        if max_length is not None:
            try:
                max_length = int(max_length)
            except ValueError:
                raise ValueError("max_length must be an integer")
            filtered = [s for s in filtered if s["properties"]["length"] <= max_length]

        if word_count is not None:
            try:
                word_count = int(word_count)
            except ValueError:
                raise ValueError("word_count must be an integer")
            filtered = [s for s in filtered if s["properties"]["word_count"] == word_count]

        if contains_character:
            if not isinstance(contains_character, str):
                raise ValueError("contains_character must be a string")
            filtered = [s for s in filtered if contains_character.lower() in s["value"].lower()]

        # ✅ Build result
        result = {
            "data": filtered,
            "count": len(filtered),
            "filters_applied": {
                "is_palindrome": is_palindrome,
                "min_length": min_length,
                "max_length": max_length,
                "word_count": word_count,
                "contains_character": contains_character,
            },
        }

        json_string = json.dumps(result, indent=2)
        return Response(json_string, mimetype="application/json"), 200

    except ValueError as e:
        return jsonify({"error": f"400 Bad Request: {str(e)}"}), 400
    except Exception as e:
        print("Unexpected Error:", str(e))
        return jsonify({"error": "400 Bad Request: Invalid query parameter values or types"}), 400

@app.route("/")
def home():
    return "Welcome to my string analyzer service".title()

@app.route("/strings", methods=["POST","GET"])
def analyze_string():
    if request.method == "POST":
        try:
            data:dict = request.get_json()
        except Exception:
            return jsonify(error="Invalid request body or missing 'value' field"),400
        
        text = data.get('value', '')
        if not isinstance(text, str):
            return jsonify(error="'value' must be a string."),422
        text= text.strip().lower()
        def check_palindrome(text:str):
            reversed_str = text[::-1]
            if text == reversed_str:
                return True
            else:
                return False
        for string in string_db:
            if text == string["value"]:
                return jsonify(error="String already exists in the system"),409
            
        result = {
        "id": hashlib.sha256(text.encode()).hexdigest(),
        "value": text,
        "properties": {
            "length": len(text),
            "is_palindrome": check_palindrome(text),
            "unique_characters": len(set(text.replace(" ", "").lower())),
            "word_count": len(text.split(" ")),
            "sha256_hash": hashlib.sha256(text.encode()).hexdigest(),
            "character_frequency_map": Counter(text.replace(" ", ""))
        },
        "created_at": (datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        string_db.append(result)
        json_string = json.dumps(result, indent=2)
        return Response(json_string, mimetype='application/json'),201
    elif request.method == "GET":
        allowed_params = {
            "is_palindrome",
            "min_length",
            "max_length",
            "word_count",
            "contains_character"
        }
        for param in request.args.keys():
            if param not in allowed_params:
                return jsonify({
                    "error": f"400 Bad Request: Unknown query parameter '{param}'"
                }), 400
        
        filters= {
            "is_palindrome": request.args.get("is_palindrome"),
            "min_length": request.args.get("min_length"),
            "max_length": request.args.get("max_length"),
            "word_count": request.args.get("word_count"),
            "contains_character": request.args.get("contains_character")
        }
        return filter_strings(string_db=string_db, filters=filters)
        

@app.route("/strings/<string_value>", methods=["GET", "DELETE"])
def get_specific_string(string_value):
    if request.method == "GET":
        for string in string_db:
            if string["value"] == string_value:
                return string
            
        return jsonify(error="String does not exist in the system"),404
    elif request.method == "DELETE":
        for i, s in enumerate(string_db):
            if s["value"] == string_value:
                string_db.pop(i)
                return jsonify(success="String deleted successfully"),204
        return jsonify(error=" String does not exist in the system"),404
    

@app.route("/strings/filter-by-natural-language", methods=["GET"])
def filter_by_nlp():
    query = request.args.get("query")
    for param in request.args.keys():
        if param != "query":
            return jsonify({
                        "error": f"400 Bad Request: Unknown query parameter '{param}'"
                    }), 400
    def convert_to_json(query):
        prompt_template = PromptTemplate(
            input_variables=["query"], 
            template="""
            You are a precise natural language to JSON converter.

            Given a user's query about strings, output only a JSON object that describes filter criteria.

            The JSON must always contain the following keys:
            "is_palindrome", "min_length", "max_length", "word_count", "contains_character"

            Rules:
            - If something isn't mentioned, set its value to null.
            - Do not include extra text or explanations.
            - Always return valid JSON only.

            Examples:

            Input: "all single word palindromic strings"
            Output:
            {{
            "is_palindrome": true,
            "min_length": null,
            "max_length": null,
            "word_count": 1,
            "contains_character": null
            }}

            Input: "strings longer than 10 characters"
            Output:
            {{
            "is_palindrome": null,
            "min_length": 11,
            "max_length": null,
            "word_count": null,
            "contains_character": null
            }}

            Input: "palindromic strings that contain the first vowel"
            Output:
            {{
            "is_palindrome": true,
            "min_length": null,
            "max_length": null,
            "word_count": null,
            "contains_character": "a"
            }}

            Input: "strings containing the letter z"
            Output:
            {{
            "is_palindrome": null,
            "min_length": null,
            "max_length": null,
            "word_count": null,
            "contains_character": "z"
            }}
            
            if the query does not in anyway relate to the output style just reply with 422

            Now convert the following query:

            "{query}" 
            """
        )
        llms= ChatGoogleGenerativeAI( model="gemini-2.0-flash",
            google_api_key=apikey,
            temperature=0.5,
            max_retries=3)
        
        chain = prompt_template | llms
        
        response = chain.invoke({"query":query})
        
        if response.content == "422":
            raise ValueError("Query parsed but resulted in conflicting filters")
        
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.strip("`").replace("json", "", 1).strip()
            data = json.loads(raw)
        return data
    try:
        data = convert_to_json(query)
        data_cleaned = { key: (None if value == "null" else value)
    for key, value in data.items()}
        return filter_strings(string_db=string_db, filters=data_cleaned)
    except ValueError as e:
        return jsonify(error=f"{e}"),422
    except Exception:
        return jsonify(error="Bad Request"),400

if __name__=="__main__":
    app.run(host='0.0.0.0', port=5000)