import sys, json, requests
from flask import Flask, request
import pyowm
import os
from datetime import datetime


try:
    import apiai
except ImportError:
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    )
    import apiai

app = Flask(__name__)

PAT = os.environ['PAGE_ACCESS_TOKEN']
CLIENT_ACCESS_TOKEN = os.environ['CLIENT_ACCESS_TOKEN']
VERIFY_TOKEN = os.environ['VERIFY_TOKEN']
OWM_KEY = os.environ['OWM_KEY']

ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)

@app.route('/', methods=['GET'])
def handle_verification():
    '''
    Verifies facebook webhook subscription
    Successful when verify_token is same as token sent by facebook app
    '''
    if (request.args.get('hub.verify_token', '') == VERIFY_TOKEN):
        print("succefully verified")
        return request.args.get('hub.challenge', '')
    else:
        print("Wrong verification token!")
        return "Wrong validation token"


@app.route('/', methods=['POST'])
def handle_message():
    '''
    Handle messages sent by facebook messenger to the applicaiton
    '''
    data = request.get_json()

    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    recipient_id = messaging_event["recipient"]["id"]
                    message_text = messaging_event["message"]["text"]
                    send_message_response(sender_id, parse_user_message(message_text))

    return "ok"


def send_message(sender_id, message_text):
    '''
    Sending response back to the user using facebook graph API
    '''
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",

        params={"access_token": PAT},

        headers={"Content-Type": "application/json"},

        data=json.dumps({
        "recipient": {"id": sender_id},
        "message": {"text": message_text}
    }))


def parse_user_message(user_text):
    '''
    Send the message to API AI which invokes an intent
    and sends the response accordingly
    The bot response is appened with weaher data fetched from
    open weather map client
    '''
    request = ai.text_request()
    request.query = user_text
    response = json.loads(request.getresponse().read().decode('utf-8'))
    responseStatus = response['status']['code']
    print('Response: \n ' + str(response))

    if (responseStatus == 200):
        print("API AI response", response['result']['fulfillment']['speech'])
        try:
            #Using open weather map client to fetch the weather report
            if 'geo-city' in response['result']['parameters']:
                input_city = response['result']['parameters']['geo-city']
                # print("City ", input_city)
                # owm = pyowm.OWM(OWM_KEY)  # You MUST provide a valid API key
                # forecast = owm.daily_forecast(input_city)
                # observation = owm.weather_at_place(input_city)
                # w = observation.get_weather()
                # print(w)
                # print(w.get_wind())
                # print(w.get_humidity())
                # max_temp = str(w.get_temperature('celsius')['temp_max'])
                # min_temp = str(w.get_temperature('celsius')['temp_min'])
                # current_temp = str(w.get_temperature('celsius')['temp'])
                # wind_speed = str(w.get_wind()['speed'])
                # humidity = str(w.get_humidity())
                # weather_report = ' max temp: ' + max_temp + ' min temp: ' + min_temp + ' current temp: ' + current_temp + ' wind speed :' + wind_speed + ' humidity ' + humidity + '%'
                # print("Weather report ", weather_report)

                r = requests.get("http://api.openweathermap.org/data/2.5/weather?q=" + input_city + "&appid=04e23b8bee0999c2ae5feb407bf67c70&units=imperial")
                name = r.json()['name']
                fahr = r.json()['main']['temp']
                weather = r.json()['weather'][0]['main']

                return (response['result']['fulfillment']['speech'] + " " + str(fahr) + " degrees and " + weather)

            if 'geo-country' in response['result']['parameters']:
                country = response['result']['parameters']['geo-country']
                endpoint = "https://restcountries.eu/rest/v2/name/" + country
                my_request = requests.get(endpoint)
                pop = my_request.json()[0]['population']
                return (response['result']['fulfillment']['speech'] + pop)
            else:
                return (response['result']['fulfillment']['speech'])

        except:
            return (response['result']['fulfillment']['speech'])
    else:
        return ("Sorry, I couldn't understand that question")



def send_message_response(sender_id, message_text):

    # sentenceDelimiter = ". "
    # messages = message_text.split(sentenceDelimiter)

    # for message in messages:
    send_message(sender_id, message_text)

if __name__ == '__main__':
    app.run()
