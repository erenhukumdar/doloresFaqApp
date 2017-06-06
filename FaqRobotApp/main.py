#!/usr/bin/env python

import sys
import qi
import os
import requests
from wit import Wit
from requests.auth import HTTPBasicAuth
import uuid
import time


class FaqApp(object):
    subscriber_list = []
    loaded_topic = ""

    def __init__(self, application):
        # Getting a session that will be reused everywhere
        self.application = application
        self.session = application.session
        self.service_name = self.__class__.__name__

        # Getting a logger. Logs will be in /var/log/naoqi/servicemanager/{application id}.{service name}
        self.logger = qi.Logger(self.service_name)

        # Do some initializations before the service is registered to NAOqi
        self.logger.info("Initializing...")
        # @TODO: insert init functions here
        self.create_signals()
        self.audio = self.session.service('ALAudioDevice')
        self.audioFilePath = '/home/nao/recordings/audio/pepperSaid.ogg'
        self.connect_to_preferences()
        self.logger.info("Initialized!")

    @qi.nobind
    def start_app(self):
        # do something when the service starts
        print "Starting app..."
        # @TODO: insert whatever the app should do to start
        self.show_screen()
        self.start_dialog()
        self.logger.info("Started!")

    @qi.nobind
    def stop_app(self):
        # To be used if internal methods need to stop the service from inside.
        # external NAOqi scripts should use ALServiceManager.stopService if they need to stop it.
        self.logger.info("Stopping service...")
        self.application.stop()
        self.logger.info("Stopped!")

    @qi.nobind
    def cleanup(self):
        # called when your module is stopped
        self.logger.info("Cleaning...")
        # @TODO: insert cleaning functions here
        self.disconnect_signals()
        self.stop_dialog()
        self.hide_screen()
        self.logger.info("Cleaned!")
        try:
            self.audio.stopMicrophonesRecording()
        except Exception, e:
            self.logger.info("microphone already closed")

    @qi.nobind
    def connect_to_preferences(self):
        # connects to cloud preferences library and gets the initial prefs
        try:
            self.preferences = self.session.service("ALPreferenceManager")
            self.preferences.update()
            self.sm_url=self.preferences.getValue('faq', 'sm_url')
            self.logger.info(self.sm_url)
            self.sm_basic_username=self.preferences.getValue('faq', 'sm_basic_user_name')
            self.sm_basic_pass = self.preferences.getValue('faq', 'sm_basic_pass')
            self.record_duration = self.preferences.getValue('faq', 'record_duration')
        except Exception, e:
            self.logger.info("failed to get preferences".format(e))
        self.logger.info("Successfully connected to preferences system")

    @qi.nobind
    def create_signals(self):
        self.logger.info("Creating ColorChosen event...")
        # When you can, prefer qi.Signals instead of ALMemory events
        memory = self.session.service("ALMemory")

        event_name = "Faq/StartRecord"
        memory.declareEvent(event_name)
        event_subscriber = memory.subscriber(event_name)
        event_connection = event_subscriber.signal.connect(self.start_record)
        # event_connection = event_subscriber.signal.connect(self.on_speech_faq_input)
        self.subscriber_list.append([event_subscriber, event_connection])

        event_name = "Faq/StopRecord"
        memory.declareEvent(event_name)
        event_subscriber = memory.subscriber(event_name)
        event_connection = event_subscriber.signal.connect(self.stop_record)
        # event_connection = event_subscriber.signal.connect(self.on_speech_faq_input)
        self.subscriber_list.append([event_subscriber, event_connection])


        event_name = "Faq/LinkSend"
        memory.declareEvent(event_name)
        event_subscriber = memory.subscriber(event_name)
        event_connection = event_subscriber.signal.connect(self.on_magiclink_wanted)
        self.subscriber_list.append([event_subscriber, event_connection])

        self.logger.info("Event created!")

    @qi.nobind
    def disconnect_signals(self):
        self.logger.info("Unsubscribing to all events...")
        for sub, i in self.subscriber_list:
            try:
                sub.signal.disconnect(i)
            except Exception, e:
                self.logger.info("Error unsubscribing: {}".format(e))
        self.logger.info("Unsubscribe done!")

    @qi.nobind
    def start_dialog(self):
        self.logger.info("Loading dialog")
        dialog = self.session.service("ALDialog")
        dir_path = os.path.dirname(os.path.realpath(__file__))
        topic_path = os.path.realpath(os.path.join(dir_path, "Faq", "Faq_enu.top"))
        self.logger.info("File is: {}".format(topic_path))
        try:
            self.loaded_topic = dialog.loadTopic(topic_path)
            dialog.activateTopic(self.loaded_topic)
            dialog.subscribe(self.service_name)
            self.logger.info("Dialog loaded!")
            dialog.gotoTag("faqStart", "Faq")
            self.logger.info('tag has been located')
        except Exception, e:
            self.logger.info("Error while loading dialog: {}".format(e))

    @qi.nobind
    def stop_dialog(self):
        self.logger.info("Unloading dialog")
        try:
            dialog = self.session.service("ALDialog")
            dialog.unsubscribe(self.service_name)
            dialog.deactivateTopic(self.loaded_topic)
            dialog.unloadTopic(self.loaded_topic)
            self.logger.info("Dialog unloaded!")
        except Exception, e:
            self.logger.info("Error while unloading dialog: {}".format(e))

    @qi.nobind
    def show_screen(self):
        folder = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger.info("Loading tablet page for app: {}".format(folder))
        try:
            self.ts = self.session.service("ALTabletService")
            self.ts.loadApplication(folder)
            self.ts.showWebview()
            self.logger.info("Tablet loaded!")
        except Exception, e:
            self.logger.info("Error while loading tablet: {}".format(e))

    @qi.nobind
    def hide_screen(self):
        self.logger.info("Unloading tablet...")
        try:
            tablet = self.session.service("ALTabletService")
            tablet.hideWebview()
            self.logger.info("Tablet unloaded!")
        except Exception, e:
            self.logger.info("Error while unloading tablet: {}".format(e))

    @qi.bind(methodName="onSpeechFaqInput", paramsType=(qi.String,), returnType=qi.Void)
    def on_speech_faq_input(self, value):
        if value:
            self.logger.info("Get the input by event: {}".format(value))
            link = self.send_question_to_smartmoderation(value)
            self.show_sm_link_on_tablet(link)

    @qi.bind(methodName="onExit", returnType=qi.Void)
    def on_exit(self, value):
        self.stop_app()

    @qi.nobind
    def send_question_to_smartmoderation(self,value):
        self.logger.info('Transfer started..')
        try:
            response = requests.get(self.sm_url, auth=HTTPBasicAuth(self.sm_basic_username, self.sm_basic_pass))
            self.logger.info(response.text)
            data=response.json()
        except Exception, e:
            self.logger.info('Error while requesting result: {}'.format(e))
        return data['link']

    @qi.bind(methodName="onMagicLinkWanted", paramsType=(), returnType=qi.Void)
    def on_magiclink_wanted(self):
        self.logger.info('magic link wanted!')
#         for a while magic link service will be pushed only to db
#         @ToDo: magic link save service will be here.

    @qi.nobind
    def show_sm_link_on_tablet(self,link):
        self.logger.info("web view has been loaded")
        self.ts.loadUrl(link)

    @qi.nobind
    def send(request, response):
        print(response['text'])

    @qi.bind(methodName="startRecord", paramsType=(qi.String, ), returnType=qi.Void)
    def start_record(self,val):
        ba_service = self.session.service("ALBasicAwareness")
        motion_service = self.session.service("ALMotion")
        ba_service.setEnabled(False)
        # folder_path='/home/nao/recordings/audio/'
        # file_name=str(uuid.uuid4().hex)+'.ogg'
        # audioName=folder_path+file_name
        self.logger.info("Audio record has been started file path:".format(self.audioFilePath))
        self.audio.startMicrophonesRecording(self.audioFilePath)

    @qi.bind(methodName="stopRecord", paramsType=(qi.String,), returnType=qi.Void)
    def stop_record(self,val):
        actions = {
            'send': self.send,
        }
        try:
            self.audio.stopMicrophonesRecording()
            with open(self.audioFilePath, 'rb') as f:
                client = Wit(access_token="XPNLWXIPXA5ZYLTYCV7JELX6JZKPRQAL", actions=actions)
                resp = client.speech(f, None, {'Content-Type': 'audio/wav'})
            self.logger.info('Yay, got Wit.ai response: ' + str(resp))
            memory = self.session.service("ALMemory")
            memory.raiseEvent('Faq/ResponseArrived', resp["_text"])
        except Exception, e:
            self.logger.info("audio error".format(e))



        return str(resp)







if __name__ == "__main__":
    # with this you can run the script for tests on remote robots
    # run : python main.py --qi-url 123.123.123.123
    app = qi.Application(sys.argv)
    app.start()
    service_instance = FaqApp(app)
    service_id = app.session.registerService(service_instance.service_name, service_instance)
    service_instance.start_app()
    app.run()
    service_instance.cleanup()
    app.session.unregisterService(service_id)
