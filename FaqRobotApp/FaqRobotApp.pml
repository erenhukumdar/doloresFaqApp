<?xml version="1.0" encoding="UTF-8" ?>
<Package name="FaqRobotApp" format_version="4">
    <Manifest src="manifest.xml" />
    <BehaviorDescriptions>
        <BehaviorDescription name="behavior" src="." xar="behavior.xar" />
    </BehaviorDescriptions>
    <Dialogs>
        <Dialog name="Faq" src="Faq/Faq.dlg" />
    </Dialogs>
    <Resources>
        <File name="main" src="main.py" />
        <File name="index" src="html/index.html" />
        <File name="main" src="html/main.js" />
        <File name="__init__" src="wit/__init__.py" />
        <File name="__init__" src="wit/__init__.pyc" />
        <File name="wit" src="wit/wit.py" />
        <File name="wit" src="wit/wit.pyc" />
        <File name="circular-countdown" src="html/circular-countdown.js" />
        <File name="qimessaging_helper" src="html/qimessaging_helper.js" />
        <File name="microphone" src="html/images/microphone.png" />
    </Resources>
    <Topics>
        <Topic name="Faq_enu" src="Faq/Faq_enu.top" topicName="Faq" language="en_US" />
    </Topics>
    <IgnoredPaths />
    <Translations auto-fill="en_US">
        <Translation name="translation_en_US" src="translations/translation_en_US.ts" language="en_US" />
    </Translations>
</Package>
