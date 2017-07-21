<?xml version="1.0" encoding="UTF-8" ?>
<Package name="FaqRobotApp" format_version="4">
    <Manifest src="manifest.xml" />
    <BehaviorDescriptions>
        <BehaviorDescription name="behavior" src="MLSend" xar="behavior.xar" />
        <BehaviorDescription name="behavior" src="faq_behave" xar="behavior.xar" />
    </BehaviorDescriptions>
    <Dialogs>
        <Dialog name="Faq" src="Faq/Faq.dlg" />
        <Dialog name="ML" src="ML/ML.dlg" />
    </Dialogs>
    <Resources>
        <File name="main" src="main.py" />
        <File name="index" src="html/index.html" />
        <File name="questionmark" src="html/images/questionmark.png" />
        <File name="swiftswords_ext" src="swiftswords_ext.mp3" />
        <File name="taichimove" src="taichimove.pmt" />
        <File name="ml" src="ml.py" />
        <File name="pepper" src="html/css/pepper.css" />
        <File name="jquery-2.1.4.min" src="html/js/jquery-2.1.4.min.js" />
        <File name="main" src="html/js/main.js" />
        <File name="qimessaging_helper" src="html/js/qimessaging_helper.js" />
        <File name="customerquery" src="customerquery.py" />
    </Resources>
    <Topics>
        <Topic name="Faq_enu" src="Faq/Faq_enu.top" topicName="Faq" language="en_US" />
        <Topic name="ML_enu" src="ML/ML_enu.top" topicName="" language="" />
    </Topics>
    <IgnoredPaths />
    <Translations auto-fill="en_US">
        <Translation name="translation_en_US" src="translations/translation_en_US.ts" language="en_US" />
    </Translations>
</Package>
