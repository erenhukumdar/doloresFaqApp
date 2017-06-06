session.subscribeToEvent("Faq/StartSpeak", function(value) {
    console.log("Event raised!")
    startSpeak();
});
session.subscribeToEvent("Faq/ResponseArrived", function(value) {
    console.log("Event raised!")
    showResponse(value);
});

function startSpeak() {

          console.log('event raised');
              // Run the countdown
          $('.timer').circularCountDown({
              delayToFadeIn: 500,
			  size: 350,
			  fontColor: '#fff',
			  colorCircle: 'white',
			  background: '#3d62c6',
              reverseLoading: false,
              duration: {
                  seconds: parseInt(10)
              },
              beforeStart: function() {
                  $('.launcher').hide();
              },
              end: function(countdown) {
                  countdown.destroy();
                  $('.launcher').show();
                  //session.raiseEvent("Faq/")
              }
          });
}
function startRecord() {

    session.raiseEvent("Faq/StartRecord",1);
    document.getElementById("testText").innerText="clicked";

}


function stopRecord() {

    session.raiseEvent("Faq/StopRecord",1);
    document.getElementById("testText").innerText="released";

}
function showResponse(response)
{
        document.getElementById("responseText").innerText=response;

}
