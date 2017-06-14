session.subscribeToEvent("Faq/StartSpeak", function (value) {
    console.log("Event raised!")
    startSpeak(value);
});
session.subscribeToEvent("Faq/Replied", function (value) {
    console.log("Event raised!")
    showResponse(value);
});
session.subscribeToEvent("Faq/StartSurvey", function (value) {
    console.log("Event raised!")
    showSurvey(value);
});
session.subscribeToEvent("Faq/Replied", function (value) {
    console.log("Event raised!")
    showResponse(value);
});

function startSpeak(value) {

    console.log('event raised');
    document.getElementById("question").innerText = value;
}



function showResponse(value) {
    document.getElementById("answer").innerText = value;

}
function sendResult(value) {

   if(value==1)
   {
       session.raiseEvent("Faq/SurveyYes", value);
   }
   else
   {
       session.raiseEvent("Faq/SurveyNo", value);
   }
}

function showSurvey(value)
{

document.getElementById("survey").style.display = 'block';
document.getElementById("faq").style.display='none';

}

