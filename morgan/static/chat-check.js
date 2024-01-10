function check_chat_status() {
    // Create a new XMLHttpRequest object
    var xhr = new XMLHttpRequest();
    xhr.responseType = 'json';
    var is_pending = false;
  
    // Define the URL you want to fetch data from
    var url = "/chat-check-status";
  
    // Configure the AJAX request
    xhr.open("GET", url, true);
  
    // Set up a callback function to handle the response
    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4 && xhr.status === 200) {
        var responseData = xhr.response;
        document.getElementById('ai_thinking').innerText = responseData.msg; 
        if(responseData.status == 'completed') {
            window.location.href = '/chat';
        } else {
            setTimeout(check_chat_status, 2000);
        }
        console.log("Response data:", responseData);
      } else if (xhr.readyState === 4 && xhr.status !== 200) {
        // An error occurred during the request
        console.error("Error fetching data. Status code:", xhr.status);
      }
    };
  
    // Send the AJAX request
    xhr.send();
};

window.addEventListener("load", function() {
    check_chat_status();
});
  