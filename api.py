from sql_conn import SqlConnection
from flask import Flask, jsonify, request, send_file, render_template, Blueprint
from flask.json import jsonify
from werkzeug.exceptions import HTTPException
import re
import traceback
import os
from flask_cors import CORS


def refine_jobs(jobs: list, regex: str):
    return list(filter(lambda j: not re.match(regex, j[1].lower()), jobs))

def create_app():
    app = Flask(__name__)
    CORS(app, origins=[os.environ.get('UI_HOST', '')])
    bp = Blueprint('api', __name__)

    @app.errorhandler(Exception)
    def handle_exception(e: Exception):
        if isinstance(e, HTTPException):
            return e
        print(e)
        if app.debug:
          traceback.print_exc()
        return  ("server error", 500)

    def process_re_filter(f):
        keywords = f.split('|')
        keywords = [k.strip().lower() for k in keywords]
        keywords = filter(lambda k: k!='', keywords)
        keywords = '|'.join(keywords)
        return f'%({keywords})%'


    @bp.route("/job_count", methods=['GET'])
    def job_count():
        query = "select count(*) from jobs where stale!= 1"
        with SqlConnection() as s:
            res = s.execute(query)
            count = res.fetchone()[0]
        return jsonify(count)



    @bp.route("/get_jobs", methods=['POST'])
    def get_jobs():
        data = request.get_json()
        companies = data.get('companies', '')
        companies = process_re_filter(companies)
        titles = data.get('titles', '')
        titles = process_re_filter(titles)
        locations = data.get('locations', '')
        locations = process_re_filter(locations)
        remote = data.get('remote', False)
        us_only = data.get('us', False)
        offset = data.get('page', 0) * 100
        query = f"""SELECT * FROM jobs
            WHERE lower(company_id) SIMILAR TO %s
            AND lower(title) SIMILAR TO %s
            AND lower(location) SIMILAR TO %s
            {'AND remote = 1' if remote else ''}
            {"AND country = 'US'" if us_only else ''}
            AND stale != 1
            ORDER BY published DESC
            NULLS LAST
            LIMIT 100
            OFFSET %s"""
        with SqlConnection() as s:
            res = s.execute(query, (companies, titles, locations, offset))
            jobs = res.fetchall()
        return jsonify(jobs)

    @bp.route("/",  methods=['GET'])
    def home():
        return jsonify("home")

    @bp.route("/ping",  methods=['GET'])
    def ping():
        return jsonify("pong")

    app.register_blueprint(bp, url_prefix='/api')
    return app

if __name__ == "__main__":
    create_app().run(host='0.0.0.0', port=8000, debug=True)

