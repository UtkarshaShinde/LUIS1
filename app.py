from flask import Flask, request, Response
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, ConversationState,MemoryStorage
from botbuilder.schema import Activity
import asyncio
#from luis.luisApp import LuisConnect
import os
from logger.logger import Log

from botbuilder.core import TurnContext,ActivityHandler
from botbuilder.ai.luis import LuisApplication,LuisPredictionOptions,LuisRecognizer
import json
from weather.weatherApp import WeatherInformation
from config.config_reader import ConfigReader
from logger.logger import Log
class LuisConnect(ActivityHandler):
    def __init__(self):
        self.config_reader = ConfigReader()
        self.configuration = self.config_reader.read_config()
        self.luis_app_id=self.configuration['LUIS_APP_ID']
        self.luis_endpoint_key = self.configuration['LUIS_ENDPOINT_KEY']
        self.luis_endpoint = self.configuration['LUIS_ENDPOINT']
        self.luis_app = LuisApplication(self.luis_app_id,self.luis_endpoint_key,self.luis_endpoint)
        self.luis_options = LuisPredictionOptions(include_all_intents=True,include_instance_data=True)
        self.luis_recognizer = LuisRecognizer(application=self.luis_app,prediction_options=self.luis_options,include_api_results=True)
        self.log=Log()
 

    async def on_message_activity(self,turn_context:TurnContext):
        weather_info=WeatherInformation()
        luis_result = await self.luis_recognizer.recognize(turn_context)
        result = luis_result.properties["luisResult"]
        json_str = json.loads((str(result.entities[0])).replace("'", "\""))
        weather=weather_info.get_weather_info(json_str.get('entity'))
        self.log.write_log(sessionID='session1',log_message="Bot Says: "+str(weather))
        await turn_context.send_activity(f"{weather}")

app = Flask(__name__)
loop = asyncio.get_event_loop()

bot_settings = BotFrameworkAdapterSettings("", "")
bot_adapter = BotFrameworkAdapter(bot_settings)

#CON_MEMORY = ConversationState(MemoryStorage())
luis_bot_dialog = LuisConnect()


@app.route("/api/messages", methods=["POST"])
def messages():
    if "application/json" in request.headers["content-type"]:
        log=Log()
        request_body = request.json
        user_says = Activity().deserialize(request_body)
        log.write_log(sessionID='session1',log_message="user says: "+str(user_says))
        authorization_header = (request.headers["Authorization"] if "Authorization" in request.headers else "")

        async def call_user_fun(turncontext):
            await luis_bot_dialog.on_turn(turncontext)

        task = loop.create_task(
            bot_adapter.process_activity(user_says, authorization_header, call_user_fun)
        )
        loop.run_until_complete(task)
        return ""
    else:
        return Response(status=406)  # status for Not Acceptable




if __name__ == '__main__':
    #app.run(port= 3978)
    app.run()