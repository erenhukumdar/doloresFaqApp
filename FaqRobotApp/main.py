#!/usr/bin/env python
import json
import sys

import requests
import cgi
import qi
import os
from customerquery import CustomerQuery


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
        self.memory = self.session.service('ALMemory')
        self.logger.info("Initializing...")
        # @TODO: insert init functions here
        self.create_signals()
        self.connect_to_preferences()
        self.logger.info("Initialized!")

    #     Special memory event to under stand ML operation status
        try:
            self.is_magic_link = self.memory.getData('Faq/MLStatus')
        except Exception, e:
            self.logger.error(e)
            self.is_magic_link = 0;

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
        self.cleanup()
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
            self.sm_timeout = int(self.preferences.getValue('faq', 'sm_timeout'))
            self.record_duration = self.preferences.getValue('faq', 'record_duration')
            self.surveyUrl = self.preferences.getValue('faq', 'survey_url')
            self.main_app_id = self.preferences.getValue('global_variables', 'main_app_id')
            self.feedback_app_id = self.preferences.getValue('global_variables', 'feedback_app_id')
            self.auth_launcher_id = self.preferences.getValue('global_variables', 'auth_launcher_id')
            self.faq_app_id = self.preferences.getValue('global_variables', 'faq_app_id')
            self.link="http://www.isbank.com.tr/TR/kobi/dis-ticaret/dis-ticaret-urunleri/doviz-havalesi/Sayfalar/doviz-havalesi.aspx"
        except Exception, e:
            self.logger.info("failed to get preferences".format(e))
        self.logger.info("Successfully connected to preferences system")

    @qi.nobind
    def create_signals(self):
        self.logger.info("Creating event realations for FAQ_App...")
        # When you can, prefer qi.Signals instead of ALMemory events
        memory = self.session.service("ALMemory")

        event_name = "Faq/StartSpeak"
        memory.declareEvent(event_name)
        event_subscriber = memory.subscriber(event_name)
        event_connection = event_subscriber.signal.connect(self.on_speech_faq_input)
        # event_connection = event_subscriber.signal.connect(self.on_speech_faq_input)
        self.subscriber_list.append([event_subscriber, event_connection])

        event_name = "Faq/LinkSend"
        memory.declareEvent(event_name)
        event_subscriber = memory.subscriber(event_name)
        event_connection = event_subscriber.signal.connect(self.on_magiclink_wanted)
        self.subscriber_list.append([event_subscriber, event_connection])

        event_name = "Faq/SurveyStart"
        memory.declareEvent(event_name)
        event_subscriber = memory.subscriber(event_name)
        event_connection = event_subscriber.signal.connect(self.on_survey_start)
        self.subscriber_list.append([event_subscriber, event_connection])

        event_name = "Faq/OpenMain"
        memory.declareEvent(event_name)
        event_subscriber = memory.subscriber(event_name)
        event_connection = event_subscriber.signal.connect(self.exit_app)
        self.subscriber_list.append([event_subscriber, event_connection])

        event_name = "Faq/OpenAuth"
        memory.declareEvent(event_name)
        event_subscriber = memory.subscriber(event_name)
        event_connection = event_subscriber.signal.connect(self.open_auth)
        self.subscriber_list.append([event_subscriber, event_connection])

        event_name = "Faq/MLQuestion"
        memory.declareEvent(event_name)
        event_subscriber = memory.subscriber(event_name)
        event_connection = event_subscriber.signal.connect(self.ml_question)
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
            if self.is_magic_link == 0:
                dialog.gotoTag("faqStart", "Faq")
            else:
                self.on_magiclink_wanted(1)
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
            answer = self.send_question_to_smartmoderation(value)
            memory = self.session.service("ALMemory")
            # self.logger.info('SM Answer is:'.format(answer['message']))
            if answer['message'] == 'Please write your request again.':
                self.logger.info('the ask again message has arrived')
                memory.raiseEvent("Faq/ReplyAndContinue", 'Please ask your question again.')
            else:
                memory.raiseEvent("Faq/ReplyAndContinue", answer['message'])

    @qi.bind(methodName="onExit", returnType=qi.Void)
    def on_exit(self, value):
        self.stop_app()

    @qi.bind(methodName="test", paramsType=(qi.String, ), returnType=qi.String)
    def send_question_to_smartmoderation(self, value):
        self.logger.info('Transfer started..')
        try:
            self.logger.info('input value is =' + value)
            value = self.escape_html(value)
            payload = {"question": value}
            self.logger.info('encoded' + value)
            response = requests.get(self.sm_url, params=payload)
            json_response = response.json()
            if response.status_code != 200 or 'Errors' in json_response:
                self.logger.error('magic link save request not completed or failed')
            else:
                self.logger.info(response.text)
                return response.json()
        except Exception, e:
            self.logger.info('Error while requesting result: {}'.format(e))
            self.memory.raiseEvent("Faq/Error", 1)
            return "oppss something happened"

    @qi.bind(methodName="onMagicLinkWanted", paramsType=(), returnType=qi.Void)
    def on_magiclink_wanted(self, value):
        self.logger.info('magic link wanted!')
#         for a while magic link service will be pushed only to db
        try:
            customer_info = CustomerQuery()
            customer_info.fromjson(self.memory.getData("Global/CurrentCustomer"))
            self.logger.info("customer no:" + customer_info.customer_number)
        except Exception, e:
            self.logger.error(e)
            customer_info = ''
        if customer_info != '':
            payload = json.dumps({'customerId': customer_info.customer_number, 'link': self.link})
            self.logger.info("request time" + str(payload))
            # response = requests.post(self.sm_url, data=payload, auth=(self.sm_basic_username, self.sm_basic_pass))
            # json_response = response.json()
            # if response.status_code != 200 or 'Errors' in json_response:
            #     self.logger.error('magic link save request not completed or failed')
            # else:
            self.memory.raiseEvent('Faq/MLSendSuccess', 1)
        else:
            self.memory.raiseEvent('Faq/MLNotAuth', 1)

    @qi.nobind
    def show_sm_link_on_tablet(self, link):
        self.logger.info("web view has been loaded")
        self.ts.loadUrl(self.link)

    @qi.nobind
    def on_survey_start(self, link):
        self.logger.info("survey has been started")
        autonomous_life = self.session.service('ALAutonomousLife')
        autonomous_life.switchFocus(self.feedback_app_id)

    @qi.nobind
    def exit_app(self, value):
        self.logger.info("exit has been started")
        self.cleanup()
        try:
            self.memory.removeData('Faq/MLStatus')
        except Exception, e:
            self.logger.error(e)
        autonomous_life = self.session.service('ALAutonomousLife')
        autonomous_life.switchFocus(self.main_app_id)
        self.stop_app()

    @qi.nobind
    def open_auth(self, value):
        self.logger.info("auth has been started")
        self.cleanup()
        self.memory.insertData('Global/RedirectingApp', self.faq_app_id)
        autonomous_life = self.session.service('ALAutonomousLife')
        autonomous_life.switchFocus(self.auth_launcher_id)
        # self.ts.loadUrl(self.surveyUrl)

    @qi.nobind
    def ml_question(self, value):
        self.logger.info('ml question:'+value)
        # which handles the ml question
        try:
            customer_info = CustomerQuery()
            customer_info.fromjson(self.memory.getData("Global/CurrentCustomer"))
            self.logger.info("customer no:" + customer_info.customer_number)
        except Exception, e:
            self.logger.error(e)
            customer_info = ''

        if customer_info != '':
            self.memory.raiseEvent('Faq/AuthNeed', 0)
            self.logger.info('auth not needed')

        else:
            self.memory.raiseEvent('Faq/AuthNeed', 1)
            self.logger.info('auth is needed')

        if value:
            self.logger.info("Get the input by event: {}".format(value))
            answer = self.send_question_to_smartmoderation(value)
            self.logger.info('SM Answer is:'.format(answer['message']))
            if answer['message'] == 'Please write your request again.':
                self.logger.info('the ask again message has arrived')
                self.memory.raiseEvent("Faq/RepliedWithML", 'Please ask your question again.')
            else:
                self.memory.raiseEvent("Faq/RepliedWithML", answer['message'])

    @qi.nobind
    def memory_cleanup(self):
        self.memory.removeData('Faq/MLStatus')

    @qi.nobind
    def make_unicode(self, value):

        value = value.decode("UTF-8")
        value = value.encode('ascii', 'ignore')
        self.logger.info('ascii encode=' + value)
        return value


    @qi.nobind
    def escape_html(self, text):
        """escape strings for display in HTML"""
        return cgi.escape(text, quote=True). \
            replace(u'\n', u'<br />'). \
            replace(u'\t', u'&emsp;'). \
            replace(u' ', u' &nbsp;')


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
