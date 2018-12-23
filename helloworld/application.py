from flask import Flask, request, Response
from datetime import date
from datetime import datetime
import boto3
import json
from boto3.dynamodb.conditions import Key, Attr
 
application = Flask(__name__)
 
@application.route('/', methods=['GET'])
def get():
    return Response(json.dumps({'Output': 'Hello World'}), mimetype='application/json', status=200)

@application.route('/', methods=['POST'])
def post():
    return Response(json.dumps({'Output': 'Hello World'}), mimetype='application/json', status=200)

@application.route('/heartbeat')
def heartbeat():
    # used in unit testing
    # responsible for heartbeating for ELB and target group
    return '', 200

def calculate_birthdate(birthdate, currentdate ):
    # can be used for unit testing
    delta = (birthdate - currentdate).days
    if delta < 0:
      delta = delta + 365
    return delta

@application.route('/hello/<user>', methods = ['GET', 'PUT']) 
def birthday_HT(user):
     if request.method == 'PUT':
         # put data to DynamoDB
         dynamodb = boto3.resource('dynamodb', region_name='eu-west-1', endpoint_url= 'http://localhost:8000')
         #dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
         table = dynamodb.Table('SRE')
         t = request.get_json (force=True)
         try: 
           birthday = t['dateOfBirth']
         except:
           birthday = ''
         if birthday:
           application.logger.debug (birthday)
           try:
             datetime.strptime (birthday, '%Y-%m-%d')
             table.put_item(
               Item={
                 'Name': user,
                 'Birthday': birthday,
               }
             )
             return '', 204
           except ValueError:
             return 'Birthday value is in the wrong format', 200
         else:
           return 'There is no the birthday value in the request', 200
     elif request.method == 'GET':
         # get data from DynamoDB
         birthday = ''
         try:
           dynamodb = boto3.resource('dynamodb', region_name='eu-west-1', endpoint_url='http://localhost:8000')
           #dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
           table = dynamodb.Table('SRE')
           response = table.query(
             KeyConditionExpression=Key('Name').eq(user)
           )
           if response:
             for i in response['Items']:
               try:
                 birthday = i['Birthday']
               except  Exception as e:
                 application.logger.debug ('User hasn''t got the birthday record')
           else:
             application.logger.debug ('User hasn''t been found in the table')
         except Exception as e:
            application.logger.debug ('Something went wrong')
         if birthday:
            # proceed with calculation
            d = datetime.strptime(birthday, '%Y-%m-%d').date()
            today = date.today()
            date_with_current_year = date (today.year, d.month, d.day )
            days = calculate_birthdate (date_with_current_year, today)
            if days == 0:
              res = '{{"message": "Hello {0}! Happy birthday!" }}'.format (user)
              res_json = Response(json.dumps(list ({'"message": "Hello {0}! Happy birthday!"'.format (user)})), mimetype='application/json', status=200)
            else:
              res = '{{"message": "Hello {0}! Your birthday is in {1} days" }}'.format (user, days)
              res_json = Response(json.dumps(list ({'"message": "Hello {0}! Your birthday is in {1} days"'.format (user, days)})), mimetype='application/json', status=200)
            return res_json, 200
         else:
           return 'User {0} has no birthday record'.format (user), 400
     else:
         return 'Wrong HTTP method!'
 
if __name__ == "__main__":
     application.run(host="0.0.0.0", port=80)
# set FLASK_DEBUG=1 
