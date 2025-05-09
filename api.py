import datetime
import time
from sql_conn import SqlConnection
from flask import Flask, jsonify, request, send_file, render_template, Blueprint
from flask.json import jsonify
from werkzeug.exceptions import HTTPException
import re
import traceback
import os
from flask_cors import CORS

PUBLISHED_ID = 6

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

    def get_recent_field(published: str):
        if not published or type(published) != str:
            return 'older'
        published = datetime.datetime.fromisoformat(published)
        now = datetime.datetime.now(datetime.timezone.utc)
        diff = now - published
        zero_td = datetime.timedelta(0)
        day_td = datetime.timedelta(days=1)
        week_td = datetime.timedelta(days=7)
        month_td = datetime.timedelta(days=30)
        if diff < zero_td:
            return ''
        elif diff < day_td:
            return 'today'
        elif diff < week_td:
            return 'this week'
        elif diff < month_td:
            return 'this month'
        else:
            return 'older'
        


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
        group_by_company = data.get('groupByCompany', False)        
        query = f"""SELECT 
                    jobs.id, 
                    jobs.title, 
                    jobs.location, 
                    jobs.company_id, 
                    jobs.salary, 
                    companies.name, 
                    jobs.published
                    {', MAX(published) OVER (PARTITION BY company_id)' if group_by_company else ''}
            FROM jobs left join companies ON jobs.company_id = companies.id
            WHERE 
                (lower(company_id) SIMILAR TO %s
                OR lower(companies.name) SIMILAR TO %s)
            AND lower(title) SIMILAR TO %s
            AND lower(location) SIMILAR TO %s
            {'AND remote = 1' if remote else ''}
            {"AND country = 'US'" if us_only else ''}
            AND jobs.stale != 1
            ORDER BY 
                {'max DESC NULLS LAST,  company_id, ' if group_by_company else ''}
                published DESC NULLS LAST
            LIMIT 100
            OFFSET %s"""
        with SqlConnection() as s:
            res = s.execute(query, (companies, companies, titles, locations, offset))
            jobs = res.fetchall()
        sub_published_tag = lambda job :  job[:PUBLISHED_ID] + (get_recent_field(job[PUBLISHED_ID]),)
        jobs = [sub_published_tag(job) for job in jobs]
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

